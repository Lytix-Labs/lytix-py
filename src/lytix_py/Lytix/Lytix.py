import asyncio
from collections import defaultdict
import contextvars
from functools import wraps
import logging
import time
from typing import Any, Callable, DefaultDict, List, TypeVar, cast
import uuid

from lytix_py.MetricCollector.MetricCollector import MetricCollector

"""
@see https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
"""
F = TypeVar("F", bound=Callable[..., Any])


_lytixTestContext: contextvars.ContextVar[DefaultDict[str, str]] = (
    contextvars.ContextVar(
        "lytixContext",
        default=defaultdict(
            lambda: {
                "traceId": None,
                "modelName": None,
                "modelInput": None,
                "modelOutput": None,
            },
        ),
    )
)

_lytixTraceContext: contextvars.ContextVar[DefaultDict[str, str]] = (
    contextvars.ContextVar(
        "lytixTraceContext",
        default=defaultdict(
            lambda: {
                "traceId": None,
                "modelName": None,
                "modelInput": None,
                "modelOutput": None,
                "userIdentifier": None,
                "sessionId": None,
            },
        ),
    )
)


class LytixWrapper:
    _logger = logging.getLogger("lytix")
    _testState = {}

    def trace(
        self,
        *kwargs,
        modelName: str,
    ) -> Callable[[F], F]:
        """
        Main trace decorator.
        @param modelName: Model name we are tracing
        """

        def decorator(func: F) -> F:
            """
            First lets see if this is an async function
            """
            isAsyncFunction = asyncio.iscoroutinefunction(func)

            """
            Wrap our function in a context state
            """
            if isAsyncFunction:
                return self._asyncTraceWrapper(func, modelName)
            else:
                return self._syncTraceWrapper(func, modelName)

        return decorator

    def test(
        self,
        *kwargs,
        testsToRun: List[str],
        _testSuiteId: str = None,
        _testName: str = None,
    ) -> Callable[[F], F]:
        """
        Main testing decorator.
        @param testGroupId: This is set when the test suite runs
        @param testName: This is set when the test suite runs
        """

        def decorator(func: F) -> F:
            """
            If we have any function args, it can't be a test
            """
            if kwargs:
                self._logger.error("Lytix tests cannot have function args")
            else:
                self._testState[func.__name__] = {
                    "function": func,
                    "testArgs": {"testsToRun": testsToRun},
                }

            """
            First lets see if this is an async function
            """
            isAsyncFunction = asyncio.iscoroutinefunction(func)

            """
            Wrap our function in a context state
            """
            if isAsyncFunction:
                return self._asyncTestWrapper(func, testsToRun, _testSuiteId, _testName)
            else:
                return self._syncTestWrapper(func, testsToRun, _testSuiteId, _testName)

        return decorator

    def _syncTraceWrapper(self, func: F, modelName: str):
        """
        Sync wrapper for the trace decorator
        """

        @wraps(func)
        def syncDecorator(*args, **kwargs):
            traceContext = self._prepTraceDecoratorContext(modelName)
            startTime = time.time()
            result = func(*args, **kwargs)
            responseTime = int(
                (time.time() - startTime) * 1000
            )  # Convert to milliseconds

            """
            If we have model IO set, send it to HQ
            """
            self.reportModelIO(responseTime, traceContext)

            return result

        return cast(F, syncDecorator)

    def _asyncTraceWrapper(self, func: F, modelName: str):
        """
        Async wrapper for the trace decorator
        """

        @wraps(func)
        async def asyncDecorator(*args, **kwargs):
            traceContext = self._prepTraceDecoratorContext(modelName)
            startTime = time.time()
            result = await func(*args, **kwargs)
            responseTime = int(
                (time.time() - startTime) * 1000
            )  # Convert to milliseconds

            """
            If we have model IO set, send it to HQ
            """
            self.reportModelIO(responseTime, traceContext)

            return result

        return cast(F, asyncDecorator)

    def reportModelIO(self, responseTime: int, traceContexT: dic):
        """
        Reports model input and output to HQ
        """

        context, valid = self._getTraceContext()
        if not valid:
            return

        modelInput = context["modelInput"]
        modelOutput = context["modelOutput"]
        modelName = context["modelName"]

        if modelInput is None or modelOutput is None or modelName is None:
            self._logger.error(
                "Missing modelInput, modelOutput, or modelName in context, make sure you have setup the correct decorator"
            )
            return

        """
        Pull optional fields now as well
        """
        userIdentifier = context["userIdentifier"]
        sessionId = context["sessionId"]

        """
        Send to HQ
        """
        MetricCollector.captureModelIO(
            modelName=modelName,
            modelInput=modelInput,
            modelOutput=modelOutput,
            userIdentifier=userIdentifier,
            sessionId=sessionId,
            modelResponseTime=responseTime,
        )

    def _syncTestWrapper(
        self, func: F, testsToRun: List[str], testSuiteId: str, testName: str
    ):
        """
        Sync wrapper for the decorator
        """

        @wraps(func)
        def syncDecorator(*args, **kwargs):
            testContext = self._prepTestDecoratorContext(testsToRun)
            func(*args, **kwargs)

            """
            Before returning to the user, send the test + IO back to HQ
            """
            testResult = self._startAndWaitForLytixTest(testSuiteId, testName)

            return testResult

        return cast(F, syncDecorator)

    def _asyncTestWrapper(
        self, func: F, testsToRun: List[str], testSuiteId: str, testName: str
    ):
        """
        Async wrapper for the decorator
        """

        @wraps(func)
        async def asyncDecorator(*args, **kwargs):
            testContext = self._prepTestDecoratorContext(testsToRun)
            await func(*args, **kwargs)

            """
            Before returning to the user, send the test + IO back to HQ
            """
            testResult = self._startAndWaitForLytixTest(testSuiteId, testName)

            return testResult

        return cast(F, asyncDecorator)

    def _startAndWaitForLytixTest(self, testSuiteId: str, testName: str):
        """
        Starts a new test in Lytix and waits for it to complete
        """
        context, valid = self._getTestContext()
        if not valid:
            return

        """
        Validate we have everything we need
        """
        input = context["modelInput"]
        output = context["modelOutput"]
        testsToRun = context["testsToRun"]
        traceId = context["traceId"]
        if input is None or output is None or testsToRun is None or traceId is None:
            self._logger.error(
                "Missing input, output, testsToRun, or traceId in context, make sure you have setup the correct decorator"
            )
            return False

        """
        Start the test
        """
        testRunIds = MetricCollector._kickoffTestRun(
            input, output, testsToRun, traceId, testSuiteId, testName
        )

        if testRunIds is False:
            return "FAILED"

        """
        Wait for it to finish
        """
        allFinished = False
        anyFailed = False
        while allFinished is False:
            allFinished = True
            """
            Loop over all testRunIds
            """
            for testRunId in testRunIds:
                testStatus = MetricCollector._getTestStatus(testRunId)
                if testStatus["testResult"] == "FAILED":
                    anyFailed = True
                if testStatus["testStatus"] not in ["FAILED", "SUCCESS"]:
                    allFinished = False
                    break

            if allFinished is False:
                time.sleep(5)

        """
        Result can be FAILED or SUCCESS, if it's FAILED
        """
        if anyFailed:
            return "FAILED"
        else:
            return "SUCCESS"

    def _prepTestDecoratorContext(self, testsToRun: List[str]) -> dict:
        """
        Prepares the decorator context
        """
        try:
            stack = _lytixTestContext.get().copy()
            stack["testsToRun"] = testsToRun
            stack["traceId"] = str(uuid.uuid4())
            _lytixTestContext.set(stack)

            return {"traceId": stack["traceId"]}
        except Exception as e:
            self._logger.error(f"Error setting up decorator context {e}")

    def _prepTraceDecoratorContext(self, modelName: str) -> dict:
        """
        Prepares the decorator context
        """
        try:
            stack = _lytixTraceContext.get().copy()
            stack["modelName"] = modelName
            stack["traceId"] = str(uuid.uuid4())
            _lytixTraceContext.set(stack)

            return {"traceId": stack["traceId"]}
        except Exception as e:
            self._logger.error(f"Error setting up trace decorator context {e}")

    def _getTestContext(self):
        """
        Gets the current context
        """
        existingContext = _lytixTestContext.get()
        if existingContext["traceId"] is None:
            self._logger.debug(
                "No traceId in context, make sure you have setup the correct decorator"
            )
            return {}, False
        return existingContext, True

    def _getTraceContext(self):
        """
        Gets the current context
        """
        existingContext = _lytixTraceContext.get()
        if existingContext["traceId"] is None:
            self._logger.debug(
                "No traceId in context, make sure you have setup the correct decorator"
            )
            return {}, False
        return existingContext, True

    def setOutput(self, modelOutput: str):
        """
        Sets model output in the current context
        """
        # Try to set on Test context
        context, valid = self._getTestContext()
        if valid:
            context["modelOutput"] = modelOutput
            _lytixTestContext.set(context)

        #  Then set on trace context
        context, valid = self._getTraceContext()
        if valid:
            context["modelOutput"] = modelOutput
            _lytixTraceContext.set(context)

    def setInput(self, modelInput: str):
        """
        Sets model input in the current context
        """
        # Try to set on Test context
        context, valid = self._getTestContext()
        if valid:
            context["modelInput"] = modelInput
            _lytixTestContext.set(context)

        #  Then set on trace context
        context, valid = self._getTraceContext()
        if valid:
            context["modelInput"] = modelInput
            _lytixTraceContext.set(context)

    def setUserIdentifier(self, userIdentifier: str):
        """
        Sets user identifier in the current context
        """
        context, valid = self._getTraceContext()
        if valid:
            context["userIdentifier"] = userIdentifier
            _lytixTraceContext.set(context)

    def setSessionId(self, sessionId: str):
        """
        Sets session id in the current context
        """
        context, valid = self._getTraceContext()
        if valid:
            context["sessionId"] = sessionId
            _lytixTraceContext.set(context)


lytix = LytixWrapper()

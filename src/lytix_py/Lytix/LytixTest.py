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
        "lytixTestContext",
        default=defaultdict(
            lambda: {
                "traceId": None,
                "modelName": None,
                "messages": None,
            },
        ),
    )
)


class LytixTestWrapper:
    _logger = logging.getLogger("lytix-test")
    _testState = {}

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
        messages = context["messages"]
        testsToRun = context["testsToRun"]
        traceId = context["traceId"]
        if messages is None or testsToRun is None or traceId is None:
            self._logger.error(
                "Missing input, output, testsToRun, or traceId in context, make sure you have setup the correct decorator"
            )
            return False

        """
        Start the test
        """
        testRunIds = MetricCollector._kickoffTestRun(
            messages, testsToRun, traceId, testSuiteId, testName
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
            stack["messages"] = []
            stack["modelName"] = None
            _lytixTestContext.set(stack)

            return {}
        except Exception as e:
            self._logger.error(f"Error setting up decorator context {e}")

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

    def setMessage(self, message: str, role: str):
        """
        Sets model input in the current context
        @param role: One of 'user', 'system', 'assistant'
        """
        messageToAdd = {"role": role, "content": message}

        # Try to set on Test context
        contextTest, validTest = self._getTestContext()
        if validTest:
            contextTest["messages"].append(messageToAdd)
            _lytixTestContext.set(contextTest)


lytixTest = LytixTestWrapper()

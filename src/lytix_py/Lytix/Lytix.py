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


_lytixTraceContext: contextvars.ContextVar[DefaultDict[str, str]] = (
    contextvars.ContextVar(
        "lytixTraceContext",
        default=defaultdict(
            lambda: {
                "traceId": None,
                "modelName": None,
                "messages": None,
                "userIdentifier": None,
                "sessionId": None,
            },
        ),
    )
)


class LytixWrapper:
    _logger = logging.getLogger("lytix")

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

    def reportModelIO(self, responseTime: int):
        """
        Reports model input and output to HQ
        """

        context, valid = self._getTraceContext()
        if not valid:
            return

        messages = context["messages"]
        modelName = context["modelName"]

        if messages is None or modelName is None:
            self._logger.error(
                "Missing messages or modelName in context, make sure you have setup the correct decorator"
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
            messages=messages,
            userIdentifier=userIdentifier,
            sessionId=sessionId,
            modelResponseTime=responseTime,
        )

    def _prepTraceDecoratorContext(self, modelName: str) -> dict:
        """
        Prepares the decorator context
        """
        try:
            stack = _lytixTraceContext.get().copy()
            stack["modelName"] = modelName
            stack["traceId"] = str(uuid.uuid4())
            stack["messages"] = []
            stack["userIdentifier"] = None
            stack["sessionId"] = None
            _lytixTraceContext.set(stack)
            return {}
        except Exception as e:
            self._logger.error(f"Error setting up trace decorator context {e}")

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

    def setMessage(self, message: str, role: str):
        """
        Sets model input in the current context
        @param role: One of 'user', 'system', 'assistant'
        """
        messageToAdd = {"role": role, "content": message}

        #  Set on trace context
        contextTrace, validTrace = self._getTraceContext()
        if validTrace:
            contextTrace["messages"].append(messageToAdd)
            _lytixTraceContext.set(contextTrace)

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

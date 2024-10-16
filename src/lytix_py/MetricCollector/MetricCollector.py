import datetime
from typing import Callable, List
import uuid
import requests
from urllib.parse import urljoin
import os.path
import time

from lytix_py.LAsyncStore.LAsyncStore import LAsyncStoreClass
from lytix_py.LLogger.LLogger import LLogger
from lytix_py.envVars import LytixCreds

"""
 Main class to collect and report metrics
 back to HQ
"""


class _MetricCollector:
    processing_metric_mutex: int = 0

    def __init__(self):
        self.processing_metric_mutex = 0

    def _get_base_url(self):
        return urljoin(LytixCreds.LX_BASE_URL, "/v2/metrics")

    def _get_base_test_url(self):
        return urljoin(LytixCreds.LX_BASE_URL, "/v2/test")

    def _sendPostRequest(self, endpoint: str, body: dict, url: str = None):
        """
        Interal wrapper to send a post request
        """
        if url is None:
            url = self._get_base_url()
        urlToUse = os.path.join(url, endpoint)
        headers = {
            "Content-Type": "application/json",
            "lx-api-key": LytixCreds.LX_API_KEY,
        }
        response = requests.post(urlToUse, headers=headers, json=body)
        if response.status_code != 200:
            print(
                f"Failed to send post request to {urlToUse} with status code {response.status_code} and response {response.text}"
            )

        return response

    def _sendGetRequest(self, endpoint: str, url: str = None):
        """
        Interal wrapper to send a get request
        """
        if url is None:
            url = self._get_base_url()
        urlToUse = os.path.join(url, endpoint)
        headers = {
            "Content-Type": "application/json",
            "lx-api-key": LytixCreds.LX_API_KEY,
        }
        response = requests.get(urlToUse, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to send get request to {urlToUse} with status code {response.status_code} and response {response.text}"
            )
        return response

    """
    Increment a given metric
    """

    def increment(
        self, metricName: str, metricValue: int = 1, metricMetadata: dict = None
    ):
        if LytixCreds.LX_API_KEY is None:
            return

        if metricMetadata is None:
            metricMetadata = {}
        body = {
            "metricName": metricName,
            "metricValue": metricValue,
            "metricMetadata": metricMetadata,
        }
        self._sendPostRequest("increment", body)

    """
    Capture a model input/output
    """

    def captureModelIO(
        self,
        modelName: str,
        messages: List[dict],
        metricMetadata: dict = None,
        userIdentifier=None,
        sessionId=None,
        logs: list[str] = [],
        modelResponseTime: int = None,
        backingModelId: str = None,
    ):
        if LytixCreds.LX_API_KEY is None:
            return

        if metricMetadata is None:
            metricMetadata = {}
        body = {
            "modelName": modelName,
            "messages": messages,
            "metricMetadata": metricMetadata,
            "userIdentifier": str(userIdentifier),
            "sessionId": str(sessionId),
            "logs": logs,
            "modelResponseTime": modelResponseTime,
            "backingModelId": backingModelId,
        }
        self._sendPostRequest("modelIO", body)

    """
    Capture a model io event while also capturing the time to respond
    """

    async def captureModelTrace(
        self,
        modelName: str,
        modelInput: str,
        callback: Callable[[LLogger], str],
        metricMetadata: dict = {},
        userIdentifier=None,
        sessionId=None,
    ):
        asyncStore = LAsyncStoreClass()
        logger = LLogger(
            f"lytix-{modelName}-trace-{uuid.uuid4()}", asyncStore=asyncStore
        )
        if LytixCreds.LX_API_KEY is None:
            print("No Lytix API key found, skipping metric collection")
            return await callback(logger)

        startTime = time.time()
        modelOutput = await callback(logger)
        try:
            responseTime = int(
                (time.time() - startTime) * 1000
            )  # Convert to milliseconds
            # Capture modelIO event along with the response time and any logs
            logs = logger.asyncStore.getLogs()
            self.captureModelIO(
                modelName,
                modelInput,
                modelOutput,
                metricMetadata,
                userIdentifier,
                sessionId,
                logs,
            )
            self.increment(
                "model.responseTime",
                responseTime,
                {"modelName": modelName}.update(metricMetadata),
            )
        except Exception as err:
            self.logger.error(
                f"Failed to capture model trace: {err}", err, modelName, modelInput
            )
        finally:
            return modelOutput

    """
    Capture a metric trace event
    @note You likeley never need to call this directly
    """

    # @deprecated use _captureLError
    def _captureMetricTrace(
        self,
        metricName: str,
        metricValue: int,
        metricMetadata: dict = {},
        logs: list = [],
    ):
        self.processing_metric_mutex += 1

        body = {
            "metricName": metricName,
            "metricValue": metricValue,
            "metricMetadata": metricMetadata,
            "logs": logs,
        }

        self._sendPostRequest("increment", body)

        self.processing_metric_mutex -= 1

    """
    Capture LError event (logs + metadata)
    """

    def _captureLError(self, errorMsg: str, errorMetadata: dict = {}, logs: list = []):
        self.processing_metric_mutex += 1

        body = {
            "errorName": errorMsg,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "metadata": errorMetadata,
            "logs": logs,
        }

        self._sendPostRequest("lerror", body)

        self.processing_metric_mutex -= 1

    def _kickoffTestRun(
        self,
        messages: List[dict],
        testsToRun: List[str],
        traceId: str,
        testSuiteId: str,
        functionName: str,
    ):
        """
        Kickoff a test run in Lytix and returns the testRunId if present
        """
        self.processing_metric_mutex += 1

        body = {
            "messages": messages,
            "testsToRun": testsToRun,
            "traceId": traceId,
            "testSuiteId": testSuiteId,
            "functionName": functionName,
        }

        response = self._sendPostRequest("ioTest", body, url=self._get_base_test_url())
        if response.status_code != 200:
            print(
                f"🚨 Failed to kickoff test run with status code {response.status_code} and response {response.text}"
            )
            return False

        jsonResponse = response.json()

        if jsonResponse.get("valid", False) is False:
            print(
                f"🚨 Failed to kickoff test run with status code {response.status_code} and response {response.text}"
            )
            return False

        self.processing_metric_mutex -= 1
        return jsonResponse["testRunIds"]

    def _getTestStatus(self, testRunId: str):
        """
        Get the status of a test run
        """
        response = self._sendGetRequest(
            f"testRun/{testRunId}", url=self._get_base_test_url()
        )
        return response.json()

    def _finalizeTestGroup(self, testSuiteId: str):
        """
        Finalize a test group
        """
        response = self._sendPostRequest(
            f"finalizeTest", {"testSuiteId": testSuiteId}, url=self._get_base_test_url()
        )
        return response.json()

    def _createTestSuite(self):
        """
        Create a test suite
        """
        response = self._sendGetRequest(f"testSuite", url=self._get_base_test_url())
        result = response.json()
        return result["testSuiteId"]

    def _captureRAGChunk(self, chunkData: str, ioEventId: str):
        """
        Capture a RAG chunk
        """
        body = {
            "chunkData": chunkData,
            "ioEventId": ioEventId,
        }
        self._sendPostRequest("ragChunk", body)


MetricCollector = _MetricCollector()

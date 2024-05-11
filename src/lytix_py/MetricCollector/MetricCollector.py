import requests
from urllib.parse import urljoin
from lytix_py.envVars import LX_API_KEY, LX_BASE_URL
import os.path
import time

"""
 Main class to collect and report metrics
 back to HQ
"""
class _MetricCollector:
    _apiKey: str = None
    _baseURL: str = None
    # _logger: str = None

    def __init__(self):
        self._apiKey = LX_API_KEY
        self._baseURL = urljoin(LX_BASE_URL, "/v1/metrics")
        pass


    """
    Interal wrapper to send a post request
    """
    def _sendPostRequest(self, endpoint: str, body: dict):
        url = os.path.join(self._baseURL, endpoint)
        headers = {
            "Content-Type": "application/json",
            "lx-api-key": self._apiKey,
        }
        response = requests.post(url, headers=headers, json=body)
        if (response.status_code != 200):
            print(f"Failed to send post request to {url} with status code {response.status_code} and response {response.text}")

    """
    Increment a given metric
    """
    def increment(self, metricName: str, metricValue: int = 1, metricMetadata: dict = None):
        if metricMetadata is None:
            metricMetadata = {}
        body = {
            "metricName": metricName,
            "metricValue": metricValue,
            "metadata": metricMetadata
        }
        self._sendPostRequest("increment", body)

    """
    Capture a model input/output
    """
    def captureModelIO(self, modelName: str, userInput: str, modelOutput: str, metricMetadata: dict = None):
        if metricMetadata is None:
            metricMetadata = {}
        body = {
            "modelName": modelName,
            "userInput": userInput,
            "modelOutput": modelOutput,
            "metricMetadata": metricMetadata
        }
        self._sendPostRequest("modelIO", body)

    """
    Capture a model io event while also capturing the time to respond
    """
    def captureModelTrace(self, modelName: str, userInput: str, callback, metricMetadata: dict = None):
        startTime = time.time()
        modelOutput = callback()
        try:
            responseTime = int((time.time() - startTime) * 1000)  # Convert to milliseconds
            # Capture modelIO event along with the response time
            self.captureModelIO(modelName, userInput, modelOutput, metricMetadata)
            self.increment("model.responseTime", responseTime, {"modelName": modelName})
        except Exception as err:
            self.logger.error(f"Failed to capture model trace: {err}", err, modelName, userInput)
            raise err
        finally:
            return modelOutput

MetricCollector = _MetricCollector()


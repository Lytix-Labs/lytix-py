import requests
from urllib.parse import urljoin
from lytix_py.envVars import LX_API_KEY, LX_BASE_URL
import os.path

"""
 Main class to collect and report metrics
 back to HQ
"""
class MetricCollector:
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

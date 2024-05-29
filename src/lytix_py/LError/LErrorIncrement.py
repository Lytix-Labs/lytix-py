from datetime import datetime
import json

from lytix_py.LAsyncStore.LAsyncStore import LAsyncStore
from lytix_py.MetricCollector.MetricCollector import MetricCollector


def LErrorIncrement(errorMsg: str, errorMetadata: dict = {}):
    try:
        """
        First get all logs from our async store
        """
        logs = LAsyncStore.getLogs()

        """
        Add a new log with our error
        """
        logs.append(json.dumps({
            "name": "LError",
            "hostname": "",
            "pid": -1,
            "level": 50,
            "msg": errorMsg,
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        }))

        """
        Send the logs+ metadata to lytix
        """
        errorMetadata["$no-index:errorMessage"] = errorMsg
        MetricCollector._captureMetricTrace(metricName="LError", metricValue=1, logs=logs, metricMetadata=errorMetadata)
    except Exception as e:
        print('Error sending Lytix metric', e)



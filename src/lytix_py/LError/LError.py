from datetime import datetime
import json
from lytix_py.LAsyncStore.LAsyncStore import LAsyncStore
from lytix_py.LLogger.LLogger import LLogger
from lytix_py.MetricCollector.MetricCollector import MetricCollector
import traceback


class LError(Exception):
    def __init__(self, message: str, errorMetadata: dict = {}):
        super().__init__(message)
        try:
            """
            First get all logs from our async store
            """
            logs = LAsyncStore.getLogs()

            """
            Add a new log with our error
            """
            error_trace = ''.join(traceback.format_stack())
            logs.append(json.dumps({
                "name": "LError",
                "hostname": "",
                "pid": -1,
                "level": 50,
                "msg": f'Error: {message}\n{error_trace}',
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            }))

            """
            Send the logs+ metadata to lytix
            """
            errorMetadata["$no-index:errorMessage"] = message
            MetricCollector._captureMetricTrace(metricName="LError", metricValue=1, logs=logs, metricMetadata=errorMetadata)
        except Exception as e:
            print('Error sending Lytix metric', e)
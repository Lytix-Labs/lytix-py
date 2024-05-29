import logging

from lytix_py.LAsyncStore.LAsyncStore import LAsyncStore

class LLoggerStreamWrapper(logging.StreamHandler):
    def emit(self, record):
        try:
            formatted = self.format(record)
            LAsyncStore.appendToLogs(formatted)
        except Exception as e:
            pass




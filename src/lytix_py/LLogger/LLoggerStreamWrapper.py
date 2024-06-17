import logging

from lytix_py.LAsyncStore.LAsyncStore import LAsyncStore, LAsyncStoreClass

class LLoggerStreamWrapper(logging.StreamHandler):
    customAsyncStore: LAsyncStoreClass  = None
    def __init__(self, customAsyncStore: LAsyncStoreClass = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if customAsyncStore:
            self.customAsyncStore = customAsyncStore

    def emit(self, record):
        try:
            formatted = self.format(record)
            if self.customAsyncStore:
                self.customAsyncStore.appendToLogs(formatted)
            else:
                LAsyncStore.appendToLogs(formatted)
        except Exception as e:
            pass




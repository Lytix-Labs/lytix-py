import asyncio
import logging
import socket
import sys
from typing import Mapping

from lytix_py.LAsyncStore.LAsyncStore import LAsyncStore, LAsyncStoreClass
from lytix_py.LLogger.LLoggerStreamWrapper import LLoggerStreamWrapper

class LLogger:
    metadata: dict = None

    """
    @param config: Optional dict of the following shape: { console: boolean }
    """
    def __init__(self, loggerName: str, metadata: dict = None, asyncStore: LAsyncStoreClass = None):
        self.logger = logging.getLogger(loggerName)
        if not len(self.logger.handlers):
            hostname = socket.gethostname()

            """
            Setup formatting and logging config
            """
            self.logger.setLevel('INFO')
            fmt = '{"time": "%(asctime)s.%(msecs)03d",  "hostname": "' + hostname + '",  "level": "%(levelname)s", "msg": "%(message)s",  "name": "%(name)s", "pid": "%(process)d"}'

            datefmt="%Y-%m-%d,%H:%M:%S"
            formatter = logging.Formatter(fmt, datefmt)
            handler = logging.StreamHandler(stream=sys.stdout)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            progress = LLoggerStreamWrapper(customAsyncStore=asyncStore)
            progress.setFormatter(formatter)
            self.logger.addHandler(progress)
        

        """
        Define our async store to store recent logs
        """
        if asyncStore:
            self.asyncStore = asyncStore
        else:
            self.asyncStore = LAsyncStore

        if (metadata): 
            self.metadata = metadata

    def info(self, msg: object):
        toLog = f'{self.getMetadataLoggerString()}{msg}'
        self.logger.info(toLog)

    def warn(self, msg: object):
        toLog = f'{self.getMetadataLoggerString()}{msg}'
        self.logger.warn(toLog)

    def error(self, msg: object):
        toLog = f'{self.getMetadataLoggerString()}{msg}'
        self.logger.error(toLog)

    def debug(self, msg: object):
        toLog = f'{self.getMetadataLoggerString()}{msg}'
        self.logger.debug(toLog)

    """
    Set metadata to be logged
    """
    def setMetadata(self, metadata: dict):
        self.metadata = metadata

    """
    Get a pretty printed version of the metadata stored to attach to a log
    """
    def getMetadataLoggerString(self):
        metadata = self.metadata
        if metadata and len(metadata) > 0:
            to_return = "["
            for key, value in metadata.items():
                to_return += f"{key}={value};"
            to_return = to_return[:-1]
            to_return += "] "
            return to_return
        return ""

    def runInAsyncContext(self, func):
        asyncio.run(func())


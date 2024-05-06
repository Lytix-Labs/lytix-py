import logging
import sys
from typing import Mapping

class LLLogger:
    def __init__(self, loggerName:str):
        self.logger = logging.getLogger(loggerName)

        self.logger.setLevel('INFO')
        fmt = '{"time": "%(asctime)s",  "hostname": "%(filename)s",  "level": "%(levelname)s", "msg": "%(message)s",  "name": "%(name)s", "pid": "%(process)d"}'
        fmt_date = '%Y-%m-%dT%T%Z'
        formatter = logging.Formatter(fmt, fmt_date)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def info(self, msg: object, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warn(self, msg: object, *args, **kwargs):
        self.logger.warn(msg, *args, **kwargs)

    def error(self, msg: object, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)


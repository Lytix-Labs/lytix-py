from lytix_py.LError import LErrorIncrement
from lytix_py.LLogger.LLogger import LLogger


async def backgroundProcess():
    logger = LLogger("background-logger", {"userId": "124"})
    logger.info("Some context on the user here")
    try:
        raise Exception("LIncrement error happened")
    except Exception as e:
        logger.error("LIncrement error happened")
        LErrorIncrement("Some error")


async def main():
    logger = LLogger("main-logger")
    logger.info("Starting in our main LIncrement process")
    await backgroundProcess()


if __name__ == "__main__":
    logger = LLogger("main")
    logger.runInAsyncContext(main)

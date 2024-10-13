from lytix_py import LErrorIncrement, LLogger


async def backgroundProcess():
    logger = LLogger("background-logger", {"userId": "124"})
    logger.info("Some context on the user here")
    try:
        raise Exception("LIncrement error happened")
    except Exception as e:
        logger.error("LIncrement error happened")
        LErrorIncrement("TEST_ERROR", {"userId": "124"})


async def main():
    logger = LLogger("main-logger")
    logger.info("Starting in our main LIncrement process")
    await backgroundProcess()


if __name__ == "__main__":
    logger = LLogger("main")
    logger.runInAsyncContext(main)

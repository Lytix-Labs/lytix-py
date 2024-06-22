from lytix_py import LError, LLogger


async def backgroundProcess():
    logger = LLogger("background-logger", {"userId": "124"})
    logger.info("Some context on the user here")
    raise LError("Some error")


async def main():
    logger = LLogger("main-logger")
    logger.info("Starting in our main process")
    await backgroundProcess()


if __name__ == "__main__":
    logger = LLogger("main")
    logger.runInAsyncContext(main)

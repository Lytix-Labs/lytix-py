from lytix_py import LLogger, LError


async def backgroundFastAPIProcess():
    logger = LLogger("background-fast-api-process")
    logger.info("In the background here")

    """
    All the logs associated with this request will get sent to lytix
    """
    raise LError("Some error")

from lytix_py import LError
from lytix_py.FastAPIMiddleware.MiddlewareState import getLytixContext
from lytix_py.LAsyncStore.LAsyncStore import LAsyncStore
from lytix_py.LLogger.LLogger import LLogger


async def backgroundFastAPIProcess(): 
    logger = LLogger("background-fast-api-process")
    logger.info("In the background here")

    """
    All the logs associated with this request will get sent to lytix
    """
    raise LError("Some error")

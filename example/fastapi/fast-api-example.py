from typing import Union

from fastapi import FastAPI
from backgroundProcess import backgroundFastAPIProcess

from lytix_py.FastAPIMiddleware.LytixMiddleware import LytixMiddleware
from lytix_py.LLogger.LLogger import LLogger

app = FastAPI()

app.add_middleware(LytixMiddleware)


@app.get("/")
async def read_root():
    logger = LLogger("read-root")
    logger.info('In the main view here...')
    await backgroundFastAPIProcess()
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
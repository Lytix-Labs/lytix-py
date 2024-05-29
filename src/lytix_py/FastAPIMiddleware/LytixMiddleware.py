from starlette.types import ASGIApp, Receive, Scope, Send

from lytix_py.LAsyncStore.LAsyncStore import LAsyncStore
from lytix_py.FastAPIMiddleware.MiddlewareState import lytix_ctx_var

class LytixMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        LAsyncStore.setHTTPMiddleware(True)

        lytixCtx = lytix_ctx_var.set({"logs": []})
        await self.app(scope, receive, send)
        lytix_ctx_var.reset(lytixCtx)
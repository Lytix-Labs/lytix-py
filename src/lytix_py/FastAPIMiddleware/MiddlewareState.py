
from contextvars import ContextVar

REQUEST_ID_CTX_KEY = "lytix-ctx-state"

lytix_ctx_var: ContextVar[str] = ContextVar(REQUEST_ID_CTX_KEY, default=None)

def getLytixContext() -> str:
    return lytix_ctx_var.get()

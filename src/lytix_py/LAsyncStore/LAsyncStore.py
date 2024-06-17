import contextvars

from lytix_py.FastAPIMiddleware.MiddlewareState import getLytixContext

class LAsyncStoreClass:
    httpMiddleware = False

    def __init__(self):
        self.lytix_context_store = contextvars.ContextVar('lytix-context-store', default={'logs': []})
        self.httpMiddleware = False

    """
    Set our context store
    """
    def setHTTPMiddleware(self, httpMiddleware: bool):
        self.httpMiddleware = httpMiddleware
    
    """
    Append logs to our context store, always only storing 20 of the last logs so 
    we don't OOM 
    """
    def appendToLogs(self, log):
        if (self.httpMiddleware):
            getLytixContext()['logs'].append(log)
            getLytixContext()['logs'] = getLytixContext()['logs'][:20]
        else:
            self.lytix_context_store.get()['logs'].append(log)
            self.lytix_context_store.get()['logs'] = self.lytix_context_store.get()['logs'][:20]

    """
    Get logs from our async store
    """
    def getLogs(self):
        if (self.httpMiddleware):
            return getLytixContext()['logs']
        else:
            return self.lytix_context_store.get()['logs']

LAsyncStore = LAsyncStoreClass()



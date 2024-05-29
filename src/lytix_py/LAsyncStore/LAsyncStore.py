import contextvars

class LAsyncStoreClass:
    def __init__(self):
        self.lytix_context_store = contextvars.ContextVar('lytix-context-store', default={'logs': []})
    
    """
    Append logs to our context store, always only storing 20 of the last logs so 
    we don't OOM 
    """
    def appendToLogs(self, log):
        self.lytix_context_store.get()['logs'].append(log)
        self.lytix_context_store.get()['logs'] = self.lytix_context_store.get()['logs'][:20]

    """
    Get logs from our async store
    """
    def getLogs(self):
        return self.lytix_context_store.get()['logs']

LAsyncStore = LAsyncStoreClass()



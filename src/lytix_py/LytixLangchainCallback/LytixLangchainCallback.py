from langchain_core.documents import Document
from langchain_core.outputs.llm_result import LLMResult
from typing import Any, Dict
from langchain.callbacks.base import BaseCallbackHandler

from lytix_py.MetricCollector import MetricCollector


class LytixLangchainCallback(BaseCallbackHandler):
    documentsInChain = []

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        try:
            lytixEventId = response.generations[0][0].message.response_metadata[
                "lytix-proxy-payload"
            ]["lytixEventId"]

            if lytixEventId is None:
                import warnings

                warnings.warn("No lytixEventId found")
                return

            if len(self.documentsInChain) > 0:
                for chunk in self.documentsInChain:
                    MetricCollector._captureRAGChunk(chunk.page_content, lytixEventId)
        except Exception as e:
            print("Error capturing RAG chunk", e)

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""
        if isinstance(outputs, list):
            """
            Check to make sure every item in the list is of type Document
            """
            allDocuments = True
            for output in outputs:
                if not isinstance(output, Document):
                    allDocuments = False
            if allDocuments:
                self.documentsInChain.extend(outputs)
                print("All items in the list are of type Document")
            else:
                print("Not all items in the list are of type Document")

import re

from rank_bm25 import BM25Okapi


class BM25Retriever:
    """
    BM25-based keyword retriever.

    Single responsibility: tokenize pre-chunked text, build a BM25
    index, and score queries against it. Does not load PDFs or
    perform chunking — those are injected as already-prepared chunks.
    """

    def __init__(self):
        self.chunks = []
        self.tokenized_chunks = []
        self.bm25 = None

    def _tokenize(self, text: str):
        return re.findall(r"[a-z]+-\d+|[a-z0-9]+", text.lower())

    def build_index(self, chunks: list[dict]):
        self.chunks = chunks
        self.tokenized_chunks = [
            self._tokenize(chunk["content"]) for chunk in self.chunks
        ]
        self.bm25 = BM25Okapi(self.tokenized_chunks)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if self.bm25 is None:
            raise RuntimeError(
                "BM25 index has not been built. Call build_index() first."
            )

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        ranked = [
            {"score": score, "document": self.chunks[index]}
            for index, score in enumerate(scores)
        ]
        ranked.sort(key=lambda item: item["score"], reverse=True)

        return ranked[:top_k]

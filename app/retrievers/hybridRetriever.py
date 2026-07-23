class HybridRetriever:
    """
    Hybrid document retriever.

    Responsibilities:
    - Execute BM25 retrieval.
    - Execute semantic retrieval.
    - Merge and re-rank retrieval results.
    """

    def search(self, query: str):
        """
        Perform hybrid document retrieval.

        Args:
            query (str):
                User search query.

        Returns:
            list:
                Ranked hybrid search results.

        Raises:
            NotImplementedError:
                Raised until the hybrid retrieval module
                is implemented.
        """

        raise NotImplementedError("HybridRetriever is not implemented yet.")

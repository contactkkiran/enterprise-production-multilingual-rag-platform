from app.orchestrator.retrieval_orchestrator import RetrievalOrchestrator
from app.retrievers.bm25_retriever import BM25Retriever
from app.retrievers.semantic_retriever import SemanticRetriever
from app.retrievers.hybridRetriever import HybridRetriever


class RAGService:
    """
    Retrieval-Augmented Generation (RAG) Service.

    Responsibilities:
    - Coordinate the retrieval workflow.
    - Delegate retrieval decisions to the Retrieval Orchestrator.
    - Execute the appropriate retriever.
    - Return the retrieved search results.
    """

    # Mapping between policy prefixes and document keywords.
    # Used to filter irrelevant search results after retrieval.
    POLICY_FILTERS = {
        "CAR": ("car", "vehicle", "motor"),
        "MED": ("health", "medical", "med"),
        "LIFE": ("life",),
        "HOME": ("home",),
        "TRAVEL": ("travel",),
    }

    def __init__(self):
        """Initialize all retrieval components."""

        # Responsible for selecting the retrieval strategy.
        self.orchestrator = RetrievalOrchestrator()

        # Initialize retrievers.
        self.bm25_retriever = BM25Retriever()
        self.semantic_retriever = SemanticRetriever()
        self.hybrid_retriever = HybridRetriever()

        # Build the BM25 index once during application startup.
        self.bm25_retriever.load_documents()
        self.bm25_retriever.build_index()

    def _filter_results_by_policy_prefix(
        self,
        query: str,
        results: list,
    ) -> list:
        """
        Filter search results using the policy prefix
        extracted from the user query.

        Example:
            Query : Does CAR-120 cover engine damage?

            Only documents related to Car Insurance
            should be returned.
        """

        # Extract policy prefix (CAR, MED, LIFE, etc.)
        policy_prefix = self.orchestrator.extract_policy_prefix(query)

        # Return all results when no policy identifier exists.
        if not policy_prefix:
            return results

        # Retrieve search keywords for the policy family.
        search_terms = self.POLICY_FILTERS.get(
            policy_prefix,
            (policy_prefix.lower(),),
        )

        filtered_results = []

        # Iterate through all retrieved documents.
        for result in results:

            document = result["document"]

            filename = document["filename"].lower()
            content = document["content"].lower()

            # Check whether the filename belongs to
            # the requested policy family.
            has_matching_filename = any(term in filename for term in search_terms)

            # Check whether the policy identifier exists
            # inside the document content.
            has_matching_policy_id = f"{policy_prefix.lower()}-" in content

            # Keep only matching documents.
            if has_matching_filename or has_matching_policy_id:
                filtered_results.append(result)

        return filtered_results

    def search(self, query: str):
        """
        Execute the retrieval workflow.

        Args:
            query:
                User search query.

        Returns:
            Retrieved search results.
        """

        # Ask the orchestrator to determine
        # the most appropriate retrieval strategy.
        strategy = self.orchestrator.determine_strategy(query)

        if strategy == "BM25":

            # Retrieve all candidate documents.
            results = self.bm25_retriever.search(
                query=query,
                top_k=len(self.bm25_retriever.documents),
            )

            # Remove documents unrelated to
            # the requested policy family.
            results = self._filter_results_by_policy_prefix(
                query,
                results,
            )

        elif strategy == "SEMANTIC":

            # Perform semantic similarity search.
            results = self.semantic_retriever.search(query)

        elif strategy == "HYBRID":

            # Perform Hybrid Retrieval
            # (BM25 + Semantic Search).
            results = self.hybrid_retriever.search(query)

        else:

            raise ValueError(f"Unsupported retrieval strategy: {strategy}")

        return results

    @staticmethod
    def display_results(
        query: str,
        results: list,
    ):
        """
        Display search results in a readable format.
        """

        print("=" * 80)
        print(f"Query : {query}")
        print("=" * 80)

        if not results:

            print("No matching documents found.")
            return

        # Display each retrieved document.
        for rank, result in enumerate(results, start=1):

            score = max(float(result["score"]), 0.0)

            print(f"Rank     : {rank}")
            print(f"Score    : {score:.2f}")
            print(f"Document : {result['document']['filename']}")

            print("=" * 80)
            print()


if __name__ == "__main__":

    # Initialize the RAG Service.
    rag_service = RAGService()

    # Sample user query.
    query = "Show policy MED-500"

    # Execute the retrieval workflow.
    results = rag_service.search(query)

    # Display retrieved results.
    rag_service.display_results(
        query=query,
        results=results,
    )

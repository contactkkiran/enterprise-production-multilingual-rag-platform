import os

from dotenv import load_dotenv

from app.ingestion.document_loader import PDFDocumentLoader
from app.ingestion.text_chunker import TextChunker
from app.orchestrator.retrieval_orchestrator import RetrievalOrchestrator
from app.retrievers.bm25_retriever import BM25Retriever
from app.retrievers.semantic_retriever import SemanticRetriever
from app.retrievers.hybridRetriever import HybridRetriever

# -------------------------------------------------------------------------
# Load environment variables from the .env file before any application
# components requiring configuration are initialized.
# -------------------------------------------------------------------------
load_dotenv()


class RAGService:
    """
    Retrieval-Augmented Generation (RAG) Service.

    Responsibilities
    ----------------
    - Compose all ingestion and retrieval components.
    - Load and preprocess the document corpus once during application startup.
    - Build both lexical (BM25) and semantic indexes from the same chunk set.
    - Delegate retrieval-strategy selection to the Retrieval Orchestrator.
    - Execute the selected retrieval strategy.
    - Apply business-specific post-processing filters.
    - Return ranked search results to the caller.

    Design Notes
    ------------
    - This class acts as the application's composition root.
    - Individual components remain focused on a single responsibility.
    - Business rules are intentionally kept outside the retrievers.
    """

    # ------------------------------------------------------------------
    # Standard chunking configuration used across the application.
    # These values ensure both lexical and semantic retrievers index
    # an identical chunk set.
    # ------------------------------------------------------------------
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    DEFAULT_TOP_K = 3

    # ------------------------------------------------------------------
    # Mapping between policy prefixes and searchable keywords.
    # Used during post-retrieval filtering to improve precision.
    # ------------------------------------------------------------------
    POLICY_FILTERS = {
        "CAR": ("car", "vehicle", "motor"),
        "MED": ("health", "medical", "med"),
        "LIFE": ("life",),
        "HOME": ("home",),
        "TRAVEL": ("travel",),
    }

    def __init__(self):
        """
        Initialize the RAG service.

        Startup activities:
        1. Resolve project paths.
        2. Instantiate ingestion components.
        3. Instantiate retrieval components.
        4. Load the document corpus.
        5. Chunk documents.
        6. Build both BM25 and Semantic indexes.

        Note:
        Index creation happens only once during application startup,
        avoiding repeated indexing for every user request.
        """

        # --------------------------------------------------------------
        # Resolve project-level directories.
        #
        # Current file:
        # app/services/rag_service.py
        #
        # Project root:
        # ../../../
        # --------------------------------------------------------------
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        data_folder_path = os.path.join(project_root, "data")
        chroma_persist_directory = os.path.join(project_root, "chroma_store")

        # --------------------------------------------------------------
        # Retrieval Orchestrator
        #
        # Responsible only for deciding which retrieval strategy
        # (BM25 / Semantic / Hybrid) should be executed.
        # --------------------------------------------------------------
        self.orchestrator = RetrievalOrchestrator()

        # --------------------------------------------------------------
        # Ingestion Components
        #
        # Responsible only for loading documents and splitting them
        # into reusable chunks.
        # --------------------------------------------------------------
        self.document_loader = PDFDocumentLoader(data_folder=data_folder_path)

        self.text_chunker = TextChunker(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
        )

        # --------------------------------------------------------------
        # Retrieval Components
        #
        # Each retriever owns its own indexing and searching logic.
        # No business rules are implemented inside the retrievers.
        # --------------------------------------------------------------
        self.bm25_retriever = BM25Retriever()

        self.semantic_retriever = SemanticRetriever(
            persist_directory=chroma_persist_directory,
        )

        self.hybrid_retriever = HybridRetriever()

        # --------------------------------------------------------------
        # Load documents once and create a single shared chunk set.
        #
        # Both BM25 and Semantic indexes are built from identical chunks
        # to ensure retrieval consistency across strategies.
        # --------------------------------------------------------------
        documents = self.document_loader.load()

        chunks = self.text_chunker.chunk_documents(documents)

        self.bm25_retriever.build_index(chunks)

        self.semantic_retriever.build_index(chunks)

    def _filter_results_by_policy_id(self, query: str, results: list) -> list:
        """
        Filter retrieved results using an exact policy identifier.

        Example:
            MED-500

        Only chunks containing the exact policy ID are returned.
        """

        policy_id = self.orchestrator.extract_policy_id(query)

        if not policy_id:
            return results

        policy_id = policy_id.lower()

        return [
            result
            for result in results
            if policy_id in result["document"]["content"].lower()
        ]

    def _filter_results_by_policy_prefix(self, query: str, results: list) -> list:
        """
        Filter retrieved results using the extracted policy prefix.

        Example:
            CAR
            MED
            HOME

        Since retrieval operates at chunk level, filename matching is
        generally more reliable than searching for a policy ID inside
        every individual chunk.
        """

        policy_prefix = self.orchestrator.extract_policy_prefix(query)

        if not policy_prefix:
            return results

        search_terms = self.POLICY_FILTERS.get(
            policy_prefix,
            (policy_prefix.lower(),),
        )

        filtered_results = []

        for result in results:

            document = result["document"]

            filename = document["filename"].lower()
            content = document["content"].lower()

            has_matching_filename = any(term in filename for term in search_terms)

            # ----------------------------------------------------------
            # Chunks represent only a portion of the original document.
            #
            # A policy ID appearing once in the source PDF may not be
            # present in every chunk.
            #
            # Therefore, filename matching is considered a stronger
            # signal after chunking.
            # ----------------------------------------------------------
            has_matching_policy_id = f"{policy_prefix.lower()}-" in content

            if has_matching_filename or has_matching_policy_id:
                filtered_results.append(result)

        return filtered_results

    def search(self, query: str):
        """
        Execute the retrieval workflow.

        Workflow:
        ----------
        1. Determine retrieval strategy.
        2. Execute the selected retriever.
        3. Apply business filters (where applicable).
        4. Return ranked search results.
        """

        # Determine the most appropriate retrieval strategy.
        strategy = self.orchestrator.determine_strategy(query)

        if strategy == "BM25":

            # Retrieve all candidate chunks.
            results = self.bm25_retriever.search(
                query=query,
                top_k=len(self.bm25_retriever.chunks),
            )

            # Apply exact policy matching if available.
            exact_results = self._filter_results_by_policy_id(query, results)

            if self.orchestrator.extract_policy_id(query):
                results = exact_results
            else:
                results = self._filter_results_by_policy_prefix(query, results)

            # Remove zero-score matches and return Top-K.
            results = [result for result in results if float(result["score"]) > 0][
                : self.DEFAULT_TOP_K
            ]

        elif strategy == "SEMANTIC":

            # Semantic similarity search using vector embeddings.
            results = self.semantic_retriever.search(
                query,
                top_k=self.DEFAULT_TOP_K,
            )

        elif strategy == "HYBRID":

            # Hybrid retrieval combines lexical and semantic signals.
            results = self.hybrid_retriever.search(query)

        else:

            raise ValueError(f"Unsupported retrieval strategy: {strategy}")

        return results

    @staticmethod
    def display_results(query: str, results: list):
        """
        Display ranked search results in a readable console format.

        Intended primarily for local testing and demonstration.
        """

        print("=" * 80)
        print(f"Query : {query}")
        print("=" * 80)

        if not results:
            print("No matching documents found.")
            return

        for rank, result in enumerate(results, start=1):

            score = max(float(result["score"]), 0.0)

            print(f"Rank     : {rank}")
            print(f"Score    : {score:.2f}")
            print(f"Document : {result['document']['filename']}")
            print(f"Preview  : {result['document']['content'][:250].strip()}")

            print("=" * 80)
            print()


if __name__ == "__main__":

    # --------------------------------------------------------------
    # Local execution entry point.
    #
    # Creates the RAG service, performs a sample query, and prints
    # the ranked retrieval results.
    # --------------------------------------------------------------
    rag_service = RAGService()

    query = "Show policy CAR-500"

    results = rag_service.search(query)

    rag_service.display_results(query=query, results=results)

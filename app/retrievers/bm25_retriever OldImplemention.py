from rank_bm25 import BM25Okapi
import fitz
import os
import re


class BM25Retriever:
    """
    BM25-based document retriever.

    Responsibilities:
    - Load PDF documents
    - Extract document content
    - Build a BM25 search index
    """

    def __init__(self):
        """Initialize the BM25 retriever."""

        # Collection of loaded documents
        self.documents = []

        # Tokenized representation of each document
        self.tokenized_documents = []

        # BM25 search index
        self.bm25 = None

    def _tokenize(self, text: str):
        """
        Normalize text into searchable tokens.

        Keeps policy IDs like CAR-120 together and removes punctuation
        from normal words like damage?
        """

        return re.findall(r"[a-z]+-\d+|[a-z0-9]+", text.lower())

    def load_documents(self):
        """
        Load all PDF documents from the data directory.

        Each document is stored together with its metadata
        for future retrieval and filtering.
        """
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        data_folder = os.path.join(project_root, "data")
        for file_name in os.listdir(data_folder):

            # Process only PDF documents
            if not file_name.lower().endswith(".pdf"):
                continue

            pdf_path = os.path.join(data_folder, file_name)

            page_contents = []

            # Read all pages from the PDF
            with fitz.open(pdf_path) as pdf_document:

                for page in pdf_document:
                    page_contents.append(page.get_text("text"))

            document_text = "\n".join(page_contents)

            self.documents.append(
                {
                    "filename": file_name,
                    "content": document_text,
                }
            )

    def build_index(self):
        """
        Build the BM25 index from all loaded documents.
        """

        # Clear previously generated tokens
        self.tokenized_documents.clear()

        # Tokenize every document
        for document in self.documents:

            tokens = self._tokenize(document["content"])

            self.tokenized_documents.append(tokens)

        # Create the BM25 search index
        self.bm25 = BM25Okapi(self.tokenized_documents)

    def search(self, query: str, top_k: int = 3):
        """
        Search the BM25 index and return the top matching documents.

        Args:
            query: User search query.
            top_k: Number of documents to return.

        Returns:
            List of ranked documents.
        """

        # Ensure the BM25 index has been built
        if self.bm25 is None:
            raise RuntimeError(
                "BM25 index has not been built. Call build_index() first."
            )

        # Tokenize the query
        query_tokens = self._tokenize(query)

        # Calculate BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Store ranked documents
        ranked_documents = []

        for index, score in enumerate(scores):
            ranked_documents.append(
                {
                    "score": score,
                    "document": self.documents[index],
                }
            )

        # Sort by score (Highest → Lowest)
        ranked_documents.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        # Return Top-K documents
        return ranked_documents[:top_k]


if __name__ == "__main__":

    retriever = BM25Retriever()

    retriever.load_documents()

    retriever.build_index()

    results = retriever.search("Does CAR-120 cover engine damage?")

    for result in results:

        print("=" * 80)

        print(f"Score    : {result['score']:.2f}")

        print(f"Document : {result['document']['filename']}")

        print()

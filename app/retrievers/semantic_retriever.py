from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


class SemanticRetriever:
    """
    Semantic (embedding-based) retriever.

    Single responsibility: embed pre-chunked text, persist it in a
    Chroma vector store, and run similarity search. Does not load
    PDFs or perform chunking — those are injected as already-prepared
    chunks, identical to what BM25Retriever receives.
    """

    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "insurance_policy_chunks",
        embedding_model: str = "text-embedding-3-small",
    ):
        self.embedding_model = OpenAIEmbeddings(model=embedding_model)
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_model,
            persist_directory=persist_directory,
        )
        self._persist_directory = persist_directory
        self._collection_name = collection_name

    def build_index(self, chunks: list[dict], force_rebuild: bool = False):
        existing_count = self.vector_store._collection.count()

        if existing_count > 0 and not force_rebuild:
            print(
                f"Semantic index already contains {existing_count} chunks — "
                "skipping rebuild. Pass force_rebuild=True to re-index."
            )
            return

        if force_rebuild and existing_count > 0:
            self.vector_store.delete_collection()
            self.vector_store = Chroma(
                collection_name=self._collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self._persist_directory,
            )

        if not chunks:
            raise RuntimeError("No chunks provided to build the semantic index.")

        self.vector_store.add_texts(
            texts=[chunk["content"] for chunk in chunks],
            metadatas=[
                {"filename": chunk["filename"], "chunk_index": chunk["chunk_index"]}
                for chunk in chunks
            ],
        )
        print(f"Indexed {len(chunks)} chunks into the semantic store.")

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        raw_results = self.vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
        )
        return [
            {
                "score": score,
                "document": {
                    "filename": document.metadata.get("filename", "unknown"),
                    "content": document.page_content,
                },
            }
            for document, score in raw_results
        ]

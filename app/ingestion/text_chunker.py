from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunker:
    """
    Splits document text into overlapping chunks.

    Single responsibility: chunking. Used identically by BM25Retriever
    and SemanticRetriever so both retrievers operate on the same
    granularity — a requirement for valid hybrid score fusion.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk_documents(self, documents: list[dict]) -> list[dict]:
        chunks = []

        for document in documents:
            text_chunks = self.splitter.split_text(document["content"])

            for chunk_index, chunk_text in enumerate(text_chunks):
                chunks.append(
                    {
                        "filename": document["filename"],
                        "chunk_index": chunk_index,
                        "content": chunk_text,
                    }
                )

        return chunks

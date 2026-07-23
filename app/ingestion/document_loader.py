import os

import fitz


class PDFDocumentLoader:
    """
    Loads raw text content from PDF files.

    Single responsibility: read PDFs from a folder and return their
    full text content. Does not chunk, tokenize, embed, or index —
    those are the responsibilities of downstream collaborators.
    """

    def __init__(self, data_folder: str):
        self.data_folder = data_folder

    def load(self) -> list[dict]:
        documents = []

        for file_name in os.listdir(self.data_folder):

            if not file_name.lower().endswith(".pdf"):
                continue

            pdf_path = os.path.join(self.data_folder, file_name)

            page_contents = []
            with fitz.open(pdf_path) as pdf_document:
                for page in pdf_document:
                    page_contents.append(page.get_text("text"))

            documents.append(
                {"filename": file_name, "content": "\n".join(page_contents)}
            )

        return documents

import fitz
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import embeddings
from langchain_chroma import Chroma
import openai

doc = fitz.open("phase3 - agentic-ai/fastapi_rag_project/data")
text = ""
for page in doc:
    page_text = page.get_text("text")
    text += str(page_text)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    chunks = splitter.split_text("text")
    embeddings = OpenAIEmbeddings()
    vectorStore = Chroma.from_texts(
        chunks,
        embeddings,
        persist_directory="./phase3 - agentic-ai/fastapi_rag_project/chroma_db/chroma.db",
    )

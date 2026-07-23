# Production RAG

This project is a small insurance-policy RAG system.

RAG means Retrieval-Augmented Generation. In simple words:

1. A user asks a question.
2. The app searches your own documents.
3. The app finds the most relevant pieces of text.
4. Later, those pieces can be given to an LLM so it can answer using your documents instead of guessing.

Right now, this project focuses mainly on the retrieval part: loading PDFs, splitting them into chunks, indexing them, searching them, and showing matching results.

## What This Project Can Do

- Read PDF files from the `data/` folder.
- Split long PDF text into smaller chunks.
- Build a BM25 keyword index for exact and keyword search.
- Build a Chroma semantic vector index using OpenAI embeddings.
- Detect policy IDs such as `MED-500`, `CAR-120`, and `LIFE-101`.
- Route exact policy ID queries to BM25.
- Route natural language queries to semantic search.
- Return only the best matching results instead of printing every chunk.
- Print the matching document name, score, and a short preview.

## Project Structure

```text
production-rag/
├── app/
│   ├── ingestion/
│   │   ├── document_loader.py
│   │   └── text_chunker.py
│   ├── orchestrator/
│   │   └── retrieval_orchestrator.py
│   ├── retrievers/
│   │   ├── bm25_retriever.py
│   │   ├── semantic_retriever.py
│   │   └── hybridRetriever.py
│   └── services/
│       └── rag_service.py
├── chroma_store/
├── data/
│   ├── Car_Insurance.pdf
│   ├── Health_Insurance.pdf
│   ├── Policy_MED-500.pdf
│   └── ...
├── .env
├── requirements.txt
└── README.md
```

## Important Files

### `app/services/rag_service.py`

This is the main coordinator.

Think of it like the manager of the RAG system. It does not do all the work itself. Instead, it connects the other pieces together.

It does these things:

- Loads environment variables from `.env`.
- Finds the project `data/` folder.
- Creates the PDF loader.
- Creates the text chunker.
- Creates BM25, semantic, and hybrid retrievers.
- Loads all PDFs.
- Splits PDF text into chunks.
- Builds the BM25 index.
- Builds or reuses the semantic Chroma index.
- Accepts a query.
- Decides which retriever to use.
- Prints the final search results.

### `app/ingestion/document_loader.py`

This file reads PDFs.

It uses PyMuPDF, imported as `fitz`, to open every `.pdf` file inside `data/`.

It returns data like this:

```python
{
    "filename": "Policy_MED-500.pdf",
    "content": "Full text extracted from the PDF..."
}
```

It does not chunk text. It does not search. It only loads PDF text.

### `app/ingestion/text_chunker.py`

This file splits long document text into smaller pieces.

Why chunking is needed:

- A PDF can be very long.
- Search works better on smaller sections.
- Embedding models have token limits.
- RAG answers are usually built from a few relevant chunks, not full documents.

Current chunk settings are in `RAGService`:

```python
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
```

That means:

- Each chunk is around 500 characters.
- Neighboring chunks share 50 characters.

The overlap helps avoid losing meaning when an important sentence is split across two chunks.

### `app/retrievers/bm25_retriever.py`

This file handles keyword search.

BM25 is good when the user query contains exact words or exact IDs.

Example:

```text
Show policy MED-500
```

For this kind of query, BM25 is a good choice because `MED-500` is an exact identifier.

BM25 works like this:

1. Break each chunk into tokens.
2. Break the query into tokens.
3. Compare query tokens with chunk tokens.
4. Give each chunk a score.
5. Return the highest scoring chunks.

### `app/retrievers/semantic_retriever.py`

This file handles semantic search.

Semantic search means the system searches by meaning, not just exact words.

Example:

```text
What medical expenses are covered during hospitalization?
```

The document might not contain that exact sentence, but it may contain related text like:

```text
MED-500 covers hospitalization expenses, daycare procedures, emergency ambulance charges...
```

Semantic search can still find it because the meaning is similar.

This retriever uses:

- `OpenAIEmbeddings` to convert text into vectors.
- `Chroma` to store and search those vectors.

### `app/orchestrator/retrieval_orchestrator.py`

This file decides which search strategy to use.

Current rule:

| Query Type | Example | Strategy |
| --- | --- | --- |
| Has exact policy ID | `Show policy MED-500` | BM25 |
| Natural language question | `What is covered in health insurance?` | SEMANTIC |

The orchestrator can extract:

```text
Policy ID     : MED-500
Policy Prefix : MED
```

The full ID is used for exact lookup. The prefix can be used to understand the policy family.

## Full Flow: What Happens When You Run The App

You run:

```bash
python3 -m app.services.rag_service
```

Then this happens:

### Step 1: Python starts `rag_service.py`

The file has this block at the bottom:

```python
if __name__ == "__main__":
    rag_service = RAGService()
    query = "Show policy MED-500"
    results = rag_service.search(query)
    rag_service.display_results(query=query, results=results)
```

That means:

1. Create the RAG service.
2. Use the test query `Show policy MED-500`.
3. Search for matching results.
4. Print the results.

### Step 2: `.env` is loaded

`rag_service.py` has:

```python
load_dotenv()
```

This loads secrets like:

```env
OPENAI_API_KEY=your_api_key_here
```

This is needed for OpenAI embeddings.

### Step 3: Project paths are found

The service calculates the project root and finds:

```text
data/
chroma_store/
```

`data/` contains PDFs.

`chroma_store/` stores the semantic vector database.

### Step 4: PDFs are loaded

`PDFDocumentLoader` reads every PDF in `data/`.

For each PDF, it extracts plain text.

Example:

```text
Policy_MED-500.pdf
```

becomes:

```text
Policy ID: MED-500
Product: Health Insurance
Plan Name: Health Secure Plus
...
```

### Step 5: Text is chunked

The full PDF text is split into smaller chunks.

Example:

```text
Policy ID: MED-500
Product: Health Insurance
Plan Name: Health Secure Plus
Coverage Summary:
MED-500 covers hospitalization expenses...
```

becomes one or more chunk dictionaries:

```python
{
    "filename": "Policy_MED-500.pdf",
    "chunk_index": 0,
    "content": "Policy ID: MED-500..."
}
```

### Step 6: BM25 index is built

BM25 indexes the chunks in memory.

This is fast and happens every time the service starts.

BM25 is useful for exact text matching, especially IDs like:

```text
MED-500
CAR-120
LIFE-101
```

### Step 7: Semantic index is built or reused

`SemanticRetriever` checks Chroma:

```python
existing_count = self.vector_store._collection.count()
```

If Chroma already has embeddings, it skips rebuilding:

```text
Semantic index already contains 80 chunks - skipping rebuild.
```

This is efficient because embeddings cost time and API usage.

If you add or change PDFs, you may need to rebuild the semantic index using:

```python
self.semantic_retriever.build_index(chunks, force_rebuild=True)
```

For learning, this is fine. In a real production system, you would use document hashes and only embed changed chunks.

### Step 8: Query strategy is selected

For:

```text
Show policy MED-500
```

The orchestrator sees a policy ID:

```text
MED-500
```

So it chooses:

```text
BM25
```

This is correct because exact IDs should be searched exactly.

### Step 9: Exact policy ID filtering happens

BM25 scores chunks, then `RAGService` filters results.

For a query with `MED-500`, the service keeps only chunks that actually contain:

```text
MED-500
```

This prevents fake-looking output where generic health-insurance chunks are returned even though the exact policy ID was not found.

### Step 10: Results are printed

The terminal shows:

```text
================================================================================
Query : Show policy MED-500
================================================================================
Rank     : 1
Score    : 6.53
Document : Policy_MED-500.pdf
Preview  : Policy ID: MED-500
Product: Health Insurance
Plan Name: Health Secure Plus
Coverage Summary:
MED-500 covers hospitalization expenses...
================================================================================
```

## Why Multiple Results Used To Print Earlier

Earlier, the code used:

```python
top_k=len(self.bm25_retriever.chunks)
```

That asked BM25 to return every chunk.

Then the code filtered by policy prefix, like:

```text
MED
```

So many chunks from `Health_Insurance.pdf` were printed, even if they did not contain `MED-500`.

That was useful for debugging, but not realistic for production.

Now the behavior is stricter:

- If the query has an exact policy ID, return chunks containing that exact ID.
- If no exact policy ID is found, show `No matching documents found.`
- General semantic queries return only top results.

## Exact Lookup vs Semantic Search

### Exact Lookup

Use this when the query contains an ID.

Example:

```text
Show policy MED-500
```

Expected behavior:

```text
Return Policy_MED-500.pdf
```

This should use BM25 because the ID must match exactly.

### Semantic Search

Use this when the query asks a natural language question.

Example:

```text
What is covered during hospitalization?
```

Expected behavior:

```text
Return chunks about hospitalization coverage.
```

This should use semantic search because the user may not use the same words as the document.

## Setup

From the `production-rag` folder:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

If you are not using a virtual environment, install dependencies into your current Python:

```bash
python3 -m pip install -r requirements.txt
```

## Create `.env`

Create this file:

```text
production-rag/.env
```

Add:

```env
OPENAI_API_KEY=your_actual_api_key_here
```

The file must be named exactly:

```text
.env
```

Not:

```text
e.en
env
.env.txt
```

## Run The RAG Service

Open a terminal in the `production-rag` folder.

Check your current folder:

```bash
pwd
```

The output should end with:

```text
production-rag
```

Then run:

```bash
python3 -m app.services.rag_service
```

## Change The Test Query

Open:

```text
app/services/rag_service.py
```

At the bottom, change:

```python
query = "Show policy MED-500"
```

Examples:

```python
query = "Show policy MED-500"
query = "What medical expenses are covered during hospitalization?"
query = "What are common policy exclusions?"
```

Then run again:

```bash
python3 -m app.services.rag_service
```

## Current Production-Like Behavior

| User Query | What The App Does |
| --- | --- |
| `Show policy MED-500` | Uses BM25 and exact ID filtering |
| `Does MED-500 cover hospitalization?` | Uses BM25 because the query has `MED-500` |
| `What is covered during hospitalization?` | Uses semantic search |
| `What are policy exclusions?` | Uses semantic search |

## Important Note About New PDFs

BM25 sees new PDFs immediately because it rebuilds when the app starts.

Semantic search may not see new PDFs immediately because Chroma reuses the old vector index.

If you add a new PDF and want semantic search to include it, rebuild the semantic index:

```python
self.semantic_retriever.build_index(chunks, force_rebuild=True)
```

After rebuilding once, change it back to:

```python
self.semantic_retriever.build_index(chunks)
```

This avoids unnecessary embedding cost on every run.

## What Would Be Added In A Full Production RAG System

This project is a strong learning version. A full production RAG system would also include:

- A FastAPI endpoint for users or frontend apps.
- An answer generator using an LLM.
- Source citations in the final answer.
- User authentication.
- Logging and monitoring.
- Better error messages.
- Document versioning.
- Incremental indexing using file hashes.
- A database for policies and metadata.
- Hybrid search that combines BM25 and semantic search.
- Evaluation tests to check retrieval quality.

## Simple Mental Model

Think of the project like a library assistant:

```text
data/ PDFs
   |
   v
PDFDocumentLoader reads the books
   |
   v
TextChunker cuts pages into small notes
   |
   v
BM25Retriever indexes exact words
SemanticRetriever indexes meaning
   |
   v
RetrievalOrchestrator chooses the right search method
   |
   v
RAGService returns the best matching notes
```

That is the heart of RAG.

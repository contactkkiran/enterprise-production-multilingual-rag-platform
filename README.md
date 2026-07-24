# Enterprise Production Multilingual RAG Platform

This project is a production-style multilingual RAG platform for insurance and document retrieval use cases. It is designed to ingest PDF documents, parse multilingual content, split text into meaningful chunks, index the content, and support semantic and keyword search across multiple languages.

RAG means Retrieval-Augmented Generation. In simple words:

1. A user asks a question.
2. The app searches your own documents.
3. The app finds the most relevant pieces of text.
4. Later, those pieces can be given to an LLM so it can answer using your documents instead of guessing.

Right now, this project focuses mainly on the retrieval part: loading PDFs, splitting them into chunks, indexing them, searching them, and showing matching results.

## What This Project Can Do

- Read PDF files from the `data/` folder.
- Support multilingual ingestion across multiple languages and document formats.
- Apply Unicode normalization to improve parsing quality for non-Latin scripts.
- Detect document language automatically before retrieval and indexing.
- Prepare for OCR-based ingestion for scanned or image-heavy documents.
- Extract and preserve metadata such as document title, author, date, and policy identifiers.
- Support hybrid retrieval with BM25 and semantic search.
- Enable reranking for higher-precision result selection.
- Support agentic workflows for multi-step document reasoning and retrieval orchestration.
- Work with multiple vector databases for flexible deployment scenarios.
- Provide an enterprise-grade orchestration layer for production retrieval pipelines.
- Detect policy IDs such as `MED-500`, `CAR-120`, `LIFE-101`, and `LIFE-102`.
- Route exact policy ID queries to BM25.
- Route natural language queries to semantic search.
- Return only the best matching results instead of printing every chunk.
- Print the matching document name, score, and a short preview.

## Multilingual PDF Parsing and Chunking Support

The platform supports multilingual content ingestion and retrieval for documents written in many languages, including:

- Chinese
- Japanese
- Italian
- French
- Arabic
- Spanish
- German

The ingestion pipeline includes:

- PDF text extraction with PyMuPDF
- Unicode normalization for non-English characters
- Language detection for incoming document content
- OCR preparation for scanned or low-quality PDFs
- Recursive chunking that works well for multilingual text
- Metadata-aware chunking strategies for multi-format documents

Example multilingual search queries:

- Chinese: "中国保险条款中关于住院报销的内容是什么？"
- Japanese: "入院時の医療費はどのようにカバーされていますか？"
- Italian: "Quali sono le coperture per le spese ospedaliere?"
- French: "Quelles sont les garanties pour les frais d'hospitalisation?"

Example search patterns:

- `Show policy MED-500`
- `What medical expenses are covered during hospitalization?`
- `中国保险条款中关于住院报销的内容是什么？`
- `入院時の医療費はどのようにカバーされていますか？`
- `Quali sono le coperture per le spese ospedaliere?`
- `Quelles sont les garanties pour les frais d'hospitalisation?`

## Enterprise Roadmap and Capabilities

The platform is being designed for enterprise-grade document intelligence with the following capabilities:

- ✅ Multilingual ingestion
- ✅ Unicode normalization
- ✅ Language detection
- ✅ OCR
- ✅ Metadata extraction
- ✅ Hybrid retrieval
- ✅ Reranking
- ✅ Agentic workflows
- ✅ Multiple vector databases
- ✅ Enterprise orchestration

The system also plans to support evaluation loops for updating chunking strategies across multi-format documents, including PDFs, scanned images, and structured text files.

## Governance and Deployment Notes

The platform is intended to support:

- Guardrails for safe and compliant retrieval
- FastAPI services for backend integrations
- React JS-based GUI experiences for search and document exploration
- Production monitoring and evaluation pipelines

## Future Updates

Planned future enhancements include:

- Advanced OCR pipelines for scanned and image-heavy documents
- Better metadata extraction from tables, headers, and footers
- Expanded evaluation loops for chunking and retrieval quality
- More robust reranking strategies for enterprise search accuracy
- Support for additional vector databases and retrieval backends
- Agent-driven workflows for multi-step document understanding
- Role-based access control and governance features
- End-to-end analytics for query success, latency, and relevance
- A polished FastAPI backend and React-based user interface

## Project Structure

```text
enterprise-production-multilingual-rag-platform/
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

From the `enterprise-production-multilingual-rag-platform` folder:

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
enterprise-production-multilingual-rag-platform/.env
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

Open a terminal in the `enterprise-production-multilingual-rag-platform` folder.

Check your current folder:

```bash
pwd
```

The output should end with:

```text
enterprise-production-multilingual-rag-platform
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


# Enterprise Roadmap

The **Enterprise Production Multilingual RAG Platform** is designed to go beyond traditional Retrieval-Augmented Generation (RAG) systems. The following enterprise capabilities will make the platform scalable, intelligent, and production-ready.

---

## 1. Intelligent Retrieval Strategy

Instead of always relying on semantic search, the platform intelligently selects the optimal retrieval strategy based on the query type.

```text
User Query
      │
      ▼
Query Analyzer
      │
      ├── Policy ID        → BM25
      ├── Natural Question → Semantic
      ├── Mixed Query      → Hybrid
      └── Table Query      → Table Retriever
```

The `RetrievalOrchestrator` acts as the decision engine to route queries to the most effective retrieval strategy.

---

## 2. Multilingual Ingestion

Unlike many RAG implementations that only support English, this platform is designed for multilingual enterprise environments.

### Supported Languages

- English
- Chinese
- Japanese
- Korean
- Arabic
- Hindi

### Features

- Unicode Normalization
- Language Detection
- Language-Aware Chunking
- Multilingual Embeddings

---

## 3. Enterprise Metadata Pipeline

Instead of storing only document content:

```json
{
  "content": "..."
}
```

The platform stores rich enterprise metadata.

```json
{
  "content": "...",
  "metadata": {
    "language": "en",
    "department": "HR",
    "classification": "Internal",
    "document_version": "3.1",
    "effective_date": "...",
    "source": "PDF"
  }
}
```

Rich metadata enables:

- Intelligent filtering
- Search optimization
- Access control
- Compliance
- Analytics
- Better enterprise governance

---

## 4. Automatic Document Classification

During ingestion, AI automatically classifies enterprise documents.

Supported document categories include:

- Insurance Policy
- Employee Handbook
- Standard Operating Procedure (SOP)
- Invoice
- Legal Contract
- Technical Manual

Automatic classification improves retrieval precision and enterprise search.

---

## 5. AI Query Rewriting

Short or ambiguous queries are automatically rewritten before retrieval.

### User Query

```text
medical insurance
```

### AI Rewritten Query

```text
Show medical insurance policy benefits and exclusions.
```

Benefits:

- Better semantic retrieval
- Improved recall
- Higher answer quality

---

## 6. Confidence Score

Every generated answer includes a confidence score.

Example:

```text
Confidence

96%
72%
41%
```

If confidence falls below a configurable threshold, the system responds:

> "I couldn't find sufficient evidence."

This helps reduce hallucinations and increases trust.

---

## 7. Document Quality Analyzer

Before indexing, every document is analyzed for quality.

Checks include:

- OCR Quality
- Missing Pages
- Duplicate Pages
- Unreadable Text
- Broken Tables

This ensures only high-quality enterprise documents are indexed.

---

## 8. Plugin Architecture

The ingestion framework is designed as a plugin architecture rather than hardcoding PDF support.

```text
Ingestion Plugin

├── PDF
├── Word
├── Excel
├── PowerPoint
├── HTML
└── Wiki
```

New document types can be added without modifying the core ingestion pipeline.

---

## 9. Enterprise Observability

The platform continuously monitors operational metrics.

Metrics include:

- Retrieval Time
- Embedding Time
- Chunk Count
- Cache Hit Ratio
- Token Usage
- Retrieval Strategy Used

These metrics help optimize production performance and diagnose issues.

---

## 10. AI Explainability

Enterprise AI should explain *why* an answer was generated.

Example:

```text
Answer

Retrieved From:
HR Policy.pdf

Strategy:
Hybrid

Confidence:
95%

Matched Chunks:
4
```

Explainability builds user trust and provides transparency into the retrieval process.

---

# AI Query Intelligence Layer

To make the platform more intelligent, an AI Query Intelligence Layer is introduced before retrieval.

```text
                User Query
                     │
                     ▼
        AI Query Intelligence Engine
                     │
     ┌───────────────┼────────────────┐
     ▼               ▼                ▼
 Intent        Language        Entity Extraction
 Detection      Detection      (Policy IDs, Names)
     │               │                │
     └───────────────┼────────────────┘
                     ▼
        Retrieval Orchestrator
                     ▼
     BM25 / Semantic / Hybrid / Table Search
```

### Responsibilities

- Intent Detection
- Language Detection
- Entity Extraction
- Query Classification
- Retrieval Strategy Selection

This transforms the platform from a traditional RAG system into an intelligent enterprise knowledge retrieval platform capable of reasoning about queries before searching.

---

# Enterprise Metadata Strategy

## Does JSON Metadata Increase Token Usage?

**Yes, but only when the metadata is included in the prompt sent to the LLM.**

---

## Case 1: Metadata Stored Only in the Vector Database (Recommended)

```json
{
  "content": "Employees are entitled to 20 days of annual leave.",
  "metadata": {
    "language": "en",
    "department": "HR",
    "document_type": "Policy"
  }
}
```

In this approach, metadata is used for:

- Filtering
- Ranking
- Access Control
- Analytics

Since the metadata is **not sent to the LLM**, it **does not increase prompt token usage**.

---

## Case 2: Metadata Included in the Prompt

```text
Document: HR Policy.pdf
Language: en
Department: HR
Version: 3.1
Classification: Internal

Employees are entitled to 20 days of annual leave...
```

Every metadata field included in the prompt contributes to token usage.

---

## Enterprise Best Practice

Store rich metadata inside the vector database while sending only relevant information to the LLM.

Example metadata model:

```json
{
  "content": "...",
  "metadata": {
    "language": "en",
    "department": "HR",
    "source": "PDF"
  }
}
```

Use metadata for:

- Filtering (e.g., HR documents only)
- Ranking
- Access Control
- Analytics

Only include metadata in the prompt when it improves answer quality.

### Recommended Metadata to Include

- ✅ Filename
- ✅ Page Number
- ✅ Section Title

### Metadata Typically Excluded

- ❌ Language (unless required)
- ❌ Document Version (unless relevant)
- ❌ Created By
- ❌ Ingestion Timestamp

This approach provides rich enterprise metadata while minimizing LLM token consumption and operational cost.

# Askify — Know your stuff.

```text
    ___        __   _ ____     
   / _ | _____/ /__(_) __/_  __
  / __ |/ (_-</  '_/ / _/ // /
 /_/ |_|___(_)_/\_/_/_/  \_, /
                         /___/
```

**Chat with your code and documents directly from the terminal.**

---

# Why I Built This

You know that feeling when you pause a project for a week—exams, work, life—and come back completely lost?

You forget how things fit together. You start opening files one by one, tracing function calls, and rebuilding the mental model from scratch.

And that's your own project.

Imagine joining a new team and trying to understand an unfamiliar codebase the same way.

That's what Askify solves.

Point it at a folder, ask questions in plain English, and get answers grounded in your actual files.

No copy-pasting code into ChatGPT. No manually searching through folders. No losing context.

---

# Features

* AST-based code chunking for accurate function and class boundaries
* Hybrid retrieval — semantic vector search + BM25 keyword search
* Cross-encoder reranking for higher context quality
* LLM-generated file and project summaries at index time
* Retrieval evaluation framework — Recall@5, Recall@10, Hit Rate
* Incremental indexing using MD5 file hashes
* Source-grounded answers with citations
* Multi-format document ingestion
* Local vector storage using ChromaDB
* Persistent indexing between sessions

---

# Retrieval Performance

Evaluated on a 23-question benchmark across all source files.

| Phase | Change | Recall@5 | Recall@10 |
|---|---|---|---|
| v1.1 baseline | Regex chunking, vector search only | 86.96% | 86.96% |
| Phase 2 | LLM file summaries added | 95.65% | 95.65% |
| Phase 3 | BM25 hybrid retrieval | 91.30% | 100.00% |
| Phase 4 | Cross-encoder reranking | 86.96% | 100.00% |
| Phase 5 | AST-based chunking | **95.65%** | **100.00%** |

---

# Example

```bash
askify chat .
```

```text
You: what does loader.py do?

Askify:
loader.py is responsible for loading supported files from disk,
filtering unsupported paths, extracting document contents,
and generating hashes for incremental indexing.

Sources:
- askify/ingester/loader.py
```

---

# Installation

```bash
pip install askify-cli
```

Get a free API key from https://console.groq.com

Create a `.env` file:

```env
GROQ_CLIENT=your_groq_api_key_here
```

---

# Commands

```bash
# Index a folder
askify index ./src/

# Ask a single question
askify ask ./src/ "how does the chunking flow work?"

# Interactive chat mode
askify chat ./src/

# Find relevant files
askify where "authentication"

# Run retrieval evaluation
askify evaluate

# View past queries
askify history

# Clear the index
askify clear
```

---

# Architecture

Askify is a production-oriented RAG system built without orchestration frameworks such as LangChain or LlamaIndex. Every component — retrieval pipeline, chunking strategy, evaluation framework, and CLI — is custom-built.

```text
Files
  │
  ▼
Loader          ← code, PDF, DOCX, MD, TXT
  │
  ▼
AST Chunker     ← function/class-aware splitting
  │
  ▼
Summarizer      ← LLM file + project summaries
  │
  ▼
Embedder        ← ChromaDB, incremental reindex
  │
  ▼
Retriever       ← BM25 + Vector Search merged
  │
  ▼
Reranker        ← cross-encoder top-5 selection
  │
  ▼
Groq LLM        ← grounded answer + citations
```

---

# How It Works

### Loader

Reads files from disk and extracts content. Supports code files, PDF, DOCX, Markdown, and plain text. Skips `.git`, `__pycache__`, `node_modules`, `.venv`.

---

### Chunker

Splits content into retrieval-friendly chunks.

**Code — AST-based**
- Parses Python source using `ast.parse()`
- Extracts each `FunctionDef`, `AsyncFunctionDef`, and `ClassDef` by exact line numbers
- Falls back to regex chunking for non-Python or syntax-error files

**Documents**
- Paragraph-based chunking with overlapping windows for context preservation

---

### Summarizer

At index time, generates two types of LLM summaries using Groq:

- **File summary** — one concise technical summary per file describing its purpose and functions
- **Project summary** — one global summary of the entire codebase, used for broad architecture questions

---

### Embedder

Uses `sentence-transformers/all-MiniLM-L6-v2` to generate vector embeddings. Stores vectors and metadata in ChromaDB. Supports incremental re-indexing using MD5 file hashes — only changed files are reprocessed.

---

### Retriever

Runs two searches in parallel and merges results:

- **Vector search** — semantic similarity via ChromaDB
- **BM25 search** — keyword matching via `rank-bm25`

Source deduplication applied after merge. Project summary deprioritized to last position for specific queries.

---

### Reranker

Uses `cross-encoder/ms-marco-MiniLM-L-6-v2` to score each retrieved chunk against the query jointly. Returns top 5 highest-scoring chunks to the LLM — reducing noise and improving answer accuracy.

---

### Responder

Uses Llama 3.3 70B (Groq) to generate grounded responses from retrieved context. Answers include source file references.

---

### Evaluator

Runs a 23-question benchmark against indexed files. Measures:

- **Recall@5** — correct source in top 5 results
- **Recall@10** — correct source in top 10 results
- **Hit Rate** — same as Recall@10

```bash
askify evaluate
```

```text
Hits@5:   22/23
Hits@10:  23/23
Recall@5:  95.65%
Recall@10: 100.00%
```

---

# Supported File Types

| Category | Extensions |
|---|---|
| Code | `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs` |
| Documents | `.pdf`, `.docx`, `.md`, `.txt`, `.rst` |

---

# Tech Stack

| Component | Technology |
|---|---|
| CLI | Typer |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Keyword Search | rank-bm25 |
| Reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| LLM | Groq (Llama 3.3 70B) |
| PDF Parsing | PyMuPDF |
| DOCX Parsing | python-docx |
| Terminal UI | Rich |

---

# Limitations

* Python 3.10+ required
* Groq API key required
* First run downloads embedding models (~90 MB total)
* AST chunking currently supports Python only; other languages fall back to regex
* Indexing large repositories makes multiple Groq API calls for summaries

---

# Development Notes

Askify was developed using AI-assisted development alongside manual engineering, debugging, testing, and iterative improvements.


---

Built with ❤️ by **Vamshi Krishna**
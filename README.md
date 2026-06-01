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

No copy-pasting code into ChatGPT.

No manually searching through folders.

No losing context.

---

# Features

* Semantic search across code and documents
* Interactive chat with your codebase
* Incremental indexing using file hashes
* Function-aware code chunking
* Source-grounded answers with citations
* Multi-format document ingestion
* Local vector storage using ChromaDB
* Retrieval debugging support
* Persistent indexing between sessions

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

Get a free API key from:

https://console.groq.com

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

# View past queries
askify history

# Clear the index
askify clear
```

---

# Architecture

Askify is a Retrieval-Augmented Generation (RAG) system built without orchestration frameworks such as LangChain or LlamaIndex.

The retrieval pipeline, indexing workflow, chunking strategy, and CLI experience are custom-built using ChromaDB, Sentence Transformers, and Groq.

```text
Files
  │
  ▼
Loader
  │
  ▼
Chunker
  │
  ▼
Embedder
  │
  ▼
ChromaDB
  │
  ▼
Retriever
  │
  ▼
Groq LLM
  │
  ▼
Answer + Citations
```

---

# How It Works

### Loader

Reads files from disk and extracts content.

Supports:

* Code files
* PDF documents
* DOCX documents
* Markdown
* Plain text

Skips unnecessary directories such as:

```text
.git
__pycache__
node_modules
.venv
```

---

### Chunker

Splits content into retrieval-friendly chunks.

**Code**

* Function-aware chunking
* Class-aware chunking

**Documents**

* Paragraph-based chunking
* Overlapping windows for context preservation

---

### Embedder

Uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

to generate vector embeddings.

Stores vectors and metadata in ChromaDB.

Supports incremental re-indexing using file hashes so only changed files are reprocessed.

---

### Retriever

* Embeds user queries
* Searches ChromaDB
* Returns the most relevant chunks
* Provides source metadata for citations

---

### Responder

Uses:

```text
Llama 3.3 70B (Groq)
```

to generate grounded responses from retrieved context.

Answers include source references whenever possible.

---

# Supported File Types

| Category  | Extensions                                               |
| --------- | -------------------------------------------------------- |
| Code      | `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs` |
| Documents | `.pdf`, `.docx`, `.md`, `.txt`, `.rst`                   |

---

# Tech Stack

| Component       | Technology            |
| --------------- | --------------------- |
| CLI             | Typer                 |
| Embeddings      | Sentence Transformers |
| Vector Database | ChromaDB              |
| LLM             | Groq (Llama 3.3 70B)  |
| PDF Parsing     | PyMuPDF               |
| DOCX Parsing    | python-docx           |
| Terminal UI     | Rich                  |

---

# Limitations

* Python 3.10+ required
* Groq API key required
* First run downloads embedding model (~80 MB)
* Broad questions may be incomplete because only the most relevant chunks are sent to the LLM
* Retrieval quality depends on chunking and embedding quality

---

# What's Next

* [ ] Hybrid Retrieval (Vector Search + BM25)
* [ ] Retrieval Reranking
* [ ] Retrieval Evaluation Framework
* [ ] AST-Based Code Chunking
* [ ] File-Level Summaries
* [ ] VS Code Extension

---

# Development Notes

Askify was developed using AI-assisted development alongside manual engineering, debugging, testing, and iterative improvements.

The primary goal of the project was to understand how modern RAG systems work internally rather than relying entirely on abstraction frameworks.

---

Built with ❤️ by **Vamshi Krishna**

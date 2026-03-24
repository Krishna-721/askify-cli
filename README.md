# Askify — Know your stuff.

```
    ___        __   _ ____     
   / _ | _____/ /__(_) __/_  __
  / __ |/ (_-</  '_/ / _/ // /
 /_/ |_|___(_)_/\_/_/_/  \_, / 
                         /___/  
```

**Chat with your code and documents from the terminal.**

---

## Why I built this

You know that feeling when you pause a project for a week- exams, life, whatever- and come back to it completely blank?

You forget how stuff works. You start reading file by file, folder by folder, trying to piece it back together. And that's just *your own* project. Imagine joining a company and trying to understand their entire codebase the same way.

That's what Askify solves.

Point it at any folder, ask anything, get answers grounded in your actual files- no copy-pasting into ChatGPT, no sending your code to the internet, no waiting.

---

## What it does

Askify is a CLI tool that lets you have a conversation with your codebase. It reads your files, understands them semantically, and answers your questions based on what's actually in there.

```bash
askify chat ./src/
```

```
You: how does authentication work here?
Askify: Auth is handled in middleware/auth.py inside verify_token()...

You: what about token expiry?
Askify: Token expiry is configured in config/settings.py...

You: exit
```

That's it. No setup beyond indexing once.

---

## Installation

```bash
pip install askify-cli
```

Get a free Groq API key at [console.groq.com](https://console.groq.com) and add it to a `.env` file:

```
GROQ_CLIENT=your_groq_api_key_here
```

---

## Commands

```bash
# index a folder — do this once
askify index ./src/

# ask a one-shot question
askify ask ./src/ "how does the chunking flow work?"

# chat interactively
askify chat ./src/

# find which files are relevant to a keyword
askify where "authentication"

# see past queries
askify history

# wipe the index and start fresh
askify clear
```

---

## Working under the hood

Askify is a RAG (Retrieval-Augmented Generation) pipeline — built from scratch, no LangChain.

```
Files → Loader → Chunker → Embedder → ChromaDB
                                           ↓
Your question → Embed → Search → Top chunks → Groq LLM → Answer
```

- **Loader** — reads code and docs, skips noise (`__pycache__`, `.git`, etc.)
- **Chunker** — splits code by function/class, documents by paragraph with overlap
- **Embedder** — converts chunks to vectors via `all-MiniLM-L6-v2`, stores in ChromaDB
- **Retriever** — embeds your query, finds the closest matching chunks
- **Responder** — sends retrieved context + query to Groq LLaMA 3.3 70B, returns a grounded answer

Each project gets its own `.askify/` folder for its index — like `.git`, but for semantic search. Index once, query forever.

---

## Supported file types

| Type | Extensions |
|---|---|
| Code | `.py` `.js` `.ts` `.go` `.java` `.cpp` `.c` `.rs` |
| Documents | `.pdf` `.md` `.txt` `.rst` `.docx` |

---

## Stack

| | |
|---|---|
| CLI | Typer |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB |
| LLM | Groq LLaMA 3.3 70B |
| PDF parsing | PyMuPDF |
| DOCX parsing | python-docx |
| Terminal UI | Rich |

---

## Limitations (being honest)

- Python 3.10+ required
- Groq API key needed (free tier works fine)
- First run downloads the embedding model (~80MB)
- Works best for specific questions — broad questions like "explain everything" will be partial since only the top 5 relevant chunks get sent to the LLM

---

## What's next

- [ ] `askify explain file.py` — per-file summary and key function breakdown
- [ ] AST-based chunking — smarter code splitting for better retrieval accuracy
- [ ] Chat memory — follow-up questions that remember what was asked before
- [ ] Evaluation system — benchmark retrieval accuracy against a Q&A dataset
- [ ] VS Code extension — use Askify directly inside your editor
---

Built with ❤️ - **Vamshi Krishna**
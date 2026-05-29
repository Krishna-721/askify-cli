import os
from pathlib import Path
import fitz  # PyMuPDF
from docx import Document
import hashlib

CODE_EXT = {".py", ".js", ".ts", ".cpp", ".c", ".java", ".go", ".rs"}
DOC_EXT = {".pdf", ".md", ".txt", ".rst", ".docx"}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", "store"}
SKIP_EXTS = {".pyc", ".pyo", ".lock", ".log"}
SKIP_DIRS = {"__pycache__",".git","node_modules",".venv","venv","store",}

def get_file_hash(content: str):
    return hashlib.md5(content.encode()).hexdigest()


def load_path(path: str) -> list[dict]:
    p = Path(path)

    if p.is_file():
        files = [p]

    elif p.is_dir():
        files = []

        for f in p.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix in SKIP_EXTS:
                continue
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            if any(part.endswith(".egg-info") for part in f.parts):
                continue
            files.append(f)

    else:
        raise ValueError(f"Path not found! {path}")

    print(f"[askify] Loaded {len(files)} files")

    results = []

    for f in files:
        ext = f.suffix.lower()

        if ext in CODE_EXT:
            results += load_code_file(f)

        elif ext in DOC_EXT:
            results += load_doc_file(f)

    return results

def load_code_file(path: Path) -> list[dict]:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return [
            {
                "content": content,
                "source": str(path),
                "type": "code",
                "hash": get_file_hash(content),
            }
        ]
    except Exception as e:
        print(f"[skip] {path}: {e}")
        return []

def load_doc_file(path: Path) -> list[dict]:
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            return load_pdf(path)
        elif ext == ".docx":
            return load_docx(path)
        else:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return [
                {
                    "content": content,
                    "source": str(path),
                    "type": "document",
                    "hash": get_file_hash(content),
                }
            ]
    except Exception as e:
        print(f"[skip] {path}:{e}")
        return []

def load_pdf(path: Path) -> list[dict]:
    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append(
                {
                    "content": text,
                    "source": f"{path}::page{i + 1}",
                    "type": "document",
                    "hash": get_file_hash(text),
                }
            )
    return pages

def load_docx(path: Path) -> list[dict]:
    doc = Document(str(path))
    content = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return [
        {
            "content": content,
            "source": str(path),
            "type": "document",
            "hash": get_file_hash(content),
        }
    ]
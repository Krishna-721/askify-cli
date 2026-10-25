import os
from pathlib import Path
import fitz  # PyMuPDF
from docx import Document
import hashlib
from dataclasses import dataclass, field

CODE_EXT = {".py", ".js", ".ts", ".cpp", ".c", ".java", ".go", ".rs"}
DOC_EXT = {".pdf", ".md", ".txt", ".rst", ".docx"}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", "store"}
SKIP_EXTS = {".pyc", ".pyo", ".lock", ".log", "structure.txt", ".DS_Store", ".egg-info", ".ipynb_checkpoints", ".zip", ".tar.gz", ".tar.bz2", ".tar.xz"}
SKIP_DIRS = {"__pycache__",".git","node_modules",".venv","venv","store",}

def get_file_hash(content: str):
    return hashlib.md5(content.encode()).hexdigest()


@dataclass
class LoadError:
    source: str
    message: str


@dataclass
class LoadReport:
    files: list[dict] = field(default_factory=list)
    errors: list[LoadError] = field(default_factory=list)



def load_path(path: str) -> list[dict]:
    """Load supported files, raising an error if any file fails to load."""
    report = load_path_with_report(path)

    if report.errors:
        error_details = "; ".join(
            f"{error.source}: {error.message}"
            for error in report.errors
        )
        raise RuntimeError(
            f"Failed to load one or more files: {error_details}"
        )

    print(f"[askify] Loaded {len(report.files)} files")
    return report.files



def load_path_with_report(path: str) -> LoadReport:
    """Load a path and return files plus any recorded read errors."""
    report = LoadReport()
    p = Path(path)

    if not p.exists():
        raise ValueError(f"Path not found! {path}")

    if p.is_file():
        candidates = [p]
    elif p.is_dir():
        candidates = []

        for f in p.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() in SKIP_EXTS:
                continue
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            if any(part.endswith(".egg-info") for part in f.parts):
                continue
            candidates.append(f)
    else:
        raise ValueError(f"Unsupported path: {path}")

    for candidate in candidates:
        ext = candidate.suffix.lower()

        if ext not in CODE_EXT and ext not in DOC_EXT:
            continue

        try:
            if ext in CODE_EXT:
                content = candidate.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
                report.files.append({
                    "content": content,
                    "source": str(candidate),
                    "type": "code",
                    "hash": get_file_hash(content),
                })

            elif ext in {".pdf", ".docx"}:
                if ext == ".pdf":
                    loaded = load_pdf(candidate)
                else:
                    loaded = load_docx(candidate)

                report.files.extend(loaded)

            else:
                content = candidate.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
                report.files.append({
                    "content": content,
                    "source": str(candidate),
                    "type": "document",
                    "hash": get_file_hash(content),
                })

        except Exception as exc:
            report.errors.append(
                LoadError(
                    source=str(candidate),
                    message=str(exc),
                )
            )

    return report


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
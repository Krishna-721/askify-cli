import os
from pathlib import Path
import fitz  # PyMuPDF


CODE_EXT= {".py",".js",".ts",".cpp",".c",".java",".go",".rs"}
DOC_EXT= {".pdf",".md",".txt",".rst"}
SKIP_DIRS={"__pycache__", ".git", "node_modules", ".venv", "venv", "store"}
SKIP_EXTS = {".pyc", ".pyo", ".lock", ".log"}


def load_path(path:str)->list[dict]:
    p=Path(path)
    files=[    
        f for f in p.rglob("*") 
        if f.is_file() 
        and f.suffix not in SKIP_EXTS
        and not any(skip in f.parts for skip in SKIP_DIRS)
    ]

    if p.is_file():
        files=[p]
    elif p.is_dir():
        files=[f for f in p.rglob("*") if f.is_file()]
    else: 
        raise ValueError(f"Path not found! {path}")

    results=[]
    for f in files:
        ext= f.suffix.lower()
        if ext in CODE_EXT:
            results+=load_code_file(f)
        elif ext in DOC_EXT:
            results+=load_doc_file(f)

    return results
    
def load_code_file(path: Path) -> list[dict]:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return [{"content": content, "source": str(path), "type": "code"}]
    except Exception as e:
        print(f"[skip] {path}: {e}")
        return []
    
def load_doc_file(path:Path)->list[dict]:
    ext=path.suffix.lower()
    try:
        if ext==".pdf":
            return load_pdf(path)
        else:
            content=path.read_text(encoding="utf-8",errors="ignore")
            return [{"content": content, "source":str(path), "type":"document"}]
    except Exception as e:
        print(f"[skip] {path}:{e}")
        return []

def load_pdf(path: Path) -> list[dict]:
    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append({
                "content": text,
                "source": f"{path}::page{i+1}",
                "type": "document"
            })
    return pages
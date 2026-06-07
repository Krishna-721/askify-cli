import ast
import re
from askify.ingester.summarizer import generate_file_summary, generate_project_summary

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_files(files: list[dict]) -> list[dict]:
    chunks = []
    
    file_summaries = []
    for f in files:
        if f["type"] == "code":
            chunks += chunk_code_ast(f)
        else:
            chunks += chunk_document(f)

        summary = generate_file_summary(f)
        file_summaries.append(summary)
        chunks.append(summary)

    chunks.append(generate_project_summary(file_summaries))

    return chunks


def chunk_code(file: dict) -> list[dict]:
    content = file["content"]
    source = file["source"]
    file_hash = file["hash"]

    pattern = r"(?=\n(?:def |class |async def ))"
    parts = re.split(pattern, content)

    chunks = []

    for part in parts:
        part = part.strip()

        if len(part) < 30:
            continue

        chunks.append(
            {
                "content": f"FILE: {source}\n\n{part}",
                "source": source,
                "type": "code",
                "hash": file_hash,
            }
        )

    return chunks


def chunk_document(file: dict) -> list[dict]:
    content = file["content"]
    source = file["source"]
    file_hash = file["hash"]

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= CHUNK_SIZE:
            current += "\n\n" + para

        else:
            if current:
                chunks.append(
                    {
                        "content": f"FILE: {source}\n\n{current.strip()}",
                        "source": source,
                        "type": "document",
                        "hash": file_hash,
                    }
                )

            current = (current[-CHUNK_OVERLAP:] if current else "") + "\n\n" + para

    if current.strip():
        chunks.append(
            {
                "content": f"FILE: {source}\n\n{current.strip()}",
                "source": source,
                "type": "document",
                "hash": file_hash,
            }
        )

    return chunks

def chunk_code_ast(file:dict):
    source = file["content"]
    source_files=source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return chunk_code(file)

    chunks = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            start_line = node.lineno - 1
            end_line = node.end_lineno
            code_chunk = "\n".join(source_files[start_line:end_line])
            chunks.append(
                {
                    "content": f"FILE: {file['source']}\n\n{code_chunk}",
                    "source": file["source"],
                    "type": "code",
                    "hash": file["hash"],
                }
            )
    return chunks
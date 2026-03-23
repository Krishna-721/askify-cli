import re

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_files(files: list[dict]) -> list[dict]:
    chunks = []
    for f in files:
        if f["type"] == "code":
            chunks += chunk_code(f)
        else:
            chunks += chunk_document(f)
    return chunks


def chunk_code(file: dict) -> list[dict]:
    content = file["content"]
    source = file["source"]

    pattern = r'(?=\n(?:def |class |async def ))'
    parts = re.split(pattern, content)

    chunks = []
    for part in parts:
        part = part.strip()
        if len(part) < 30:
            continue
        chunks.append({
            "content": part,
            "source": source,
            "type": "code"
        })
    return chunks


def chunk_document(file: dict) -> list[dict]:
    content = file["content"]
    source = file["source"]

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= CHUNK_SIZE:
            current += "\n\n" + para
        else:
            if current:
                chunks.append({
                    "content": current.strip(),
                    "source": source,
                    "type": "document"
                })
            current = (current[-CHUNK_OVERLAP:] if current else "") + "\n\n" + para

    if current.strip():
        chunks.append({
            "content": current.strip(),
            "source": source,
            "type": "document"
        })

    return chunks
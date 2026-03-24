import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer
import hashlib

from dotenv import load_dotenv
load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_DIR = ".askify/store"

model = SentenceTransformer(MODEL_NAME)

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection("askify_collection")


def already_indexed(source: str, collection) -> bool:
    results = collection.get(where={"source": source})
    return len(results["ids"]) > 0


def make_id(source, content):
    return hashlib.md5((source + content).encode()).hexdigest()


def embed_chunks(chunks: list[dict]):
    collection = get_collection()

    new_chunks = [
        c for c in chunks
        if not already_indexed(c["source"], collection)
    ]

    if not new_chunks:
        print("[askify] Already indexed, skipping...")
        return

    contents = [c["content"] for c in new_chunks]
    sources = [c["source"] for c in new_chunks]
    types = [c["type"] for c in new_chunks]

    embeddings = model.encode(contents).tolist()
    ids = [make_id(sources[i], contents[i]) for i in range(len(new_chunks))]

    collection.upsert(
        ids=ids,
        documents=contents,
        embeddings=embeddings,
        metadatas=[
            {"source": sources[i], "type": types[i]}
            for i in range(len(new_chunks))
        ]
    )

    print(f"[askify] Indexed {len(new_chunks)} chunks")
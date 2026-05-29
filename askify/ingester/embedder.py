import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer
import hashlib

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_DIR = ".askify/store"

model = None


def get_model():
    global model

    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    return model


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection("askify_collection")


def file_needs_reindex(chunk, collection):
    source = chunk["source"]
    file_hash = chunk["hash"]

    existing = collection.get(where={"source": source})

    if not existing["metadatas"] or not existing["metadatas"][0]:
        return True
    old_hash = existing["metadatas"][0].get("hash")
    return old_hash != file_hash


def make_id(source, content):
    return hashlib.md5((source + content).encode()).hexdigest()


def embed_chunks(chunks: list[dict]):
    collection = get_collection()

    new_chunks = [c for c in chunks if file_needs_reindex(c, collection)]

    if not new_chunks:
        print("[askify] Already indexed, skipping...")
        return

    processed_sources = set()

    for chunk in new_chunks:
        source = chunk["source"]

        if source not in processed_sources:
            delete_existing_chunks(source, collection)
            processed_sources.add(source)

    contents = [c["content"] for c in new_chunks]
    sources = [c["source"] for c in new_chunks]
    types = [c["type"] for c in new_chunks]

    embeddings = get_model().encode(contents).tolist()
    ids = [make_id(sources[i], contents[i]) for i in range(len(new_chunks))]

    hashes = [c["hash"] for c in new_chunks]
    collection.upsert(
        ids=ids,
        documents=contents,
        embeddings=embeddings,
        metadatas=[
            {"source": sources[i], "type": types[i], "hash": hashes[i]}
            for i in range(len(new_chunks))
        ],
    )

    print(f"[askify] Indexed {len(new_chunks)} chunks")


def delete_existing_chunks(source, collection):
    existing = collection.get(where={"source": source})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_DIR = "askify/store/chroma"

model=SentenceTransformer(MODEL_NAME)

def get_collection():
    client=chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection("askify_collection")

def embed_chunks(chunks: list[dict]):
    contents=[c["content"] for c in chunks]
    sources=[s["source"] for s in chunks]
    types=[t["type"] for t in chunks]

    embeddings=model.encode(contents).tolist()
    collection=get_collection()

    ids=[f"{sources[i]}::{i}" for i in range(len(chunks))]

    collection.upsert(
    ids=ids,
    documents=contents,
    embeddings=embeddings,
    metadatas=[{"source": sources[i], "type": types[i]} for i in range(len(chunks))]
    )

    print(f"[askify] Indexed {len(chunks)} chunks")
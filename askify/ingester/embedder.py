import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_DIR = "askify/store/chroma"

model=SentenceTransformer(MODEL_NAME)

def get_collection():
    client=chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection("askify_collection")

def already_indexed(source: str, collection) -> bool:
    results = collection.get(where={"source": source})
    return len(results["ids"]) > 0

def embed_chunks(chunks: list[dict]):
    collection=get_collection()
    new_chunks = [c for c in chunks if not already_indexed(c["source"], collection)]
    
    if not new_chunks:
        print("[askify] Already indexed, skipping...")
        return
    contents=[c["content"] for c in new_chunks]
    
    sources=[s["source"] for s in new_chunks]
    types=[t["type"] for t in new_chunks]

    embeddings=model.encode(contents).tolist()
    ids=[f"{sources[i]}::{i}" for i in range(len(new_chunks))]

    collection.upsert(
    ids=ids,
    documents=contents,
    embeddings=embeddings,
    metadatas=[{"source": sources[i], "type": types[i]} for i in range(len(new_chunks))]
    )
    
    print(f"[askify] Indexed {len(new_chunks)} chunks")
from askify.ingester.embedder import get_collection, get_model


def retriever(query: str, top_k: int = 10):
    collection = get_collection()
    query_embedding = get_model().encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    docs = results["documents"][0]
    meta = results["metadatas"][0]

    seen = set()

    unique_docs=[]
    unique_meta=[]
    for doc, meta in zip(docs, meta):
        source = meta["source"]

        if source in seen:
            continue

        seen.add(source)

        unique_docs.append(doc)
        unique_meta.append(meta)

    print("\n[askify] Retrieved:")
    for meta in unique_meta:
        print(f"  -> {meta['source']}")

    return {
        "documents": [unique_docs],
        "metadatas": [unique_meta]
    }
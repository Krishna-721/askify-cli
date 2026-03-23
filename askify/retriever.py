from askify.ingester.embedder import get_collection, model


def retriever(query: str, top_k: int = 5):
    collection = get_collection()
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results
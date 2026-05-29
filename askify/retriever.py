from askify.ingester.embedder import get_collection, get_model


def retriever(query: str, top_k: int = 10):
    collection = get_collection()
    query_embedding = get_model().encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # DEBUG: 
    # print("\n[askify] Retrieved:")
    # for meta in results["metadatas"][0]:
    #     print(f"  -> {meta['source']}")

    return results
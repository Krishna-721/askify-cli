from askify.ingester.embedder import get_collection, get_model
from rank_bm25 import BM25Okapi as bm25
def retriever(query: str, top_k: int = 20):
    collection = get_collection()
    query_embedding = get_model().encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    docs = results["documents"][0]
    meta = results["metadatas"][0]

    # bm25 search results
    bm25_results = bm25_search(query, top_k)
    docs += bm25_results["documents"]
    meta += bm25_results["metadatas"]

    #deduplicate results based on source
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

    # after deduplication, reordered so project_summary is last
    main = [d for d, m in zip(unique_docs, unique_meta) if m["source"] != "project_summary"]
    main_meta = [m for m in unique_meta if m["source"] != "project_summary"]

    proj = [d for d, m in zip(unique_docs, unique_meta) if m["source"] == "project_summary"]
    proj_meta = [m for m in unique_meta if m["source"] == "project_summary"]

    unique_docs = main + proj
    unique_meta = main_meta + proj_meta

    for meta in unique_meta:
        print(f"  -> {meta['source']}")

    return {
        "documents": [unique_docs],
        "metadatas": [unique_meta]
    }

def bm25_search(query,top_k):
    collection=get_collection()
    
    results = collection.get(include=["documents","metadatas"])
    tokenized=[doc.lower().split() for doc in results["documents"]]

    bm25_model = bm25(tokenized)
    scores = bm25_model.get_scores(query.lower().split())
    
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return { "documents": [results["documents"][i] for i in top_indices], "metadatas": [results["metadatas"][i] for i in top_indices] }
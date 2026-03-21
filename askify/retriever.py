from askify.ingester.embedder import get_collection
from askify.ingester.embedder import model

def retriever(query: str, top_k: int=5):
    result=get_collection()
    query_embeddings=model.encode(query).tolist()

    output=result.query(
        query_embeddings=[query_embeddings],n_results=top_k)
    
    return output
from sentence_transformers import CrossEncoder

model= CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank(query:str, docs:list[str], metadatas:list[dict], top_k:int=5):

    scores=model.predict([(query,doc) for doc in docs])
    ranked=sorted(zip(scores,docs,metadatas), reverse=True)[:top_k]

    return {
        "documents": [doc for score, doc, meta in ranked],
        "metadatas": [meta for score, doc, meta in ranked]
    }
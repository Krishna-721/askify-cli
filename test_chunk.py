from askify.ingester.loader import load_path
from askify.ingester.chunker import chunk_files
from askify.ingester.embedder import embed_chunks
from askify.retriever import retriever
from askify.responder import get_llama_response

files = load_path('askify/ingester/loader.py')
chunks = chunk_files(files)

embed_chunks(chunks)
query="How does pdf loading look?"

results=retriever(query)
docs=results["documents"][0]

answer=get_llama_response(query,docs)
print(answer)
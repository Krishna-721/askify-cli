import typer
from askify.ingester import chunker, embedder, loader
from askify.responder import get_llama_response
from askify.retriever import retriever
from rich import print as rprint
from rich.console import Console

app=typer.Typer()
console=Console()

@app.command()
def index(path: str):
    files=loader.load_path(path)
    chunks=chunker.chunk_files(files)
    embeded_chunks=embedder.embed_chunks(chunks)
    print("Files indexing done successfully!")

@app.command()
def ask(path:str, query: str):
    
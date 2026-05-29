import typer
from askify.ingester import chunker, embedder, loader
from askify.responder import get_llama_response
from askify.retriever import retriever

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

import shutil
import json
from pathlib import Path

app = typer.Typer()
console = Console()

def print_banner():
    console.print(r"""
[bold yellow]
    ___        __   _ ____     
   / _ | _____/ /__(_) __/_  __
  / __ |/ (_-</  '_/ / _/ // /
 /_/ |_|___(_)_/\_/_/_/  \_, / 
                         /___/  
[/bold yellow]
[dim]v1.1.0 — Know your stuff. Chat with your code and documents[/dim]
""")

def save_history(query: str, answer: str):
    """Save query and answer to history"""
    history_file = Path(".askify/history.json")
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history = []
    if history_file.exists():
        history = json.loads(history_file.read_text())
    history.append({"query": query, "answer": answer})
    history_file.write_text(json.dumps(history, indent=2))

@app.command()
def index(path: str):
    """Index a folder or file"""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("Indexing files...", total=None)
        files = loader.load_path(path)
        chunks = chunker.chunk_files(files)
        embedder.embed_chunks(chunks)
    console.print("[bold green]✓[/bold green] Indexed successfully!")

@app.command()
def ask(path: str, query: str):
    """Index a path and ask questions"""
    print_banner()
    index(path)
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("Thinking...", total=None)
        results = retriever(query)
        docs = results["documents"][0]
        metadata = results["metadatas"][0]
        answer = get_llama_response(query, docs, metadata)
    console.print(Panel(answer, title="[bold cyan]Askify[/bold cyan]", border_style="cyan"))
    save_history(query, answer)

@app.command()
def chat(path: str):
    """Chat with askify by giving the path"""
    print_banner()
    index(path)
    console.print("[dim]Type 'exit' to quit[/dim]\n")
    while True:
        query = typer.prompt("You")
        if query.lower() == "exit":
            console.print("[dim]Bye.[/dim]")
            break
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task("Thinking...", total=None)
            results = retriever(query)
            metadata = results["metadatas"][0]
            docs = results["documents"][0]
            answer = get_llama_response(query, docs, metadata)
        console.print(Panel(answer, title="[bold cyan]Askify[/bold cyan]", border_style="cyan"))
        save_history(query, answer)

@app.command()
def where(query: str):
    """Find which files are relevant to a keyword"""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("Searching...", total=None)
        results = retriever(query)
        sources = [m["source"] for m in results["metadatas"][0]]
    console.print(f"\n[bold yellow]Relevant files for:[/bold yellow] {query}")
    for source in set(sources):
        console.print(f"  [yellow]→[/yellow] {source}")

@app.command()
def clear():
    """Clear the index"""
    shutil.rmtree(".askify/store", ignore_errors=True)
    console.print("[bold red]✓[/bold red] Index cleared!")

@app.command()
def history():
    """View past queries"""
    history_file = Path(".askify/history.json")
    if not history_file.exists():
        console.print("[yellow]No history yet.[/yellow]")
        return
    history = json.loads(history_file.read_text())
    console.print("\n[bold]Query History[/bold]")
    for i, entry in enumerate(history):
        console.print(f"  [cyan]{i+1}.[/cyan] {entry['query']}")

if __name__ == "__main__":
    app()
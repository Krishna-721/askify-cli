import ast

def build_dependency_graph(files: list[dict]) -> dict:
    graph = {}
    
    for file in files:
        if file["type"] != "code":
            continue
        
        source = file["source"]
        try:
            tree = ast.parse(file["content"])
        except SyntaxError:
            continue
        
        imports = []
        calls = []
        
        # walk tree, collect ImportFrom and Call nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.append(node.module)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)


        graph[source] = {"imports": imports, "calls": calls}
    
    return graph


def graph_to_chunks(graph: dict) -> list[dict]:
    import hashlib
    chunks = []
    
    for source, data in graph.items():
        content = f"DEPENDENCY GRAPH: {source}\n\nImports: {', '.join(data['imports'])}\nCalls: {', '.join(data['calls'])}"
        chunks.append({
            "content": content,
            "source": source,
            "type": "graph",
            "hash": hashlib.md5(content.encode()).hexdigest()
        })
    
    return chunks
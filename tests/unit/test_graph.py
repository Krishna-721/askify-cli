
from askify.graph import graph_to_chunks


def test_graph_chunks_have_consistent_hash_fields():
    graph = {
        "app.py": {
            "imports": ["os", "pathlib"],
            "calls": ["print", "open"],
        }
    }

    chunks = graph_to_chunks(graph)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk["source"] == "graph:app.py"
    assert chunk["type"] == "graph"
    assert chunk["source_hash"] == chunk["chunk_hash"]
    assert chunk["hash"] == chunk["source_hash"]


def test_graph_chunk_hash_changes_when_content_changes():
    graph_before = {
        "app.py": {"imports": ["os"], "calls": ["print"]}
    }
    graph_after = {
        "app.py": {"imports": ["os"], "calls": ["print", "open"]}
    }

    before = graph_to_chunks(graph_before)[0]
    after = graph_to_chunks(graph_after)[0]

    assert before["source_hash"] != after["source_hash"]
    assert before["chunk_hash"] != after["chunk_hash"]

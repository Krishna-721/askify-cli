
from unittest.mock import MagicMock, patch

from askify.ingester import embedder



def make_chunk(source, content, file_hash):
    return {
        "source": source,
        "content": content,
        "type": "code",
        "hash": file_hash,
        "source_hash": file_hash,
    }

def test_new_source_is_indexed():
    collection = MagicMock()
    collection.get.return_value = {
        "ids": [],
        "metadatas": [],
    }

    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    chunks = [
        make_chunk("app.py", "def first(): pass", "hash-1"),
        make_chunk("app.py", "def second(): pass", "hash-1"),
    ]

    with (
        patch.object(embedder, "get_collection", return_value=collection),
        patch.object(embedder, "get_model", return_value=fake_model),
    ):
        embedder.embed_chunks(chunks)

    collection.upsert.assert_called_once()
    assert len(collection.upsert.call_args.kwargs["documents"]) == 2


def test_unchanged_source_is_skipped():
    collection = MagicMock()
    collection.get.return_value = {
        "ids": ["old-chunk"],
        "metadatas": [{"hash": "hash-1"}],
    }

    chunks = [
        make_chunk("app.py", "def first(): pass", "hash-1"),
        make_chunk("app.py", "def second(): pass", "hash-1"),
    ]

    with (
        patch.object(embedder, "get_collection", return_value=collection),
        patch.object(embedder, "get_model") as get_model,
    ):
        embedder.embed_chunks(chunks)

    collection.upsert.assert_not_called()
    collection.delete.assert_not_called()
    get_model.assert_not_called()


def test_changed_source_replaces_all_chunks():
    collection = MagicMock()

    # Existing chunks belong to the previous version.
    collection.get.return_value = {
        "ids": ["old-1", "old-2"],
        "metadatas": [
            {"hash": "hash-old"},
            {"hash": "hash-old"},
        ],
    }

    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    chunks = [
        make_chunk("app.py", "def first(): pass", "hash-new"),
        make_chunk("app.py", "def second(): pass", "hash-new"),
    ]

    with (
        patch.object(embedder, "get_collection", return_value=collection),
        patch.object(embedder, "get_model", return_value=fake_model),
    ):
        embedder.embed_chunks(chunks)

    collection.delete.assert_called_once()

    deleted_ids = collection.delete.call_args.kwargs["ids"]

    assert set(deleted_ids) == {"old-1", "old-2"}
    collection.upsert.assert_called_once()

    indexed_documents = collection.upsert.call_args.kwargs["documents"]
    assert len(indexed_documents) == 2



def test_unchanged_source_hash_is_not_reindexed():
    collection = MagicMock()
    collection.get.return_value = {
        "ids": ["code-1", "summary-1"],
        "metadatas": [
            {"source_hash": "file-hash", "hash": "file-hash"},
            {"source_hash": "file-hash", "hash": "file-hash"},
        ],
    }

    chunk = make_chunk("app.py", "def changed(): pass", "file-hash")

    assert embedder.file_needs_reindex(chunk, collection) is False


def test_graph_and_file_have_separate_source_identities():
    collection = MagicMock()
    collection.get.return_value = {
        "ids": ["code-1"],
        "metadatas": [
            {"source_hash": "file-hash", "hash": "file-hash"},
        ],
    }

    graph_chunk = {
        "source": "graph:app.py",
        "content": "DEPENDENCY GRAPH: app.py\n\nImports: os\nCalls: run",
        "type": "graph",
        "hash": "graph-hash",
        "source_hash": "graph-hash",
    }

    assert embedder.file_needs_reindex(graph_chunk, collection) is True

    collection.get.assert_called_once_with(
        where={"source": "graph:app.py"},
        include=["metadatas"],
    )


def test_inconsistent_incoming_source_hashes_are_rejected():
    collection = MagicMock()

    chunks = [
        make_chunk("app.py", "def first(): pass", "hash-1"),
        make_chunk("app.py", "def second(): pass", "hash-2"),
    ]

    with patch.object(
        embedder, "get_collection", return_value=collection
    ):
        try:
            embedder.embed_chunks(chunks)
            assert collection.get.call_count == 1
        except ValueError as exc:
            assert "Inconsistent source fingerprints" in str(exc)
        else:
            raise AssertionError("Expected inconsistent fingerprints to fail")

    collection.upsert.assert_not_called()



def test_deleted_source_chunks_are_removed(tmp_path):
    collection = MagicMock()

    deleted_file = tmp_path / "deleted.py"

    collection.get.return_value = {
        "ids": ["deleted-chunk-1", "deleted-chunk-2"],
        "metadatas": [
            {
                "source": str(deleted_file),
                "source_hash": "old-hash",
            },
            {
                "source": str(deleted_file),
                "source_hash": "old-hash",
            },
        ],
    }

    with (
        patch.object(embedder, "get_collection", return_value=collection),
        patch.object(embedder, "get_model") as get_model,
    ):
        embedder.embed_chunks([], scan_path=str(tmp_path))

    collection.delete.assert_called_once_with(
        ids=["deleted-chunk-1", "deleted-chunk-2"]
    )

    get_model.assert_not_called()


def test_stale_cleanup_does_not_delete_sources_outside_scan_scope(tmp_path):
    collection = MagicMock()

    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"

    project_a.mkdir()
    project_b.mkdir()

    active_file = project_a / "app.py"
    deleted_file = project_a / "deleted.py"
    external_file = project_b / "main.py"

    collection.get.return_value = {
        "ids": ["deleted-1", "external-1"],
        "metadatas": [
            {"source": str(deleted_file)},
            {"source": str(external_file)},
        ],
    }

    embedder.delete_stale_sources(
        active_sources={str(active_file)},
        collection=collection,
        scan_path=str(project_a),
    )

    collection.delete.assert_called_once_with(ids=["deleted-1"])


def test_old_chunks_are_preserved_when_upsert_fails():
    collection = MagicMock()

    collection.get.return_value = {
        "ids": ["old-1", "old-2"],
        "metadatas": [
            {"source_hash": "hash-old", "hash": "hash-old"},
            {"source_hash": "hash-old", "hash": "hash-old"},
        ],
    }

    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    collection.upsert.side_effect = RuntimeError("Database write failed")

    chunks = [
        make_chunk("app.py", "def first(): pass", "hash-new"),
        make_chunk("app.py", "def second(): pass", "hash-new"),
    ]

    with (
        patch.object(embedder, "get_collection", return_value=collection),
        patch.object(embedder, "get_model", return_value=fake_model),
    ):
        try:
            embedder.embed_chunks(chunks)
        except RuntimeError as exc:
            assert "Database write failed" in str(exc)
        else:
            raise AssertionError("Expected database write to fail")

    collection.delete.assert_not_called()

# Regression test
def test_reindex_preserves_reused_chunk_ids():
    collection = MagicMock()

    unchanged_content = "def unchanged(): pass"
    added_content = "def added(): pass"

    unchanged_id = embedder.make_id(
        "app.py", unchanged_content
    )

    collection.get.return_value = {
        "ids": [unchanged_id, "obsolete-id"],
        "metadatas": [
            {"source_hash": "old-hash", "hash": "old-hash"},
            {"source_hash": "old-hash", "hash": "old-hash"},
        ],
    }

    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    chunks = [
        make_chunk(
            "app.py",
            unchanged_content,
            "new-hash",
        ),
        make_chunk(
            "app.py",
            added_content,
            "new-hash",
        ),
    ]

    with patch.object(
        embedder, "get_collection", return_value=collection
    ), patch.object(
        embedder, "get_model", return_value=fake_model
    ):
        embedder.embed_chunks(chunks)

    upserted_ids = collection.upsert.call_args.kwargs["ids"]

    # The unchanged chunk must still be included in the new index.
    assert unchanged_id in upserted_ids

    # Only the obsolete chunk should be deleted.
    collection.delete.assert_called_once_with(
        ids=["obsolete-id"]
    )

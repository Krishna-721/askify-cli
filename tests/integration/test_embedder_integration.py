
from unittest.mock import patch, MagicMock

from askify.ingester import embedder


def make_chunk(source, content, file_hash):
    return {
        "source": source,
        "content": content,
        "type": "code",
        "hash": file_hash,
        "source_hash": file_hash,
    }


def test_real_chromadb_indexes_and_replaces_chunks(
    tmp_path,
    monkeypatch,
):
    # Use an isolated temporary database.
    db_path = tmp_path / "chroma"
    monkeypatch.setattr(
        embedder,
        "CHROMA_DIR",
        str(db_path),
    )

    # Avoid downloading/loading the actual embedding model.
    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    old_chunks = [
        make_chunk(
            "app.py",
            "def unchanged(): pass",
            "old-hash",
        ),
        make_chunk(
            "app.py",
            "def removed(): pass",
            "old-hash",
        ),
    ]

    new_chunks = [
        make_chunk(
            "app.py",
            "def unchanged(): pass",
            "new-hash",
        ),
        make_chunk(
            "app.py",
            "def added(): pass",
            "new-hash",
        ),
    ]

    with patch.object(
        embedder,
        "get_model",
        return_value=fake_model,
    ):
        # First indexing.
        embedder.embed_chunks(old_chunks)

        collection = embedder.get_collection()

        first_result = collection.get(
            where={"source": "app.py"},
            include=["documents"],
        )

        assert set(first_result["documents"]) == {
            "def unchanged(): pass",
            "def removed(): pass",
        }

        # Reindex after changing the source.
        embedder.embed_chunks(new_chunks)

        second_result = collection.get(
            where={"source": "app.py"},
            include=["documents"],
        )

        assert set(second_result["documents"]) == {
            "def unchanged(): pass",
            "def added(): pass",
        }


def test_real_chromadb_skips_unchanged_source(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "chroma"
    monkeypatch.setattr(
        embedder,
        "CHROMA_DIR",
        str(db_path),
    )

    chunks = [
        make_chunk(
            "app.py",
            "def hello(): pass",
            "same-hash",
        ),
    ]

    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [
        [0.1, 0.2],
    ]

    with patch.object(
        embedder,
        "get_model",
        return_value=fake_model,
    ):
        # First indexing.
        embedder.embed_chunks(chunks)

        collection = embedder.get_collection()

        first_result = collection.get(
            where={"source": "app.py"},
            include=["documents", "metadatas"],
        )

        assert len(first_result["ids"]) == 1

        # Reset the model mock to detect unnecessary embedding.
        fake_model.reset_mock()

        # Index the exact same source again.
        embedder.embed_chunks(chunks)

        second_result = collection.get(
            where={"source": "app.py"},
            include=["documents", "metadatas"],
        )

        # No duplicate records.
        assert len(second_result["ids"]) == 1

        # Embedding should not run again.
        fake_model.encode.assert_not_called()


def test_real_chromadb_persists_data_across_clients(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "chroma"

    monkeypatch.setattr(
        embedder,
        "CHROMA_DIR",
        str(db_path),
    )

    chunks = [
        make_chunk(
            "app.py",
            "def persistent_function(): pass",
            "persistent-hash",
        ),
    ]

    fake_model = MagicMock()
    fake_model.encode.return_value.tolist.return_value = [
        [0.1, 0.2],
    ]

    with patch.object(
        embedder,
        "get_model",
        return_value=fake_model,
    ):
        embedder.embed_chunks(chunks)

    # First client reads the indexed data.
    first_collection = embedder.get_collection()

    first_result = first_collection.get(
        where={"source": "app.py"},
        include=["documents"],
    )

    assert len(first_result["ids"]) == 1

    # Create another client pointing to the same database.
    second_collection = embedder.get_collection()

    second_result = second_collection.get(
        where={"source": "app.py"},
        include=["documents"],
    )

    assert second_result["ids"] == first_result["ids"]
    assert second_result["documents"] == first_result["documents"]


def test_real_chromadb_removes_stale_sources_within_scan_scope(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "chroma"
    project_dir = tmp_path / "project"
    other_dir = tmp_path / "other"

    project_dir.mkdir()
    other_dir.mkdir()

    monkeypatch.setattr(
        embedder,
        "CHROMA_DIR",
        str(db_path),
    )

    collection = embedder.get_collection()

    project_file = str(project_dir / "app.py")
    other_file = str(other_dir / "other.py")

    # Insert two real records into ChromaDB.
    collection.add(
        ids=["project-chunk", "other-chunk"],
        documents=[
            "def project_function(): pass",
            "def other_function(): pass",
        ],
        embeddings=[
            [0.1, 0.2],
            [0.3, 0.4],
        ],
        metadatas=[
            {
                "source": project_file,
                "type": "code",
                "source_hash": "project-hash",
            },
            {
                "source": other_file,
                "type": "code",
                "source_hash": "other-hash",
            },
        ],
    )

    # The project scan no longer discovers app.py.
    embedder.delete_stale_sources(
        active_sources=set(),
        collection=collection,
        scan_path=str(project_dir),
    )

    remaining = collection.get(
        include=["metadatas"],
    )

    remaining_ids = set(remaining["ids"])

    # Project data should be removed.
    assert "project-chunk" not in remaining_ids

    # Data outside the scan directory must survive.
    assert "other-chunk" in remaining_ids

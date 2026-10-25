
from pathlib import Path

import pytest
from typer.testing import CliRunner

from askify.cli import app
from askify.ingester import chunker, embedder, loader


runner = CliRunner()


# --------------------------------------------------
# Test helpers
# --------------------------------------------------

class FakeEmbeddings:
    """Provides the same tolist() interface as model embeddings."""

    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows


class FakeModel:
    """A lightweight replacement for the sentence transformer."""

    def __init__(self):
        self.calls = 0

    def encode(self, contents):
        self.calls += 1

        return FakeEmbeddings(
            [[0.1, 0.2] for _ in contents]
        )


def fake_file_summary(file):
    """Generate a predictable file summary without an LLM."""

    return {
        "content": f"Summary of {file['source']}",
        "source": file["source"],
        "type": "summary",
        "hash": file["hash"],
        "source_hash": file["hash"],
    }


def fake_project_summary(summaries):
    """Generate a predictable project summary without an LLM."""

    content = "\n".join(
        summary["content"] for summary in summaries
    )

    return {
        "content": content or "Empty project",
        "source": "__project_summary__",
        "type": "summary",
        "hash": "project-summary-hash",
        "source_hash": "project-summary-hash",
    }


def configure_test_environment(tmp_path, monkeypatch):
    """Configure real ChromaDB with fake AI dependencies."""

    db_path = tmp_path / "chroma"

    monkeypatch.setattr(
        embedder,
        "CHROMA_DIR",
        str(db_path),
    )

    fake_model = FakeModel()

    monkeypatch.setattr(
        embedder,
        "get_model",
        lambda: fake_model,
    )

    monkeypatch.setattr(
        chunker,
        "generate_file_summary",
        fake_file_summary,
    )

    monkeypatch.setattr(
        chunker,
        "generate_project_summary",
        fake_project_summary,
    )

    return fake_model


def create_python_project(tmp_path):
    """Create a small project for CLI indexing."""

    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    source_file = project_dir / "app.py"

    source_file.write_text(
        """
def hello():
    return "Hello from Askify"


def calculate_total(a, b):
    return a + b
""",
        encoding="utf-8",
    )

    return project_dir, source_file


# --------------------------------------------------
# Test 1: Complete CLI indexing
# --------------------------------------------------

def test_cli_indexes_python_project(
    tmp_path,
    monkeypatch,
):
    configure_test_environment(tmp_path, monkeypatch)

    project_dir, source_file = create_python_project(tmp_path)

    result = runner.invoke(
        app,
        ["index", str(project_dir)],
    )

    assert result.exit_code == 0, result.output
    assert "Indexed successfully" in result.output

    collection = embedder.get_collection()

    indexed = collection.get(
        include=["documents", "metadatas"],
    )

    assert len(indexed["ids"]) > 0

    sources = {
        metadata["source"]
        for metadata in indexed["metadatas"]
        if metadata is not None
    }

    assert str(source_file) in sources

    documents = "\n".join(indexed["documents"])

    assert "hello" in documents
    assert "calculate_total" in documents


# --------------------------------------------------
# Test 2: Reindexing is idempotent
# --------------------------------------------------

def test_cli_reindex_does_not_create_duplicates(
    tmp_path,
    monkeypatch,
):
    fake_model = configure_test_environment(
        tmp_path,
        monkeypatch,
    )

    project_dir, _ = create_python_project(tmp_path)

    first_result = runner.invoke(
        app,
        ["index", str(project_dir)],
    )

    assert first_result.exit_code == 0, first_result.output

    collection = embedder.get_collection()

    first_index = collection.get(
        include=["documents", "metadatas"],
    )

    first_ids = set(first_index["ids"])
    first_count = len(first_ids)
    first_embedding_calls = fake_model.calls

    assert first_count > 0
    assert first_embedding_calls > 0

    # Run indexing again without changing any files.
    second_result = runner.invoke(
        app,
        ["index", str(project_dir)],
    )

    assert second_result.exit_code == 0, second_result.output

    second_index = collection.get(
        include=["documents", "metadatas"],
    )

    second_ids = set(second_index["ids"])

    # No duplicate or missing records.
    assert second_ids == first_ids
    assert len(second_ids) == first_count

    # No new embedding generation.
    assert fake_model.calls == first_embedding_calls


# --------------------------------------------------
# Test 3: Deleted files are cleaned up
# --------------------------------------------------

def test_cli_removes_deleted_file_chunks(
    tmp_path,
    monkeypatch,
):
    configure_test_environment(tmp_path, monkeypatch)

    project_dir, source_file = create_python_project(tmp_path)

    # First index the project.
    first_result = runner.invoke(
        app,
        ["index", str(project_dir)],
    )

    assert first_result.exit_code == 0, first_result.output

    collection = embedder.get_collection()

    before_deletion = collection.get(
        include=["metadatas"],
    )

    assert any(
        metadata
        and Path(
            metadata["source"].removeprefix("graph:")
            .split("::page", 1)[0]
        ).resolve() == source_file.resolve()
        for metadata in before_deletion["metadatas"]
    )

    # Delete the actual source file.
    source_file.unlink()

    # Index the project again.
    second_result = runner.invoke(
        app,
        ["index", str(project_dir)],
    )

    assert second_result.exit_code == 0, second_result.output

    after_deletion = collection.get(
        include=["metadatas"],
    )

    remaining_sources = [
        metadata["source"]
        for metadata in after_deletion["metadatas"]
        if metadata is not None
    ]

    # No chunks belonging to the deleted file should remain.
    for source in remaining_sources:
        original_source = source.removeprefix("graph:")
        original_source = original_source.split("::page", 1)[0]

        assert Path(original_source).resolve() != source_file.resolve()


# --------------------------------------------------
# Test 4: Loader failures must not report success
# --------------------------------------------------

def test_cli_does_not_report_success_when_loading_fails(
    tmp_path,
    monkeypatch,
):
    project_dir, _ = create_python_project(tmp_path)

    def failing_loader(path):
        raise RuntimeError("Simulated file loading failure")

    monkeypatch.setattr(
        loader,
        "load_path",
        failing_loader,
    )

    result = runner.invoke(
        app,
        ["index", str(project_dir)],
    )

    assert result.exit_code != 0

    assert "Indexed successfully" not in result.output

    assert isinstance(result.exception, RuntimeError)
    assert "Simulated file loading failure" in str(result.exception)

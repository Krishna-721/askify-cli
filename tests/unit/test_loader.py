
from pathlib import Path

import pytest

from askify.ingester import loader


def test_load_path_rejects_missing_path(tmp_path):
    missing_path = tmp_path / "does_not_exist"

    with pytest.raises(ValueError, match="Path not found"):
        loader.load_path(str(missing_path))


def test_load_path_loads_supported_python_file(tmp_path):
    source_file = tmp_path / "app.py"
    source_file.write_text(
        "def greet():\n    return 'hello'\n",
        encoding="utf-8",
    )

    files = loader.load_path(str(source_file))

    assert len(files) == 1
    assert files[0]["source"] == str(source_file)
    assert files[0]["type"] == "code"
    assert files[0]["content"] == (
        "def greet():\n    return 'hello'\n"
    )
    assert files[0]["hash"] == loader.get_file_hash(
        files[0]["content"]
    )


def test_load_path_ignores_unsupported_file_types(tmp_path):
    unsupported_file = tmp_path / "notes.xlsx"
    unsupported_file.write_text("not a supported document")

    files = loader.load_path(str(tmp_path))

    assert files == []


def test_load_path_skips_configured_directories(tmp_path):
    ignored_dir = tmp_path / ".git"
    ignored_dir.mkdir()

    ignored_file = ignored_dir / "secret.py"
    ignored_file.write_text("def ignored(): pass", encoding="utf-8")

    files = loader.load_path(str(tmp_path))

    assert files == []


def test_load_path_discovers_supported_files_recursively(tmp_path):
    nested_dir = tmp_path / "src" / "utils"
    nested_dir.mkdir(parents=True)

    python_file = nested_dir / "helper.py"
    python_file.write_text(
        "def helper():\n    return 42\n",
        encoding="utf-8",
    )

    readme_file = tmp_path / "README.md"
    readme_file.write_text(
        "# Example\n\nA small project.",
        encoding="utf-8",
    )

    files = loader.load_path(str(tmp_path))

    sources = {item["source"] for item in files}

    assert str(python_file) in sources
    assert str(readme_file) in sources
    assert len(files) == 2


def test_load_code_file_reports_read_failure(tmp_path, monkeypatch):
    source_file = tmp_path / "broken.py"
    source_file.write_text("def example(): pass", encoding="utf-8")

    def fail_read(*args, **kwargs):
        raise PermissionError("Access denied")

    monkeypatch.setattr(Path, "read_text", fail_read)

    files = loader.load_code_file(source_file)

    assert files == []



def test_scan_report_records_file_read_failure(tmp_path, monkeypatch):
    source_file = tmp_path / "broken.py"
    source_file.write_text(
        "def example(): pass",
        encoding="utf-8",
    )

    def fail_read(*args, **kwargs):
        raise PermissionError("Access denied")

    monkeypatch.setattr(Path, "read_text", fail_read)

    report = loader.load_path_with_report(str(tmp_path))

    assert report.files == []
    assert len(report.errors) == 1
    assert str(source_file) in report.errors[0].source
    assert "Access denied" in report.errors[0].message


def test_load_path_raises_when_a_file_read_fails(tmp_path, monkeypatch):
    source_file = tmp_path / "broken.py"
    source_file.write_text(
        "def example(): pass",
        encoding="utf-8",
    )

    def fail_read(*args, **kwargs):
        raise PermissionError("Access denied")

    monkeypatch.setattr(Path, "read_text", fail_read)

    with pytest.raises(RuntimeError, match="Failed to load one or more files"):
        loader.load_path(str(tmp_path))

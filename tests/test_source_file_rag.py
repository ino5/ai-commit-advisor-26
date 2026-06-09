from pathlib import Path

from src.rag.chunker import _is_source_file, chunk_lines
from src.rag.source_verifier import hash_text, verify_source_file_chunk


def test_chunk_lines_preserves_line_ranges():
    chunks = chunk_lines(["alpha", "beta", "gamma"], chunk_size=10, overlap=0)

    assert chunks == [
        (1, 2, "alpha\nbeta"),
        (3, 3, "gamma"),
    ]


def test_is_source_file_excludes_virtualenv_and_binary_suffix(tmp_path: Path):
    repo = tmp_path
    source = repo / "src" / "app.py"
    java_source = repo / "src" / "main" / "java" / "OrderService.java"
    jsp_source = repo / "src" / "main" / "webapp" / "WEB-INF" / "views" / "orders" / "new.jsp"
    binary = repo / "docs" / "image.png"
    venv_file = repo / ".venv" / "Lib" / "site-packages" / "x.py"

    assert _is_source_file(source, repo) is True
    assert _is_source_file(java_source, repo) is True
    assert _is_source_file(jsp_source, repo) is True
    assert _is_source_file(binary, repo) is False
    assert _is_source_file(venv_file, repo) is False


def test_verify_source_file_chunk_detects_stale_line_range(tmp_path: Path):
    repo = tmp_path
    source = repo / "src" / "service.py"
    source.parent.mkdir()
    source.write_text("one\ntwo\nthree\n", encoding="utf-8")
    metadata = {
        "file_path": "src/service.py",
        "line_start": 1,
        "line_end": 2,
        "chunk_content_hash": hash_text("one\ntwo"),
    }

    verified = verify_source_file_chunk(str(repo), metadata)
    assert verified.status == "verified"

    source.write_text("one\nchanged\nthree\n", encoding="utf-8")
    stale = verify_source_file_chunk(str(repo), metadata)
    assert stale.status == "stale"


def test_verify_source_file_chunk_rejects_deleted_file(tmp_path: Path):
    metadata = {
        "file_path": "missing.py",
        "line_start": 1,
        "line_end": 1,
        "chunk_content_hash": hash_text("missing"),
    }

    verification = verify_source_file_chunk(str(tmp_path), metadata)

    assert verification.status == "invalid"

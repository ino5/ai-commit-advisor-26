from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import DocumentChunk, Project, VectorItem
from src.rag.chunker import SOURCE_FILE_TYPE
from src.rag.source_index_service import ChangedSourceFile, refresh_changed_source_files
from src.utils.config import settings


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _create_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "src").mkdir()
    (repo / "src" / "service.py").write_text("def value():\n    return 'old'\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    return repo


def _create_project(db, repo: Path) -> Project:
    project = Project(name=f"incremental-index-test-{uuid.uuid4()}", git_repo_path=str(repo))
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _source_chunks(db, project_id: int) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
        .order_by(DocumentChunk.id)
        .all()
    )


def test_incremental_modified_file_replaces_old_chunks_and_vectors(tmp_path: Path):
    init_db()
    repo = _create_repo(tmp_path)

    with SessionLocal() as db:
        project = _create_project(db, repo)
        try:
            first = refresh_changed_source_files(
                db,
                project,
                [ChangedSourceFile(file_path="src/service.py", change_type="Added")],
            )
            old_chunk = _source_chunks(db, project.id)[0]
            db.add(
                VectorItem(
                    chunk_id=old_chunk.id,
                    embedding_model="test-model",
                    embedding=[0.0] * settings.pgvector_dimension,
                )
            )
            db.commit()

            (repo / "src" / "service.py").write_text("def value():\n    return 'new'\n", encoding="utf-8")
            result = refresh_changed_source_files(
                db,
                project,
                [ChangedSourceFile(file_path="src/service.py", change_type="Modified")],
            )

            chunks = _source_chunks(db, project.id)
            assert first.chunk_result.created_count == 1
            assert result.chunk_result.created_count == 1
            assert len(chunks) == 1
            assert "return 'new'" in chunks[0].chunk_text
            assert chunks[0].raw_metadata["embedding_status"] == "pending"
            assert db.query(VectorItem).join(DocumentChunk).filter(DocumentChunk.project_id == project.id).count() == 0
        finally:
            db.delete(project)
            db.commit()


def test_incremental_deleted_file_removes_chunks_and_vectors(tmp_path: Path):
    init_db()
    repo = _create_repo(tmp_path)

    with SessionLocal() as db:
        project = _create_project(db, repo)
        try:
            refresh_changed_source_files(
                db,
                project,
                [ChangedSourceFile(file_path="src/service.py", change_type="Added")],
            )
            chunk = _source_chunks(db, project.id)[0]
            db.add(
                VectorItem(
                    chunk_id=chunk.id,
                    embedding_model="test-model",
                    embedding=[0.0] * settings.pgvector_dimension,
                )
            )
            db.commit()
            (repo / "src" / "service.py").unlink()

            result = refresh_changed_source_files(
                db,
                project,
                [ChangedSourceFile(file_path="src/service.py", change_type="Deleted")],
            )

            assert result.deleted_file_count == 1
            assert _source_chunks(db, project.id) == []
            assert db.query(VectorItem).join(DocumentChunk).filter(DocumentChunk.project_id == project.id).count() == 0
        finally:
            db.delete(project)
            db.commit()


def test_incremental_renamed_file_removes_old_path_and_indexes_new_path(tmp_path: Path):
    init_db()
    repo = _create_repo(tmp_path)

    with SessionLocal() as db:
        project = _create_project(db, repo)
        try:
            refresh_changed_source_files(
                db,
                project,
                [ChangedSourceFile(file_path="src/service.py", change_type="Added")],
            )
            (repo / "src" / "renamed_service.py").write_text(
                (repo / "src" / "service.py").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (repo / "src" / "service.py").unlink()

            result = refresh_changed_source_files(
                db,
                project,
                [
                    ChangedSourceFile(
                        file_path="src/renamed_service.py",
                        old_file_path="src/service.py",
                        change_type="Renamed",
                    )
                ],
            )

            chunks = _source_chunks(db, project.id)
            assert result.deleted_file_count == 1
            assert result.chunk_result.created_count == 1
            assert [chunk.raw_metadata["file_path"] for chunk in chunks] == ["src/renamed_service.py"]
        finally:
            db.delete(project)
            db.commit()


def test_incremental_non_source_file_is_skipped(tmp_path: Path):
    init_db()
    repo = _create_repo(tmp_path)
    (repo / "docs").mkdir()
    (repo / "docs" / "image.png").write_bytes(b"\x89PNG\r\n")

    with SessionLocal() as db:
        project = _create_project(db, repo)
        try:
            result = refresh_changed_source_files(
                db,
                project,
                [ChangedSourceFile(file_path="docs/image.png", change_type="Added")],
            )

            assert result.indexed_file_count == 1
            assert result.chunk_result.created_count == 0
            assert result.chunk_result.skipped_count == 1
            assert _source_chunks(db, project.id) == []
        finally:
            db.delete(project)
            db.commit()

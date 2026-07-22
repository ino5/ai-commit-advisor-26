from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import NoResultFound

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import (
    CommitFile,
    DocumentChunk,
    GitCommit,
    Program,
    ProgramCommitMapping,
    Project,
)
from src.rag.chunker import build_project_chunks
from src.rag.vector_store import VectorStore
from src.services.commit_impact_service import get_commit_impact_analysis
from src.services.git_service import sync_git_repository
from src.services.neo4j_graph_service import build_project_graph_payload
from src.utils.config import settings


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _create_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "shared-repository"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "scope@example.local")
    _git(repo, "config", "user.name", "Scope Tester")
    (repo / "src").mkdir()
    (repo / "src" / "payment.py").write_text("def pay():\n    return 'ok'\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Add payment flow")
    return repo, _git(repo, "rev-parse", "HEAD")


def test_git_commit_model_uses_only_project_scoped_hash_uniqueness() -> None:
    unique_constraints = {
        constraint.name: tuple(column.name for column in constraint.columns)
        for constraint in GitCommit.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert unique_constraints["uq_git_commits_project_hash"] == ("project_id", "commit_hash")
    assert "uq_git_commits_commit_hash" not in unique_constraints


def test_same_repository_isolated_across_relational_rag_vector_and_graph_stores(tmp_path: Path) -> None:
    init_db()
    repo, commit_hash = _create_repo(tmp_path)
    suffix = uuid.uuid4()

    with SessionLocal() as db:
        project_a = Project(name=f"project-scope-a-{suffix}", git_repo_path=str(repo))
        project_b = Project(name=f"project-scope-b-{suffix}", git_repo_path=str(repo))
        db.add_all([project_a, project_b])
        db.commit()

        try:
            first_sync = sync_git_repository(db, project_a, full=True)
            second_sync = sync_git_repository(db, project_b, full=True)
            repeated_sync = sync_git_repository(db, project_b, full=True)

            assert first_sync.errors == []
            assert second_sync.errors == []
            assert first_sync.saved_commit_count == 1
            assert second_sync.saved_commit_count == 1
            assert repeated_sync.saved_commit_count == 0
            assert repeated_sync.skipped_duplicate_count == 1

            commit_a = (
                db.query(GitCommit)
                .filter(GitCommit.project_id == project_a.id, GitCommit.commit_hash == commit_hash)
                .one()
            )
            commit_b = (
                db.query(GitCommit)
                .filter(GitCommit.project_id == project_b.id, GitCommit.commit_hash == commit_hash)
                .one()
            )
            assert commit_a.id != commit_b.id
            assert commit_a.project_id == project_a.id
            assert commit_b.project_id == project_b.id
            assert db.query(GitCommit).filter(GitCommit.commit_hash == commit_hash).count() == 2
            assert (
                db.query(CommitFile)
                .join(GitCommit, CommitFile.commit_id == GitCommit.id)
                .filter(GitCommit.project_id == project_a.id)
                .count()
                == 1
            )
            assert (
                db.query(CommitFile)
                .join(GitCommit, CommitFile.commit_id == GitCommit.id)
                .filter(GitCommit.project_id == project_b.id)
                .count()
                == 1
            )

            program_a = Program(project_id=project_a.id, program_id="PAY-A", program_name="결제 A")
            program_b = Program(project_id=project_b.id, program_id="PAY-B", program_name="결제 B")
            db.add_all([program_a, program_b])
            db.flush()
            mapping_a = ProgramCommitMapping(
                program_id=program_a.id,
                commit_id=commit_a.id,
                is_related=True,
                relevance_score=90,
                implementation_status="구현됨",
            )
            mapping_b = ProgramCommitMapping(
                program_id=program_b.id,
                commit_id=commit_b.id,
                is_related=True,
                relevance_score=80,
                implementation_status="구현됨",
            )
            db.add_all([mapping_a, mapping_b])
            db.commit()

            assert mapping_a.commit_id != mapping_b.commit_id
            assert get_commit_impact_analysis(db, project_a.id, commit_a.id).programs[0].program_id == "PAY-A"
            with pytest.raises(NoResultFound):
                get_commit_impact_analysis(db, project_b.id, commit_a.id)

            chunks_a = build_project_chunks(db, project_a.id)
            chunks_b = build_project_chunks(db, project_b.id)
            assert chunks_a.created_count == 3
            assert chunks_b.created_count == 3

            commit_chunk_a = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.project_id == project_a.id, DocumentChunk.source_type == "commit")
                .one()
            )
            commit_chunk_b = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.project_id == project_b.id, DocumentChunk.source_type == "commit")
                .one()
            )
            assert commit_chunk_a.id != commit_chunk_b.id
            assert commit_chunk_a.source_id == str(commit_a.id)
            assert commit_chunk_b.source_id == str(commit_b.id)
            assert commit_chunk_a.raw_metadata["commit_hash"] == commit_hash
            assert commit_chunk_b.raw_metadata["commit_hash"] == commit_hash

            embedding = [0.0] * settings.pgvector_dimension
            embedding[0] = 1.0
            vector_store = VectorStore(db)
            vector_store.save_vector(commit_chunk_a.id, embedding, embedding_model="scope-test")
            vector_store.save_vector(commit_chunk_b.id, embedding, embedding_model="scope-test")

            search_a = vector_store.search_similar(
                embedding,
                project_id=project_a.id,
                source_types=["commit"],
                embedding_model="scope-test",
            )
            search_b = vector_store.search_similar(
                embedding,
                project_id=project_b.id,
                source_types=["commit"],
                embedding_model="scope-test",
            )
            assert [row["chunk"].id for row in search_a] == [commit_chunk_a.id]
            assert [row["chunk"].id for row in search_b] == [commit_chunk_b.id]

            graph_a = build_project_graph_payload(db, project_a.id)
            graph_b = build_project_graph_payload(db, project_b.id)
            graph_a_commit_ids = {node.node_id for node in graph_a.nodes if node.node_type == "commit"}
            graph_b_commit_ids = {node.node_id for node in graph_b.nodes if node.node_type == "commit"}
            assert graph_a_commit_ids == {f"p{project_a.id}:commit:{commit_hash}"}
            assert graph_b_commit_ids == {f"p{project_b.id}:commit:{commit_hash}"}
            assert graph_a_commit_ids.isdisjoint(graph_b_commit_ids)
        finally:
            db.rollback()
            for project_id in (project_a.id, project_b.id):
                project = db.get(Project, project_id)
                if project is not None:
                    db.delete(project)
            db.commit()

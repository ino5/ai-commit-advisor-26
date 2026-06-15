from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import CommitFile, GitCommit, Program, Project, RiskFinding
from src.rag.source_index_service import SourceIndexStatus
from src.services import git_followup_service
from src.services.git_followup_service import (
    GROUP_LATER,
    GROUP_RECOMMENDED,
    STATUS_DONE,
    STATUS_RECOMMENDED,
    STATUS_WAITING,
    build_git_sync_follow_up,
)
from src.services.git_repository_status_service import GitRepositoryStatus
from src.services.git_service import GitSyncResult
from src.services.neo4j_graph_service import Neo4jGraphFreshness


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _repo_status(head_hash: str = "head123456789") -> GitRepositoryStatus:
    return GitRepositoryStatus(
        configured_path="C:/repo",
        resolved_path="C:/repo",
        is_repository=True,
        head_hash=head_hash,
        db_last_synced_commit_hash=head_hash,
        db_matches_head=True,
    )


def _source_status(
    *,
    needs_reindex: bool,
    missing_embedding_count: int,
    source_chunk_count: int = 10,
    source_vector_count: int = 5,
) -> SourceIndexStatus:
    return SourceIndexStatus(
        repo_path="C:/repo",
        current_head_hash="head123456789",
        latest_indexed_head_hash="old123456789",
        indexed_head_hashes=["old123456789"],
        source_chunk_count=source_chunk_count,
        source_vector_count=source_vector_count,
        missing_embedding_count=missing_embedding_count,
        head_mismatch_chunk_count=source_chunk_count if needs_reindex else 0,
        stale_chunk_count=source_chunk_count if needs_reindex else 0,
        invalid_chunk_count=0,
        needs_reindex=needs_reindex,
        errors=[],
    )


def test_git_sync_follow_up_recommends_restartable_post_sync_actions(monkeypatch):
    init_db()
    monkeypatch.setattr(git_followup_service, "get_repository_status", lambda project: _repo_status())
    monkeypatch.setattr(
        git_followup_service,
        "get_source_index_status",
        lambda db, project: _source_status(needs_reindex=True, missing_embedding_count=4),
    )
    monkeypatch.setattr(
        git_followup_service,
        "get_changed_source_files_since_latest_index",
        lambda db, project: ["src/payment/PaymentService.java", "src/order/OrderService.java"],
    )
    monkeypatch.setattr(
        git_followup_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness(
            "stale",
            "DB Git Sync HEAD가 graph sync 이후 변경되었습니다.",
            repo_head_hash="head123456789",
            db_sync_head_hash="head123456789",
            graph_sync_head_hash="old123456789",
            node_count=10,
            edge_count=20,
        ),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("followup-project"), git_repo_path="C:/repo")
        db.add(project)
        db.flush()
        db.add(Program(project_id=project.id, program_id=_unique("P"), program_name="Payment"))
        commit_a = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="payment update",
            committed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        commit_b = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="order update",
            mapping_analysis_status="failed",
            committed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        db.add_all([commit_a, commit_b])
        db.flush()
        db.add_all(
            [
                CommitFile(commit_id=commit_a.id, git_commit_id=commit_a.id, file_path="src/payment/PaymentService.java"),
                CommitFile(commit_id=commit_b.id, git_commit_id=commit_b.id, file_path="src/order/OrderService.java"),
            ]
        )
        db.commit()

        try:
            sync_result = GitSyncResult(saved_commit_count=2, saved_file_count=2, latest_commit_hash="head123456789")
            summary = build_git_sync_follow_up(db, project.id, sync_result)
            steps = {step.step_id: step for step in summary.steps}

            assert summary.synced_commit_count == 2
            assert summary.synced_file_count == 2
            assert [step.step_id for step in summary.recommended_steps] == [
                "source_index",
                "embedding",
                "mapping",
                "risk_analysis",
                "knowledge_graph",
            ]
            assert steps["source_index"].status == STATUS_RECOMMENDED
            assert "changed_files=2" in steps["source_index"].current_value
            assert steps["embedding"].status == STATUS_WAITING
            assert steps["mapping"].status == STATUS_RECOMMENDED
            assert "pending=2" in steps["mapping"].current_value
            assert "failed=1" in steps["mapping"].current_value
            assert steps["risk_analysis"].status == STATUS_WAITING
            assert steps["knowledge_graph"].status == STATUS_WAITING
            assert all(step.restartable for step in summary.recommended_steps)
        finally:
            db.delete(project)
            db.commit()


def test_git_sync_follow_up_moves_clean_actions_to_later_group(monkeypatch):
    init_db()
    monkeypatch.setattr(git_followup_service, "get_repository_status", lambda project: _repo_status())
    monkeypatch.setattr(
        git_followup_service,
        "get_source_index_status",
        lambda db, project: _source_status(
            needs_reindex=False,
            missing_embedding_count=0,
            source_chunk_count=12,
            source_vector_count=12,
        ),
    )
    monkeypatch.setattr(git_followup_service, "get_changed_source_files_since_latest_index", lambda db, project: [])
    monkeypatch.setattr(
        git_followup_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness(
            "latest",
            "Neo4j graph가 현재 DB/Git 기준과 일치합니다.",
            repo_head_hash="head123456789",
            db_sync_head_hash="head123456789",
            graph_sync_head_hash="head123456789",
            node_count=10,
            edge_count=20,
        ),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("followup-clean-project"), git_repo_path="C:/repo")
        db.add(project)
        db.flush()
        program = Program(project_id=project.id, program_id=_unique("P"), program_name="Payment")
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="payment update",
            mapping_analysis_status="completed",
            committed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        db.add_all([program, commit])
        db.flush()
        db.add(
            RiskFinding(
                project_id=project.id,
                program_id=program.id,
                risk_type="PROGRESS_GAP",
                risk_level="LOW",
                title="확인 항목",
                resolved_yn="N",
            )
        )
        db.commit()

        try:
            summary = build_git_sync_follow_up(db, project.id)
            later_steps = {step.step_id: step for step in summary.later_steps}

            assert summary.recommended_steps == []
            assert {step.group for step in summary.steps} == {GROUP_LATER}
            assert later_steps["source_index"].status == STATUS_DONE
            assert later_steps["embedding"].status == STATUS_DONE
            assert later_steps["mapping"].status == STATUS_DONE
            assert later_steps["knowledge_graph"].status == STATUS_DONE
            assert later_steps["risk_analysis"].group == GROUP_LATER
        finally:
            db.delete(project)
            db.commit()

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import (
    AnalysisRun,
    CodeReviewResult,
    CommitFile,
    Developer,
    DocumentChunk,
    GitCommit,
    Program,
    ProgramCommitMapping,
    ProgramImplementationStatus,
    Project,
    ProjectDeveloper,
    ProjectChatMessage,
    ProjectChatSession,
    ResourceMetricSnapshot,
    RiskFinding,
    StandardTerm,
    VectorItem,
)
from src.services.project_management_service import (
    delete_project,
    get_project_delete_impact,
    get_project_reset_impact,
    reset_project_analysis_data,
)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _create_project_graph(db):
    marker = _unique("delete-marker")
    developer = Developer(
        developer_key=_unique("developer-key"),
        developer_id=_unique("developer-id"),
        developer_name="Demo Developer",
        email=f"{uuid.uuid4()}@example.local",
    )
    target_project = Project(
        name=_unique("delete-target"),
        git_repo_path=None,
        last_synced_commit_hash="abc123",
        last_synced_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
    )
    other_project = Project(name=_unique("delete-other"), git_repo_path=None)
    db.add_all([developer, target_project, other_project])
    db.flush()
    db.add(ProjectDeveloper(project_id=target_project.id, developer_id=developer.developer_id, source="manual"))

    target_program = Program(
        project_id=target_project.id,
        program_id=_unique("program"),
        program_name="Target Program",
        developer_id=developer.developer_id,
        developer=developer.developer_name,
    )
    other_program = Program(project_id=other_project.id, program_id=_unique("program"), program_name="Other Program")
    target_commit = GitCommit(
        project_id=target_project.id,
        commit_hash=uuid.uuid4().hex,
        message="Target commit",
        author_name="Demo Developer",
        committed_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
    )
    other_commit = GitCommit(
        project_id=other_project.id,
        commit_hash=uuid.uuid4().hex,
        message="Other commit",
        author_name="Other Developer",
        committed_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
    )
    db.add_all([target_program, other_program, target_commit, other_commit])
    db.flush()

    analysis_run = AnalysisRun(project_id=target_project.id, run_type="mapping", status="completed")
    db.add(analysis_run)
    db.flush()

    db.add_all(
        [
            CommitFile(
                commit_id=target_commit.id,
                git_commit_id=target_commit.id,
                file_path=f"src/{marker}_target.py",
                change_type="Modified",
                diff_text="+target",
            ),
            ProgramCommitMapping(
                program_id=target_program.id,
                commit_id=target_commit.id,
                analysis_run_id=analysis_run.id,
                relevance_score=90,
                is_related=True,
                implementation_status="구현완료",
                reason=marker,
            ),
            ProgramImplementationStatus(
                program_id=target_program.id,
                status="COMPLETED",
                summary=marker,
                completed_features=[],
                incomplete_features=[],
                evidence_commits=[],
            ),
            RiskFinding(
                project_id=target_project.id,
                program_id=target_program.id,
                risk_type="NO_COMMIT",
                risk_level="HIGH",
                title=marker,
            ),
            CodeReviewResult(
                project_id=target_project.id,
                target_type="commit",
                target_ref=target_commit.commit_hash,
                status="completed",
            ),
            ResourceMetricSnapshot(
                project_id=target_project.id,
                snapshot_label="delete-test",
                unresolved_risk_count=1,
                high_risk_count=1,
                forecasted_delay_program_count=1,
                ai_code_review_count=1,
                estimated_review_hours_saved=0.5,
                estimated_extra_mm_avoidance=0.4,
                average_workload_score=50,
                average_difficulty_score=40,
                developer_count=1,
                program_count=1,
                raw_summary={"marker": marker},
            ),
            StandardTerm(
                project_id=target_project.id,
                korean_term="결제금액",
                english_term="payment amount",
                derived_keywords=[],
            ),
        ]
    )
    chat_session = ProjectChatSession(project_id=target_project.id, title="demo")
    chunk = DocumentChunk(
        project_id=target_project.id,
        source_type="source_file",
        source_id=f"src/{marker}_target.py",
        chunk_index=0,
        chunk_text=marker,
    )
    db.add_all([chat_session, chunk])
    db.flush()
    chat_message = ProjectChatMessage(session_id=chat_session.id, role="user", content=marker, message_index=1)
    vector = VectorItem(chunk_id=chunk.id, embedding_model="mock", embedding=None)
    db.add_all(
        [
            chat_message,
            vector,
            CommitFile(
                commit_id=other_commit.id,
                git_commit_id=other_commit.id,
                file_path=f"src/{marker}_other.py",
                change_type="Added",
                diff_text="+other",
            ),
        ]
    )
    db.commit()
    return target_project.id, other_project.id, developer.id, marker, chat_message.id, vector.id


def test_delete_project_removes_project_owned_data_and_preserves_developers():
    init_db()
    with SessionLocal() as db:
        target_project_id, other_project_id, developer_pk, marker, chat_message_id, vector_id = _create_project_graph(
            db
        )
        try:
            impact = get_project_delete_impact(db, target_project_id)

            assert impact is not None
            assert impact.program_count == 1
            assert impact.git_commit_count == 1
            assert impact.commit_file_count == 1
            assert impact.mapping_count == 1
            assert impact.analysis_run_count == 1
            assert impact.implementation_status_count == 1
            assert impact.risk_finding_count == 1
            assert impact.code_review_count == 1
            assert impact.resource_metric_snapshot_count == 1
            assert impact.chat_session_count == 1
            assert impact.chat_message_count == 1
            assert impact.document_chunk_count == 1
            assert impact.vector_item_count == 1
            assert impact.standard_term_count == 1
            assert impact.project_developer_count == 1

            deleted = delete_project(db, target_project_id)

            assert deleted is not None
            assert db.get(Project, target_project_id) is None
            assert db.get(Project, other_project_id) is not None
            assert db.get(Developer, developer_pk) is not None
            assert db.query(ProjectDeveloper).filter(ProjectDeveloper.project_id == target_project_id).count() == 0
            assert db.query(Program).filter(Program.project_id == target_project_id).count() == 0
            assert db.query(GitCommit).filter(GitCommit.project_id == target_project_id).count() == 0
            assert db.query(CommitFile).filter(CommitFile.file_path == f"src/{marker}_target.py").count() == 0
            assert db.query(ProgramCommitMapping).filter(ProgramCommitMapping.reason == marker).count() == 0
            assert (
                db.query(ProgramImplementationStatus).filter(ProgramImplementationStatus.summary == marker).count()
                == 0
            )
            assert db.query(AnalysisRun).filter(AnalysisRun.project_id == target_project_id).count() == 0
            assert db.query(RiskFinding).filter(RiskFinding.project_id == target_project_id).count() == 0
            assert db.query(CodeReviewResult).filter(CodeReviewResult.project_id == target_project_id).count() == 0
            assert (
                db.query(ResourceMetricSnapshot)
                .filter(ResourceMetricSnapshot.project_id == target_project_id)
                .count()
                == 0
            )
            assert db.query(ProjectChatSession).filter(ProjectChatSession.project_id == target_project_id).count() == 0
            assert db.get(ProjectChatMessage, chat_message_id) is None
            assert db.query(DocumentChunk).filter(DocumentChunk.project_id == target_project_id).count() == 0
            assert db.get(VectorItem, vector_id) is None
            assert db.query(StandardTerm).filter(StandardTerm.project_id == target_project_id).count() == 0
            assert db.query(Program).filter(Program.project_id == other_project_id).count() == 1
            assert db.query(GitCommit).filter(GitCommit.project_id == other_project_id).count() == 1
            assert db.query(CommitFile).filter(CommitFile.file_path == f"src/{marker}_other.py").count() == 1
        finally:
            remaining_project = db.get(Project, other_project_id)
            if remaining_project is not None:
                db.delete(remaining_project)
            remaining_developer = db.get(Developer, developer_pk)
            if remaining_developer is not None:
                db.delete(remaining_developer)
            db.commit()


def test_delete_project_returns_none_for_missing_project():
    init_db()
    with SessionLocal() as db:
        assert get_project_delete_impact(db, -1) is None
        assert delete_project(db, -1) is None


def test_reset_project_analysis_data_preserves_project_and_artifacts():
    init_db()
    with SessionLocal() as db:
        target_project_id, other_project_id, developer_pk, marker, chat_message_id, vector_id = _create_project_graph(
            db
        )
        try:
            impact = get_project_reset_impact(db, target_project_id)

            assert impact is not None
            assert impact.preserved_program_count == 1
            assert impact.preserved_standard_term_count == 1
            assert impact.preserved_project_developer_count == 1
            assert impact.git_commit_count == 1
            assert impact.commit_file_count == 1
            assert impact.mapping_count == 1
            assert impact.analysis_run_count == 1
            assert impact.implementation_status_count == 1
            assert impact.risk_finding_count == 1
            assert impact.code_review_count == 1
            assert impact.resource_metric_snapshot_count == 1
            assert impact.chat_session_count == 1
            assert impact.chat_message_count == 1
            assert impact.document_chunk_count == 1
            assert impact.vector_item_count == 1

            reset = reset_project_analysis_data(db, target_project_id)

            assert reset is not None
            target_project = db.get(Project, target_project_id)
            assert target_project is not None
            assert target_project.last_synced_commit_hash is None
            assert target_project.last_synced_at is None
            assert db.get(Project, other_project_id) is not None
            assert db.get(Developer, developer_pk) is not None
            assert db.query(ProjectDeveloper).filter(ProjectDeveloper.project_id == target_project_id).count() == 1
            assert db.query(Program).filter(Program.project_id == target_project_id).count() == 1
            assert db.query(StandardTerm).filter(StandardTerm.project_id == target_project_id).count() == 1
            assert db.query(GitCommit).filter(GitCommit.project_id == target_project_id).count() == 0
            assert db.query(CommitFile).filter(CommitFile.file_path == f"src/{marker}_target.py").count() == 0
            assert db.query(ProgramCommitMapping).filter(ProgramCommitMapping.reason == marker).count() == 0
            assert (
                db.query(ProgramImplementationStatus).filter(ProgramImplementationStatus.summary == marker).count()
                == 0
            )
            assert db.query(AnalysisRun).filter(AnalysisRun.project_id == target_project_id).count() == 0
            assert db.query(RiskFinding).filter(RiskFinding.project_id == target_project_id).count() == 0
            assert db.query(CodeReviewResult).filter(CodeReviewResult.project_id == target_project_id).count() == 0
            assert (
                db.query(ResourceMetricSnapshot)
                .filter(ResourceMetricSnapshot.project_id == target_project_id)
                .count()
                == 0
            )
            assert db.query(ProjectChatSession).filter(ProjectChatSession.project_id == target_project_id).count() == 0
            assert db.get(ProjectChatMessage, chat_message_id) is None
            assert db.query(DocumentChunk).filter(DocumentChunk.project_id == target_project_id).count() == 0
            assert db.get(VectorItem, vector_id) is None
            assert db.query(Program).filter(Program.project_id == other_project_id).count() == 1
            assert db.query(GitCommit).filter(GitCommit.project_id == other_project_id).count() == 1
            assert db.query(CommitFile).filter(CommitFile.file_path == f"src/{marker}_other.py").count() == 1
        finally:
            for project_id in (target_project_id, other_project_id):
                remaining_project = db.get(Project, project_id)
                if remaining_project is not None:
                    db.delete(remaining_project)
            remaining_developer = db.get(Developer, developer_pk)
            if remaining_developer is not None:
                db.delete(remaining_developer)
            db.commit()


def test_reset_project_analysis_data_returns_none_for_missing_project():
    init_db()
    with SessionLocal() as db:
        assert get_project_reset_impact(db, -1) is None
        assert reset_project_analysis_data(db, -1) is None

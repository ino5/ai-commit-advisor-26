from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import CodeReviewResult, CommitFile, Developer, GitCommit, Program, ProgramCommitMapping, Project, RiskFinding
from src.services.resource_metrics_service import get_resource_metrics_summary


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _cleanup_project_graph(db, project_id: int, developer_pk: int | None = None) -> None:
    db.query(CodeReviewResult).filter(CodeReviewResult.project_id == project_id).delete(synchronize_session=False)
    db.query(RiskFinding).filter(RiskFinding.project_id == project_id).delete(synchronize_session=False)
    db.query(Project).filter(Project.id == project_id).delete(synchronize_session=False)
    if developer_pk is not None:
        developer = db.get(Developer, developer_pk)
        if developer is not None:
            db.delete(developer)
    db.commit()


def test_resource_metrics_summary_aggregates_workload_difficulty_and_value_kpis():
    init_db()
    with SessionLocal() as db:
        developer = Developer(
            developer_key=_unique("alice-key"),
            developer_id=_unique("alice-id"),
            developer_name="Alice",
            email=f"{uuid.uuid4()}@example.local",
        )
        project = Project(name=_unique("resource-project"), git_repo_path=None)
        db.add_all([developer, project])
        db.flush()

        program_a = Program(
            project_id=project.id,
            program_id=_unique("P-A"),
            program_name="Order Risk Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="진행중",
            progress_rate=80,
        )
        program_b = Program(
            project_id=project.id,
            program_id=_unique("P-B"),
            program_name="Payment Complete Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="완료",
            progress_rate=100,
        )
        commit_a = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Implement order risk flow",
            author_name="Alice",
            committed_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        commit_cross = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Connect order and payment",
            author_name="Alice",
            committed_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
        )
        db.add_all([program_a, program_b, commit_a, commit_cross])
        db.flush()

        db.add_all(
            [
                CommitFile(
                    commit_id=commit_a.id,
                    git_commit_id=commit_a.id,
                    file_path="src/orders/OrderService.java",
                    change_type="Modified",
                    diff_text="+new line\n-old line\n context",
                ),
                CommitFile(
                    commit_id=commit_a.id,
                    git_commit_id=commit_a.id,
                    file_path="src/orders/OrderMapper.xml",
                    change_type="Modified",
                    diff_text="+select\n+where\n-old",
                ),
                CommitFile(
                    commit_id=commit_cross.id,
                    git_commit_id=commit_cross.id,
                    file_path="src/payments/PaymentService.java",
                    change_type="Modified",
                    diff_text="+payment\n-order",
                ),
                ProgramCommitMapping(
                    program_id=program_a.id,
                    commit_id=commit_a.id,
                    relevance_score=80,
                    is_related=True,
                    implementation_status="일부구현",
                    reason="order work",
                ),
                ProgramCommitMapping(
                    program_id=program_a.id,
                    commit_id=commit_cross.id,
                    relevance_score=75,
                    is_related=True,
                    implementation_status="일부구현",
                    reason="cross work",
                ),
                ProgramCommitMapping(
                    program_id=program_b.id,
                    commit_id=commit_cross.id,
                    relevance_score=90,
                    is_related=True,
                    implementation_status="구현완료",
                    reason="payment work",
                ),
                RiskFinding(
                    project_id=project.id,
                    program_id=program_a.id,
                    risk_type="PROGRESS_GAP",
                    risk_level="HIGH",
                    title="gap",
                    resolved_yn="N",
                ),
                CodeReviewResult(
                    project_id=project.id,
                    target_type="commit",
                    target_ref=commit_a.commit_hash,
                    status="completed",
                ),
            ]
        )
        db.commit()

        try:
            summary = get_resource_metrics_summary(db, project.id)

            assert summary.interpretation_note
            assert len(summary.program_metrics) == 2
            assert len(summary.developer_metrics) == 1

            metrics_by_name = {metric.program_name: metric for metric in summary.program_metrics}
            risky = metrics_by_name["Order Risk Program"]
            complete = metrics_by_name["Payment Complete Program"]

            assert risky.ai_progress_rate == 50.0
            assert risky.progress_gap == 30.0
            assert risky.related_commit_count == 2
            assert risky.touched_file_count == 3
            assert risky.diff_line_count == 7
            assert risky.cross_program_commit_count == 1
            assert risky.unresolved_risk_count == 1
            assert risky.difficulty_score > complete.difficulty_score
            assert risky.workload_points > complete.workload_points
            assert risky.evidence["unfinished"] is True

            developer_metric = summary.developer_metrics[0]
            assert developer_metric.developer == "Alice"
            assert developer_metric.assigned_program_count == 2
            assert developer_metric.unfinished_program_count == 1
            assert developer_metric.risk_program_count == 1
            assert developer_metric.related_commit_count == 3
            assert developer_metric.workload_score > 0

            assert summary.business_value.unresolved_risk_count == 1
            assert summary.business_value.high_risk_count == 1
            assert summary.business_value.ai_code_review_count == 1
            assert summary.business_value.estimated_review_hours_saved == 0.5
            assert summary.business_value.estimated_extra_mm_avoidance == 0.25
        finally:
            _cleanup_project_graph(db, project.id, developer.id)


def test_resource_metrics_summary_handles_empty_project():
    init_db()
    with SessionLocal() as db:
        project = Project(name=_unique("empty-resource-project"), git_repo_path=None)
        db.add(project)
        db.commit()

        try:
            summary = get_resource_metrics_summary(db, project.id)

            assert summary.program_metrics == []
            assert summary.developer_metrics == []
            assert summary.business_value.unresolved_risk_count == 0
            assert summary.business_value.estimated_review_hours_saved == 0.0
            assert summary.business_value.estimated_extra_mm_avoidance == 0.0
        finally:
            _cleanup_project_graph(db, project.id)

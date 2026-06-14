from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import (
    CodeReviewResult,
    CommitFile,
    Developer,
    GitCommit,
    Program,
    ProgramCommitMapping,
    Project,
    ResourceMetricSnapshot,
    RiskFinding,
)
from src.services.resource_metrics_service import (
    get_resource_metric_snapshots,
    get_resource_metrics_summary,
    save_resource_metric_snapshot,
)
from src.services.ai_resource_radar_service import build_ai_resource_radar, generate_pl_briefing
from src.services.risk_service import RISK_FORECAST_DELAY, run_risk_analysis


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _cleanup_project_graph(db, project_id: int, developer_pk: int | None = None) -> None:
    db.query(ResourceMetricSnapshot).filter(ResourceMetricSnapshot.project_id == project_id).delete(synchronize_session=False)
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
            planned_start_date=date.today() - timedelta(days=30),
            planned_end_date=date.today() + timedelta(days=10),
        )
        program_b = Program(
            project_id=project.id,
            program_id=_unique("P-B"),
            program_name="Payment Complete Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="완료",
            progress_rate=100,
            planned_start_date=date.today() - timedelta(days=30),
            planned_end_date=date.today() + timedelta(days=1),
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
            assert risky.forecast_level == "DELAY_EXPECTED"
            assert risky.forecast_delay_days is not None
            assert risky.forecast_delay_days >= 7
            assert risky.forecast_confidence == "HIGH"
            assert risky.difficulty_score > complete.difficulty_score
            assert risky.workload_points > complete.workload_points
            assert risky.evidence["unfinished"] is True

            assert complete.forecast_level == "COMPLETED"
            assert complete.forecast_delay_days == 0

            developer_metric = summary.developer_metrics[0]
            assert developer_metric.developer == "Alice"
            assert developer_metric.assigned_program_count == 2
            assert developer_metric.unfinished_program_count == 1
            assert developer_metric.risk_program_count == 1
            assert developer_metric.related_commit_count == 3
            assert developer_metric.workload_score > 0

            assert summary.business_value.unresolved_risk_count == 1
            assert summary.business_value.high_risk_count == 1
            assert summary.business_value.forecasted_delay_program_count == 1
            assert summary.business_value.ai_code_review_count == 1
            assert summary.business_value.estimated_review_hours_saved == 0.5
            assert summary.business_value.estimated_extra_mm_avoidance == 0.4
            assert "현재 계산 기준" in summary.business_value.assumption
            assert "PoC" not in summary.business_value.assumption
        finally:
            _cleanup_project_graph(db, project.id, developer.id)


def test_ai_resource_radar_ranks_risky_program_and_generates_briefing():
    init_db()
    with SessionLocal() as db:
        developer = Developer(
            developer_key=_unique("radar-key"),
            developer_id=_unique("radar-id"),
            developer_name="Radar Owner",
            email=f"{uuid.uuid4()}@example.local",
        )
        project = Project(name=_unique("radar-project"), git_repo_path=None)
        db.add_all([developer, project])
        db.flush()

        risky_program = Program(
            project_id=project.id,
            program_id=_unique("P-R"),
            program_name="Radar Risk Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="진행중",
            progress_rate=90,
            planned_start_date=date.today() - timedelta(days=40),
            planned_end_date=date.today() + timedelta(days=5),
        )
        normal_program = Program(
            project_id=project.id,
            program_id=_unique("P-N"),
            program_name="Radar Normal Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="완료",
            progress_rate=100,
            planned_start_date=date.today() - timedelta(days=20),
            planned_end_date=date.today() + timedelta(days=10),
        )
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Partial risky radar implementation",
            author_name="Radar Owner",
            committed_at=datetime.now(timezone.utc),
        )
        db.add_all([risky_program, normal_program, commit])
        db.flush()
        db.add_all(
            [
                CommitFile(
                    commit_id=commit.id,
                    git_commit_id=commit.id,
                    file_path="src/radar/RadarService.java",
                    change_type="Modified",
                    diff_text="+partial\n-risk\n+branch",
                ),
                ProgramCommitMapping(
                    program_id=risky_program.id,
                    commit_id=commit.id,
                    relevance_score=85,
                    is_related=True,
                    implementation_status="일부구현",
                    reason="partial risky work",
                ),
                RiskFinding(
                    project_id=project.id,
                    program_id=risky_program.id,
                    risk_type="PROGRESS_GAP",
                    risk_level="HIGH",
                    title="gap",
                    resolved_yn="N",
                ),
            ]
        )
        db.commit()

        try:
            summary = get_resource_metrics_summary(db, project.id)
            radar = build_ai_resource_radar(db, summary, limit=2)

            assert radar.items
            assert radar.items[0].program_name == "Radar Risk Program"
            assert radar.items[0].priority_level == "HIGH"
            assert any("HIGH 리스크" in reason for reason in radar.items[0].reasons)
            assert radar.items[0].related_commits

            class MockLLM:
                provider = "mock"

            briefing = generate_pl_briefing(radar, MockLLM())

            assert briefing.provider == "mock"
            assert briefing.used_llm is False
            assert "Radar Risk Program" in briefing.text
            assert "회의 질문" in briefing.text
        finally:
            _cleanup_project_graph(db, project.id, developer.id)


def test_pl_briefing_uses_configured_llm_when_available():
    class FakeResponse:
        text = "LLM briefing text"
        raw = {"provider": "fake"}

    class FakeLLM:
        provider = "local_openai"

        def __init__(self):
            self.prompt = ""

        def generate(self, prompt: str):
            self.prompt = prompt
            return FakeResponse()

    init_db()
    with SessionLocal() as db:
        project = Project(name=_unique("briefing-project"), git_repo_path=None)
        db.add(project)
        db.flush()
        program = Program(
            project_id=project.id,
            program_id=_unique("P-BR"),
            program_name="Briefing Program",
            developer="Briefing Owner",
            status="진행중",
            progress_rate=80,
            planned_start_date=date.today() - timedelta(days=20),
            planned_end_date=date.today() + timedelta(days=5),
        )
        db.add(program)
        db.flush()
        db.add(
            RiskFinding(
                project_id=project.id,
                program_id=program.id,
                risk_type="NO_COMMITS",
                risk_level="HIGH",
                title="no commits",
                resolved_yn="N",
            )
        )
        db.commit()

        try:
            summary = get_resource_metrics_summary(db, project.id)
            radar = build_ai_resource_radar(db, summary)
            fake_llm = FakeLLM()
            briefing = generate_pl_briefing(radar, fake_llm)

            assert briefing.used_llm is True
            assert briefing.provider == "local_openai"
            assert briefing.text == "LLM briefing text"
            assert "Briefing Program" in fake_llm.prompt
        finally:
            _cleanup_project_graph(db, project.id)


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
            assert summary.business_value.forecasted_delay_program_count == 0
            assert summary.business_value.estimated_review_hours_saved == 0.0
            assert summary.business_value.estimated_extra_mm_avoidance == 0.0
        finally:
            _cleanup_project_graph(db, project.id)


def test_resource_metric_snapshots_persist_current_kpis_in_chronological_order():
    init_db()
    with SessionLocal() as db:
        developer = Developer(
            developer_key=_unique("snapshot-key"),
            developer_id=_unique("snapshot-id"),
            developer_name="Snapshot Owner",
            email=f"{uuid.uuid4()}@example.local",
        )
        project = Project(name=_unique("snapshot-project"), git_repo_path=None)
        db.add_all([developer, project])
        db.flush()

        program = Program(
            project_id=project.id,
            program_id=_unique("P-S"),
            program_name="Snapshot Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="진행중",
            progress_rate=90,
            planned_start_date=date.today() - timedelta(days=40),
            planned_end_date=date.today() + timedelta(days=5),
        )
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Partial snapshot implementation",
            author_name="Snapshot Owner",
            committed_at=datetime.now(timezone.utc),
        )
        db.add_all([program, commit])
        db.flush()
        db.add_all(
            [
                CommitFile(
                    commit_id=commit.id,
                    git_commit_id=commit.id,
                    file_path="src/snapshot/SnapshotService.java",
                    change_type="Modified",
                    diff_text="+partial\n-old",
                ),
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=commit.id,
                    relevance_score=80,
                    is_related=True,
                    implementation_status="일부구현",
                    reason="partial",
                ),
                RiskFinding(
                    project_id=project.id,
                    program_id=program.id,
                    risk_type="PROGRESS_GAP",
                    risk_level="HIGH",
                    title="gap",
                    resolved_yn="N",
                ),
                CodeReviewResult(
                    project_id=project.id,
                    target_type="commit",
                    target_ref=commit.commit_hash,
                    status="completed",
                ),
            ]
        )
        db.commit()

        try:
            first = save_resource_metric_snapshot(db, project.id, "baseline")
            second = save_resource_metric_snapshot(db, project.id, "after review")
            rows = get_resource_metric_snapshots(db, project.id, limit=5)

            assert [row.id for row in rows] == [first.id, second.id]
            assert rows[0].snapshot_label == "baseline"
            assert rows[1].snapshot_label == "after review"
            assert rows[0].unresolved_risk_count == 1
            assert rows[0].high_risk_count == 1
            assert rows[0].forecasted_delay_program_count == 1
            assert rows[0].ai_code_review_count == 1
            assert rows[0].estimated_review_hours_saved == 0.5
            assert rows[0].average_workload_score > 0
            assert rows[0].average_difficulty_score > 0
            assert rows[0].developer_count == 1
            assert rows[0].program_count == 1

            stored = db.get(ResourceMetricSnapshot, first.id)
            assert stored is not None
            assert stored.raw_summary["business_value"]["high_risk_count"] == 1
            assert stored.raw_summary["program_metrics"][0]["forecast_end_date"]
        finally:
            _cleanup_project_graph(db, project.id, developer.id)


def test_risk_analysis_records_forecast_delay_risk():
    init_db()
    with SessionLocal() as db:
        developer = Developer(
            developer_key=_unique("forecast-key"),
            developer_id=_unique("forecast-id"),
            developer_name="Forecast Owner",
            email=f"{uuid.uuid4()}@example.local",
        )
        project = Project(name=_unique("forecast-project"), git_repo_path=None)
        db.add_all([developer, project])
        db.flush()

        program = Program(
            project_id=project.id,
            program_id=_unique("P-F"),
            program_name="Forecast Delay Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="진행중",
            progress_rate=90,
            planned_start_date=date.today() - timedelta(days=40),
            planned_end_date=date.today() + timedelta(days=5),
        )
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Partial forecast implementation",
            author_name="Forecast Owner",
            committed_at=datetime.now(timezone.utc),
        )
        db.add_all([program, commit])
        db.flush()
        db.add_all(
            [
                CommitFile(
                    commit_id=commit.id,
                    git_commit_id=commit.id,
                    file_path="src/forecast/ForecastService.java",
                    change_type="Modified",
                    diff_text="+partial",
                ),
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=commit.id,
                    relevance_score=80,
                    is_related=True,
                    implementation_status="일부구현",
                    reason="partial",
                ),
            ]
        )
        db.commit()

        try:
            result = run_risk_analysis(db, project.id)
            forecast_findings = [
                finding for finding in result.findings if finding.risk_type == RISK_FORECAST_DELAY
            ]

            assert forecast_findings
            finding = forecast_findings[0]
            assert finding.risk_level in {"MEDIUM", "HIGH"}
            assert finding.evidence["forecast_delay_days"] >= 7
            assert finding.evidence["forecast_end_date"]
        finally:
            _cleanup_project_graph(db, project.id, developer.id)

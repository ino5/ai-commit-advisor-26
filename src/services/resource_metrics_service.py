from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from math import ceil
from typing import Any

from sqlalchemy.orm import Session, joinedload

from src.db.models import CodeReviewResult, GitCommit, Program, ProgramCommitMapping, ResourceMetricSnapshot, RiskFinding
from src.services.progress_service import normalize_implementation_status


DIFFICULTY_LABELS = {
    "LOW": "낮음",
    "MEDIUM": "보통",
    "HIGH": "높음",
}

WORKLOAD_LABELS = {
    "LOW": "여유",
    "MEDIUM": "주의",
    "HIGH": "집중관리",
}

FORECAST_LABELS = {
    "COMPLETED": "완료 추정",
    "ON_TRACK": "정상 범위",
    "AT_RISK": "주의",
    "DELAY_EXPECTED": "지연 예상",
    "UNKNOWN": "판단 보류",
}

CONFIDENCE_LABELS = {
    "HIGH": "높음",
    "MEDIUM": "보통",
    "LOW": "낮음",
}


@dataclass
class ProgramResourceMetric:
    program_db_id: int
    program_id: str | None
    program_name: str
    developer: str
    plan_progress_rate: float
    ai_progress_rate: float
    progress_gap: float
    related_commit_count: int
    touched_file_count: int
    diff_line_count: int
    touched_area_count: int
    cross_program_commit_count: int
    unresolved_risk_count: int
    forecast_end_date: date | None
    forecast_delay_days: int | None
    forecast_level: str
    forecast_label: str
    forecast_confidence: str
    forecast_confidence_label: str
    difficulty_score: float
    difficulty_level: str
    difficulty_label: str
    workload_points: float
    evidence: dict = field(default_factory=dict)


@dataclass
class DeveloperResourceMetric:
    developer: str
    assigned_program_count: int
    unfinished_program_count: int
    risk_program_count: int
    related_commit_count: int
    touched_file_count: int
    average_plan_progress_rate: float
    average_ai_progress_rate: float
    average_progress_gap: float
    average_difficulty_score: float
    workload_score: float
    workload_level: str
    workload_label: str
    difficulty_level: str
    difficulty_label: str


@dataclass
class BusinessValueMetric:
    unresolved_risk_count: int
    high_risk_count: int
    forecasted_delay_program_count: int
    ai_code_review_count: int
    estimated_review_hours_saved: float
    estimated_extra_mm_avoidance: float
    assumption: str


@dataclass
class ResourceMetricsSummary:
    project_id: int
    program_metrics: list[ProgramResourceMetric]
    developer_metrics: list[DeveloperResourceMetric]
    business_value: BusinessValueMetric
    interpretation_note: str


@dataclass
class ResourceMetricSnapshotRow:
    id: int
    project_id: int
    snapshot_label: str | None
    captured_at: datetime
    unresolved_risk_count: int
    high_risk_count: int
    forecasted_delay_program_count: int
    ai_code_review_count: int
    estimated_review_hours_saved: float
    estimated_extra_mm_avoidance: float
    average_workload_score: float
    average_difficulty_score: float
    developer_count: int
    program_count: int


def _json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _summary_payload(summary: ResourceMetricsSummary) -> dict[str, Any]:
    return _json_safe(
        {
            "project_id": summary.project_id,
            "program_metrics": [asdict(row) for row in summary.program_metrics],
            "developer_metrics": [asdict(row) for row in summary.developer_metrics],
            "business_value": asdict(summary.business_value),
            "interpretation_note": summary.interpretation_note,
        }
    )


def _snapshot_row(snapshot: ResourceMetricSnapshot) -> ResourceMetricSnapshotRow:
    return ResourceMetricSnapshotRow(
        id=snapshot.id,
        project_id=snapshot.project_id,
        snapshot_label=snapshot.snapshot_label,
        captured_at=snapshot.captured_at,
        unresolved_risk_count=snapshot.unresolved_risk_count,
        high_risk_count=snapshot.high_risk_count,
        forecasted_delay_program_count=snapshot.forecasted_delay_program_count,
        ai_code_review_count=snapshot.ai_code_review_count,
        estimated_review_hours_saved=snapshot.estimated_review_hours_saved,
        estimated_extra_mm_avoidance=snapshot.estimated_extra_mm_avoidance,
        average_workload_score=snapshot.average_workload_score,
        average_difficulty_score=snapshot.average_difficulty_score,
        developer_count=snapshot.developer_count,
        program_count=snapshot.program_count,
    )


def _developer_name(program: Program) -> str:
    if program.assigned_developer and program.assigned_developer.developer_name:
        return program.assigned_developer.developer_name
    return program.developer or "미지정"


def _ai_progress_for_mappings(mappings: list[ProgramCommitMapping]) -> tuple[float, str]:
    statuses = [normalize_implementation_status(mapping.implementation_status) for mapping in mappings]
    if "구현됨" in statuses:
        return 100.0, "구현됨"
    if "일부구현" in statuses:
        return 50.0, "일부구현"
    return 0.0, "판단불가" if statuses else "매핑없음"


def _is_unfinished(program: Program, ai_progress_rate: float) -> bool:
    status = (program.status or "").strip().lower()
    if status in {"완료", "done", "completed", "complete", "finished"}:
        return False
    return ai_progress_rate < 100


def _diff_line_count(diff_text: str | None) -> int:
    if not diff_text:
        return 0
    return sum(
        1
        for line in diff_text.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    )


def _file_area(file_path: str | None) -> str:
    normalized = (file_path or "").replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part]
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return normalized or "unknown"


def _score_level(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def _forecast_completion(
    program: Program,
    ai_progress_rate: float,
    related_commit_count: int,
    today: date | None = None,
) -> tuple[date | None, int | None, str, str]:
    today = today or date.today()
    planned_end = program.planned_end_date
    if ai_progress_rate >= 100:
        return today, 0 if planned_end else None, "COMPLETED", "HIGH" if related_commit_count else "MEDIUM"
    if planned_end is None:
        return None, None, "UNKNOWN", "LOW"

    forecast_end: date
    confidence: str
    if ai_progress_rate > 0 and program.planned_start_date:
        elapsed_days = max((today - program.planned_start_date).days, 1)
        daily_progress = ai_progress_rate / elapsed_days
        remaining_days = ceil((100 - ai_progress_rate) / daily_progress) if daily_progress > 0 else 14
        forecast_end = today + timedelta(days=max(remaining_days, 1))
        confidence = "HIGH" if related_commit_count >= 2 else "MEDIUM"
    else:
        anchor = max(today, planned_end)
        forecast_end = anchor + timedelta(days=14)
        confidence = "LOW"

    delay_days = max((forecast_end - planned_end).days, 0)
    if delay_days >= 7:
        level = "DELAY_EXPECTED"
    elif delay_days > 0 or ((planned_end - today).days <= 7 and ai_progress_rate < 80):
        level = "AT_RISK"
    else:
        level = "ON_TRACK"
    return forecast_end, delay_days, level, confidence


def _difficulty_score(
    related_commit_count: int,
    touched_file_count: int,
    diff_line_count: int,
    touched_area_count: int,
    cross_program_commit_count: int,
    unresolved_risk_count: int,
) -> float:
    score = (
        related_commit_count * 8
        + touched_file_count * 4
        + min(diff_line_count, 300) * 0.08
        + touched_area_count * 8
        + cross_program_commit_count * 10
        + unresolved_risk_count * 12
    )
    return round(min(score, 100.0), 1)


def _workload_score(
    assigned_program_count: int,
    unfinished_program_count: int,
    risk_program_count: int,
    average_progress_gap: float,
    average_difficulty_score: float,
) -> float:
    score = (
        assigned_program_count * 10
        + unfinished_program_count * 15
        + risk_program_count * 15
        + max(average_progress_gap, 0) * 0.5
        + average_difficulty_score * 0.25
    )
    return round(min(score, 100.0), 1)


def _round_average(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def _related_commit_counts_by_commit(programs: list[Program]) -> Counter:
    counter: Counter = Counter()
    for program in programs:
        for mapping in program.mappings or []:
            if mapping.is_related is True and mapping.commit_id is not None:
                counter[mapping.commit_id] += 1
    return counter


def _program_metric(
    program: Program,
    unresolved_risks_by_program: Counter,
    related_mapping_counts_by_commit: Counter,
) -> ProgramResourceMetric:
    related_mappings = [mapping for mapping in (program.mappings or []) if mapping.is_related is True]
    ai_progress_rate, _ = _ai_progress_for_mappings(related_mappings)
    plan_progress_rate = float(program.progress_rate or 0)
    progress_gap = plan_progress_rate - ai_progress_rate

    files = []
    commit_ids = set()
    for mapping in related_mappings:
        if mapping.commit is None:
            continue
        commit_ids.add(mapping.commit.id)
        files.extend(list(mapping.commit.files or []))

    touched_files = {file.file_path for file in files if file.file_path}
    touched_areas = {_file_area(file.file_path) for file in files}
    diff_lines = sum(_diff_line_count(file.diff_text) for file in files)
    cross_program_commit_count = sum(
        1 for commit_id in commit_ids if related_mapping_counts_by_commit.get(commit_id, 0) >= 2
    )
    unresolved_risk_count = int(unresolved_risks_by_program.get(program.id, 0))
    forecast_end_date, forecast_delay_days, forecast_level, forecast_confidence = _forecast_completion(
        program,
        ai_progress_rate=ai_progress_rate,
        related_commit_count=len(commit_ids),
    )
    difficulty_score = _difficulty_score(
        related_commit_count=len(commit_ids),
        touched_file_count=len(touched_files),
        diff_line_count=diff_lines,
        touched_area_count=len(touched_areas),
        cross_program_commit_count=cross_program_commit_count,
        unresolved_risk_count=unresolved_risk_count,
    )
    difficulty_level = _score_level(difficulty_score)
    unfinished = _is_unfinished(program, ai_progress_rate)
    workload_points = (
        10
        + (15 if unfinished else 0)
        + unresolved_risk_count * 15
        + max(progress_gap, 0) * 0.5
        + difficulty_score * 0.25
    )

    return ProgramResourceMetric(
        program_db_id=program.id,
        program_id=program.program_id,
        program_name=program.program_name,
        developer=_developer_name(program),
        plan_progress_rate=plan_progress_rate,
        ai_progress_rate=ai_progress_rate,
        progress_gap=round(progress_gap, 1),
        related_commit_count=len(commit_ids),
        touched_file_count=len(touched_files),
        diff_line_count=diff_lines,
        touched_area_count=len(touched_areas),
        cross_program_commit_count=cross_program_commit_count,
        unresolved_risk_count=unresolved_risk_count,
        forecast_end_date=forecast_end_date,
        forecast_delay_days=forecast_delay_days,
        forecast_level=forecast_level,
        forecast_label=FORECAST_LABELS[forecast_level],
        forecast_confidence=forecast_confidence,
        forecast_confidence_label=CONFIDENCE_LABELS[forecast_confidence],
        difficulty_score=difficulty_score,
        difficulty_level=difficulty_level,
        difficulty_label=DIFFICULTY_LABELS[difficulty_level],
        workload_points=round(workload_points, 1),
        evidence={
            "metric_basis": "program_assignments_commits_diffs_risks",
            "unfinished": unfinished,
            "forecast_basis": "planned_dates_ai_progress_related_commit_activity",
            "touched_areas": sorted(touched_areas),
        },
    )


def _developer_metrics(program_metrics: list[ProgramResourceMetric]) -> list[DeveloperResourceMetric]:
    by_developer: dict[str, list[ProgramResourceMetric]] = defaultdict(list)
    for metric in program_metrics:
        by_developer[metric.developer].append(metric)

    developer_rows = []
    for developer, rows in by_developer.items():
        unfinished_program_count = sum(1 for row in rows if row.ai_progress_rate < 100)
        risk_program_count = sum(1 for row in rows if row.unresolved_risk_count > 0)
        avg_plan = _round_average([row.plan_progress_rate for row in rows])
        avg_ai = _round_average([row.ai_progress_rate for row in rows])
        avg_gap = _round_average([row.progress_gap for row in rows])
        avg_difficulty = _round_average([row.difficulty_score for row in rows])
        workload_score = _workload_score(
            assigned_program_count=len(rows),
            unfinished_program_count=unfinished_program_count,
            risk_program_count=risk_program_count,
            average_progress_gap=avg_gap,
            average_difficulty_score=avg_difficulty,
        )
        workload_level = _score_level(workload_score)
        difficulty_level = _score_level(avg_difficulty)
        developer_rows.append(
            DeveloperResourceMetric(
                developer=developer,
                assigned_program_count=len(rows),
                unfinished_program_count=unfinished_program_count,
                risk_program_count=risk_program_count,
                related_commit_count=sum(row.related_commit_count for row in rows),
                touched_file_count=sum(row.touched_file_count for row in rows),
                average_plan_progress_rate=avg_plan,
                average_ai_progress_rate=avg_ai,
                average_progress_gap=avg_gap,
                average_difficulty_score=avg_difficulty,
                workload_score=workload_score,
                workload_level=workload_level,
                workload_label=WORKLOAD_LABELS[workload_level],
                difficulty_level=difficulty_level,
                difficulty_label=DIFFICULTY_LABELS[difficulty_level],
            )
        )

    return sorted(developer_rows, key=lambda row: (row.workload_score, row.assigned_program_count), reverse=True)


def _business_value_metric(
    db: Session,
    project_id: int,
    unresolved_findings: list[RiskFinding],
    program_metrics: list[ProgramResourceMetric],
) -> BusinessValueMetric:
    code_review_count = db.query(CodeReviewResult).filter(CodeReviewResult.project_id == project_id).count()
    high_risk_count = sum(1 for finding in unresolved_findings if finding.risk_level == "HIGH")
    forecasted_delay_program_count = sum(
        1 for metric in program_metrics if metric.forecast_level == "DELAY_EXPECTED"
    )
    estimated_review_hours_saved = round(code_review_count * 0.5, 1)
    estimated_extra_mm_avoidance = round((high_risk_count * 0.25) + (forecasted_delay_program_count * 0.15), 2)
    return BusinessValueMetric(
        unresolved_risk_count=len(unresolved_findings),
        high_risk_count=high_risk_count,
        forecasted_delay_program_count=forecasted_delay_program_count,
        ai_code_review_count=code_review_count,
        estimated_review_hours_saved=estimated_review_hours_saved,
        estimated_extra_mm_avoidance=estimated_extra_mm_avoidance,
        assumption=(
            "PoC 가정: 완료된 AI 코드리뷰 1건은 리뷰 시간 절감 가능성 0.5h로 계산하고, "
            "조기 대응 시 HIGH 미해결 리스크 1건은 0.25MM, 예상 지연 프로그램 1건은 0.15MM의 "
            "추가 투입 예방 가능성으로 계산합니다. 실제 확정 절감액이 아니라 의사결정 보조 추정값입니다."
        ),
    )


def get_resource_metrics_summary(db: Session, project_id: int) -> ResourceMetricsSummary:
    programs = (
        db.query(Program)
        .options(
            joinedload(Program.assigned_developer),
            joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit).joinedload(GitCommit.files),
        )
        .filter(Program.project_id == project_id)
        .order_by(Program.program_id, Program.program_name)
        .all()
    )
    unresolved_findings = (
        db.query(RiskFinding)
        .filter(RiskFinding.project_id == project_id, RiskFinding.resolved_yn == "N")
        .all()
    )
    unresolved_risks_by_program = Counter(finding.program_id for finding in unresolved_findings)
    related_mapping_counts_by_commit = _related_commit_counts_by_commit(programs)
    program_metrics = [
        _program_metric(program, unresolved_risks_by_program, related_mapping_counts_by_commit)
        for program in programs
    ]
    return ResourceMetricsSummary(
        project_id=project_id,
        program_metrics=program_metrics,
        developer_metrics=_developer_metrics(program_metrics),
        business_value=_business_value_metric(db, project_id, unresolved_findings, program_metrics),
        interpretation_note=(
            "자원관리 지표는 커밋, diff, 매핑, 계획, 리스크를 조합한 의사결정 보조 신호입니다. "
            "개인 성과를 확정 평가하는 값이 아니며 PL 검토와 함께 사용해야 합니다."
        ),
    )


def save_resource_metric_snapshot(
    db: Session,
    project_id: int,
    snapshot_label: str | None = None,
) -> ResourceMetricSnapshotRow:
    summary = get_resource_metrics_summary(db, project_id)
    business_value = summary.business_value
    average_workload = _round_average([row.workload_score for row in summary.developer_metrics])
    average_difficulty = _round_average([row.average_difficulty_score for row in summary.developer_metrics])
    snapshot = ResourceMetricSnapshot(
        project_id=project_id,
        snapshot_label=(snapshot_label or "").strip() or None,
        unresolved_risk_count=business_value.unresolved_risk_count,
        high_risk_count=business_value.high_risk_count,
        forecasted_delay_program_count=business_value.forecasted_delay_program_count,
        ai_code_review_count=business_value.ai_code_review_count,
        estimated_review_hours_saved=business_value.estimated_review_hours_saved,
        estimated_extra_mm_avoidance=business_value.estimated_extra_mm_avoidance,
        average_workload_score=average_workload,
        average_difficulty_score=average_difficulty,
        developer_count=len(summary.developer_metrics),
        program_count=len(summary.program_metrics),
        raw_summary=_summary_payload(summary),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return _snapshot_row(snapshot)


def get_resource_metric_snapshots(
    db: Session,
    project_id: int,
    limit: int = 30,
) -> list[ResourceMetricSnapshotRow]:
    rows = (
        db.query(ResourceMetricSnapshot)
        .filter(ResourceMetricSnapshot.project_id == project_id)
        .order_by(ResourceMetricSnapshot.captured_at.desc(), ResourceMetricSnapshot.id.desc())
        .limit(limit)
        .all()
    )
    return [_snapshot_row(row) for row in reversed(rows)]

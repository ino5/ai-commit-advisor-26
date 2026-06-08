from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from src.db.models import Program, ProgramCommitMapping


AI_PROGRESS_BY_STATUS = {
    "implemented": 100.0,
    "partial": 50.0,
    "unknown": 0.0,
}


@dataclass
class ProgramProgressRow:
    program_db_id: int
    program_id: str | None
    program_name: str
    developer: str
    planned_start_date: date | None
    planned_end_date: date | None
    status: str
    plan_progress_rate: float
    ai_progress_rate: float
    progress_gap: float
    best_implementation_status: str
    mapping_count: int
    related_commit_count: int
    implementation_analysis_status: str | None = None
    implementation_analysis_status_label: str = "분석없음"
    implementation_analysis_summary: str = ""
    implementation_analyzed_at: datetime | None = None
    implementation_evidence_count: int = 0
    risk_reasons: list[str] = field(default_factory=list)

    @property
    def is_risk(self) -> bool:
        return bool(self.risk_reasons)


@dataclass
class CommitMappingDetail:
    commit_hash: str
    message: str
    committed_at: str | None
    author: str | None
    relevance_score: float
    implementation_status: str
    reason: str
    is_related: bool | None


@dataclass
class AiProgressSummary:
    rows: list[ProgramProgressRow]
    plan_average: float
    ai_average: float
    progress_gap_average: float
    risk_count: int


def normalize_implementation_status(status: str | None) -> str:
    value = (status or "").strip().lower()
    if not value:
        return "판단불가"
    if value in {"구현됨", "구현완료", "implemented", "done", "complete", "completed"}:
        return "구현됨"
    if value in {"일부구현", "부분구현", "partial", "partially_implemented"}:
        return "일부구현"
    if value in {"판단불가", "unknown", "unclear", "not_applicable"}:
        return "판단불가"
    return status.strip()


def implementation_analysis_status_label(status: str | None) -> str:
    value = str(status or "").strip().upper()
    labels = {
        "NOT_STARTED": "구현전 추정",
        "IN_PROGRESS": "진행중 추정",
        "COMPLETED": "구현완료 추정",
        "UNKNOWN": "판단불가",
    }
    if not value:
        return "분석없음"
    return labels.get(value, "판단불가")


def implementation_evidence_count(evidence_commits: object) -> int:
    return len(evidence_commits) if isinstance(evidence_commits, list) else 0


def _status_rank(status: str) -> int:
    return {"구현됨": 2, "일부구현": 1, "판단불가": 0}.get(normalize_implementation_status(status), 0)


def _ai_progress_for_mappings(mappings: list[ProgramCommitMapping]) -> tuple[float, str]:
    if not mappings:
        return 0.0, "매핑없음"

    statuses = [normalize_implementation_status(mapping.implementation_status) for mapping in mappings]
    best_status = max(statuses, key=_status_rank)
    if best_status == "구현됨":
        return AI_PROGRESS_BY_STATUS["implemented"], best_status
    if best_status == "일부구현":
        return AI_PROGRESS_BY_STATUS["partial"], best_status
    return AI_PROGRESS_BY_STATUS["unknown"], "판단불가"


def _developer_name(program: Program) -> str:
    if program.assigned_developer and program.assigned_developer.developer_name:
        return program.assigned_developer.developer_name
    return program.developer or "미지정"


def _risk_reasons(
    program: Program,
    mappings: list[ProgramCommitMapping],
    ai_progress_rate: float,
    progress_gap: float,
) -> list[str]:
    reasons = []
    today = date.today()
    if program.planned_end_date and program.planned_end_date < today and ai_progress_rate < 100:
        reasons.append("계획 종료일 경과")
    if progress_gap >= 30:
        reasons.append("계획 대비 AI 진척도 차이 30 이상")
    if mappings and all(normalize_implementation_status(mapping.implementation_status) == "판단불가" for mapping in mappings):
        reasons.append("LLM 판단불가만 존재")
    if not mappings or not any(mapping.is_related is True for mapping in mappings):
        reasons.append("관련 커밋 없음")
    return reasons


def get_ai_progress_summary(db: Session, project_id: int) -> AiProgressSummary:
    programs = (
        db.query(Program)
        .options(
            joinedload(Program.assigned_developer),
            joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit),
            joinedload(Program.implementation_status_result),
        )
        .filter(Program.project_id == project_id)
        .order_by(Program.program_id, Program.program_name)
        .all()
    )

    rows: list[ProgramProgressRow] = []
    for program in programs:
        mappings = list(program.mappings or [])
        related_mappings = [mapping for mapping in mappings if mapping.is_related is True]
        ai_progress_rate, best_status = _ai_progress_for_mappings(related_mappings)
        plan_progress_rate = float(program.progress_rate or 0)
        progress_gap = plan_progress_rate - ai_progress_rate
        related_commit_count = len(related_mappings)
        reasons = _risk_reasons(program, related_mappings, ai_progress_rate, progress_gap)
        implementation_status = program.implementation_status_result

        rows.append(
            ProgramProgressRow(
                program_db_id=program.id,
                program_id=program.program_id,
                program_name=program.program_name,
                developer=_developer_name(program),
                planned_start_date=program.planned_start_date,
                planned_end_date=program.planned_end_date,
                status=program.status or "미지정",
                plan_progress_rate=plan_progress_rate,
                ai_progress_rate=ai_progress_rate,
                progress_gap=progress_gap,
                best_implementation_status=best_status,
                mapping_count=len(related_mappings),
                related_commit_count=related_commit_count,
                implementation_analysis_status=implementation_status.status if implementation_status else None,
                implementation_analysis_status_label=implementation_analysis_status_label(
                    implementation_status.status if implementation_status else None
                ),
                implementation_analysis_summary=(implementation_status.summary or "") if implementation_status else "",
                implementation_analyzed_at=implementation_status.analyzed_at if implementation_status else None,
                implementation_evidence_count=implementation_evidence_count(
                    implementation_status.evidence_commits if implementation_status else None
                ),
                risk_reasons=reasons,
            )
        )

    plan_average = round(sum(row.plan_progress_rate for row in rows) / len(rows), 1) if rows else 0.0
    ai_average = round(sum(row.ai_progress_rate for row in rows) / len(rows), 1) if rows else 0.0
    progress_gap_average = round(plan_average - ai_average, 1)
    risk_count = sum(1 for row in rows if row.is_risk)
    return AiProgressSummary(
        rows=rows,
        plan_average=plan_average,
        ai_average=ai_average,
        progress_gap_average=progress_gap_average,
        risk_count=risk_count,
    )


def get_program_commit_details(db: Session, program_db_id: int) -> list[CommitMappingDetail]:
    mappings = (
        db.query(ProgramCommitMapping)
        .options(joinedload(ProgramCommitMapping.commit))
        .filter(ProgramCommitMapping.program_id == program_db_id)
        .order_by(ProgramCommitMapping.relevance_score.desc().nullslast())
        .all()
    )

    details = []
    for mapping in mappings:
        commit = mapping.commit
        details.append(
            CommitMappingDetail(
                commit_hash=commit.commit_hash[:12] if commit else "",
                message=((commit.message or "").splitlines()[0] if commit else ""),
                committed_at=commit.committed_at.isoformat() if commit and commit.committed_at else None,
                author=(commit.author_name or commit.author if commit else None),
                relevance_score=float(mapping.relevance_score or 0),
                implementation_status=normalize_implementation_status(mapping.implementation_status),
                reason=mapping.reason or "",
                is_related=mapping.is_related,
            )
        )
    return details

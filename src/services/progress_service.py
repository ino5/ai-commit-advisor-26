from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from src.db.models import Program, ProgramCommitMapping, ProgramImplementationStatus


AI_PROGRESS_BY_STATUS = {
    "implemented": 100.0,
    "partial": 50.0,
    "unknown": 0.0,
}

AI_PROGRESS_BY_IMPLEMENTATION_ANALYSIS = {
    "COMPLETED": 100.0,
    "IN_PROGRESS": 50.0,
    "NOT_STARTED": 0.0,
    "UNKNOWN": 0.0,
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
    ai_progress_rate: float | None
    ai_progress_state: str
    ai_progress_state_label: str
    progress_gap: float | None
    mapping_ai_progress_rate: float
    mapping_progress_gap: float
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
    ai_progress_ready_count: int = 0
    ai_progress_needs_analysis_count: int = 0


@dataclass(frozen=True)
class AiProgressResolution:
    ai_progress_rate: float | None
    ai_progress_state: str
    ai_progress_state_label: str
    mapping_ai_progress_rate: float
    best_mapping_status: str
    implementation_analysis_status: str | None


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


def implementation_analysis_signature(mappings: list[ProgramCommitMapping]) -> str:
    hashes = sorted(
        mapping.commit.commit_hash
        for mapping in mappings
        if mapping.commit is not None and mapping.commit.commit_hash and mapping.is_related is not False
    )
    joined = "\n".join(hashes)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _normalize_analysis_status(status: str | None) -> str:
    value = str(status or "").strip().upper()
    return value if value in AI_PROGRESS_BY_IMPLEMENTATION_ANALYSIS else "UNKNOWN"


def resolve_ai_progress(
    mappings: list[ProgramCommitMapping],
    implementation_status: ProgramImplementationStatus | None,
) -> AiProgressResolution:
    related_mappings = [mapping for mapping in mappings if mapping.is_related is True]
    mapping_ai_progress_rate, best_mapping_status = _ai_progress_for_mappings(related_mappings)

    if implementation_status is None:
        return AiProgressResolution(
            ai_progress_rate=None,
            ai_progress_state="missing_analysis",
            ai_progress_state_label="분석 필요",
            mapping_ai_progress_rate=mapping_ai_progress_rate,
            best_mapping_status=best_mapping_status,
            implementation_analysis_status=None,
        )

    if implementation_status.commit_hash_signature != implementation_analysis_signature(mappings):
        return AiProgressResolution(
            ai_progress_rate=None,
            ai_progress_state="stale_analysis",
            ai_progress_state_label="재분석 필요",
            mapping_ai_progress_rate=mapping_ai_progress_rate,
            best_mapping_status=best_mapping_status,
            implementation_analysis_status=implementation_status.status,
        )

    analysis_status = _normalize_analysis_status(implementation_status.status)
    return AiProgressResolution(
        ai_progress_rate=AI_PROGRESS_BY_IMPLEMENTATION_ANALYSIS[analysis_status],
        ai_progress_state="current_analysis",
        ai_progress_state_label="최신 분석",
        mapping_ai_progress_rate=mapping_ai_progress_rate,
        best_mapping_status=best_mapping_status,
        implementation_analysis_status=analysis_status,
    )


def _developer_name(program: Program) -> str:
    if program.assigned_developer and program.assigned_developer.developer_name:
        return program.assigned_developer.developer_name
    return program.developer or "미지정"


def _risk_reasons(
    program: Program,
    mappings: list[ProgramCommitMapping],
    resolution: AiProgressResolution,
    progress_gap: float | None,
) -> list[str]:
    reasons = []
    today = date.today()
    if resolution.ai_progress_rate is None:
        reasons.append(resolution.ai_progress_state_label)
    if program.planned_end_date and program.planned_end_date < today:
        if resolution.ai_progress_rate is None:
            reasons.append("계획 종료일 경과 + 구현상태 분석 필요")
        elif resolution.ai_progress_rate < 100:
            reasons.append("계획 종료일 경과")
    if progress_gap is not None and progress_gap >= 30:
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
        implementation_status = program.implementation_status_result
        resolution = resolve_ai_progress(mappings, implementation_status)
        ai_progress_rate = resolution.ai_progress_rate
        plan_progress_rate = float(program.progress_rate or 0)
        progress_gap = plan_progress_rate - ai_progress_rate if ai_progress_rate is not None else None
        mapping_progress_gap = plan_progress_rate - resolution.mapping_ai_progress_rate
        related_commit_count = len(related_mappings)
        reasons = _risk_reasons(program, related_mappings, resolution, progress_gap)

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
                ai_progress_state=resolution.ai_progress_state,
                ai_progress_state_label=resolution.ai_progress_state_label,
                progress_gap=progress_gap,
                mapping_ai_progress_rate=resolution.mapping_ai_progress_rate,
                mapping_progress_gap=mapping_progress_gap,
                best_implementation_status=resolution.best_mapping_status,
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
    ready_rows = [row for row in rows if row.ai_progress_rate is not None]
    gap_rows = [row for row in rows if row.progress_gap is not None]
    ai_average = round(sum(float(row.ai_progress_rate) for row in ready_rows) / len(ready_rows), 1) if ready_rows else 0.0
    progress_gap_average = round(sum(float(row.progress_gap) for row in gap_rows) / len(gap_rows), 1) if gap_rows else 0.0
    risk_count = sum(1 for row in rows if row.is_risk)
    return AiProgressSummary(
        rows=rows,
        plan_average=plan_average,
        ai_average=ai_average,
        progress_gap_average=progress_gap_average,
        risk_count=risk_count,
        ai_progress_ready_count=len(ready_rows),
        ai_progress_needs_analysis_count=len(rows) - len(ready_rows),
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

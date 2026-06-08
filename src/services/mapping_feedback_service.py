from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, Program, ProgramCommitMapping


IMPLEMENTATION_STATUS_OPTIONS = ["구현됨", "일부구현", "판단불가"]
LOW_RELEVANCE_MIN = 30.0
LOW_RELEVANCE_MAX = 70.0
SHORT_REASON_LENGTH = 20


@dataclass
class MappingFeedbackRow:
    mapping_id: int
    program_id: str | None
    program_name: str
    commit_hash: str
    commit_message: str
    author_name: str | None
    relevance_score: float
    is_related: bool | None
    implementation_status: str
    reason: str
    has_feedback: bool
    feedback_updated_at: datetime | None
    review_needed: bool = False
    review_reasons: list[str] = None

    def __post_init__(self) -> None:
        if self.review_reasons is None:
            self.review_reasons = []


@dataclass
class MappingFeedbackQualitySummary:
    total_count: int = 0
    feedback_completed_count: int = 0
    feedback_pending_count: int = 0
    review_needed_count: int = 0
    unknown_status_count: int = 0
    low_relevance_count: int = 0


def normalize_feedback_status(status: str | None) -> str:
    value = (status or "").strip()
    return value if value in IMPLEMENTATION_STATUS_OPTIONS else "판단불가"


def is_low_relevance_score(score: float | None) -> bool:
    value = float(score or 0)
    return LOW_RELEVANCE_MIN <= value < LOW_RELEVANCE_MAX


def mapping_review_reasons(row: MappingFeedbackRow) -> list[str]:
    reasons = []
    if not row.has_feedback:
        reasons.append("피드백 미완료")
    if row.is_related is None:
        reasons.append("관련 여부 미확정")
    elif row.is_related is False:
        reasons.append("비관련 판정")
    if normalize_feedback_status(row.implementation_status) == "판단불가":
        reasons.append("구현상태 판단불가")
    if is_low_relevance_score(row.relevance_score):
        reasons.append("낮거나 애매한 관련도")
    if not (row.reason or "").strip() or len((row.reason or "").strip()) < SHORT_REASON_LENGTH:
        reasons.append("근거 부족")
    if row.commit_hash and normalize_feedback_status(row.implementation_status) == "판단불가":
        reasons.append("관련 커밋 있음 + 판단불가")
    return reasons


def _base_mapping_feedback_query(db: Session, project_id: int):
    return (
        db.query(ProgramCommitMapping)
        .join(ProgramCommitMapping.program)
        .join(ProgramCommitMapping.commit)
        .options(joinedload(ProgramCommitMapping.program), joinedload(ProgramCommitMapping.commit))
        .filter(Program.project_id == project_id)
    )


def _keyword_filter(query, keyword: str | None):
    if not keyword:
        return query
    pattern = f"%{keyword}%"
    return query.filter(
        or_(
            Program.program_name.ilike(pattern),
            Program.program_id.ilike(pattern),
            GitCommit.message.ilike(pattern),
            GitCommit.commit_hash.ilike(pattern),
        )
    )


def feedback_row_matches_keyword(row: MappingFeedbackRow, keyword: str | None) -> bool:
    if not keyword:
        return True
    needle = keyword.strip().lower()
    if not needle:
        return True
    values = [
        row.program_name,
        row.program_id or "",
        row.commit_message,
        row.commit_hash,
    ]
    return any(needle in str(value or "").lower() for value in values)


def summarize_mapping_feedback_quality_rows(rows: list[MappingFeedbackRow]) -> MappingFeedbackQualitySummary:
    return MappingFeedbackQualitySummary(
        total_count=len(rows),
        feedback_completed_count=sum(1 for row in rows if row.has_feedback),
        feedback_pending_count=sum(1 for row in rows if not row.has_feedback),
        review_needed_count=sum(1 for row in rows if row.review_needed),
        unknown_status_count=sum(1 for row in rows if row.implementation_status == "판단불가"),
        low_relevance_count=sum(1 for row in rows if is_low_relevance_score(row.relevance_score)),
    )


def filter_mapping_review_queue_rows(
    rows: list[MappingFeedbackRow],
    *,
    queue_filter: str = "전체",
    keyword: str | None = None,
) -> list[MappingFeedbackRow]:
    filtered = [row for row in rows if feedback_row_matches_keyword(row, keyword)]
    if queue_filter == "리뷰 필요만":
        return [row for row in filtered if row.review_needed]
    if queue_filter == "피드백 미완료":
        return [row for row in filtered if not row.has_feedback]
    if queue_filter == "판단불가":
        return [row for row in filtered if row.implementation_status == "판단불가"]
    if queue_filter == "낮은 관련도":
        return [row for row in filtered if is_low_relevance_score(row.relevance_score)]
    if queue_filter == "비관련 판정":
        return [row for row in filtered if row.is_related is False]
    return filtered


def _mapping_to_feedback_row(mapping: ProgramCommitMapping) -> MappingFeedbackRow:
    program = mapping.program
    commit = mapping.commit
    row = MappingFeedbackRow(
        mapping_id=mapping.id,
        program_id=program.program_id if program else None,
        program_name=program.program_name if program else "",
        commit_hash=commit.commit_hash if commit else "",
        commit_message=((commit.message or "").splitlines()[0] if commit else ""),
        author_name=(commit.author_name or commit.author if commit else None),
        relevance_score=float(mapping.relevance_score or 0),
        is_related=mapping.is_related,
        implementation_status=normalize_feedback_status(mapping.implementation_status),
        reason=mapping.reason or "",
        has_feedback=mapping.feedback_updated_at is not None,
        feedback_updated_at=mapping.feedback_updated_at,
    )
    row.review_reasons = mapping_review_reasons(row)
    row.review_needed = bool(row.review_reasons)
    return row


def list_mapping_feedback_rows(
    db: Session,
    project_id: int,
    *,
    only_feedback: bool = False,
    related_filter: bool | None = None,
    keyword: str | None = None,
    limit: int = 300,
) -> list[MappingFeedbackRow]:
    query = _base_mapping_feedback_query(db, project_id)

    if only_feedback:
        query = query.filter(ProgramCommitMapping.feedback_updated_at.isnot(None))
    if related_filter is not None:
        query = query.filter(ProgramCommitMapping.is_related.is_(related_filter))
    query = _keyword_filter(query, keyword)

    mappings = (
        query.order_by(
            ProgramCommitMapping.feedback_updated_at.desc().nullslast(),
            ProgramCommitMapping.relevance_score.desc().nullslast(),
            ProgramCommitMapping.id.desc(),
        )
        .limit(limit)
        .all()
    )

    return [_mapping_to_feedback_row(mapping) for mapping in mappings]


def summarize_mapping_feedback_quality(db: Session, project_id: int) -> MappingFeedbackQualitySummary:
    rows = [_mapping_to_feedback_row(mapping) for mapping in _base_mapping_feedback_query(db, project_id).all()]
    return summarize_mapping_feedback_quality_rows(rows)


def list_mapping_review_queue_rows(
    db: Session,
    project_id: int,
    *,
    queue_filter: str = "전체",
    keyword: str | None = None,
    limit: int = 300,
) -> list[MappingFeedbackRow]:
    query = _keyword_filter(_base_mapping_feedback_query(db, project_id), keyword)
    mappings = (
        query.order_by(
            ProgramCommitMapping.feedback_updated_at.asc().nullsfirst(),
            ProgramCommitMapping.relevance_score.asc().nullsfirst(),
            ProgramCommitMapping.id.desc(),
        )
        .limit(limit)
        .all()
    )
    rows = [_mapping_to_feedback_row(mapping) for mapping in mappings]

    return filter_mapping_review_queue_rows(rows, queue_filter=queue_filter)


def apply_mapping_feedback(
    db: Session,
    mapping_id: int,
    *,
    is_related: bool,
    relevance_score: float,
    implementation_status: str,
    reason: str,
) -> ProgramCommitMapping:
    mapping = db.query(ProgramCommitMapping).filter(ProgramCommitMapping.id == mapping_id).one()
    score = min(max(float(relevance_score), 0.0), 100.0)
    normalized_status = normalize_feedback_status(implementation_status)
    now = datetime.now(timezone.utc)

    mapping.is_related = is_related
    mapping.relevance_score = score
    mapping.implementation_status = normalized_status
    mapping.reason = reason.strip()
    mapping.feedback_is_related = is_related
    mapping.feedback_relevance_score = score
    mapping.feedback_implementation_status = normalized_status
    mapping.feedback_reason = reason.strip()
    mapping.feedback_updated_at = now
    db.commit()
    db.refresh(mapping)
    return mapping

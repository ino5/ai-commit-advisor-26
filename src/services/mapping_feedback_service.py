from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, Program, ProgramCommitMapping


IMPLEMENTATION_STATUS_OPTIONS = ["구현됨", "일부구현", "판단불가"]


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


def normalize_feedback_status(status: str | None) -> str:
    value = (status or "").strip()
    return value if value in IMPLEMENTATION_STATUS_OPTIONS else "판단불가"


def list_mapping_feedback_rows(
    db: Session,
    project_id: int,
    *,
    only_feedback: bool = False,
    related_filter: bool | None = None,
    keyword: str | None = None,
    limit: int = 300,
) -> list[MappingFeedbackRow]:
    query = (
        db.query(ProgramCommitMapping)
        .join(ProgramCommitMapping.program)
        .join(ProgramCommitMapping.commit)
        .options(joinedload(ProgramCommitMapping.program), joinedload(ProgramCommitMapping.commit))
        .filter(Program.project_id == project_id)
    )

    if only_feedback:
        query = query.filter(ProgramCommitMapping.feedback_updated_at.isnot(None))
    if related_filter is not None:
        query = query.filter(ProgramCommitMapping.is_related.is_(related_filter))
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (Program.program_name.ilike(pattern))
            | (Program.program_id.ilike(pattern))
            | (GitCommit.message.ilike(pattern))
            | (GitCommit.commit_hash.ilike(pattern))
        )

    mappings = (
        query.order_by(
            ProgramCommitMapping.feedback_updated_at.desc().nullslast(),
            ProgramCommitMapping.relevance_score.desc().nullslast(),
            ProgramCommitMapping.id.desc(),
        )
        .limit(limit)
        .all()
    )

    rows = []
    for mapping in mappings:
        program = mapping.program
        commit = mapping.commit
        rows.append(
            MappingFeedbackRow(
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
        )
    return rows


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

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import AIInvocationLog


@dataclass(frozen=True)
class AIInvocationLogRow:
    id: int
    project_id: int | None
    feature: str
    provider: str
    model: str | None
    status: str
    mode: str | None
    fallback_used: bool
    validation_status: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    prompt_length: int | None
    response_length: int | None
    error_message: str | None
    raw_metadata: dict | None


@dataclass(frozen=True)
class AIInvocationSummary:
    total_count: int
    success_count: int
    failed_count: int
    fallback_count: int
    average_duration_ms: float


def _to_row(record: AIInvocationLog) -> AIInvocationLogRow:
    return AIInvocationLogRow(
        id=int(record.id),
        project_id=int(record.project_id) if record.project_id is not None else None,
        feature=record.feature,
        provider=record.provider,
        model=record.model,
        status=record.status,
        mode=record.mode,
        fallback_used=bool(record.fallback_used),
        validation_status=record.validation_status,
        started_at=record.started_at,
        finished_at=record.finished_at,
        duration_ms=record.duration_ms,
        prompt_length=record.prompt_length,
        response_length=record.response_length,
        error_message=record.error_message,
        raw_metadata=record.raw_metadata,
    )


def record_ai_invocation(
    db: Session,
    *,
    project_id: int | None,
    feature: str,
    provider: str,
    model: str | None = None,
    status: str = "completed",
    mode: str | None = None,
    fallback_used: bool = False,
    validation_status: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    duration_ms: int | None = None,
    prompt_length: int | None = None,
    response_length: int | None = None,
    error_message: str | None = None,
    raw_metadata: dict | None = None,
    commit: bool = False,
) -> AIInvocationLogRow:
    record = AIInvocationLog(
        project_id=project_id,
        feature=feature,
        provider=provider or "unknown",
        model=model,
        status=status,
        mode=mode,
        fallback_used=fallback_used,
        validation_status=validation_status,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        prompt_length=prompt_length,
        response_length=response_length,
        error_message=error_message,
        raw_metadata=raw_metadata,
    )
    db.add(record)
    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()
    return _to_row(record)


def list_ai_invocations(db: Session, project_id: int, limit: int = 50) -> list[AIInvocationLogRow]:
    records = (
        db.query(AIInvocationLog)
        .filter(AIInvocationLog.project_id == project_id)
        .order_by(AIInvocationLog.created_at.desc(), AIInvocationLog.id.desc())
        .limit(limit)
        .all()
    )
    return [_to_row(record) for record in records]


def summarize_ai_invocations(db: Session, project_id: int) -> AIInvocationSummary:
    rows = db.query(AIInvocationLog).filter(AIInvocationLog.project_id == project_id).all()
    total = len(rows)
    success = sum(1 for row in rows if row.status == "completed")
    failed = sum(1 for row in rows if row.status == "failed")
    fallback = sum(1 for row in rows if row.fallback_used)
    durations = [int(row.duration_ms) for row in rows if row.duration_ms is not None]
    average = round(sum(durations) / len(durations), 1) if durations else 0.0
    return AIInvocationSummary(
        total_count=total,
        success_count=success,
        failed_count=failed,
        fallback_count=fallback,
        average_duration_ms=average,
    )


from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import ProjectChatMessage, ProjectChatSession


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_chat_session(db: Session, project_id: int, title: str | None = None) -> ProjectChatSession:
    session = ProjectChatSession(
        project_id=project_id,
        title=title or "새 대화",
        status="active",
        last_message_at=_now(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_chat_sessions(db: Session, project_id: int, *, limit: int = 30) -> list[ProjectChatSession]:
    return (
        db.query(ProjectChatSession)
        .filter(ProjectChatSession.project_id == project_id)
        .order_by(ProjectChatSession.last_message_at.desc().nullslast(), ProjectChatSession.id.desc())
        .limit(limit)
        .all()
    )


def get_chat_session(db: Session, project_id: int, session_id: int) -> ProjectChatSession | None:
    return (
        db.query(ProjectChatSession)
        .filter(ProjectChatSession.id == session_id, ProjectChatSession.project_id == project_id)
        .one_or_none()
    )


def get_session_messages(db: Session, session_id: int) -> list[ProjectChatMessage]:
    return (
        db.query(ProjectChatMessage)
        .filter(ProjectChatMessage.session_id == session_id)
        .order_by(ProjectChatMessage.message_index)
        .all()
    )


def _next_message_index(db: Session, session_id: int) -> int:
    current = (
        db.query(func.max(ProjectChatMessage.message_index))
        .filter(ProjectChatMessage.session_id == session_id)
        .scalar()
    )
    return int(current or 0) + 1


def _derive_title(question: str) -> str:
    title = " ".join(question.strip().split())
    if len(title) > 60:
        title = title[:57].rstrip() + "..."
    return title or "새 대화"


def append_chat_message(
    db: Session,
    session_id: int,
    *,
    role: str,
    content: str,
    sources: list[dict] | None = None,
    expanded_queries: list[str] | None = None,
    matched_terms: list[dict] | None = None,
    excluded_count: int | None = None,
    used_source_count: int | None = None,
    insufficient_evidence: bool = False,
    raw_metadata: dict | None = None,
) -> ProjectChatMessage:
    session = db.get(ProjectChatSession, session_id)
    if session is None:
        raise ValueError(f"Project chat session not found: {session_id}")

    message = ProjectChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        message_index=_next_message_index(db, session_id),
        sources=sources,
        expanded_queries=expanded_queries,
        matched_terms=matched_terms,
        excluded_count=excluded_count,
        used_source_count=used_source_count,
        insufficient_evidence=insufficient_evidence,
        raw_metadata=raw_metadata,
    )
    db.add(message)
    now = _now()
    session.last_message_at = now
    if role == "user" and (not session.title or session.title == "새 대화"):
        session.title = _derive_title(content)
    db.commit()
    db.refresh(message)
    return message


def message_to_ui_dict(message: ProjectChatMessage) -> dict:
    return {
        "role": message.role,
        "content": message.content,
        "sources": message.sources or [],
        "expanded_queries": message.expanded_queries or [],
        "matched_terms": message.matched_terms or [],
        "excluded_count": message.excluded_count or 0,
        "used_source_count": message.used_source_count or 0,
        "insufficient_evidence": bool(message.insufficient_evidence),
    }


def messages_to_ui_dicts(messages: list[ProjectChatMessage]) -> list[dict]:
    return [message_to_ui_dict(message) for message in messages]


def format_sources_for_export(sources: list[dict]) -> str:
    lines: list[str] = []
    for rank, source in enumerate(sources, start=1):
        metadata = source.get("metadata") or {}
        source_type = source.get("source_type") or "-"
        file_path = metadata.get("file_path") or source.get("source_id") or "-"
        line_start = metadata.get("line_start")
        line_end = metadata.get("line_end")
        line_range = f"{line_start}-{line_end}" if line_start and line_end else "-"
        verification = source.get("verification_status") or "-"
        similarity = source.get("similarity")
        score = f"{float(similarity):.4f}" if similarity is not None else "-"
        lines.append(f"{rank}. `{file_path}:{line_range}` ({source_type}, {verification}, score={score})")
    return "\n".join(lines) if lines else "근거 없음"


def format_message_citation_export(message: dict | ProjectChatMessage) -> str:
    if isinstance(message, ProjectChatMessage):
        content = message.content
        sources = message.sources or []
        used_source_count = message.used_source_count or 0
    else:
        content = str(message.get("content") or "")
        sources = message.get("sources") or []
        used_source_count = int(message.get("used_source_count") or 0)

    current_sources = [
        source
        for source in sources
        if source.get("source_type") == "source_file" and source.get("verification_status") == "verified"
    ]
    reference_sources = [
        source
        for source in sources
        if not (source.get("source_type") == "source_file" and source.get("verification_status") == "verified")
    ]
    return "\n\n".join(
        [
            "## Project Chat 답변",
            content.strip() or "-",
            "## 현재 소스 근거",
            format_sources_for_export(current_sources[: used_source_count or len(current_sources)]),
            "## 이력/참고 근거",
            format_sources_for_export(reference_sources),
        ]
    )

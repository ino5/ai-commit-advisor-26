from __future__ import annotations

import uuid

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.rag.chat_history_service import (
    append_chat_message,
    create_chat_session,
    format_message_citation_export,
    get_session_messages,
    list_chat_sessions,
    messages_to_ui_dicts,
)


def _create_project(db) -> Project:
    project = Project(name=f"chat-history-test-{uuid.uuid4()}", git_repo_path=None)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_project_chat_session_persists_messages_in_order():
    init_db()
    with SessionLocal() as db:
        project = _create_project(db)
        try:
            session = create_chat_session(db, project.id)
            append_chat_message(db, session.id, role="user", content="결제 금액 검증은 어디인가요?")
            append_chat_message(
                db,
                session.id,
                role="assistant",
                content="`src/payment.py:1-3`에서 검증합니다.",
                sources=[
                    {
                        "source_type": "source_file",
                        "source_id": "src/payment.py",
                        "verification_status": "verified",
                        "similarity": 0.91,
                        "metadata": {"file_path": "src/payment.py", "line_start": 1, "line_end": 3},
                    }
                ],
                expanded_queries=["결제 금액 검증", "payment amount validation"],
                used_source_count=1,
                raw_metadata={
                    "graph_evidence": [
                        {
                            "evidence_type": "class_import",
                            "source_class": "PaymentService",
                            "target_class": "OrderMapper",
                            "path": ["PaymentService", "OrderMapper"],
                            "matched_seeds": ["paymentservice"],
                        }
                    ],
                    "graph_evidence_metadata": {"status": "completed", "evidence_count": 1},
                },
            )

            sessions = list_chat_sessions(db, project.id)
            messages = get_session_messages(db, session.id)
            ui_messages = messages_to_ui_dicts(messages)

            assert sessions[0].id == session.id
            assert sessions[0].title == "결제 금액 검증은 어디인가요?"
            assert [message.role for message in messages] == ["user", "assistant"]
            assert [message.message_index for message in messages] == [1, 2]
            assert ui_messages[1]["sources"][0]["metadata"]["file_path"] == "src/payment.py"
            assert ui_messages[1]["expanded_queries"] == ["결제 금액 검증", "payment amount validation"]
            assert ui_messages[1]["graph_evidence"][0]["target_class"] == "OrderMapper"
            assert ui_messages[1]["graph_evidence_metadata"]["status"] == "completed"
        finally:
            db.delete(project)
            db.commit()


def test_format_message_citation_export_groups_current_and_reference_sources():
    export = format_message_citation_export(
        {
            "content": "결제 금액은 현재 소스에서 검증합니다.",
            "used_source_count": 1,
            "sources": [
                {
                    "source_type": "source_file",
                    "source_id": "src/payment.py",
                    "verification_status": "verified",
                    "similarity": 0.91,
                    "metadata": {"file_path": "src/payment.py", "line_start": 1, "line_end": 3},
                },
                {
                    "source_type": "commit_file",
                    "source_id": "src/payment.py",
                    "verification_status": "historical",
                    "similarity": 0.72,
                    "metadata": {"file_path": "src/payment.py", "commit_hash": "abc123"},
                },
            ],
            "graph_evidence": [
                {
                    "evidence_type": "class_import",
                    "source_class": "PaymentService",
                    "target_class": "OrderMapper",
                    "source_file": "src/payment.py",
                    "target_file": "src/order.py",
                    "path": ["PaymentService", "OrderMapper"],
                    "matched_seeds": ["paymentservice"],
                }
            ],
        }
    )

    assert "## Project Chat 답변" in export
    assert "`src/payment.py:1-3` (source_file, verified, score=0.9100)" in export
    assert "`src/payment.py:-` (commit_file, historical, score=0.7200)" in export
    assert "## 그래프 관계 근거" in export
    assert "PaymentService -> OrderMapper" in export

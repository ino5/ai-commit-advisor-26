from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import (
    AIInvocationLog,
    CodeReviewResult,
    CommitFile,
    Developer,
    DocumentChunk,
    GitCommit,
    PLBriefingHistory,
    Program,
    ProgramCommitMapping,
    ProgramImplementationStatus,
    Project,
    ProjectChatMessage,
    ProjectChatSession,
    RiskFinding,
    VectorItem,
)
from src.services.ai_evidence_service import (
    FAIL,
    PASS,
    WARN,
    EvidenceStatusRow,
    generate_weekly_ai_report,
    get_ai_evaluation_scorecard,
    get_ai_operations_status_rows,
    get_evidence_trace,
    get_ai_readiness_rows,
    priority_status_rows,
    summarize_status_rows,
)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def test_ai_evidence_status_summary_prioritizes_attention_rows():
    rows = [
        EvidenceStatusRow("통과 영역", PASS, "ok", "없음"),
        EvidenceStatusRow("주의 영역", WARN, "partial", "확인"),
        EvidenceStatusRow("실패 영역", FAIL, "missing", "조치"),
    ]

    summary = summarize_status_rows(rows)
    focused = priority_status_rows(rows)
    all_rows = priority_status_rows(rows, include_pass=True)

    assert summary.total_count == 3
    assert summary.pass_count == 1
    assert summary.warn_count == 1
    assert summary.fail_count == 1
    assert summary.attention_count == 2
    assert [row.area for row in focused] == ["실패 영역", "주의 영역"]
    assert [row.status for row in all_rows] == [FAIL, WARN, PASS]


def test_ai_evidence_service_returns_readiness_trace_scorecard_and_report():
    init_db()
    with SessionLocal() as db:
        developer = Developer(
            developer_key=_unique("evidence-key"),
            developer_id=_unique("evidence-id"),
            developer_name="Evidence Owner",
            email=f"{uuid.uuid4()}@example.local",
        )
        project = Project(
            name=_unique("evidence-project"),
            git_repo_path=None,
            last_synced_commit_hash="abc123",
            last_synced_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        db.add_all([developer, project])
        db.flush()
        program = Program(
            project_id=project.id,
            program_id=_unique("P-EV"),
            program_name="Evidence Program",
            developer_id=developer.developer_id,
            developer=developer.developer_name,
            status="진행중",
            progress_rate=80,
            planned_start_date=date.today() - timedelta(days=20),
            planned_end_date=date.today() + timedelta(days=5),
        )
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Implement evidence path",
            author_name=developer.developer_name,
            committed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
            mapping_analyzed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        db.add_all([program, commit])
        db.flush()
        db.add_all(
            [
                CommitFile(
                    commit_id=commit.id,
                    git_commit_id=commit.id,
                    file_path="src/evidence/EvidenceService.java",
                    change_type="Modified",
                    diff_text="+evidence",
                ),
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=commit.id,
                    relevance_score=90,
                    is_related=True,
                    implementation_status="일부구현",
                    reason="evidence mapping",
                    raw_response={"llm": {"provider": "local_openai"}, "prompt_length": 100},
                ),
                ProgramImplementationStatus(
                    program_id=program.id,
                    status="IN_PROGRESS",
                    summary="partial",
                    completed_features=[],
                    incomplete_features=["remaining"],
                    evidence_commits=[commit.commit_hash],
                    analyzed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
                ),
                RiskFinding(
                    project_id=project.id,
                    program_id=program.id,
                    risk_type="PROGRESS_GAP",
                    risk_level="HIGH",
                    title="progress gap",
                    resolved_yn="N",
                ),
                CodeReviewResult(
                    project_id=project.id,
                    target_type="commit",
                    target_ref=commit.commit_hash,
                    status="completed",
                    summary="review summary",
                    commit_analysis={"risk_level": "medium"},
                    bug_findings=[],
                    refactoring_suggestions=[],
                    raw_response={"llm": {"provider": "local_openai"}},
                ),
                PLBriefingHistory(
                    project_id=project.id,
                    provider="local_openai",
                    model="test-model",
                    mode="LLM 생성",
                    title="PL 주간 점검 브리핑",
                    summary="Evidence Program 확인 필요",
                    priority_items=[{"program_name": "Evidence Program"}],
                    meeting_questions=["확인했나요?"],
                    next_actions=[{"action": "확인"}],
                    rendered_text="## PL 주간 점검 브리핑\n### 요약\nEvidence Program 확인 필요",
                    evidence_payload={"items": [{"program_name": "Evidence Program"}]},
                    raw_response={"validation_status": "valid", "repair_attempted": False},
                ),
                AIInvocationLog(
                    project_id=project.id,
                    feature="pl_briefing",
                    provider="local_openai",
                    model="test-model",
                    status="completed",
                    mode="LLM 생성",
                    fallback_used=False,
                    validation_status="valid",
                    duration_ms=100,
                    prompt_length=1000,
                    response_length=500,
                    raw_metadata={"history_title": "PL 주간 점검 브리핑"},
                ),
            ]
        )
        chat_session = ProjectChatSession(project_id=project.id, title="evidence chat")
        chunk = DocumentChunk(
            project_id=project.id,
            source_type="source_file",
            source_id="src/evidence/EvidenceService.java",
            chunk_index=0,
            chunk_text="evidence",
            raw_metadata={"file_path": "src/evidence/EvidenceService.java", "line_start": 1, "line_end": 1},
        )
        db.add_all([chat_session, chunk])
        db.flush()
        db.add_all(
            [
                ProjectChatMessage(
                    session_id=chat_session.id,
                    role="assistant",
                    content="근거 답변",
                    message_index=1,
                    sources=[{"source_type": "source_file", "verification_status": "verified"}],
                    used_source_count=1,
                    excluded_count=0,
                    raw_metadata={
                        "graph_evidence": [
                            {
                                "evidence_type": "impact_path",
                                "program": "Evidence Program",
                                "commit": commit.commit_hash[:12],
                                "file_path": "src/evidence/EvidenceService.java",
                                "class_name": "EvidenceService",
                                "path": ["Evidence Program", commit.commit_hash[:12], "EvidenceService"],
                            }
                        ],
                        "graph_evidence_metadata": {"status": "completed", "evidence_count": 1},
                    },
                ),
                VectorItem(chunk_id=chunk.id, embedding_model="mock", embedding=None),
            ]
        )
        db.commit()

        try:
            readiness = get_ai_readiness_rows(db, project.id)
            operations = get_ai_operations_status_rows(db, project.id)
            scorecard = get_ai_evaluation_scorecard(db, project.id)
            trace = get_evidence_trace(db, project.id)
            report = generate_weekly_ai_report(db, project.id)

            assert any(row.area == "AI Telemetry" and row.status == PASS for row in readiness)
            assert any(row.area == "LLM" for row in operations)
            assert any(row.area == "Embedding" and row.value.endswith("d") for row in operations)
            assert any(row.area == "최근 AI 호출" and "pl_briefing" in row.value for row in operations)
            assert any(row.area == "검색 준비" and "vectors=1" in row.value for row in operations)
            assert any(row.area == "PL Briefing" and row.status == PASS for row in scorecard)
            assert trace.latest_pl_briefing is not None
            assert trace.latest_pl_briefing["validation_status"] == "valid"
            assert trace.recent_mappings
            assert trace.recent_chat_answers
            assert trace.recent_chat_answers[0]["graph_evidence_count"] == 1
            assert trace.recent_chat_answers[0]["graph_status"] == "completed"
            assert trace.recent_code_reviews
            assert "# 주간 AI 점검 보고서" in report
            assert "Evidence Program" in report
            assert "AI 호출 Telemetry" in report
        finally:
            db.delete(project)
            db.delete(developer)
            db.commit()

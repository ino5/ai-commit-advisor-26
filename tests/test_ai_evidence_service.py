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
from src.services import ai_evidence_service
from src.services.neo4j_graph_service import Neo4jConnectionStatus, Neo4jGraphFreshness, Neo4jGraphPreview, Neo4jSyncResult


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


def test_ai_evidence_service_returns_readiness_trace_scorecard_and_report(monkeypatch):
    init_db()
    monkeypatch.setattr(
        ai_evidence_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness(
            "latest",
            "Neo4j graph가 현재 DB/Git 기준과 일치합니다.",
            repo_head_hash="abc123456789",
            graph_sync_head_hash="abc123456789",
            node_count=10,
            edge_count=20,
        ),
    )
    monkeypatch.setattr(
        ai_evidence_service,
        "get_neo4j_project_summary",
        lambda project_id: Neo4jSyncResult(
            "completed",
            "Neo4j summary 조회 완료",
            node_count=10,
            edge_count=20,
            node_counts={"class": 2, "commit": 2},
            edge_counts={"IMPORTS_CLASS": 1, "MAPPED_TO_COMMIT": 2},
        ),
    )
    monkeypatch.setattr(
        ai_evidence_service,
        "get_neo4j_project_preview",
        lambda project_id: Neo4jGraphPreview(
            "completed",
            "Neo4j graph preview 조회 완료",
            class_import_rows=[{"source": "EvidenceService", "target": "EvidenceClient"}],
            impact_rows=[{"program": "Evidence Program"}],
        ),
    )
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
        low_confidence_commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Adjust evidence fallback path",
            author_name=developer.developer_name,
            committed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
            mapping_analyzed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        db.add_all([program, commit, low_confidence_commit])
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
                    reason="evidence mapping reason is clear enough",
                    raw_response={"llm": {"provider": "local_openai"}, "prompt_length": 100},
                ),
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=low_confidence_commit.id,
                    relevance_score=55,
                    is_related=True,
                    implementation_status="판단불가",
                    reason="짧음",
                    raw_response={"fallback": True, "prompt_length": 50},
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
            scorecard_rows = {row.area: row for row in scorecard}
            assert scorecard_rows["Mapping"].status == WARN
            assert "unknown=1" in scorecard_rows["Mapping"].value
            assert "low=1" in scorecard_rows["Mapping"].value
            assert "short_reason=1" in scorecard_rows["Mapping"].value
            assert "feedback_pending=2" in scorecard_rows["Mapping"].value
            assert "fallback=1" in scorecard_rows["Mapping"].value
            assert scorecard_rows["Mapping"].target_page == "Mapping"
            assert scorecard_rows["RAG / Project Chat"].status == PASS
            assert "verified_source=100.0%" in scorecard_rows["RAG / Project Chat"].value
            assert "insufficient=0.0%" in scorecard_rows["RAG / Project Chat"].value
            assert scorecard_rows["RAG / Project Chat"].target_page == "Project Chat"
            assert "provider=local_openai" in scorecard_rows["PL Briefing"].value
            assert "validation=valid" in scorecard_rows["PL Briefing"].value
            assert scorecard_rows["PL Briefing"].target_page == "Dashboard"
            assert "completed=1/1" in scorecard_rows["AI Code Review"].value
            assert scorecard_rows["Knowledge Graph"].status == PASS
            assert "classes=2" in scorecard_rows["Knowledge Graph"].value
            assert "imports=1" in scorecard_rows["Knowledge Graph"].value
            assert "impact_paths=1" in scorecard_rows["Knowledge Graph"].value
            assert all("샘플" not in row.action for row in scorecard)
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


def test_ai_operations_status_includes_graph_readiness_rows(monkeypatch):
    init_db()
    synced_at = datetime(2026, 6, 15, tzinfo=timezone.utc)

    monkeypatch.setattr(
        ai_evidence_service,
        "get_neo4j_connection_status",
        lambda: Neo4jConnectionStatus(True, True, "Neo4j 연결됨", "bolt://localhost:7687", "neo4j"),
    )
    monkeypatch.setattr(
        ai_evidence_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness(
            "latest",
            "Neo4j graph가 현재 DB/Git 기준과 일치합니다.",
            repo_head_hash="abc123456789",
            db_sync_head_hash="abc123456789",
            graph_sync_head_hash="abc123456789",
            synced_at=synced_at,
            sync_mode="incremental",
            node_count=10,
            edge_count=20,
        ),
    )
    monkeypatch.setattr(
        ai_evidence_service,
        "get_neo4j_project_summary",
        lambda project_id: Neo4jSyncResult("completed", "Neo4j summary 조회 완료", node_count=10, edge_count=20),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("graph-ops-project"), git_repo_path=None)
        db.add(project)
        db.flush()
        session = ProjectChatSession(project_id=project.id, title="graph chat")
        db.add(session)
        db.flush()
        db.add(
            ProjectChatMessage(
                session_id=session.id,
                role="assistant",
                content="graph answer",
                message_index=1,
                raw_metadata={
                    "graph_evidence": [{"evidence_type": "impact_path"}],
                    "graph_evidence_metadata": {"status": "completed", "evidence_count": 1},
                },
            )
        )
        db.commit()

        try:
            rows = {row.area: row for row in get_ai_operations_status_rows(db, project.id)}

            assert rows["Neo4j"].status == PASS
            assert "database=neo4j" in rows["Neo4j"].value
            assert rows["Knowledge Graph"].status == PASS
            assert "최신" in rows["Knowledge Graph"].value
            assert rows["Graph Readback"].status == PASS
            assert rows["Graph Readback"].value == "nodes=10, edges=20"
            assert rows["Project Chat GraphRAG"].status == PASS
            assert "evidence=1" in rows["Project Chat GraphRAG"].value
        finally:
            db.delete(project)
            db.commit()


def test_ai_operations_status_reports_graph_readback_failure(monkeypatch):
    init_db()
    monkeypatch.setattr(
        ai_evidence_service,
        "get_neo4j_connection_status",
        lambda: Neo4jConnectionStatus(True, True, "Neo4j 연결됨", "bolt://localhost:7687", "neo4j"),
    )
    monkeypatch.setattr(
        ai_evidence_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness(
            "latest",
            "Neo4j graph가 현재 DB/Git 기준과 일치합니다.",
            repo_head_hash="abc123",
            graph_sync_head_hash="abc123",
            node_count=10,
            edge_count=20,
        ),
    )
    monkeypatch.setattr(
        ai_evidence_service,
        "get_neo4j_project_summary",
        lambda project_id: Neo4jSyncResult("failed", "Neo4j summary 조회 실패", errors=["readback failed"]),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("graph-readback-project"), git_repo_path=None)
        db.add(project)
        db.commit()

        try:
            rows = {row.area: row for row in get_ai_operations_status_rows(db, project.id)}

            assert rows["Graph Readback"].status == FAIL
            assert rows["Graph Readback"].action == "readback failed"
            assert rows["Project Chat GraphRAG"].status == WARN
            assert "recent=없음" in rows["Project Chat GraphRAG"].value
        finally:
            db.delete(project)
            db.commit()

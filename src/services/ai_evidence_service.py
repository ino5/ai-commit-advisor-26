from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.db.models import (
    AIInvocationLog,
    CodeReviewResult,
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
from src.rag.chunker import SOURCE_FILE_TYPE
from src.rag.embedding_client import EmbeddingClient
from src.rag.source_index_service import get_source_index_status, refresh_source_file_index
from src.rag.vector_store import VectorStore
from src.services.ai_invocation_service import list_ai_invocations, summarize_ai_invocations
from src.services.ai_resource_radar_service import (
    build_ai_resource_radar,
    generate_pl_briefing,
    get_latest_pl_briefing,
    save_pl_briefing,
)
from src.services.mapping_feedback_service import (
    SHORT_REASON_LENGTH,
    summarize_mapping_feedback_quality,
)
from src.services.mapping_service import MappingService
from src.services.neo4j_graph_service import (
    get_neo4j_connection_status,
    get_neo4j_project_preview,
    get_neo4j_project_summary,
    get_project_graph_freshness,
)
from src.services.resource_metrics_service import get_resource_metrics_summary
from src.services.risk_service import run_risk_analysis
from src.utils.config import settings


PASS = "통과"
WARN = "주의"
FAIL = "실패"


@dataclass(frozen=True)
class EvidenceStatusRow:
    area: str
    status: str
    value: str
    action: str
    target_group: str | None = None
    target_page: str | None = None


@dataclass(frozen=True)
class EvidenceStatusSummary:
    total_count: int
    pass_count: int
    warn_count: int
    fail_count: int

    @property
    def attention_count(self) -> int:
        return self.warn_count + self.fail_count


@dataclass(frozen=True)
class EvidenceTrace:
    latest_pl_briefing: dict | None
    recent_mappings: list[dict]
    recent_chat_answers: list[dict]
    recent_code_reviews: list[dict]
    recent_invocations: list[dict]


@dataclass(frozen=True)
class EvidenceActionResult:
    title: str
    summary: str
    status: str = "completed"
    details: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


_STATUS_PRIORITY = {FAIL: 0, WARN: 1, PASS: 2}


def _status(ok: bool, *, warn: bool = False) -> str:
    if ok:
        return PASS
    return WARN if warn else FAIL


def _format_dt(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def summarize_status_rows(rows: list[EvidenceStatusRow]) -> EvidenceStatusSummary:
    counter = Counter(row.status for row in rows)
    return EvidenceStatusSummary(
        total_count=len(rows),
        pass_count=counter.get(PASS, 0),
        warn_count=counter.get(WARN, 0),
        fail_count=counter.get(FAIL, 0),
    )


def priority_status_rows(rows: list[EvidenceStatusRow], *, include_pass: bool = False) -> list[EvidenceStatusRow]:
    visible_rows = rows if include_pass else [row for row in rows if row.status != PASS]
    return sorted(visible_rows, key=lambda row: (_STATUS_PRIORITY.get(row.status, 99), row.area))


def _graph_freshness_label(status: str) -> str:
    return {
        "latest": "최신",
        "stale": "갱신 필요",
        "missing": "저장 필요",
        "failed": "실패",
        "skipped": "미사용",
    }.get(status, status)


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def _format_percent(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "-"
    return f"{(numerator / denominator) * 100:.1f}%"


def _contains_truthy_key(payload: object, key: str) -> bool:
    if isinstance(payload, dict):
        for raw_key, value in payload.items():
            if str(raw_key).lower() == key.lower() and bool(value):
                return True
            if _contains_truthy_key(value, key):
                return True
    if isinstance(payload, list):
        return any(_contains_truthy_key(item, key) for item in payload)
    return False


def _recent_graph_evidence_row(db: Session, project_id: int, *, graph_ready: bool, graph_freshness_status: str) -> EvidenceStatusRow:
    messages = (
        db.query(ProjectChatMessage)
        .join(ProjectChatSession, ProjectChatMessage.session_id == ProjectChatSession.id)
        .filter(ProjectChatSession.project_id == project_id, ProjectChatMessage.role == "assistant")
        .order_by(ProjectChatMessage.created_at.desc(), ProjectChatMessage.id.desc())
        .limit(20)
        .all()
    )
    latest_metadata = None
    latest_count = 0
    for message in messages:
        metadata = message.raw_metadata or {}
        graph_metadata = metadata.get("graph_evidence_metadata") or {}
        if not graph_metadata:
            continue
        latest_metadata = graph_metadata
        latest_count = len(metadata.get("graph_evidence") or [])
        break

    if latest_metadata is None:
        return EvidenceStatusRow(
            "Project Chat GraphRAG",
            WARN,
            f"ready={graph_ready}, recent=없음",
            "Knowledge Graph를 최신으로 맞춘 뒤 Project Chat에서 graph 관계 질문을 실행하세요.",
        )

    graph_status = str(latest_metadata.get("status") or "-")
    evidence_count = int(latest_metadata.get("evidence_count") or latest_count or 0)
    if graph_status == "failed":
        row_status = FAIL
    elif graph_ready and graph_freshness_status == "latest" and graph_status == "completed" and evidence_count > 0:
        row_status = PASS
    else:
        row_status = WARN

    return EvidenceStatusRow(
        "Project Chat GraphRAG",
        row_status,
        f"ready={graph_ready}, recent={graph_status}, evidence={evidence_count}",
        "Graph evidence가 없거나 오래되면 Knowledge Graph 동기화와 Project Chat 질문 seed를 확인하세요.",
    )


def get_ai_operations_status_rows(db: Session, project_id: int) -> list[EvidenceStatusRow]:
    project = db.get(Project, project_id)
    if project is None:
        return [EvidenceStatusRow("프로젝트", FAIL, "-", "프로젝트를 다시 선택하세요.")]

    llm_provider = settings.llm_provider or "mock"
    llm_model = settings.llm_model or "-"
    embedding_provider = settings.embedding_provider or "mock"
    embedding_model = settings.embedding_model or "-"

    latest_invocation = list_ai_invocations(db, project_id, limit=1)
    telemetry = summarize_ai_invocations(db, project_id)
    if latest_invocation:
        latest = latest_invocation[0]
        invocation_status = FAIL if latest.status == "failed" else WARN if latest.fallback_used else PASS
        latest_value = f"{latest.feature} / {latest.provider} / {latest.model or '-'} / fallback={latest.fallback_used}"
        latest_action = "실패나 fallback이 있으면 호출 기록을 확인하세요."
    else:
        invocation_status = WARN
        latest_value = "호출 없음"
        latest_action = "AI 기능을 한 번 실행하면 기록됩니다."

    try:
        source_status = get_source_index_status(db, project)
    except Exception as exc:
        source_status = None
        source_value = str(exc)
        source_row_status = WARN
    else:
        embedding_models = sorted(
            {
                model or "-"
                for (model,) in (
                    db.query(VectorItem.embedding_model)
                    .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
                    .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
                    .distinct()
                    .all()
                )
            }
        )
        source_row_status = _status(
            source_status.source_chunk_count > 0
            and source_status.source_vector_count > 0
            and source_status.missing_embedding_count == 0
            and not source_status.needs_reindex,
            warn=source_status.source_chunk_count > 0 or source_status.source_vector_count > 0,
        )
        model_count = len(embedding_models)
        source_value = (
            f"chunks={source_status.source_chunk_count}, vectors={source_status.source_vector_count}, "
            f"missing={source_status.missing_embedding_count}, models={model_count}"
        )

    neo4j_status = get_neo4j_connection_status()
    graph_freshness = get_project_graph_freshness(db, project_id)
    graph_summary = get_neo4j_project_summary(project_id) if neo4j_status.connected else None
    graph_ready = (
        neo4j_status.connected
        and graph_freshness.status == "latest"
        and graph_summary is not None
        and graph_summary.status == "completed"
        and graph_summary.node_count > 0
        and graph_summary.edge_count > 0
    )
    neo4j_row_status = PASS if neo4j_status.connected else WARN if not neo4j_status.enabled else FAIL
    graph_row_status = (
        PASS
        if graph_freshness.status == "latest"
        else FAIL
        if graph_freshness.status == "failed"
        else WARN
    )
    if graph_summary is None:
        readback_status = WARN if not neo4j_status.enabled else FAIL
        readback_value = "미연결"
        readback_action = neo4j_status.message
    else:
        readback_status = (
            PASS
            if graph_summary.status == "completed" and graph_summary.node_count > 0 and graph_summary.edge_count > 0
            else FAIL
            if graph_summary.status == "failed"
            else WARN
        )
        readback_value = f"nodes={graph_summary.node_count}, edges={graph_summary.edge_count}"
        readback_action = graph_summary.errors[0] if graph_summary.errors else graph_summary.summary

    return [
        EvidenceStatusRow(
            "LLM",
            _status(llm_provider != "mock", warn=True),
            f"{llm_provider} / {llm_model}",
            "chat model 설정을 확인하세요.",
        ),
        EvidenceStatusRow(
            "Embedding",
            _status(embedding_provider != "mock", warn=True),
            f"{embedding_provider} / {embedding_model} / {settings.pgvector_dimension}d",
            "embedding model과 dimension을 확인하세요.",
        ),
        EvidenceStatusRow(
            "최근 AI 호출",
            invocation_status,
            latest_value,
            latest_action,
        ),
        EvidenceStatusRow(
            "검색 준비",
            source_row_status,
            source_value,
            "소스 근거와 검색 준비 상태를 맞추세요.",
        ),
        EvidenceStatusRow(
            "호출 요약",
            _status(telemetry.total_count > 0, warn=True),
            f"total={telemetry.total_count}, failed={telemetry.failed_count}, fallback={telemetry.fallback_count}, avg={telemetry.average_duration_ms}ms",
            "AI 기능 실행 뒤 상태를 다시 확인하세요.",
        ),
        EvidenceStatusRow(
            "Neo4j",
            neo4j_row_status,
            f"enabled={neo4j_status.enabled}, connected={neo4j_status.connected}, database={neo4j_status.database or 'default'}",
            neo4j_status.message,
        ),
        EvidenceStatusRow(
            "Knowledge Graph",
            graph_row_status,
            (
                f"{_graph_freshness_label(graph_freshness.status)}, "
                f"repo={_short_hash(graph_freshness.repo_head_hash)}, "
                f"graph={_short_hash(graph_freshness.graph_sync_head_hash)}, "
                f"nodes={graph_freshness.node_count}, edges={graph_freshness.edge_count}, "
                f"sync={_format_dt(graph_freshness.synced_at)}"
            ),
            graph_freshness.summary,
        ),
        EvidenceStatusRow(
            "Graph Readback",
            readback_status,
            readback_value,
            readback_action,
        ),
        _recent_graph_evidence_row(
            db,
            project_id,
            graph_ready=graph_ready,
            graph_freshness_status=graph_freshness.status,
        ),
    ]


def run_mapping_shortcut(db: Session, project_id: int) -> EvidenceActionResult:
    result = MappingService().analyze_commits(
        db,
        project_id=project_id,
        candidates_per_commit=10,
        skip_completed=True,
    )
    status = "completed_with_warnings" if result.errors else "completed"
    return EvidenceActionResult(
        title="Mapping 실행",
        summary=(
            "Mapping 완료: "
            f"분석 {result.analyzed_count}건, 생성 {result.created_count}건, "
            f"갱신 {result.updated_count}건, 건너뜀 {result.skipped_count}건, 실패 {result.failed_count}건"
        ),
        status=status,
        details={
            "analyzed_count": result.analyzed_count,
            "created_count": result.created_count,
            "updated_count": result.updated_count,
            "skipped_count": result.skipped_count,
            "failed_count": result.failed_count,
            "recent_results": result.recent_results[:10],
        },
        errors=result.errors[:20],
    )


def run_risk_analysis_shortcut(db: Session, project_id: int) -> EvidenceActionResult:
    result = run_risk_analysis(db, project_id)
    return EvidenceActionResult(
        title="Risk Analysis 실행",
        summary=(
            "Risk Analysis 완료: "
            f"감지 {result.detected_count}건, 생성 {result.created_count}건, "
            f"갱신 {result.updated_count}건, 자동 해결 {result.auto_resolved_count}건"
        ),
        details={
            "detected_count": result.detected_count,
            "created_count": result.created_count,
            "updated_count": result.updated_count,
            "auto_resolved_count": result.auto_resolved_count,
        },
    )


def run_pl_briefing_shortcut(db: Session, project_id: int) -> EvidenceActionResult:
    resource_summary = get_resource_metrics_summary(db, project_id)
    radar = build_ai_resource_radar(db, resource_summary, limit=5)
    briefing = generate_pl_briefing(radar)
    saved = save_pl_briefing(db, radar, briefing)
    return EvidenceActionResult(
        title="PL Briefing 생성",
        summary=(
            "PL Briefing 저장 완료: "
            f"provider={briefing.provider}, model={briefing.model or '-'}, mode={briefing.mode}"
        ),
        details={
            "history_id": saved.id,
            "provider": briefing.provider,
            "model": briefing.model or "-",
            "mode": briefing.mode,
            "validation_status": briefing.validation_status,
            "repair_attempted": briefing.repair_attempted,
            "radar_item_count": len(radar.items),
            "summary": saved.summary,
        },
    )


def run_search_ready_shortcut(db: Session, project_id: int, *, embedding_limit: int = 50) -> EvidenceActionResult:
    project = db.get(Project, project_id)
    if project is None:
        return EvidenceActionResult("검색 준비 생성", "프로젝트를 찾을 수 없습니다.", status="failed")
    if not project.git_repo_path:
        return EvidenceActionResult(
            "검색 준비 생성",
            "앱 서버 Git 저장소 경로가 없어 현재 소스 기준 검색 준비를 만들 수 없습니다.",
            status="failed",
        )

    status_before = get_source_index_status(db, project)
    if status_before.source_chunk_count == 0 or status_before.needs_reindex:
        refresh_result = refresh_source_file_index(
            db,
            project,
            embed_after_refresh=True,
            embedding_limit=embedding_limit,
        )
        return EvidenceActionResult(
            title="검색 준비 생성",
            summary=(
                "현재 소스 다시 읽기와 검색 준비 완료: "
                f"새 근거 {refresh_result.chunk_result.created_count}건, "
                f"검색 준비 {refresh_result.embedding_result.created_count}건, "
                f"실패 {refresh_result.embedding_result.failed_count}건"
            ),
            status="completed_with_warnings" if refresh_result.embedding_result.failed_count else "completed",
            details={
                "mode": "refresh_source_file_index",
                "source_chunk_count": refresh_result.status.source_chunk_count,
                "source_vector_count": refresh_result.status.source_vector_count,
                "missing_embedding_count": refresh_result.status.missing_embedding_count,
                "deleted_unverified_count": refresh_result.deleted_unverified_count,
                "chunk_created_count": refresh_result.chunk_result.created_count,
                "chunk_skipped_count": refresh_result.chunk_result.skipped_count,
                "embedding_created_count": refresh_result.embedding_result.created_count,
                "embedding_skipped_count": refresh_result.embedding_result.skipped_count,
                "embedding_failed_count": refresh_result.embedding_result.failed_count,
            },
            errors=refresh_result.embedding_result.errors[:20],
        )

    client = EmbeddingClient()
    embedding_result = VectorStore(db).embed_missing_chunks(
        client,
        project_id=project_id,
        source_types=[SOURCE_FILE_TYPE],
        limit=embedding_limit,
    )
    status_after = get_source_index_status(db, project)
    return EvidenceActionResult(
        title="검색 준비 생성",
        summary=(
            "검색 준비 완료: "
            f"생성 {embedding_result.created_count}건, 이미 준비됨 {embedding_result.skipped_count}건, "
            f"실패 {embedding_result.failed_count}건"
        ),
        status="completed_with_warnings" if embedding_result.failed_count else "completed",
        details={
            "mode": "embed_missing_source_file_chunks",
            "embedding_model": client.embedding_model_name,
            "source_chunk_count": status_after.source_chunk_count,
            "source_vector_count": status_after.source_vector_count,
            "missing_embedding_count": status_after.missing_embedding_count,
            "embedding_created_count": embedding_result.created_count,
            "embedding_skipped_count": embedding_result.skipped_count,
            "embedding_failed_count": embedding_result.failed_count,
        },
        errors=embedding_result.errors[:20],
    )


def get_ai_readiness_rows(db: Session, project_id: int) -> list[EvidenceStatusRow]:
    project = db.get(Project, project_id)
    if project is None:
        return [EvidenceStatusRow("프로젝트", FAIL, "-", "프로젝트를 다시 선택하세요.")]

    program_count = db.query(Program).filter(Program.project_id == project_id).count()
    commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()
    analyzed_commit_count = (
        db.query(GitCommit)
        .filter(GitCommit.project_id == project_id, GitCommit.mapping_analyzed_at.isnot(None))
        .count()
    )
    implementation_count = (
        db.query(ProgramImplementationStatus)
        .join(Program, ProgramImplementationStatus.program_id == Program.id)
        .filter(Program.project_id == project_id)
        .count()
    )
    risk_count = db.query(RiskFinding).filter(RiskFinding.project_id == project_id).count()
    latest_briefing = get_latest_pl_briefing(db, project_id)
    invocation_count = db.query(AIInvocationLog).filter(AIInvocationLog.project_id == project_id).count()

    try:
        source_status = get_source_index_status(db, project)
    except Exception as exc:
        source_status = None
        source_error = str(exc)
    else:
        source_error = "; ".join(source_status.errors)

    rows = [
        EvidenceStatusRow("DB", PASS, "연결됨", "추가 조치 없음"),
        EvidenceStatusRow(
            "Git 저장소",
            _status(bool(project.git_repo_path and commit_count > 0)),
            f"repo={project.git_repo_path or '-'}, commits={commit_count}, last_sync={_format_dt(project.last_synced_at)}",
            "프로젝트/Git 설정과 Git 동기화를 확인하세요.",
        ),
        EvidenceStatusRow(
            "산출물 데이터",
            _status(program_count > 0),
            f"programs={program_count}",
            "프로그램 목록과 개발계획을 업로드하세요.",
        ),
        EvidenceStatusRow(
            "Mapping",
            _status(commit_count > 0 and analyzed_commit_count >= commit_count, warn=analyzed_commit_count > 0),
            f"analyzed_commits={analyzed_commit_count}/{commit_count}",
            "Mapping에서 미분석 commit을 처리하세요.",
        ),
        EvidenceStatusRow(
            "AI Progress",
            _status(implementation_count > 0, warn=commit_count > 0),
            f"implementation_status={implementation_count}",
            "Program Detail 또는 Mapping 후속 구현상태 분석을 실행하세요.",
        ),
        EvidenceStatusRow(
            "Risk Analysis",
            _status(risk_count > 0, warn=program_count > 0),
            f"risk_findings={risk_count}",
            "Risk Analysis를 실행해 리스크 근거를 저장하세요.",
        ),
        EvidenceStatusRow(
            "LLM 설정",
            _status(settings.llm_provider != "mock", warn=settings.llm_provider == "mock"),
            f"provider={settings.llm_provider}, model={settings.llm_model or '-'}",
            "실제 AI 품질 검증 전 local_openai와 모델 로드를 확인하세요.",
        ),
        EvidenceStatusRow(
            "Embedding 설정",
            _status(settings.embedding_provider != "mock", warn=settings.embedding_provider == "mock"),
            f"provider={settings.embedding_provider}, model={settings.embedding_model or '-'}, dimension={settings.pgvector_dimension}",
            "RAG 품질 검증 전 embedding provider/model/dimension을 확인하세요.",
        ),
    ]
    if source_status is None:
        rows.append(EvidenceStatusRow("Source Index", WARN, source_error or "-", "RAG 검색에서 전체 소스 다시 읽기를 실행하세요."))
    else:
        rows.append(
            EvidenceStatusRow(
                "Source Index",
                _status(source_status.source_chunk_count > 0 and not source_status.needs_reindex, warn=source_status.source_chunk_count > 0),
                (
                    f"chunks={source_status.source_chunk_count}, vectors={source_status.source_vector_count}, "
                    f"missing={source_status.missing_embedding_count}, reindex={source_status.needs_reindex}"
                ),
                "Project Chat/RAG 사용 전 최신 변경분 반영 또는 전체 소스 다시 읽기를 실행하세요.",
            )
        )
    rows.extend(
        [
            EvidenceStatusRow(
                "PL Briefing",
                _status(bool(latest_briefing and latest_briefing.mode == "LLM 생성"), warn=latest_briefing is not None),
                f"latest={latest_briefing.mode if latest_briefing else '-'}",
                "Dashboard에서 PL Briefing 생성을 실행하세요.",
            ),
            EvidenceStatusRow(
                "AI Telemetry",
                _status(invocation_count > 0, warn=True),
                f"invocations={invocation_count}",
                "PL Briefing, Project Chat, Mapping, AI Code Review 중 하나를 실행해 호출 로그를 쌓으세요.",
            ),
        ]
    )
    return rows


def get_ai_evaluation_scorecard(db: Session, project_id: int) -> list[EvidenceStatusRow]:
    project = db.get(Project, project_id)
    if project is None:
        return [EvidenceStatusRow("프로젝트", FAIL, "-", "프로젝트를 다시 선택하세요.")]

    program_count = db.query(Program).filter(Program.project_id == project_id).count()
    commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()
    mappings = (
        db.query(ProgramCommitMapping)
        .join(Program, ProgramCommitMapping.program_id == Program.id)
        .filter(Program.project_id == project_id)
        .all()
    )
    mapping_count = len(mappings)
    mapping_quality = summarize_mapping_feedback_quality(db, project_id)
    mapping_short_reason_count = sum(
        1 for mapping in mappings if len((mapping.reason or "").strip()) < SHORT_REASON_LENGTH
    )
    mapping_fallback_count = sum(
        1
        for mapping in mappings
        if _contains_truthy_key(mapping.raw_response or {}, "fallback") or "fallback" in (mapping.reason or "").lower()
    )
    mapping_status = PASS
    if commit_count > 0 and mapping_count == 0:
        mapping_status = FAIL
    elif commit_count == 0:
        mapping_status = WARN
    elif (
        mapping_quality.unknown_status_count
        or mapping_quality.low_relevance_count
        or mapping_short_reason_count
        or mapping_quality.feedback_pending_count
        or mapping_fallback_count
    ):
        mapping_status = WARN

    implementation_count = (
        db.query(ProgramImplementationStatus)
        .join(Program, ProgramImplementationStatus.program_id == Program.id)
        .filter(Program.project_id == project_id)
        .count()
    )
    implementation_coverage_status = PASS
    if program_count > 0 and implementation_count == 0:
        implementation_coverage_status = FAIL
    elif program_count == 0 or implementation_count < program_count:
        implementation_coverage_status = WARN

    risk_count = db.query(RiskFinding).filter(RiskFinding.project_id == project_id).count()
    unresolved_risk_count = db.query(RiskFinding).filter(RiskFinding.project_id == project_id, RiskFinding.resolved_yn == "N").count()
    high_risk_count = (
        db.query(RiskFinding)
        .filter(RiskFinding.project_id == project_id, RiskFinding.resolved_yn == "N", RiskFinding.risk_level == "HIGH")
        .count()
    )
    source_chunk_count = db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == "source_file").count()
    vector_count = (
        db.query(VectorItem)
        .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
        .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == "source_file")
        .count()
    )
    chat_answers = (
        db.query(ProjectChatMessage)
        .join(ProjectChatSession, ProjectChatMessage.session_id == ProjectChatSession.id)
        .filter(ProjectChatSession.project_id == project_id, ProjectChatMessage.role == "assistant")
        .all()
    )
    chat_answer_count = len(chat_answers)
    chat_verified_source_count = sum(
        1
        for message in chat_answers
        if (message.used_source_count or 0) > 0
        and any(
            str(source.get("verification_status") or "").lower() == "verified"
            for source in (message.sources or [])
            if isinstance(source, dict)
        )
    )
    chat_insufficient_count = sum(1 for message in chat_answers if message.insufficient_evidence)
    chat_excluded_count = sum(int(message.excluded_count or 0) for message in chat_answers)
    chat_status = PASS
    if source_chunk_count == 0 or vector_count == 0:
        chat_status = FAIL
    elif chat_answer_count == 0:
        chat_status = WARN
    elif chat_verified_source_count == 0:
        chat_status = FAIL
    elif chat_verified_source_count < chat_answer_count or chat_insufficient_count or chat_excluded_count:
        chat_status = WARN

    reviews = (
        db.query(CodeReviewResult)
        .filter(CodeReviewResult.project_id == project_id)
        .order_by(CodeReviewResult.created_at.desc().nullslast(), CodeReviewResult.id.desc())
        .all()
    )
    review_count = len(reviews)
    completed_reviews = [review for review in reviews if review.status == "completed"]
    failed_review_count = sum(1 for review in reviews if review.status == "failed")
    latest_review = reviews[0] if reviews else None
    review_risk_counter = Counter(
        str((review.commit_analysis or {}).get("risk_level") or "-").upper() for review in completed_reviews
    )
    code_review_status = PASS
    if not reviews:
        code_review_status = WARN
    elif not completed_reviews:
        code_review_status = FAIL
    elif failed_review_count:
        code_review_status = WARN

    latest_briefing = get_latest_pl_briefing(db, project_id)
    briefing_invocations = (
        db.query(AIInvocationLog)
        .filter(AIInvocationLog.project_id == project_id, AIInvocationLog.feature.ilike("%briefing%"))
        .order_by(AIInvocationLog.started_at.desc().nullslast(), AIInvocationLog.id.desc())
        .limit(20)
        .all()
    )
    briefing_validation = "-"
    briefing_repair_attempted = False
    if latest_briefing is not None:
        briefing_validation = str((latest_briefing.raw_response or {}).get("validation_status") or "-")
        briefing_repair_attempted = bool((latest_briefing.raw_response or {}).get("repair_attempted"))
    briefing_fallback_count = sum(1 for row in briefing_invocations if row.fallback_used)
    briefing_failed_count = sum(1 for row in briefing_invocations if row.status == "failed")
    briefing_status = PASS
    if latest_briefing is None:
        briefing_status = FAIL
    elif (
        latest_briefing.mode != "LLM 생성"
        or briefing_validation not in {"valid", "not_applicable", "-"}
        or briefing_repair_attempted
        or briefing_fallback_count
        or briefing_failed_count
    ):
        briefing_status = WARN

    resource_summary = get_resource_metrics_summary(db, project_id)
    radar = build_ai_resource_radar(db, resource_summary, limit=5)
    graph_freshness = get_project_graph_freshness(db, project_id)
    graph_summary = get_neo4j_project_summary(project_id)
    graph_preview = get_neo4j_project_preview(project_id) if graph_summary.status == "completed" else None
    graph_error = "; ".join(graph_summary.errors)
    if graph_preview is not None and graph_preview.errors:
        graph_error = "; ".join([value for value in [graph_error, "; ".join(graph_preview.errors)] if value])
    graph_class_count = graph_summary.node_counts.get("class", 0) if graph_summary.status == "completed" else 0
    graph_import_count = graph_summary.edge_counts.get("IMPORTS_CLASS", 0) if graph_summary.status == "completed" else 0
    graph_impact_count = len(graph_preview.impact_rows) if graph_preview is not None and graph_preview.status == "completed" else 0
    graph_status = PASS
    if graph_freshness.status == "failed" or graph_summary.status == "failed":
        graph_status = FAIL
    elif graph_freshness.status != "latest" or graph_summary.status != "completed" or graph_class_count == 0 or graph_impact_count == 0:
        graph_status = WARN

    risk_status = PASS
    if program_count == 0:
        risk_status = WARN
    elif risk_count == 0:
        risk_status = WARN

    return [
        EvidenceStatusRow(
            "Mapping",
            mapping_status,
            (
                f"mappings={mapping_count}, commits={commit_count}, "
                f"unknown={mapping_quality.unknown_status_count}({_format_percent(mapping_quality.unknown_status_count, mapping_count)}), "
                f"low={mapping_quality.low_relevance_count}, short_reason={mapping_short_reason_count}, "
                f"feedback_pending={mapping_quality.feedback_pending_count}, fallback={mapping_fallback_count}"
            ),
            "판단불가, 낮은 관련도, 짧은 근거, 미검토 피드백이 많으면 Mapping 리뷰 큐에서 보정하세요.",
            "분석 실행",
            "Mapping",
        ),
        EvidenceStatusRow(
            "AI Progress",
            implementation_coverage_status,
            f"implementation_status={implementation_count}/{program_count}",
            "프로그램별 구현상태 분석이 비어 있거나 일부만 있으면 Program Detail에서 재분석하세요.",
            "개요",
            "AI Progress",
        ),
        EvidenceStatusRow(
            "Risk Analysis",
            risk_status,
            f"risk_findings={risk_count}, unresolved={unresolved_risk_count}, high={high_risk_count}",
            "리스크가 전혀 없으면 Risk Analysis 실행 여부와 산출물/Mapping 데이터를 확인하세요.",
            "분석 실행",
            "Risk Analysis",
        ),
        EvidenceStatusRow(
            "RAG / Project Chat",
            chat_status,
            (
                f"chunks={source_chunk_count}, vectors={vector_count}, answers={chat_answer_count}, "
                f"verified_source={_format_percent(chat_verified_source_count, chat_answer_count)}, "
                f"insufficient={_format_percent(chat_insufficient_count, chat_answer_count)}, excluded={chat_excluded_count}"
            ),
            "검색 준비 후 Project Chat에서 현재 소스 근거가 붙는 대표 질문을 실행하세요.",
            "분석 실행",
            "Project Chat",
        ),
        EvidenceStatusRow(
            "AI Code Review",
            code_review_status,
            (
                f"completed={len(completed_reviews)}/{review_count}, failed={failed_review_count}, "
                f"latest={latest_review.target_ref[:12] if latest_review and latest_review.target_ref else '-'}, "
                f"risk={dict(review_risk_counter)}"
            ),
            "최근 변경 commit 1개 이상을 AI Code Review로 실행하고 실패한 리뷰를 확인하세요.",
            "분석 실행",
            "AI Code Review",
        ),
        EvidenceStatusRow(
            "PL Briefing",
            briefing_status,
            (
                f"latest={latest_briefing.mode if latest_briefing else '-'}, "
                f"provider={latest_briefing.provider if latest_briefing else '-'}, "
                f"model={(latest_briefing.model or '-') if latest_briefing else '-'}, validation={briefing_validation}, "
                f"repair={briefing_repair_attempted}, fallback={briefing_fallback_count}/{len(briefing_invocations)}"
            ),
            "fallback이나 repair가 반복되면 provider/model 설정과 PL Briefing raw response를 확인하세요.",
            "개요",
            "Dashboard",
        ),
        EvidenceStatusRow(
            "AI Resource Radar",
            _status(len(radar.items) > 0, warn=len(resource_summary.program_metrics) > 0),
            f"radar_items={len(radar.items)}",
            "Dashboard 자원관리 지표와 Risk Analysis 근거를 확인하세요.",
            "개요",
            "Dashboard",
        ),
        EvidenceStatusRow(
            "Knowledge Graph",
            graph_status,
            (
                f"graph={_graph_freshness_label(graph_freshness.status)}, "
                f"classes={graph_class_count}, imports={graph_import_count}, impact_paths={graph_impact_count}, "
                f"repo={_short_hash(graph_freshness.repo_head_hash)}, graph_head={_short_hash(graph_freshness.graph_sync_head_hash)}"
            ),
            graph_error or "Graph가 오래되었거나 class/import/impact path가 부족하면 Knowledge Graph에서 동기화하세요.",
            "분석 결과",
            "Knowledge Graph",
        ),
    ]


def get_evidence_trace(db: Session, project_id: int, limit: int = 10) -> EvidenceTrace:
    latest = (
        db.query(PLBriefingHistory)
        .filter(PLBriefingHistory.project_id == project_id)
        .order_by(PLBriefingHistory.generated_at.desc(), PLBriefingHistory.id.desc())
        .first()
    )
    latest_pl = None
    if latest is not None:
        latest_pl = {
            "generated_at": _format_dt(latest.generated_at),
            "provider": latest.provider,
            "model": latest.model or "-",
            "mode": latest.mode,
            "validation_status": (latest.raw_response or {}).get("validation_status"),
            "repair_attempted": (latest.raw_response or {}).get("repair_attempted"),
            "summary": latest.summary or "-",
            "evidence_payload": latest.evidence_payload or {},
            "raw_response": latest.raw_response or {},
        }

    mappings = (
        db.query(ProgramCommitMapping, Program, GitCommit)
        .join(Program, ProgramCommitMapping.program_id == Program.id)
        .join(GitCommit, ProgramCommitMapping.commit_id == GitCommit.id)
        .filter(Program.project_id == project_id)
        .order_by(ProgramCommitMapping.updated_at.desc().nullslast(), ProgramCommitMapping.id.desc())
        .limit(limit)
        .all()
    )
    recent_mappings = [
        {
            "program": f"{program.program_id or '-'} {program.program_name}",
            "commit": f"{commit.commit_hash[:12]} {commit.message or ''}".strip(),
            "score": mapping.relevance_score,
            "status": mapping.implementation_status,
            "fallback": bool((mapping.raw_response or {}).get("fallback")),
            "reason": mapping.reason or "-",
            "raw_response": mapping.raw_response or {},
        }
        for mapping, program, commit in mappings
    ]

    chat_messages = (
        db.query(ProjectChatMessage, ProjectChatSession)
        .join(ProjectChatSession, ProjectChatMessage.session_id == ProjectChatSession.id)
        .filter(ProjectChatSession.project_id == project_id, ProjectChatMessage.role == "assistant")
        .order_by(ProjectChatMessage.created_at.desc(), ProjectChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    recent_chat = [
        {
            "session": session.title or f"Session {session.id}",
            "message_index": message.message_index,
            "used_sources": message.used_source_count or 0,
            "excluded_sources": message.excluded_count or 0,
            "graph_evidence_count": len(((message.raw_metadata or {}).get("graph_evidence") or [])),
            "graph_status": ((message.raw_metadata or {}).get("graph_evidence_metadata") or {}).get("status") or "-",
            "insufficient_evidence": bool(message.insufficient_evidence),
            "answer": message.content[:500],
            "sources": message.sources or [],
            "graph_evidence": (message.raw_metadata or {}).get("graph_evidence") or [],
            "graph_evidence_metadata": (message.raw_metadata or {}).get("graph_evidence_metadata") or {},
        }
        for message, session in chat_messages
    ]

    reviews = (
        db.query(CodeReviewResult)
        .filter(CodeReviewResult.project_id == project_id)
        .order_by(CodeReviewResult.created_at.desc(), CodeReviewResult.id.desc())
        .limit(limit)
        .all()
    )
    recent_reviews = [
        {
            "target": f"{review.target_type}:{review.target_ref or '-'}",
            "status": review.status,
            "summary": review.summary or "-",
            "risk_level": (review.commit_analysis or {}).get("risk_level"),
            "bug_findings": len(review.bug_findings or []),
            "raw_response": review.raw_response or {},
        }
        for review in reviews
    ]

    invocations = list_ai_invocations(db, project_id, limit=limit)
    recent_invocations = [
        {
            "feature": row.feature,
            "provider": row.provider,
            "model": row.model or "-",
            "status": row.status,
            "mode": row.mode or "-",
            "fallback": row.fallback_used,
            "duration_ms": row.duration_ms,
            "prompt_length": row.prompt_length,
            "response_length": row.response_length,
            "error": row.error_message or "-",
            "metadata": row.raw_metadata or {},
        }
        for row in invocations
    ]
    return EvidenceTrace(latest_pl, recent_mappings, recent_chat, recent_reviews, recent_invocations)


def generate_weekly_ai_report(db: Session, project_id: int) -> str:
    project = db.get(Project, project_id)
    if project is None:
        return "# 주간 AI 점검 보고서\n\n프로젝트를 찾을 수 없습니다.\n"

    generated_at = datetime.now(timezone.utc)
    readiness = get_ai_readiness_rows(db, project_id)
    scorecard = get_ai_evaluation_scorecard(db, project_id)
    resource_summary = get_resource_metrics_summary(db, project_id)
    radar = build_ai_resource_radar(db, resource_summary, limit=5)
    latest = get_latest_pl_briefing(db, project_id)
    telemetry = summarize_ai_invocations(db, project_id)
    risks = (
        db.query(RiskFinding, Program)
        .join(Program, RiskFinding.program_id == Program.id)
        .filter(RiskFinding.project_id == project_id, RiskFinding.resolved_yn == "N")
        .order_by(RiskFinding.risk_level.desc(), RiskFinding.detected_at.desc().nullslast(), RiskFinding.id.desc())
        .limit(10)
        .all()
    )
    progress_gaps = [
        metric
        for metric in sorted(resource_summary.program_metrics, key=lambda row: row.progress_gap, reverse=True)
        if metric.progress_gap > 0
    ][:10]

    lines = [
        "# 주간 AI 점검 보고서",
        "",
        f"- 프로젝트: {project.name} ({project.id})",
        f"- 생성 시각(UTC): {generated_at.strftime('%Y-%m-%d %H:%M')}",
        f"- Git 저장소: {project.git_repo_path or '-'}",
        "",
        "## 운영 준비 상태",
        "| 영역 | 상태 | 현재 값 | 다음 조치 |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {row.area} | {row.status} | {row.value} | {row.action} |" for row in readiness)
    lines.extend(["", "## AI 평가 Scorecard", "| 영역 | 상태 | 관측값 | 다음 조치 |", "|---|---|---|---|"])
    lines.extend(f"| {row.area} | {row.status} | {row.value} | {row.action} |" for row in scorecard)
    lines.extend(
        [
            "",
            "## AI Resource Radar",
            "| 순위 | 프로그램 | 우선도 | 점수 | 주요 이유 | 권장 action |",
            "|---|---|---|---:|---|---|",
        ]
    )
    if radar.items:
        lines.extend(
            (
                f"| {item.rank} | {item.program_id or '-'} {item.program_name} | {item.priority_level} | "
                f"{item.priority_score} | {', '.join(item.reasons)} | {item.recommended_action} |"
            )
            for item in radar.items
        )
    else:
        lines.append("| - | - | - | - | Radar 항목 없음 | Git/Mapping/Risk 데이터를 확인하세요. |")

    lines.extend(["", "## 최근 PL Briefing", ""])
    lines.append(latest.rendered_text if latest else "저장된 PL Briefing이 없습니다.")

    lines.extend(["", "## 미해결 리스크", "| 등급 | 프로그램 | 제목 |", "|---|---|---|"])
    if risks:
        lines.extend(f"| {risk.risk_level} | {program.program_id or '-'} {program.program_name} | {risk.title} |" for risk, program in risks)
    else:
        lines.append("| - | - | 미해결 리스크 없음 |")

    lines.extend(["", "## AI Progress Gap", "| 프로그램 | 계획 | AI | 차이 |", "|---|---:|---:|---:|"])
    if progress_gaps:
        lines.extend(
            f"| {metric.program_id or '-'} {metric.program_name} | {metric.plan_progress_rate:.1f}% | "
            f"{metric.ai_progress_rate:.1f}% | {metric.progress_gap:.1f}p |"
            for metric in progress_gaps
        )
    else:
        lines.append("| - | - | - | 차이 없음 |")

    lines.extend(
        [
            "",
            "## AI 호출 Telemetry",
            f"- 총 호출: {telemetry.total_count}",
            f"- 성공/실패: {telemetry.success_count}/{telemetry.failed_count}",
            f"- fallback 사용: {telemetry.fallback_count}",
            f"- 평균 지연시간: {telemetry.average_duration_ms}ms",
            "",
            "## 해석 기준",
            "- 이 보고서는 AI output을 확정 판단이 아니라 PL 검토 보조 근거로 묶은 것입니다.",
            "- 일정, 개인 성과, 배포 가능 여부는 담당자 확인과 테스트 결과를 함께 검토해야 합니다.",
        ]
    )
    return "\n".join(lines) + "\n"

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import MutableMapping

import pandas as pd
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

from src.db.database import SessionLocal
from src.db.models import Project
from src.rag.chat_service import answer_source_question
from src.rag.chat_history_service import (
    append_chat_message,
    create_chat_session,
    format_message_citation_export,
    get_chat_session,
    get_session_messages,
    list_chat_sessions,
    messages_to_ui_dicts,
)
from src.rag.source_index_service import (
    SourceIndexStatus,
    SourceIndexSummary,
    get_changed_source_files_since_latest_index,
    get_source_index_summary,
    get_source_index_status,
    refresh_changed_source_files,
    refresh_source_file_index,
)
from src.services.neo4j_graph_service import Neo4jGraphFreshness, get_project_graph_freshness
from src.ui.project_context import require_project_context
from src.utils.config import settings


VERIFICATION_LABELS = {
    "verified": "현재 코드 검증됨",
    "stale": "인덱싱 이후 변경됨",
    "invalid": "검증 실패",
    "historical": "변경 이력",
    "not_applicable": "검증 대상 아님",
}

SOURCE_TYPE_LABELS = {
    "source_file": "현재 소스 파일",
    "program": "프로그램 정보",
    "commit": "커밋 이력",
    "commit_file": "커밋 파일 변경",
}

PROJECT_CHAT_HELP = {
    "source_count": "Project Chat이 답변 근거로 사용할 수 있도록 읽어 둔 현재 소스 조각 수입니다.",
    "search_ready": "질문과 비슷한 소스 근거를 찾을 준비가 끝난 수입니다. 예: 70/70이면 70개 근거 모두 검색 준비가 끝난 상태입니다.",
    "code_status": "앱 서버 Git 저장소의 현재 코드가 Project Chat 근거에 반영되어 있는지 보여줍니다.",
    "verify_status": "저장소의 현재 소스 파일을 읽고 저장된 근거 hash와 직접 비교합니다. 파일 수에 따라 시간이 걸릴 수 있습니다.",
    "missing_ready": "소스 근거는 있지만 아직 질문 검색 준비가 끝나지 않은 수입니다. 0이면 추가 작업 없이 질문할 수 있습니다.",
    "refresh_changed": "Git 동기화 후 바뀐 파일만 빠르게 다시 읽습니다. 보통 최신 commit을 가져온 뒤 먼저 누르면 됩니다.",
    "refresh_all": "현재 소스를 전체 기준으로 다시 읽습니다. 처음 준비하거나 브랜치를 크게 바꿨거나 근거가 오래되어 보일 때 사용합니다.",
    "session": "이 프로젝트에서 저장된 이전 대화를 다시 여는 선택입니다. 새 대화를 시작해도 기존 대화는 삭제되지 않습니다.",
    "new_chat": "현재 대화를 지우지 않고 새 질문 흐름을 시작합니다. 이전 대화는 저장된 대화에서 다시 열 수 있습니다.",
    "top_k": "질문할 때 후보로 가져올 소스 근거의 최대 개수입니다. 값이 크면 더 넓게 찾지만 답변이 느려지거나 덜 집중될 수 있습니다.",
    "include_history": "현재 소스 근거만으로 부족할 때 과거 커밋 이력도 참고 후보에 포함합니다. 현재 코드 사실과 과거 변경 이력은 답변에서 구분됩니다.",
}

GRAPH_AWARE_QUESTION_TEMPLATES = [
    {
        "label": "프로그램 구현 근거",
        "question": "이 프로그램 구현 근거를 commit/file/class 기준으로 설명해줘.",
    },
    {
        "label": "커밋 영향 범위",
        "question": "이 commit이 어떤 프로그램과 class에 영향을 줬어?",
    },
    {
        "label": "클래스 연결",
        "question": "이 class 변경이 어떤 domain이나 프로그램과 연결돼?",
    },
    {
        "label": "리스크 근거",
        "question": "최근 리스크가 높은 프로그램의 근거 commit과 파일을 알려줘.",
    },
    {
        "label": "도메인 연결",
        "question": "결제 도메인과 주문 도메인의 연결 근거를 찾아줘.",
    },
]

GRAPH_STATUS_LABELS = {
    "latest": "최신",
    "stale": "갱신 필요",
    "missing": "저장 필요",
    "failed": "실패",
    "skipped": "미사용",
}

GRAPH_NODE_STYLE = {
    "program": {
        "color": "#DCEBFF",
        "highlight": "#C8DDFF",
        "border": "#6EA1E8",
        "shape": "box",
        "size": 28,
    },
    "commit": {
        "color": "#EADFFF",
        "highlight": "#DCCBFF",
        "border": "#9B7BE8",
        "shape": "diamond",
        "size": 24,
    },
    "file": {
        "color": "#D8F7DF",
        "highlight": "#C5EDCF",
        "border": "#62B879",
        "shape": "box",
        "size": 24,
    },
    "class": {
        "color": "#FFE6BF",
        "highlight": "#FFD8A3",
        "border": "#E89A3C",
        "shape": "dot",
        "size": 30,
    },
    "domain": {
        "color": "#CFF5EF",
        "highlight": "#B8ECE4",
        "border": "#43ADA4",
        "shape": "hexagon",
        "size": 26,
    },
}
GRAPH_NODE_VARIANT_STYLES = (
    {"color": "#DCEBFF", "highlight": "#C8DDFF", "border": "#6EA1E8"},
    {"color": "#EADFFF", "highlight": "#DCCBFF", "border": "#9B7BE8"},
    {"color": "#D8F7DF", "highlight": "#C5EDCF", "border": "#62B879"},
    {"color": "#FFE6BF", "highlight": "#FFD8A3", "border": "#E89A3C"},
    {"color": "#CFF5EF", "highlight": "#B8ECE4", "border": "#43ADA4"},
    {"color": "#FDE2F3", "highlight": "#FBCBE8", "border": "#E879C1"},
    {"color": "#E0F2FE", "highlight": "#BAE6FD", "border": "#38A6D9"},
    {"color": "#ECFCCB", "highlight": "#D9F99D", "border": "#84B93F"},
)
GRAPH_HIGHLIGHT_COLOR = "#60A5FA"
GRAPH_HIGHLIGHT_BORDER_COLOR = "#2563EB"
GRAPH_EDGE_COLOR = "#94A3B8"
GRAPH_EDGE_HIGHLIGHT_COLOR = "#64748B"
SOURCE_VERIFICATION_CACHE_KEY = "project_chat_source_verification_cache"

GRAPH_HIGHLIGHT_SEED_STOPWORDS = {
    "src",
    "main",
    "java",
    "com",
    "example",
    "market",
    "service",
    "mapper",
    "controller",
}


@dataclass(frozen=True)
class GraphDisplayNode:
    id: str
    label: str
    node_type: str
    title: str
    highlighted: bool = False


@dataclass(frozen=True)
class GraphDisplayEdge:
    source: str
    target: str
    label: str


@dataclass(frozen=True)
class SourceVerificationCacheKey:
    project_id: int
    repo_head_hash: str | None
    db_sync_head_hash: str | None
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    source_index_signature: str


@dataclass(frozen=True)
class CachedSourceVerification:
    cache_key: SourceVerificationCacheKey
    status: SourceIndexStatus
    verified_at: datetime


def build_source_verification_cache_key(
    project: Project,
    summary: SourceIndexSummary,
    *,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
    embedding_dimension: int | None = None,
) -> SourceVerificationCacheKey:
    return SourceVerificationCacheKey(
        project_id=int(project.id),
        repo_head_hash=summary.current_head_hash,
        db_sync_head_hash=project.last_synced_commit_hash,
        embedding_provider=embedding_provider or settings.embedding_provider,
        embedding_model=embedding_model or settings.embedding_model or "text-embedding-model",
        embedding_dimension=int(embedding_dimension or settings.pgvector_dimension),
        source_index_signature=summary.index_signature,
    )


def _get_cached_source_verification(
    cache_key: SourceVerificationCacheKey,
    session_state: MutableMapping | None = None,
) -> CachedSourceVerification | None:
    state = st.session_state if session_state is None else session_state
    cache = state.get(SOURCE_VERIFICATION_CACHE_KEY, {})
    cached = cache.get(cache_key)
    return cached if isinstance(cached, CachedSourceVerification) else None


def _cache_source_verification(
    cache_key: SourceVerificationCacheKey,
    status: SourceIndexStatus,
    session_state: MutableMapping | None = None,
) -> CachedSourceVerification:
    state = st.session_state if session_state is None else session_state
    cached = CachedSourceVerification(cache_key, status, datetime.now(timezone.utc))
    cache = dict(state.get(SOURCE_VERIFICATION_CACHE_KEY, {}))
    cache[cache_key] = cached
    state[SOURCE_VERIFICATION_CACHE_KEY] = cache
    return cached


def _load_initial_source_summary(db, project: Project) -> SourceIndexSummary:
    return get_source_index_summary(db, project)


def _run_source_file_verification(db, project: Project) -> SourceIndexStatus:
    return get_source_index_status(db, project)


def _graph_component_variant_indexes(
    nodes: list[GraphDisplayNode],
    edges: list[GraphDisplayEdge],
) -> dict[str, int]:
    adjacency: dict[str, set[str]] = {node.id: set() for node in nodes}
    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)

    component_indexes: dict[str, int] = {}
    visited: set[str] = set()
    component_count = 0
    for node in nodes:
        if node.id in visited:
            continue
        stack = [node.id]
        component: list[str] = []
        visited.add(node.id)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        variant_index = component_count % len(GRAPH_NODE_VARIANT_STYLES)
        component_count += 1
        for node_id in component:
            component_indexes[node_id] = variant_index
    return component_indexes


def _chat_key(project_id: int) -> str:
    return f"project_chat_messages_{project_id}"


def _active_session_key(project_id: int) -> str:
    return f"project_chat_active_session_{project_id}"


def _pending_question_key(project_id: int) -> str:
    return f"project_chat_pending_question_{project_id}"


def _graph_template_status(freshness: Neo4jGraphFreshness) -> tuple[bool, str]:
    label = GRAPH_STATUS_LABELS.get(freshness.status, freshness.status)
    if freshness.status == "latest":
        return True, "Knowledge Graph가 최신입니다. 아래 질문은 graph 관계 근거를 함께 사용할 수 있습니다."
    if freshness.status == "stale":
        return False, "Knowledge Graph가 갱신 필요 상태입니다. `Knowledge Graph`에서 최신 변경분 반영 후 사용할 수 있습니다."
    if freshness.status == "missing":
        return False, "Knowledge Graph가 아직 저장되지 않았습니다. `Knowledge Graph`에서 전체 재동기화를 먼저 실행하세요."
    if freshness.status == "failed":
        return False, "최근 Knowledge Graph 동기화가 실패했습니다. `Knowledge Graph`에서 오류를 확인하고 전체 재동기화하세요."
    if freshness.status == "skipped":
        return False, "Neo4j가 꺼져 있어 graph 질문 템플릿을 실행하지 않습니다. 필요하면 `NEO4J_ENABLED=true`로 켜세요."
    return False, f"Knowledge Graph 상태가 {label}입니다. graph 질문 템플릿을 실행하려면 graph 상태를 먼저 확인하세요."


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def _format_source(source: dict) -> str:
    metadata = source.get("metadata") or {}
    source_type = source.get("source_type")
    if source_type == "source_file":
        return (
            f"{metadata.get('file_path') or source.get('source_id')}:"
            f"{metadata.get('line_start')}-{metadata.get('line_end')}"
        )
    if source_type == "commit_file":
        return f"{_short_hash(metadata.get('commit_hash'))} / {metadata.get('file_path') or source.get('source_id')}"
    if source_type == "commit":
        return _short_hash(metadata.get("commit_hash") or str(source.get("source_id") or ""))
    return f"{source_type} / {source.get('source_id')}"


def _source_row(source: dict, rank: int) -> dict:
    metadata = source.get("metadata") or {}
    return {
        "rank": rank,
        "source_type": SOURCE_TYPE_LABELS.get(source.get("source_type"), source.get("source_type")),
        "source": _format_source(source),
        "file_path": metadata.get("file_path") or source.get("source_id"),
        "line_range": (
            f"{metadata.get('line_start')}-{metadata.get('line_end')}"
            if metadata.get("line_start") and metadata.get("line_end")
            else "-"
        ),
        "verification_status": VERIFICATION_LABELS.get(
            source.get("verification_status"),
            source.get("verification_status"),
        ),
        "score": round(float(source.get("similarity") or 0), 4),
        "reason": source.get("verification_reason"),
    }


def _format_status_time(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _render_source_index_status(project: Project) -> SourceIndexSummary | None:
    with SessionLocal() as db:
        current_project = db.get(Project, project.id)
        if current_project is None:
            st.error("프로젝트를 찾을 수 없습니다.")
            return
        summary = _load_initial_source_summary(db, current_project)
        cache_key = build_source_verification_cache_key(current_project, summary)

    cached_verification = _get_cached_source_verification(cache_key)
    verified_status = cached_verification.status if cached_verification else None
    needs_refresh = summary.needs_refresh or bool(verified_status and verified_status.needs_reindex)

    st.subheader("답변 근거 상태")
    st.caption(
        "Project Chat은 저장된 근거 요약과 Repo HEAD를 먼저 확인합니다. "
        "실제 파일 hash 검증은 아래 새로고침을 누르거나 질문할 때 관련 근거에 한해 실행합니다."
    )

    search_ready_count = max(summary.source_chunk_count - summary.missing_embedding_count, 0)
    if needs_refresh:
        code_status = "새로고침 필요"
    elif cached_verification:
        code_status = "파일 검증 완료"
    elif summary.head_matches_index:
        code_status = "HEAD 일치 · 파일 확인 전"
    else:
        code_status = "확인 필요"
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("소스 근거", summary.source_chunk_count, help=PROJECT_CHAT_HELP["source_count"])
    metric2.metric("검색 준비", f"{search_ready_count}/{summary.source_chunk_count}", help=PROJECT_CHAT_HELP["search_ready"])
    metric3.metric("코드 반영 상태", code_status, help=PROJECT_CHAT_HELP["code_status"])
    metric4.metric("추가 준비 필요", summary.missing_embedding_count, help=PROJECT_CHAT_HELP["missing_ready"])

    st.caption(
        f"Repo HEAD 확인: {_format_status_time(summary.checked_at)} · "
        f"마지막 근거 저장: {_format_status_time(summary.last_indexed_at)} · "
        f"전체 파일 검증: {_format_status_time(cached_verification.verified_at) if cached_verification else '이번 상태 기준 미실행'}"
    )

    if summary.source_chunk_count == 0:
        st.warning(
            "아직 질문에 사용할 소스 근거가 준비되지 않았습니다. "
            "아래에서 `전체 소스 다시 읽기`를 먼저 실행한 뒤, 검색 준비가 남아 있으면 `RAG 검색` 화면에서 이어서 처리하세요."
        )
    elif needs_refresh:
        st.warning(
            "Repo HEAD 또는 실제 파일 검증 결과가 저장된 근거와 다릅니다. "
            "최신 변경분을 반영하기 전에는 이전 근거를 현재 코드처럼 사용하지 않습니다."
        )
    elif summary.missing_embedding_count > 0 or summary.source_vector_count == 0:
        st.warning(
            "소스 근거는 준비되어 있지만 질문과 연결할 준비가 일부 남아 있습니다. "
            "`RAG 검색` 화면에서 남은 검색 준비를 적은 수량으로 실행한 뒤 질문해 주세요."
        )
    elif cached_verification:
        st.success("Repo HEAD와 저장된 소스 근거의 파일 내용이 현재 상태와 일치합니다.")
    else:
        st.info(
            "Repo HEAD는 저장된 근거와 일치하지만 전체 파일 내용은 아직 확인하지 않았습니다. "
            "질문을 보내면 검색된 근거 파일은 답변 전에 직접 검증합니다."
        )

    for error in [*summary.errors, *(verified_status.errors if verified_status else [])]:
        st.warning(error)

    with st.expander("어떤 버튼을 누르면 되나요?", expanded=False):
        st.markdown(
            "- `최신 변경분 반영`: Git 동기화 후 바뀐 파일만 빠르게 읽어 Project Chat 근거를 최신화합니다.\n"
            "- `전체 소스 다시 읽기`: 처음 준비하거나 브랜치를 크게 바꿨거나 오래된 근거가 계속 보일 때 사용합니다.\n"
            "- `근거 상태 새로고침`: 저장소 파일을 변경하지 않고 현재 파일 내용과 저장된 hash를 직접 비교합니다.\n"
            "- `검색 준비`가 남아 있으면 `RAG 검색` 화면에서 남은 작업을 소량씩 실행하세요."
        )
        st.caption(
            "기술 상세: 화면의 소스 근거는 내부적으로 source chunk로 저장되고, 검색 준비는 embedding/vector 생성 상태를 뜻합니다."
        )

    with st.expander("기술 상세", expanded=False):
        st.write(
            {
                "Current HEAD": _short_hash(summary.current_head_hash),
                "Indexed HEAD": _short_hash(summary.latest_indexed_head_hash),
                "DB Sync HEAD": _short_hash(current_project.last_synced_commit_hash),
                "source_file chunks": summary.source_chunk_count,
                "source_file vectors": summary.source_vector_count,
                "HEAD mismatch chunks": summary.head_mismatch_chunk_count,
                "stale chunks": verified_status.stale_chunk_count if verified_status else "미확인",
                "invalid chunks": verified_status.invalid_chunk_count if verified_status else "미확인",
                "missing embeddings": summary.missing_embedding_count,
                "embedding provider": settings.embedding_provider,
                "embedding model": settings.embedding_model,
                "embedding dimension": settings.pgvector_dimension,
            }
        )

    action_col1, action_col2, action_col3 = st.columns(3)
    if action_col1.button(
        "근거 상태 새로고침",
        type="primary" if not cached_verification and not needs_refresh else "secondary",
        disabled=not bool(project.git_repo_path),
        use_container_width=True,
        help=PROJECT_CHAT_HELP["verify_status"],
    ):
        with st.spinner("현재 저장소의 소스 파일을 읽고 저장된 근거 hash와 비교하는 중입니다."):
            with SessionLocal() as db:
                current_project = db.get(Project, project.id)
                if current_project is None:
                    st.error("프로젝트를 찾을 수 없습니다.")
                    return
                status = _run_source_file_verification(db, current_project)
                refreshed_summary = _load_initial_source_summary(db, current_project)
                refreshed_cache_key = build_source_verification_cache_key(current_project, refreshed_summary)
        _cache_source_verification(refreshed_cache_key, status)
        st.success("현재 저장소 파일과 저장된 근거 hash 비교를 완료했습니다.")
        st.rerun()

    if action_col2.button(
        "최신 변경분 반영",
        type="primary" if needs_refresh else "secondary",
        disabled=not bool(project.git_repo_path),
        use_container_width=True,
        help=PROJECT_CHAT_HELP["refresh_changed"],
    ):
        with SessionLocal() as db:
            current_project = db.get(Project, project.id)
            if current_project is None:
                st.error("프로젝트를 찾을 수 없습니다.")
                return
            changed_files = get_changed_source_files_since_latest_index(db, current_project)
            if not changed_files:
                st.info(
                    "Git 동기화 이후 새로 반영할 변경 파일이 없습니다. "
                    "처음 준비하는 중이거나 근거가 계속 오래되어 보이면 `전체 소스 다시 읽기`를 실행하세요."
                )
                return
            with st.spinner("최신 변경 파일을 Project Chat 답변 근거에 반영하는 중입니다."):
                result = refresh_changed_source_files(db, current_project, changed_files)
                refreshed_summary = _load_initial_source_summary(db, current_project)
                refreshed_cache_key = build_source_verification_cache_key(current_project, refreshed_summary)
        if result.status is not None:
            _cache_source_verification(refreshed_cache_key, result.status)
        st.success(
            "최신 변경분 반영 완료: "
            f"변경 파일 {result.changed_file_count}건, "
            f"반영 대상 {result.indexed_file_count}건, "
            f"정리한 이전 근거 {result.deleted_file_count}건, "
            f"새 근거 {result.chunk_result.created_count}건, "
            f"건너뜀 {result.chunk_result.skipped_count + result.skipped_file_count}건"
        )
        st.rerun()

    if action_col3.button(
        "전체 소스 다시 읽기",
        disabled=not bool(project.git_repo_path),
        use_container_width=True,
        help=PROJECT_CHAT_HELP["refresh_all"],
    ):
        with SessionLocal() as db:
            current_project = db.get(Project, project.id)
            if current_project is None:
                st.error("프로젝트를 찾을 수 없습니다.")
                return
            with st.spinner("현재 코드 전체를 다시 읽어 Project Chat 답변 근거를 정리하는 중입니다."):
                result = refresh_source_file_index(db, current_project)
                refreshed_summary = _load_initial_source_summary(db, current_project)
                refreshed_cache_key = build_source_verification_cache_key(current_project, refreshed_summary)
        _cache_source_verification(refreshed_cache_key, result.status)
        st.success(
            "전체 소스 다시 읽기 완료: "
            f"새 근거 {result.chunk_result.created_count}건, "
            f"오래된 근거 정리 {result.deleted_unverified_count}건"
        )
        st.rerun()

    return summary


def _render_graph_question_templates(project_id: int, repo_head_hash: str | None = None) -> None:
    with SessionLocal() as db:
        freshness = get_project_graph_freshness(db, project_id, repo_head_hash=repo_head_hash)
    enabled, message = _graph_template_status(freshness)

    with st.container(border=True):
        st.markdown("#### 관계 질문")
        if enabled:
            st.success(message)
        else:
            st.warning(message)

        cols = st.columns(2)
        for index, template in enumerate(GRAPH_AWARE_QUESTION_TEMPLATES):
            col = cols[index % 2]
            with col:
                if st.button(
                    template["label"],
                    key=f"project_chat_graph_template_{project_id}_{index}",
                    use_container_width=True,
                    disabled=not enabled,
                ):
                    st.session_state[_pending_question_key(project_id)] = template["question"]
                    st.rerun()
                st.caption(template["question"])


def _split_sources(sources: list[dict]) -> tuple[list[dict], list[dict]]:
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
    return current_sources, reference_sources


def _render_source_group(title: str, sources: list[dict], message_index: int, key_prefix: str) -> None:
    if not sources:
        st.caption(f"{title}: 없음")
        return

    rows = [_source_row(source, rank) for rank, source in enumerate(sources, start=1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    for rank, source in enumerate(sources, start=1):
        row = rows[rank - 1]
        detail_title = f"#{rank} {row['verification_status']} / {row['source']}"
        st.markdown(f"**{detail_title}**")
        st.caption(
            f"source_type: {source.get('source_type')} | "
            f"verification_status: {source.get('verification_status')} | "
            f"line_range: {row['line_range']}"
        )
        st.text_area(
            "근거 내용",
            value=(source.get("text") or "")[:2000],
            height=220,
            disabled=True,
            key=f"project_chat_source_{key_prefix}_{message_index}_{rank}_{source.get('id')}",
        )


def _render_sources(sources: list[dict], message_index: int, used_source_count: int = 0) -> None:
    if not sources:
        return

    current_sources, reference_sources = _split_sources(sources)
    with st.expander("답변 근거 보기", expanded=False):
        st.caption(
            f"답변에 사용된 현재 소스 근거 {used_source_count or len(current_sources)}건, "
            f"참고/제외 근거 {len(reference_sources)}건"
        )
        st.subheader("현재 소스 근거")
        _render_source_group("현재 소스 근거", current_sources, message_index, "current")
        st.subheader("이력/참고 근거")
        _render_source_group("이력/참고 근거", reference_sources, message_index, "reference")


def _graph_evidence_row(evidence: dict, rank: int) -> dict:
    path = " -> ".join(str(part) for part in evidence.get("path") or [] if part)
    matched = ", ".join(str(seed) for seed in evidence.get("matched_seeds") or [])
    evidence_type = evidence.get("evidence_type") or "-"
    if evidence_type == "impact_path":
        detail = (
            f"{evidence.get('program') or '-'} / {evidence.get('commit') or '-'} / "
            f"{evidence.get('file_path') or '-'} / {evidence.get('class_name') or '-'}"
        )
    elif evidence_type == "class_import":
        detail = f"{evidence.get('source_class') or '-'} -> {evidence.get('target_class') or '-'}"
    elif evidence_type == "domain_summary":
        detail = (
            f"{evidence.get('domain') or '-'} "
            f"(program {evidence.get('program_count') or 0}, "
            f"file {evidence.get('file_count') or 0}, class {evidence.get('class_count') or 0})"
        )
    else:
        detail = evidence.get("title") or "-"
    return {
        "rank": rank,
        "type": evidence_type,
        "path": path or detail,
        "detail": detail,
        "matched": matched or "-",
    }


def _short_graph_label(value: str, *, max_length: int = 34) -> str:
    if not value:
        label = "-"
    elif "/" in value or "\\" in value:
        label = value.replace("\\", "/").rsplit("/", 1)[-1]
    else:
        label = value.rsplit(".", 1)[-1]
    if len(label) > max_length:
        return label[: max_length - 1].rstrip() + "..."
    return label


def _graph_node_id(node_type: str, value: str | None) -> str | None:
    if not value or value == "-":
        return None
    return f"{node_type}:{value}"


def _add_graph_node(
    nodes: dict[str, GraphDisplayNode],
    node_type: str,
    value: str | None,
    *,
    highlighted: bool = False,
    title: str | None = None,
) -> str | None:
    node_id = _graph_node_id(node_type, value)
    if node_id is None:
        return None
    existing = nodes.get(node_id)
    if existing is not None:
        next_title = existing.title
        if title and title not in existing.title:
            next_title = f"{existing.title}\n{title}"
        if (highlighted and not existing.highlighted) or next_title != existing.title:
            nodes[node_id] = GraphDisplayNode(
                id=existing.id,
                label=existing.label,
                node_type=existing.node_type,
                title=next_title,
                highlighted=existing.highlighted or highlighted,
            )
        return node_id
    nodes[node_id] = GraphDisplayNode(
        id=node_id,
        label=_short_graph_label(str(value)),
        node_type=node_type,
        title=title or f"{node_type}: {value}",
        highlighted=highlighted,
    )
    return node_id


def _add_graph_edge(
    edges: dict[tuple[str, str, str], GraphDisplayEdge],
    source: str | None,
    target: str | None,
    label: str,
) -> None:
    if not source or not target or source == target:
        return
    key = (source, target, label)
    edges.setdefault(key, GraphDisplayEdge(source=source, target=target, label=label))


def _is_graph_seed_match(value: str | None, evidence: dict) -> bool:
    if not value:
        return False
    label = _short_graph_label(str(value)).lower()
    compact_label = "".join(ch for ch in label if ch.isalnum())
    meaningful_seeds = [
        "".join(ch for ch in str(seed).lower() if ch.isalnum())
        for seed in evidence.get("matched_seeds") or []
        if len(str(seed)) > 4 and str(seed).lower() not in GRAPH_HIGHLIGHT_SEED_STOPWORDS
    ]
    return any(seed == compact_label or (len(seed) >= 8 and seed in compact_label) for seed in meaningful_seeds)


def _file_path_matches_class(file_path: str | None, class_name: str | None) -> bool:
    if not file_path or not class_name or class_name == "-":
        return False
    file_name = file_path.replace("\\", "/").rsplit("/", 1)[-1]
    file_stem = file_name.rsplit(".", 1)[0]
    class_label = _short_graph_label(str(class_name))
    return bool(file_stem) and file_stem == class_label


def build_graph_evidence_display(
    graph_evidence: list[dict],
    *,
    max_nodes: int = 12,
    max_edges: int = 16,
) -> tuple[list[GraphDisplayNode], list[GraphDisplayEdge]]:
    nodes: dict[str, GraphDisplayNode] = {}
    edges: dict[tuple[str, str, str], GraphDisplayEdge] = {}

    for evidence in graph_evidence:
        evidence_type = evidence.get("evidence_type")
        if evidence_type == "class_import":
            source_class = evidence.get("source_class") or ((evidence.get("path") or [None, None])[0])
            target_class = evidence.get("target_class") or (
                (evidence.get("path") or [None, None])[1] if len(evidence.get("path") or []) > 1 else None
            )
            source_id = _add_graph_node(
                nodes,
                "class",
                source_class,
                highlighted=_is_graph_seed_match(source_class, evidence),
            )
            target_id = _add_graph_node(
                nodes,
                "class",
                target_class,
                highlighted=_is_graph_seed_match(target_class, evidence),
            )
            _add_graph_edge(edges, source_id, target_id, "IMPORTS_CLASS")
        elif evidence_type == "impact_path":
            file_path = evidence.get("file_path")
            class_name = evidence.get("class_name")
            program_id = _add_graph_node(
                nodes,
                "program",
                evidence.get("program"),
                highlighted=_is_graph_seed_match(evidence.get("program"), evidence),
            )
            commit_label = evidence.get("commit") or (
                str(evidence.get("commit_hash") or "")[:12] if evidence.get("commit_hash") else None
            )
            commit_id = _add_graph_node(nodes, "commit", commit_label)
            _add_graph_edge(edges, program_id, commit_id, "MAPPED_COMMIT")
            if _file_path_matches_class(file_path, class_name):
                class_id = _add_graph_node(
                    nodes,
                    "class",
                    class_name,
                    highlighted=_is_graph_seed_match(class_name, evidence) or _is_graph_seed_match(file_path, evidence),
                    title=f"class: {class_name}\nfile: {file_path}",
                )
                _add_graph_edge(edges, commit_id, class_id, "TOUCHES_FILE")
            else:
                file_id = _add_graph_node(
                    nodes,
                    "file",
                    file_path,
                    highlighted=_is_graph_seed_match(file_path, evidence),
                )
                class_id = _add_graph_node(
                    nodes,
                    "class",
                    class_name,
                    highlighted=_is_graph_seed_match(class_name, evidence),
                )
                _add_graph_edge(edges, commit_id, file_id, "TOUCHES_FILE")
                _add_graph_edge(edges, file_id, class_id, "CONTAINS_CLASS")

        if len(nodes) >= max_nodes and len(edges) >= max_edges:
            break

    return list(nodes.values())[:max_nodes], list(edges.values())[:max_edges]


def _render_graph_evidence_visualization(graph_evidence: list[dict]) -> None:
    nodes, edges = build_graph_evidence_display(graph_evidence)
    if not nodes or not edges:
        st.caption("시각화할 수 있는 graph 관계가 없습니다. 아래 표에서 원본 근거를 확인하세요.")
        return

    st.markdown("#### GraphRAG 관계도")
    st.caption("질문과 매칭된 class import와 program-commit-file-class 영향 경로를 함께 표시합니다. 연결이 약한 domain 요약은 원본 메타데이터에만 남깁니다.")
    agraph_nodes = []
    single_type_graph = len({node.node_type for node in nodes}) == 1
    component_variant_indexes = _graph_component_variant_indexes(nodes, edges) if single_type_graph else {}
    for node in nodes:
        style = GRAPH_NODE_STYLE.get(
            node.node_type,
            {"color": "#F3F4F6", "highlight": "#E5E7EB", "border": "#D1D5DB", "shape": "dot", "size": 22},
        )
        color_style = (
            GRAPH_NODE_VARIANT_STYLES[component_variant_indexes.get(node.id, 0)] if single_type_graph else style
        )
        background = color_style["color"]
        highlight_background = color_style["highlight"]
        border = GRAPH_HIGHLIGHT_COLOR if node.highlighted else color_style["border"]
        highlight_border = GRAPH_HIGHLIGHT_BORDER_COLOR if node.highlighted else color_style["border"]
        agraph_nodes.append(
            Node(
                id=node.id,
                label=node.label,
                title=node.title,
                color={
                    "background": background,
                    "border": border,
                    "highlight": {"background": highlight_background, "border": highlight_border},
                    "hover": {"background": highlight_background, "border": highlight_border},
                },
                shape=style["shape"],
                size=style["size"] + (3 if node.highlighted else 0),
                borderWidth=3 if node.highlighted else 2,
                font={"color": "#111827", "face": "Inter, Arial", "size": 14},
            )
        )
    agraph_edges = [
        Edge(
            source=edge.source,
            target=edge.target,
            label="",
            title=edge.label,
            color={"color": GRAPH_EDGE_COLOR, "highlight": GRAPH_EDGE_HIGHLIGHT_COLOR},
            smooth={"type": "dynamic"},
            width=2.4,
        )
        for edge in edges
    ]
    config = Config(
        height=560 if not single_type_graph else 480,
        width="100%",
        directed=True,
        physics=not single_type_graph,
        hierarchical=single_type_graph,
        groups={},
    )
    agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)


def _render_graph_evidence(graph_evidence: list[dict], message_index: int, key_prefix: str) -> None:
    if not graph_evidence:
        return

    visible_graph_evidence = _visible_graph_evidence(graph_evidence)
    rows = [_graph_evidence_row(evidence, rank) for rank, evidence in enumerate(visible_graph_evidence, start=1)]
    type_counts = Counter(str(evidence.get("evidence_type") or "-") for evidence in visible_graph_evidence)
    type_summary = ", ".join(f"{evidence_type} {count}건" for evidence_type, count in type_counts.items())
    with st.expander("그래프 관계 근거 보기", expanded=False):
        st.caption("Neo4j graph read model에서 조회한 코드 관계와 영향 경로 근거입니다.")
        st.caption(f"관계 유형: {type_summary or '표시할 근거 0건'}")
        _render_graph_evidence_visualization(visible_graph_evidence)
        st.markdown("#### 관계 근거 표")
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("기본 화면에 표시할 코드 관계나 영향 경로 근거가 없습니다. 원본 메타데이터에서 추가 근거를 확인하세요.")
        show_metadata = st.checkbox(
            "원본 메타데이터 표시",
            value=False,
            key=f"project_chat_graph_metadata_{key_prefix}_{message_index}",
        )
        if show_metadata:
            st.caption("검증이나 디버깅이 필요할 때만 펼쳐 보는 Neo4j graph evidence 원본입니다.")
            for rank, evidence in enumerate(graph_evidence, start=1):
                st.markdown(f"**Graph {rank}: {_graph_evidence_row(evidence, rank)['path']}**")
                st.json(
                    evidence,
                    expanded=False,
                )


def _visible_graph_evidence(graph_evidence: list[dict]) -> list[dict]:
    visible_types = {"class_import", "impact_path"}
    return [evidence for evidence in graph_evidence if evidence.get("evidence_type") in visible_types]


def _render_expansion_context(message: dict) -> None:
    expanded_queries = message.get("expanded_queries") or []
    matched_terms = message.get("matched_terms") or []
    if not expanded_queries and not matched_terms:
        return

    with st.expander("검색 확장 정보", expanded=False):
        if matched_terms:
            st.caption("표준용어/표준단어 매칭")
            st.dataframe(pd.DataFrame(matched_terms), use_container_width=True, hide_index=True)
        if expanded_queries:
            st.caption("검색에 사용된 쿼리")
            st.write("\n".join(f"- {query}" for query in expanded_queries))


def _render_chat_history(messages: list[dict]) -> None:
    for index, message in enumerate(messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                provider = message.get("provider") or "-"
                model = message.get("model") or "-"
                fallback_used = bool(message.get("fallback_used"))
                if provider != "-" or model != "-":
                    st.caption(f"Provider: {provider} / {model} / fallback={fallback_used}")
                validation_status = message.get("validation_status") or "not_applicable"
                if validation_status != "not_applicable":
                    st.caption(
                        f"답변 근거 검증: {validation_status} / "
                        f"repair={bool(message.get('repair_attempted', False))}"
                    )
                used_source_count = int(message.get("used_source_count") or 0)
                insufficient = bool(message.get("insufficient_evidence"))
                if insufficient:
                    st.warning("근거 부족으로 추측성 답변을 생성하지 않았습니다.")
                elif used_source_count:
                    st.caption(f"답변에 사용된 현재 소스 근거 {used_source_count}건")
                graph_evidence = message.get("graph_evidence") or []
                if graph_evidence:
                    st.caption(f"답변에 사용된 그래프 관계 근거 {len(graph_evidence)}건")

                excluded_count = int(message.get("excluded_count") or 0)
                if excluded_count:
                    st.caption(f"검증되지 않았거나 현재 코드 근거가 아닌 근거 {excluded_count}건은 답변에서 제외했습니다.")
                _render_expansion_context(message)
                _render_sources(message.get("sources") or [], index, used_source_count)
                _render_graph_evidence(graph_evidence, index, "history")
                export_message = dict(message)
                export_message["graph_evidence"] = _visible_graph_evidence(graph_evidence)
                st.text_area(
                    "근거 복사용 Markdown",
                    value=format_message_citation_export(export_message),
                    height=180,
                    key=f"project_chat_citation_export_{index}",
                )


def _format_session_title(title: str | None) -> str:
    if not title or title == "새 대화":
        return "빈 대화"
    return title


def _render_chat_session_selector(project_id: int) -> tuple[int | None, list[dict]]:
    active_key = _active_session_key(project_id)
    with SessionLocal() as db:
        sessions = list_chat_sessions(db, project_id)
        if not sessions:
            session = create_chat_session(db, project_id)
            sessions = [session]
        active_session_id = st.session_state.get(active_key)
        if active_session_id is None or all(session.id != active_session_id for session in sessions):
            active_session_id = sessions[0].id
            st.session_state[active_key] = active_session_id

    session_options = {
        (
            f"{_format_session_title(session.title)} · "
            f"{session.last_message_at.strftime('%Y-%m-%d %H:%M') if session.last_message_at else '-'} · "
            f"#{session.id}"
        ): session.id
        for session in sessions
    }
    labels = list(session_options.keys())
    selected_index = max(0, [session_options[label] for label in labels].index(st.session_state[active_key]))
    with st.container(border=True):
        st.markdown("#### 대화 관리")
        history_col, action_col = st.columns([5, 1.35])
        selected_label = history_col.selectbox(
            "저장된 대화",
            labels,
            index=selected_index,
            help=PROJECT_CHAT_HELP["session"],
        )
        st.session_state[active_key] = session_options[selected_label]

        action_col.markdown("&nbsp;", unsafe_allow_html=True)
        if action_col.button(
            "새 대화 시작",
            type="primary",
            use_container_width=True,
            help=PROJECT_CHAT_HELP["new_chat"],
        ):
            with SessionLocal() as db:
                session = create_chat_session(db, project_id)
                st.session_state[active_key] = session.id
            st.rerun()
        st.caption("새 대화를 시작해도 기존 대화는 삭제되지 않으며, 저장된 대화에서 다시 선택할 수 있습니다.")

    with SessionLocal() as db:
        session = get_chat_session(db, project_id, int(st.session_state[active_key]))
        if session is None:
            return None, []
        messages = messages_to_ui_dicts(get_session_messages(db, session.id))
    return int(st.session_state[active_key]), messages


def render_project_chat_page() -> None:
    st.title("Project Chat")
    st.caption("현재 코드에서 확인된 소스 근거를 찾아 프로젝트 질문에 답합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return
    project_id = context.project_id
    project = Project(id=context.project_id, name=context.project_name, git_repo_path=context.git_repo_path)

    source_summary = _render_source_index_status(project)

    control1, control2 = st.columns([1, 3])
    top_k = control1.slider(
        "TOP K",
        min_value=3,
        max_value=30,
        value=8,
        help=PROJECT_CHAT_HELP["top_k"],
    )
    include_history = control2.checkbox(
        "커밋 이력도 참고에 포함",
        value=False,
        help=PROJECT_CHAT_HELP["include_history"],
    )

    st.divider()
    st.subheader("대화")
    _render_graph_question_templates(
        project_id,
        repo_head_hash=source_summary.current_head_hash if source_summary else None,
    )
    active_session_id, messages = _render_chat_session_selector(project_id)
    _render_chat_history(messages)

    pending_prompt_key = _pending_question_key(project_id)
    pending_prompt = st.session_state.pop(pending_prompt_key, None)
    prompt = pending_prompt or st.chat_input("프로젝트에 대해 질문하세요.")
    if not prompt or active_session_id is None:
        return

    with SessionLocal() as db:
        append_chat_message(db, active_session_id, role="user", content=prompt)

    with st.chat_message("user"):
        st.write(prompt)

    with SessionLocal() as db:
        current_project = db.get(Project, project_id)
        if current_project is None:
            st.error("프로젝트를 찾을 수 없습니다.")
            return
        with st.chat_message("assistant"):
            with st.spinner("질문과 관련된 근거를 검색하고 현재 파일을 검증한 뒤 답변을 생성합니다."):
                answer = answer_source_question(
                    db,
                    current_project,
                    prompt,
                    top_k=int(top_k),
                    include_history=include_history,
                )
            if answer.errors:
                content = "\n".join(answer.errors)
                st.error(content)
            else:
                content = answer.answer
                if answer.insufficient_evidence:
                    st.warning(content)
                else:
                    st.write(content)
                    st.caption(f"Provider: {answer.provider or '-'} / {answer.model or '-'} / fallback={answer.fallback_used}")
                    if answer.validation_status != "not_applicable":
                        st.caption(
                            f"답변 근거 검증: {answer.validation_status} / "
                            f"repair={answer.repair_attempted}"
                        )
                    if answer.used_source_count:
                        st.caption(f"답변에 사용된 현재 소스 근거 {answer.used_source_count}건")
                    if answer.graph_evidence:
                        st.caption(f"답변에 사용된 그래프 관계 근거 {len(answer.graph_evidence)}건")
                if answer.excluded_count:
                    st.caption(f"검증되지 않았거나 현재 코드 근거가 아닌 근거 {answer.excluded_count}건은 답변에서 제외했습니다.")
                _render_expansion_context(
                    {
                        "expanded_queries": [] if answer.errors else answer.expanded_queries,
                        "matched_terms": [] if answer.errors else answer.matched_terms,
                    }
                )
                _render_sources(answer.sources, len(messages), answer.used_source_count)
                _render_graph_evidence(answer.graph_evidence, len(messages), "live")
                st.text_area(
                    "근거 복사용 Markdown",
                    value=format_message_citation_export(
                        {
                            "content": content,
                            "sources": answer.sources,
                            "used_source_count": answer.used_source_count,
                            "graph_evidence": _visible_graph_evidence(answer.graph_evidence),
                        }
                    ),
                    height=180,
                    key=f"project_chat_citation_export_live_{active_session_id}",
                )

        append_chat_message(
            db,
            active_session_id,
            role="assistant",
            content=content,
            sources=[] if answer.errors else answer.sources,
            expanded_queries=[] if answer.errors else answer.expanded_queries,
            matched_terms=[] if answer.errors else answer.matched_terms,
            excluded_count=0 if answer.errors else answer.excluded_count,
            used_source_count=0 if answer.errors else answer.used_source_count,
            insufficient_evidence=False if answer.errors else answer.insufficient_evidence,
            raw_metadata=(
                {
                    "errors": answer.errors,
                    "graph_evidence": answer.graph_evidence,
                    "graph_evidence_metadata": answer.graph_evidence_metadata,
                    "provider": answer.provider,
                    "model": answer.model,
                    "fallback_used": answer.fallback_used,
                    "validation_status": answer.validation_status,
                    "repair_attempted": answer.repair_attempted,
                }
                if answer.errors
                else {
                    "graph_evidence": answer.graph_evidence,
                    "graph_evidence_metadata": answer.graph_evidence_metadata,
                    "provider": answer.provider,
                    "model": answer.model,
                    "fallback_used": answer.fallback_used,
                    "validation_status": answer.validation_status,
                    "repair_attempted": answer.repair_attempted,
                }
            ),
        )
    st.rerun()

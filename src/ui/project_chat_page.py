from __future__ import annotations

import pandas as pd
import streamlit as st

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
    get_changed_source_files_since_latest_index,
    get_source_index_status,
    refresh_changed_source_files,
    refresh_source_file_index,
)
from src.services.neo4j_graph_service import Neo4jGraphFreshness, get_project_graph_freshness
from src.ui.project_context import require_project_context


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


def _render_source_index_status(project: Project) -> None:
    with SessionLocal() as db:
        current_project = db.get(Project, project.id)
        if current_project is None:
            st.error("프로젝트를 찾을 수 없습니다.")
            return
        status = get_source_index_status(db, current_project)

    st.subheader("답변 근거 상태")
    st.caption("Project Chat은 앱 서버 Git 저장소에서 읽어 둔 소스 근거로 답합니다. 코드가 바뀌었으면 최신 변경분을 먼저 반영하세요.")

    search_ready_count = max(status.source_chunk_count - status.missing_embedding_count, 0)
    code_status = "확인 필요" if status.needs_reindex else "최신"
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("소스 근거", status.source_chunk_count, help=PROJECT_CHAT_HELP["source_count"])
    metric2.metric("검색 준비", f"{search_ready_count}/{status.source_chunk_count}", help=PROJECT_CHAT_HELP["search_ready"])
    metric3.metric("코드 반영 상태", code_status, help=PROJECT_CHAT_HELP["code_status"])
    metric4.metric("추가 준비 필요", status.missing_embedding_count, help=PROJECT_CHAT_HELP["missing_ready"])

    if status.source_chunk_count == 0:
        st.warning(
            "아직 질문에 사용할 소스 근거가 준비되지 않았습니다. "
            "아래에서 `전체 소스 다시 읽기`를 먼저 실행한 뒤, 검색 준비가 남아 있으면 `RAG 검색` 화면에서 이어서 처리하세요."
        )
    elif status.needs_reindex:
        st.warning(
            "코드가 바뀐 뒤 Project Chat의 답변 근거가 아직 최신 상태가 아닐 수 있습니다. "
            "아래에서 최신 변경분을 반영한 뒤 질문하는 것을 권장합니다."
        )
    elif status.missing_embedding_count > 0 or status.source_vector_count == 0:
        st.warning(
            "소스 근거는 준비되어 있지만 질문과 연결할 준비가 일부 남아 있습니다. "
            "`RAG 검색` 화면에서 남은 검색 준비를 적은 수량으로 실행한 뒤 질문해 주세요."
        )
    else:
        st.success("Project Chat이 현재 코드 기준 소스 근거로 답변할 준비가 되어 있습니다.")

    for error in status.errors:
        st.warning(error)

    with st.expander("어떤 버튼을 누르면 되나요?", expanded=False):
        st.markdown(
            "- `최신 변경분 반영`: Git 동기화 후 바뀐 파일만 빠르게 읽어 Project Chat 근거를 최신화합니다.\n"
            "- `전체 소스 다시 읽기`: 처음 준비하거나 브랜치를 크게 바꿨거나 오래된 근거가 계속 보일 때 사용합니다.\n"
            "- `검색 준비`가 남아 있으면 `RAG 검색` 화면에서 남은 작업을 소량씩 실행하세요."
        )
        st.caption(
            "기술 상세: 화면의 소스 근거는 내부적으로 source chunk로 저장되고, 검색 준비는 embedding/vector 생성 상태를 뜻합니다."
        )

    with st.expander("기술 상세", expanded=False):
        st.write(
            {
                "Current HEAD": _short_hash(status.current_head_hash),
                "Indexed HEAD": _short_hash(status.latest_indexed_head_hash),
                "source_file chunks": status.source_chunk_count,
                "source_file vectors": status.source_vector_count,
                "HEAD mismatch chunks": status.head_mismatch_chunk_count,
                "stale chunks": status.stale_chunk_count,
                "invalid chunks": status.invalid_chunk_count,
                "missing embeddings": status.missing_embedding_count,
            }
        )

    action_col1, action_col2 = st.columns(2)
    if action_col1.button(
        "최신 변경분 반영",
        type="primary" if status.needs_reindex else "secondary",
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
        st.success(
            "최신 변경분 반영 완료: "
            f"변경 파일 {result.changed_file_count}건, "
            f"반영 대상 {result.indexed_file_count}건, "
            f"정리한 이전 근거 {result.deleted_file_count}건, "
            f"새 근거 {result.chunk_result.created_count}건, "
            f"건너뜀 {result.chunk_result.skipped_count + result.skipped_file_count}건"
        )
        st.rerun()

    if action_col2.button(
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
        st.success(
            "전체 소스 다시 읽기 완료: "
            f"새 근거 {result.chunk_result.created_count}건, "
            f"오래된 근거 정리 {result.deleted_unverified_count}건"
        )
        st.rerun()


def _render_graph_question_templates(project_id: int) -> None:
    with SessionLocal() as db:
        freshness = get_project_graph_freshness(db, project_id)
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


def _render_graph_evidence(graph_evidence: list[dict], message_index: int, key_prefix: str) -> None:
    if not graph_evidence:
        return

    rows = [_graph_evidence_row(evidence, rank) for rank, evidence in enumerate(graph_evidence, start=1)]
    with st.expander("그래프 관계 근거 보기", expanded=False):
        st.caption("Neo4j graph read model에서 조회한 program, commit, file, class, domain 관계 근거입니다.")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        for rank, evidence in enumerate(graph_evidence, start=1):
            st.markdown(f"**Graph {rank}: {rows[rank - 1]['path']}**")
            st.json(
                evidence,
                expanded=False,
            )


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
                st.text_area(
                    "근거 복사용 Markdown",
                    value=format_message_citation_export(message),
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

    _render_source_index_status(project)

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
    _render_graph_question_templates(project_id)
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
            with st.spinner("검증된 현재 소스 근거를 검색하고 답변을 생성합니다."):
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
                            "graph_evidence": answer.graph_evidence,
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
                }
                if answer.errors
                else {
                    "graph_evidence": answer.graph_evidence,
                    "graph_evidence_metadata": answer.graph_evidence_metadata,
                }
            ),
        )
    st.rerun()

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
def _chat_key(project_id: int) -> str:
    return f"project_chat_messages_{project_id}"


def _active_session_key(project_id: int) -> str:
    return f"project_chat_active_session_{project_id}"


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

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("source_file chunks", status.source_chunk_count)
    metric2.metric("source_file vectors", status.source_vector_count)
    metric3.metric("Current HEAD", _short_hash(status.current_head_hash))
    metric4.metric("Indexed HEAD", _short_hash(status.latest_indexed_head_hash))
    st.caption(
        f"HEAD 불일치 chunk {status.head_mismatch_chunk_count}건, "
        f"stale chunk {status.stale_chunk_count}건, 검증 불가 {status.invalid_chunk_count}건, "
        f"embedding 필요 {status.missing_embedding_count}건"
    )

    if status.source_vector_count == 0:
        st.warning("현재 소스 파일 vector가 없습니다. `RAG 검색 > Index`에서 현재 소스 파일 인덱싱을 먼저 실행하세요.")
    elif status.needs_reindex:
        st.warning(
            "현재 Git HEAD와 인덱싱 시점이 다를 수 있습니다. "
            "최신 코드 기준 답변을 위해 source_file 재인덱싱을 권장합니다."
        )
    else:
        st.caption("현재 소스 인덱스가 Git 저장소 기준으로 검증되었습니다.")

    for error in status.errors:
        st.warning(error)

    st.caption(
        "Project Chat의 재인덱싱은 PC 부하를 줄이기 위해 chunk만 갱신합니다. "
        "embedding 생성은 `RAG 검색 > Embedding`에서 제한 수량으로 실행하세요."
    )
    if st.button("최근 Git sync 변경 파일만 인덱싱", type="primary", disabled=not bool(project.git_repo_path)):
        with SessionLocal() as db:
            current_project = db.get(Project, project.id)
            if current_project is None:
                st.error("프로젝트를 찾을 수 없습니다.")
                return
            changed_files = get_changed_source_files_since_latest_index(db, current_project)
            if not changed_files:
                st.info(
                    "최근 indexed HEAD 이후 Git sync에 저장된 변경 파일이 없습니다. "
                    "최초 구축이나 복구가 필요하면 전체 source_file 재인덱싱을 실행하세요."
                )
                return
            with st.spinner("최근 Git sync 변경 파일만 source_file chunk로 갱신합니다. embedding은 자동 실행하지 않습니다."):
                result = refresh_changed_source_files(db, current_project, changed_files)
        st.success(
            "증분 source_file 인덱싱 완료: "
            f"변경 파일 {result.changed_file_count}건, "
            f"인덱싱 대상 {result.indexed_file_count}건, "
            f"삭제 chunk {result.deleted_file_count}건, "
            f"신규 chunk {result.chunk_result.created_count}건, "
            f"건너뜀 {result.chunk_result.skipped_count + result.skipped_file_count}건"
        )
        st.rerun()

    if st.button("현재 소스 다시 인덱싱", disabled=not bool(project.git_repo_path)):
        with SessionLocal() as db:
            current_project = db.get(Project, project.id)
            if current_project is None:
                st.error("프로젝트를 찾을 수 없습니다.")
                return
            with st.spinner("현재 HEAD 기준으로 source_file chunk를 갱신합니다. embedding은 여기서 자동 실행하지 않습니다."):
                result = refresh_source_file_index(db, current_project)
        st.success(
            "source_file 재인덱싱 완료: "
            f"chunk {result.chunk_result.created_count}건, "
            f"오래된 chunk 정리 {result.deleted_unverified_count}건"
        )
        st.rerun()


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
            "chunk",
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

                excluded_count = int(message.get("excluded_count") or 0)
                if excluded_count:
                    st.caption(f"검증되지 않았거나 현재 코드 근거가 아닌 chunk {excluded_count}건은 현재 코드 답변 근거에서 제외했습니다.")
                _render_expansion_context(message)
                _render_sources(message.get("sources") or [], index, used_source_count)
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
        selected_label = history_col.selectbox("저장된 대화", labels, index=selected_index)
        st.session_state[active_key] = session_options[selected_label]

        action_col.markdown("&nbsp;", unsafe_allow_html=True)
        if action_col.button("새 대화 시작", type="primary", use_container_width=True):
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
    st.caption("현재 소스 파일에서 검증된 RAG 근거로 프로젝트 질문에 답합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return
    project_id = context.project_id
    project = Project(id=context.project_id, name=context.project_name, git_repo_path=context.git_repo_path)

    _render_source_index_status(project)

    control1, control2 = st.columns([1, 3])
    top_k = control1.slider("TOP K", min_value=3, max_value=30, value=8)
    include_history = control2.checkbox("커밋 이력도 참고에 포함", value=False)

    st.divider()
    st.subheader("대화")
    active_session_id, messages = _render_chat_session_selector(project_id)
    _render_chat_history(messages)

    prompt = st.chat_input("프로젝트에 대해 질문하세요.")
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
                if answer.excluded_count:
                    st.caption(f"검증되지 않았거나 현재 코드 근거가 아닌 chunk {answer.excluded_count}건은 현재 코드 답변 근거에서 제외했습니다.")
                _render_expansion_context(
                    {
                        "expanded_queries": [] if answer.errors else answer.expanded_queries,
                        "matched_terms": [] if answer.errors else answer.matched_terms,
                    }
                )
                _render_sources(answer.sources, len(messages), answer.used_source_count)
                st.text_area(
                    "근거 복사용 Markdown",
                    value=format_message_citation_export(
                        {
                            "content": content,
                            "sources": answer.sources,
                            "used_source_count": answer.used_source_count,
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
            raw_metadata={"errors": answer.errors} if answer.errors else None,
        )
    st.rerun()

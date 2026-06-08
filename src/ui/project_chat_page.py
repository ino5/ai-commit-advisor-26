from __future__ import annotations

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import DocumentChunk, Project, VectorItem
from src.rag.chat_service import answer_source_question


VERIFICATION_LABELS = {
    "verified": "현재 코드 검증됨",
    "stale": "인덱스 오래됨",
    "invalid": "검증 실패",
    "historical": "변경 이력",
    "not_applicable": "검증 대상 아님",
}


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _chat_key(project_id: int) -> str:
    return f"project_chat_messages_{project_id}"


def _format_source(source: dict) -> str:
    metadata = source.get("metadata") or {}
    source_type = source.get("source_type")
    if source_type == "source_file":
        return (
            f"{metadata.get('file_path') or source.get('source_id')}:"
            f"{metadata.get('line_start')}-{metadata.get('line_end')}"
        )
    if source_type == "commit_file":
        return f"{metadata.get('commit_hash') or ''} / {metadata.get('file_path') or source.get('source_id')}"
    if source_type == "commit":
        return metadata.get("commit_hash") or str(source.get("source_id"))
    return f"{source_type} / {source.get('source_id')}"


def _index_counts(project_id: int) -> tuple[int, int]:
    with SessionLocal() as db:
        source_chunk_count = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == "source_file")
            .count()
        )
        source_vector_count = (
            db.query(VectorItem)
            .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
            .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == "source_file")
            .count()
        )
    return source_chunk_count, source_vector_count


def _render_sources(sources: list[dict], message_index: int) -> None:
    if not sources:
        return

    rows = []
    for rank, source in enumerate(sources, start=1):
        rows.append(
            {
                "rank": rank,
                "score": round(float(source.get("similarity") or 0), 4),
                "source": _format_source(source),
                "status": VERIFICATION_LABELS.get(source.get("verification_status"), source.get("verification_status")),
                "reason": source.get("verification_reason"),
            }
        )

    with st.expander("근거 보기", expanded=False):
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        for rank, source in enumerate(sources, start=1):
            title = f"#{rank} {rows[rank - 1]['status']} / {_format_source(source)}"
            with st.expander(title, expanded=False):
                st.text_area(
                    "chunk",
                    value=(source.get("text") or "")[:2000],
                    height=220,
                    disabled=True,
                    key=f"project_chat_source_{message_index}_{rank}_{source.get('id')}",
                )


def _render_chat_history(messages: list[dict]) -> None:
    for index, message in enumerate(messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                excluded_count = int(message.get("excluded_count") or 0)
                if excluded_count:
                    st.caption(f"검증되지 않았거나 현재 코드 근거가 아닌 chunk {excluded_count}건은 제외했습니다.")
                _render_sources(message.get("sources") or [], index)


def render_project_chat_page() -> None:
    st.title("Project Chat")
    st.caption("현재 소스 파일에서 검증된 RAG 근거로 프로젝트 질문에 답합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]
    project = next(project for project in projects if project.id == project_id)
    messages_key = _chat_key(project_id)
    st.session_state.setdefault(messages_key, [])

    source_chunk_count, source_vector_count = _index_counts(project_id)
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("source_file chunks", source_chunk_count)
    metric2.metric("source_file vectors", source_vector_count)
    metric3.metric("Git repo", "등록됨" if project.git_repo_path else "미등록")

    if source_vector_count == 0:
        st.warning("현재 소스 파일 vector가 없습니다. `RAG 검색 > Index`에서 `현재 소스 파일` 인덱싱을 먼저 실행하세요.")

    control1, control2, control3 = st.columns([1, 1, 2])
    top_k = control1.slider("TOP K", min_value=3, max_value=30, value=8)
    include_history = control2.checkbox("커밋 이력도 후보에 포함", value=False)
    if control3.button("대화 초기화"):
        st.session_state[messages_key] = []
        st.rerun()

    st.divider()
    _render_chat_history(st.session_state[messages_key])

    prompt = st.chat_input("프로젝트에 대해 질문하세요.")
    if not prompt:
        return

    st.session_state[messages_key].append({"role": "user", "content": prompt})
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
                st.write(content)
                if answer.excluded_count:
                    st.caption(
                        f"검증되지 않았거나 현재 코드 근거가 아닌 chunk {answer.excluded_count}건은 제외했습니다."
                    )
                _render_sources(answer.sources, len(st.session_state[messages_key]))

    st.session_state[messages_key].append(
        {
            "role": "assistant",
            "content": content,
            "sources": [] if answer.errors else answer.sources,
            "excluded_count": 0 if answer.errors else answer.excluded_count,
        }
    )

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import DocumentChunk, Project, VectorItem
from src.rag.chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, build_project_chunks
from src.rag.chat_service import answer_source_question
from src.rag.embedding_client import EmbeddingClient
from src.rag.retriever import Retriever
from src.rag.source_index_service import get_source_index_status, refresh_source_file_index
from src.rag.source_verifier import annotate_retrieval_result
from src.rag.vector_store import VectorStore
from src.utils.config import settings


SOURCE_TYPE_OPTIONS = ["source_file", "program", "commit", "commit_file"]
SOURCE_TYPE_LABELS = {
    "source_file": "현재 소스 파일",
    "program": "프로그램 정보",
    "commit": "커밋 메시지",
    "commit_file": "변경 파일/diff",
}
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


def _source_label(source_type: str) -> str:
    return SOURCE_TYPE_LABELS.get(source_type, source_type)


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def _format_source(result: dict) -> str:
    metadata = result.get("metadata") or {}
    source_type = result.get("source_type")
    if source_type == "source_file":
        file_path = metadata.get("file_path") or result.get("source_id")
        line_start = metadata.get("line_start")
        line_end = metadata.get("line_end")
        return f"{_source_label(source_type)} / {file_path}:{line_start}-{line_end}".strip(" /")
    if source_type == "program":
        program_id = metadata.get("program_id") or result.get("source_id")
        program_name = metadata.get("program_name") or ""
        return f"{_source_label(source_type)} / {program_id} / {program_name}".strip(" /")
    if source_type == "commit":
        return f"{_source_label(source_type)} / {metadata.get('commit_hash') or result.get('source_id')}"
    if source_type == "commit_file":
        commit_hash = metadata.get("commit_hash") or ""
        file_path = metadata.get("file_path") or result.get("source_id")
        return f"{_source_label(source_type)} / {commit_hash} / {file_path}".strip(" /")
    return f"{_source_label(source_type)} / {result.get('source_id')}"


def _render_index_stats(project_id: int) -> None:
    with SessionLocal() as db:
        chunk_count = db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).count()
        vector_count = (
            db.query(VectorItem)
            .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
            .filter(DocumentChunk.project_id == project_id)
            .count()
        )
        source_rows = db.query(DocumentChunk.source_type).filter(DocumentChunk.project_id == project_id).all()

    source_counts = pd.Series([row[0] for row in source_rows]).value_counts().to_dict() if source_rows else {}
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Chunks", chunk_count)
    col2.metric("Vectors", vector_count)
    col3.metric("Source types", len(source_counts))
    col4.metric("Embedding", settings.embedding_provider)
    if source_counts:
        st.caption(", ".join(f"{_source_label(key)}: {value}" for key, value in source_counts.items()))


def _selected_source_types(label: str, default: list[str] | None = None) -> list[str]:
    labels = {SOURCE_TYPE_LABELS[value]: value for value in SOURCE_TYPE_OPTIONS}
    selected = st.multiselect(label, list(labels.keys()), default=[SOURCE_TYPE_LABELS[v] for v in (default or SOURCE_TYPE_OPTIONS)])
    return [labels[item] for item in selected]


def _run_chunking(
    project: Project,
    source_types: list[str],
    chunk_size: int,
    overlap: int,
):
    with SessionLocal() as db:
        return build_project_chunks(
            db,
            project_id=project.id,
            include_programs="program" in source_types,
            include_commits="commit" in source_types,
            include_commit_files="commit_file" in source_types,
            include_source_files="source_file" in source_types,
            repo_path=project.git_repo_path,
            chunk_size=chunk_size,
            overlap=overlap,
        )


def _run_embedding(project_id: int, source_types: list[str], limit: int):
    with SessionLocal() as db:
        client = EmbeddingClient()
        store = VectorStore(db)
        return client, store.embed_missing_chunks(
            client,
            project_id=project_id,
            source_types=source_types,
            limit=limit,
        )


def _render_source_index_status(project: Project) -> None:
    with SessionLocal() as db:
        current_project = db.get(Project, project.id)
        if current_project is None:
            st.error("프로젝트를 찾을 수 없습니다.")
            return
        status = get_source_index_status(db, current_project)

    st.markdown("#### 현재 소스 인덱스 상태")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current HEAD", _short_hash(status.current_head_hash))
    col2.metric("Indexed HEAD", _short_hash(status.latest_indexed_head_hash))
    col3.metric("source_file chunks", status.source_chunk_count)
    col4.metric("source_file vectors", status.source_vector_count)

    col5, col6, col7 = st.columns(3)
    col5.metric("HEAD 불일치 chunk", status.head_mismatch_chunk_count)
    col6.metric("stale chunk", status.stale_chunk_count)
    col7.metric("검증 불가", status.invalid_chunk_count)
    if status.indexed_head_hashes:
        with st.expander("인덱싱된 HEAD 종류", expanded=False):
            st.write([_short_hash(value) for value in status.indexed_head_hashes])

    for error in status.errors:
        st.warning(error)
    if status.needs_reindex:
        st.warning(
            "현재 Git HEAD와 인덱싱 시점이 다를 수 있습니다. "
            "최신 코드 기준 답변을 위해 source_file 재인덱싱을 권장합니다."
        )
    elif status.source_chunk_count:
        st.success("현재 소스 인덱스가 등록된 Git 저장소 기준으로 검증되었습니다.")
    else:
        st.info("현재 소스 파일 인덱스가 아직 없습니다.")

    embed_after_refresh = st.checkbox(
        "재인덱싱 후 embedding도 바로 생성",
        value=False,
        help="LM Studio/local embedding 서버를 많이 사용할 수 있습니다. 기본값은 chunk만 갱신합니다.",
    )
    refresh_embedding_limit = 0
    if embed_after_refresh:
        refresh_embedding_limit = st.number_input(
            "재인덱싱 후 embedding 최대 처리 수",
            min_value=1,
            max_value=500,
            value=100,
            step=50,
            help="큰 저장소에서 PC가 느려지는 것을 막기 위해 한 번에 처리할 수를 제한합니다.",
        )

    if st.button("현재 소스 다시 인덱싱", type="secondary", disabled=not bool(project.git_repo_path)):
        with SessionLocal() as db:
            current_project = db.get(Project, project.id)
            if current_project is None:
                st.error("프로젝트를 찾을 수 없습니다.")
                return
            with st.spinner("현재 HEAD 기준으로 source_file chunk를 갱신합니다. embedding은 선택한 경우에만 제한 수량만 생성합니다."):
                result = refresh_source_file_index(
                    db,
                    current_project,
                    embed_after_refresh=embed_after_refresh,
                    embedding_limit=int(refresh_embedding_limit or 0),
                )
        st.success(
            "source_file 재인덱싱 완료: "
            f"chunk {result.chunk_result.created_count}건, "
            f"오래된 chunk 정리 {result.deleted_unverified_count}건, "
            f"vector {result.embedding_result.created_count}건 생성, "
            f"embedding 실패 {result.embedding_result.failed_count}건"
        )
        if result.embedding_result.errors:
            with st.expander("Embedding 실패 상세", expanded=False):
                for error in result.embedding_result.errors[:30]:
                    st.error(error)
        st.rerun()


def _render_index_controls(project: Project) -> None:
    st.subheader("RAG 인덱싱")
    _render_source_index_status(project)
    st.divider()
    col1, col2, col3 = st.columns(3)
    chunk_size = col1.number_input("Chunk size", min_value=300, max_value=4000, value=DEFAULT_CHUNK_SIZE, step=100)
    overlap = col2.number_input("Overlap", min_value=0, max_value=500, value=DEFAULT_CHUNK_OVERLAP, step=50)
    limit = col3.number_input("Embedding 최대 처리 수", min_value=1, max_value=10000, value=500, step=100)
    source_types = _selected_source_types("인덱싱 대상", SOURCE_TYPE_OPTIONS)
    if "source_file" in source_types and not project.git_repo_path:
        st.warning("현재 소스 파일을 인덱싱하려면 프로젝트에 Git 저장소 경로가 필요합니다.")

    if st.button("RAG 인덱싱 실행", type="primary"):
        with st.spinner("현재 소스, 프로그램, 커밋, 변경 파일/diff를 chunk로 만들고 누락 embedding을 저장합니다."):
            chunk_result = _run_chunking(project, source_types, int(chunk_size), int(overlap))
            client, embedding_result = _run_embedding(project.id, source_types, int(limit))
        st.success(
            "인덱싱 완료: "
            f"chunk 신규 {chunk_result.created_count}건, chunk 중복 건너뜀 {chunk_result.skipped_count}건, "
            f"vector 신규 {embedding_result.created_count}건, vector 중복 건너뜀 {embedding_result.skipped_count}건, "
            f"embedding 실패 {embedding_result.failed_count}건"
        )
        st.caption(f"Embedding model: {client.embedding_model_name}")
        if embedding_result.errors:
            with st.expander("Embedding 실패 상세", expanded=False):
                for error in embedding_result.errors[:30]:
                    st.error(error)


def _render_chunk_controls(project: Project) -> None:
    st.subheader("Chunk 생성")
    col1, col2 = st.columns(2)
    chunk_size = col1.number_input("Chunk size", min_value=300, max_value=4000, value=DEFAULT_CHUNK_SIZE, step=100, key="chunk_size_only")
    overlap = col2.number_input("Overlap", min_value=0, max_value=500, value=DEFAULT_CHUNK_OVERLAP, step=50, key="overlap_only")
    source_types = _selected_source_types("Chunk 대상", SOURCE_TYPE_OPTIONS)
    if "source_file" in source_types and not project.git_repo_path:
        st.warning("현재 소스 파일을 chunk로 만들려면 프로젝트에 Git 저장소 경로가 필요합니다.")

    if not st.button("Chunk 생성", type="primary"):
        return

    result = _run_chunking(project, source_types, int(chunk_size), int(overlap))
    st.success(f"Chunk 생성 완료: 신규 {result.created_count}건, 중복 건너뜀 {result.skipped_count}건")


def _render_embedding_controls(project_id: int) -> None:
    st.subheader("Embedding 생성")
    st.caption(
        f"provider={settings.embedding_provider}, "
        f"base_url={settings.embedding_base_url or settings.llm_base_url or '미설정'}, "
        f"model={settings.embedding_model or '미설정'}, dimension={settings.pgvector_dimension}"
    )
    source_types = _selected_source_types("Embedding 대상 source_type", SOURCE_TYPE_OPTIONS)
    limit = st.number_input("이번 실행에서 처리할 최대 chunk 수", min_value=1, max_value=10000, value=500, step=100)

    col1, col2 = st.columns([1, 2])
    if col1.button("Embedding 연결 테스트"):
        client = EmbeddingClient()
        ok, message = client.test_connection()
        if ok:
            st.success(message)
        else:
            st.error(message)

    if not col2.button("Embedding 생성", type="primary"):
        return

    with st.spinner("누락 embedding을 생성합니다."):
        client, result = _run_embedding(project_id, source_types, int(limit))

    st.success(
        f"Embedding 완료: 신규 {result.created_count}건, 중복 건너뜀 {result.skipped_count}건, 실패 {result.failed_count}건"
    )
    st.caption(f"Embedding model: {client.embedding_model_name}")
    if result.errors:
        with st.expander("Embedding 실패 상세", expanded=False):
            for error in result.errors[:30]:
                st.error(error)


def _render_search(project: Project) -> None:
    st.subheader("검색 품질 확인")
    if "rag_search_query" not in st.session_state:
        st.session_state["rag_search_query"] = ""
    query = st.text_area(
        "검색어",
        placeholder="커밋 메시지, 파일 경로, diff 일부 또는 프로그램 설명을 입력하세요.",
        key="rag_search_query",
    )
    col1, col2 = st.columns(2)
    top_k = col1.slider("TOP K", min_value=1, max_value=50, value=10)
    source_types = _selected_source_types("source_type 필터", ["source_file"])

    if not st.button("검색", type="primary"):
        return
    query_text = st.session_state.get("rag_search_query", query).strip()
    if not query_text:
        st.warning("검색어를 입력하세요.")
        return

    with SessionLocal() as db:
        retriever = Retriever(db)
        try:
            results = retriever.retrieve(query_text, limit=top_k, project_id=project.id, source_types=source_types)
            results = [annotate_retrieval_result(result, project.git_repo_path) for result in results]
            model_name = retriever.embedding_client.embedding_model_name
        except Exception as exc:
            st.error(f"검색 실패: {exc}")
            return

    st.markdown(f"**검색어:** {query_text}")
    st.caption(f"Embedding model: {model_name}")
    if not results:
        st.info("검색 결과가 없습니다. RAG 인덱싱 또는 embedding 생성이 완료되었는지 확인하세요.")
        return

    rows = []
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        rows.append(
            {
                "rank": rank,
                "similarity": round(result["similarity"], 4),
                "distance": round(result["distance"], 4),
                "source": _format_source(result),
                "source_type": result["source_type"],
                "verification": VERIFICATION_LABELS.get(result.get("verification_status"), result.get("verification_status")),
                "source_id": result["source_id"],
                "chunk_index": result["chunk_index"],
                "program_id": metadata.get("program_id"),
                "commit_hash": metadata.get("commit_hash"),
                "file_path": metadata.get("file_path"),
                "line_start": metadata.get("line_start"),
                "line_end": metadata.get("line_end"),
                "preview": result["text"][:300],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("#### 조회된 chunk 목록")
    for rank, result in enumerate(results, start=1):
        title = (
            f"#{rank} score={result['similarity']:.4f} "
            f"{_format_source(result)} chunk={result['chunk_index']}"
        )
        with st.expander(title, expanded=rank <= 3):
            st.write(
                {
                    "source_type": result["source_type"],
                    "source_id": result["source_id"],
                    "chunk_index": result["chunk_index"],
                    "similarity": round(result["similarity"], 6),
                    "distance": round(result["distance"], 6),
                    "verification_status": result.get("verification_status"),
                    "verification_reason": result.get("verification_reason"),
                    "metadata": result["metadata"],
                }
            )
            st.text_area("원문 일부", value=result["text"][:2000], height=220, disabled=True, key=f"chunk_text_{result['id']}")


def _render_chat(project: Project) -> None:
    st.subheader("소스 검색 챗")
    st.caption("기본적으로 현재 파일에서 검증된 `source_file` chunk만 근거로 사용합니다.")
    question = st.text_area(
        "질문",
        placeholder="예: 매핑 피드백 저장 흐름이 어디에서 처리되는지 알려줘.",
        key="rag_chat_question",
    )
    col1, col2 = st.columns([1, 1])
    top_k = col1.slider("검색 TOP K", min_value=3, max_value=30, value=8, key="rag_chat_top_k")
    include_history = col2.checkbox("커밋 이력도 검색 후보에 포함", value=False)

    if not st.button("질문하기", type="primary"):
        return
    if not question.strip():
        st.warning("질문을 입력하세요.")
        return

    with SessionLocal() as db:
        current_project = db.get(Project, project.id)
        if current_project is None:
            st.error("프로젝트를 찾을 수 없습니다.")
            return
        with st.spinner("검증된 현재 소스 근거를 검색하고 답변을 생성합니다."):
            answer = answer_source_question(
                db,
                current_project,
                question.strip(),
                top_k=int(top_k),
                include_history=include_history,
            )

    if answer.errors:
        for error in answer.errors:
            st.error(error)
        return

    st.markdown("#### 답변")
    st.write(answer.answer)
    if answer.excluded_count:
        st.caption(f"검증되지 않았거나 현재 코드 근거가 아닌 chunk {answer.excluded_count}건은 답변 근거에서 제외했습니다.")

    if not answer.sources:
        return
    st.markdown("#### 검색 근거")
    rows = []
    for rank, source in enumerate(answer.sources, start=1):
        metadata = source.get("metadata") or {}
        rows.append(
            {
                "rank": rank,
                "similarity": round(source.get("similarity") or 0, 4),
                "source": _format_source(source),
                "verification": VERIFICATION_LABELS.get(source.get("verification_status"), source.get("verification_status")),
                "reason": source.get("verification_reason"),
                "preview": (source.get("text") or "")[:240],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_rag_page() -> None:
    st.title("RAG 검색")
    st.caption("프로그램 정보, 커밋 메시지, 변경 파일/diff를 chunk로 만들고 pgvector cosine 검색 품질을 확인합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록하세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]
    project = next(project for project in projects if project.id == project_id)

    _render_index_stats(project_id)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Index", "Chunk", "Embedding", "Search", "Chat"])
    with tab1:
        _render_index_controls(project)
    with tab2:
        _render_chunk_controls(project)
    with tab3:
        _render_embedding_controls(project_id)
    with tab4:
        _render_search(project)
    with tab5:
        _render_chat(project)

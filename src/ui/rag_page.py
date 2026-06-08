import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import DocumentChunk, Project, VectorItem
from src.rag.chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, build_project_chunks
from src.rag.embedding_client import EmbeddingClient
from src.rag.retriever import Retriever
from src.rag.vector_store import VectorStore
from src.utils.config import settings


SOURCE_TYPE_OPTIONS = ["program", "commit", "commit_file"]
SOURCE_TYPE_LABELS = {
    "program": "프로그램 정보",
    "commit": "커밋 메시지",
    "commit_file": "변경 파일/diff",
}


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _source_label(source_type: str) -> str:
    return SOURCE_TYPE_LABELS.get(source_type, source_type)


def _format_source(result: dict) -> str:
    metadata = result.get("metadata") or {}
    source_type = result.get("source_type")
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
    project_id: int,
    source_types: list[str],
    chunk_size: int,
    overlap: int,
):
    with SessionLocal() as db:
        return build_project_chunks(
            db,
            project_id=project_id,
            include_programs="program" in source_types,
            include_commits="commit" in source_types,
            include_commit_files="commit_file" in source_types,
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


def _render_index_controls(project_id: int) -> None:
    st.subheader("RAG 인덱싱")
    col1, col2, col3 = st.columns(3)
    chunk_size = col1.number_input("Chunk size", min_value=300, max_value=4000, value=DEFAULT_CHUNK_SIZE, step=100)
    overlap = col2.number_input("Overlap", min_value=0, max_value=500, value=DEFAULT_CHUNK_OVERLAP, step=50)
    limit = col3.number_input("Embedding 최대 처리 수", min_value=1, max_value=10000, value=500, step=100)
    source_types = _selected_source_types("인덱싱 대상", SOURCE_TYPE_OPTIONS)

    if st.button("RAG 인덱싱 실행", type="primary"):
        with st.spinner("프로그램, 커밋, 변경 파일/diff를 chunk로 만들고 누락 embedding을 저장합니다."):
            chunk_result = _run_chunking(project_id, source_types, int(chunk_size), int(overlap))
            client, embedding_result = _run_embedding(project_id, source_types, int(limit))
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


def _render_chunk_controls(project_id: int) -> None:
    st.subheader("Chunk 생성")
    col1, col2 = st.columns(2)
    chunk_size = col1.number_input("Chunk size", min_value=300, max_value=4000, value=DEFAULT_CHUNK_SIZE, step=100, key="chunk_size_only")
    overlap = col2.number_input("Overlap", min_value=0, max_value=500, value=DEFAULT_CHUNK_OVERLAP, step=50, key="overlap_only")
    source_types = _selected_source_types("Chunk 대상", SOURCE_TYPE_OPTIONS)

    if not st.button("Chunk 생성", type="primary"):
        return

    result = _run_chunking(project_id, source_types, int(chunk_size), int(overlap))
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


def _render_search(project_id: int) -> None:
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
    source_types = _selected_source_types("source_type 필터", ["program", "commit", "commit_file"])

    if not st.button("검색", type="primary"):
        return
    query_text = st.session_state.get("rag_search_query", query).strip()
    if not query_text:
        st.warning("검색어를 입력하세요.")
        return

    with SessionLocal() as db:
        retriever = Retriever(db)
        try:
            results = retriever.retrieve(query_text, limit=top_k, project_id=project_id, source_types=source_types)
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
                "source_id": result["source_id"],
                "chunk_index": result["chunk_index"],
                "program_id": metadata.get("program_id"),
                "commit_hash": metadata.get("commit_hash"),
                "file_path": metadata.get("file_path"),
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
                    "metadata": result["metadata"],
                }
            )
            st.text_area("원문 일부", value=result["text"][:2000], height=220, disabled=True, key=f"chunk_text_{result['id']}")


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

    _render_index_stats(project_id)

    tab1, tab2, tab3, tab4 = st.tabs(["Index", "Chunk", "Embedding", "Search"])
    with tab1:
        _render_index_controls(project_id)
    with tab2:
        _render_chunk_controls(project_id)
    with tab3:
        _render_embedding_controls(project_id)
    with tab4:
        _render_search(project_id)

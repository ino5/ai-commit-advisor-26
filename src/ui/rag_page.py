import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import DocumentChunk, Project, VectorItem
from src.rag.chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, build_project_chunks
from src.rag.embedding_client import EmbeddingClient
from src.rag.retriever import Retriever
from src.rag.vector_store import VectorStore


SOURCE_TYPE_OPTIONS = ["program", "commit", "commit_file"]


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _render_index_stats(project_id: int) -> None:
    with SessionLocal() as db:
        chunk_count = db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).count()
        vector_count = (
            db.query(VectorItem)
            .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
            .filter(DocumentChunk.project_id == project_id)
            .count()
        )
        source_rows = (
            db.query(DocumentChunk.source_type)
            .filter(DocumentChunk.project_id == project_id)
            .all()
        )

    source_counts = pd.Series([row[0] for row in source_rows]).value_counts().to_dict() if source_rows else {}
    col1, col2, col3 = st.columns(3)
    col1.metric("Chunks", chunk_count)
    col2.metric("Vectors", vector_count)
    col3.metric("Source types", len(source_counts))
    if source_counts:
        st.caption(", ".join(f"{key}: {value}" for key, value in source_counts.items()))


def _render_chunk_controls(project_id: int) -> None:
    st.subheader("Chunk 생성")
    col1, col2 = st.columns(2)
    chunk_size = col1.number_input("Chunk size", min_value=300, max_value=4000, value=DEFAULT_CHUNK_SIZE, step=100)
    overlap = col2.number_input("Overlap", min_value=0, max_value=500, value=DEFAULT_CHUNK_OVERLAP, step=50)
    source_types = st.multiselect("Chunk 대상", SOURCE_TYPE_OPTIONS, default=SOURCE_TYPE_OPTIONS)

    if not st.button("Chunk 생성", type="primary"):
        return

    with SessionLocal() as db:
        result = build_project_chunks(
            db,
            project_id=project_id,
            include_programs="program" in source_types,
            include_commits="commit" in source_types,
            include_commit_files="commit_file" in source_types,
            chunk_size=int(chunk_size),
            overlap=int(overlap),
        )
    st.success(f"Chunk 생성 완료: 신규 {result.created_count}건, 중복 건너뜀 {result.skipped_count}건")


def _render_embedding_controls(project_id: int) -> None:
    st.subheader("Embedding 생성")
    source_types = st.multiselect("Embedding 대상 source_type", SOURCE_TYPE_OPTIONS, default=SOURCE_TYPE_OPTIONS)
    limit = st.number_input("이번 실행에서 처리할 최대 chunk 수", min_value=1, max_value=10000, value=500, step=100)

    if not st.button("Embedding 생성", type="primary"):
        return

    with SessionLocal() as db:
        client = EmbeddingClient()
        store = VectorStore(db)
        with st.spinner(f"{client.embedding_model_name} embedding 생성 중입니다."):
            result = store.embed_missing_chunks(
                client,
                project_id=project_id,
                source_types=source_types,
                limit=int(limit),
            )

    st.success(f"Embedding 완료: 신규 {result.created_count}건, 중복 건너뜀 {result.skipped_count}건, 실패 {result.failed_count}건")
    if result.errors:
        with st.expander("Embedding 실패 상세", expanded=False):
            for error in result.errors[:30]:
                st.error(error)


def _render_search(project_id: int) -> None:
    st.subheader("검색 테스트")
    query = st.text_area("검색어", value="커밋 메시지, 파일 경로, diff 일부 또는 프로그램 설명을 입력하세요.")
    col1, col2 = st.columns(2)
    top_k = col1.slider("TOP K", min_value=1, max_value=50, value=10)
    source_types = col2.multiselect("source_type 필터", SOURCE_TYPE_OPTIONS, default=["program"])

    if not st.button("검색"):
        return

    with SessionLocal() as db:
        retriever = Retriever(db)
        try:
            results = retriever.retrieve(query, limit=top_k, project_id=project_id, source_types=source_types)
        except Exception as exc:
            st.error(f"검색 실패: {exc}")
            return

    if not results:
        st.info("검색 결과가 없습니다. chunk와 embedding을 먼저 생성했는지 확인하세요.")
        return

    rows = []
    for result in results:
        metadata = result["metadata"]
        rows.append(
            {
                "similarity": round(result["similarity"], 4),
                "source_type": result["source_type"],
                "source_id": result["source_id"],
                "chunk_index": result["chunk_index"],
                "program_id": metadata.get("program_id"),
                "program_name": metadata.get("program_name"),
                "commit_hash": metadata.get("commit_hash"),
                "file_path": metadata.get("file_path"),
                "text": result["text"][:500],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_rag_page() -> None:
    st.title("RAG")
    st.caption("programs, git_commits, commit_files 데이터를 chunk로 만들고 pgvector로 후보 검색을 테스트합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]

    _render_index_stats(project_id)

    tab1, tab2, tab3 = st.tabs(["Chunk", "Embedding", "Search"])
    with tab1:
        _render_chunk_controls(project_id)
    with tab2:
        _render_embedding_controls(project_id)
    with tab3:
        _render_search(project_id)

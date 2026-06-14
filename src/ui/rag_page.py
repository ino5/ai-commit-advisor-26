import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.models import DocumentChunk, Project, VectorItem
from src.rag.chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, build_project_chunks
from src.rag.chat_service import answer_source_question
from src.rag.embedding_client import EmbeddingClient
from src.rag.retriever import Retriever
from src.rag.source_index_service import (
    get_changed_source_files_since_latest_index,
    get_source_index_status,
    refresh_changed_source_files,
    refresh_source_file_index,
)
from src.rag.source_verifier import annotate_retrieval_result
from src.rag.vector_store import VectorStore
from src.ui.project_context import project_scoped_key, require_project_context
from src.utils.config import settings
from src.utils.runtime_estimator import estimate_runtime


SOURCE_TYPE_OPTIONS = ["source_file", "program", "commit", "commit_file"]
SOURCE_TYPE_LABELS = {
    "source_file": "현재 소스 파일",
    "program": "프로그램 정보",
    "commit": "커밋 메시지",
    "commit_file": "변경 파일/diff",
}

RAG_HELP = {
    "evidence_chunks": "질문 검색에 사용할 수 있도록 잘라 둔 근거 조각 수입니다.",
    "search_data": "근거 조각 중 질문과 유사도를 비교할 수 있도록 검색 준비가 끝난 데이터 수입니다.",
    "source_types": "검색 준비에 포함된 근거 종류 수입니다. 현재 소스, 프로그램 정보, 커밋 메시지 등이 포함될 수 있습니다.",
    "search_engine": "검색 준비를 만들 때 사용하는 embedding provider입니다. local_openai는 LM Studio 같은 로컬 서버를 뜻합니다.",
    "source_count": "현재 소스 파일에서 만들어 둔 Project Chat/RAG용 근거 수입니다.",
    "search_ready": "현재 소스 근거 중 검색 준비가 끝난 수입니다. 전체 수보다 작으면 `검색 준비` 탭에서 남은 작업을 실행하세요.",
    "code_status": "앱 서버 Git 저장소의 현재 코드가 소스 근거에 반영되어 있는지 보여줍니다.",
    "missing_ready": "소스 근거는 있지만 아직 검색 준비가 끝나지 않은 수입니다.",
    "refresh_changed": "Git 동기화 후 바뀐 파일만 빠르게 다시 읽습니다. 최신 commit 반영 직후에 적합합니다.",
    "refresh_all": "현재 소스를 전체 기준으로 다시 읽습니다. 처음 준비하거나 브랜치를 크게 바꿨을 때 사용합니다.",
    "search_after_refresh": "전체 소스 다시 읽기 직후 검색 준비까지 이어서 실행할지 선택합니다. PC 부하가 있을 수 있어 기본값은 꺼져 있습니다.",
    "chunk_size": "긴 파일을 검색 가능한 근거로 나눌 때 한 조각의 최대 길이입니다. 기본값을 먼저 사용하세요.",
    "overlap": "근거 조각을 나눌 때 앞뒤 조각이 일부 겹치도록 하는 길이입니다. 문맥이 끊기는 것을 줄입니다.",
    "limit": "이번 실행에서 검색 준비를 처리할 최대 근거 수입니다. 값이 작으면 PC 부하는 낮지만 여러 번 실행해야 할 수 있습니다.",
    "source_filter": "이번 작업에 포함할 근거 종류입니다. Project Chat 품질 확인은 보통 `현재 소스 파일`부터 준비합니다.",
    "run_all": "선택한 근거를 만들고 검색 준비까지 한 번에 실행합니다. 처음 준비할 때 사용합니다.",
    "run_evidence": "선택한 자료를 질문 검색에 사용할 근거 조각으로 만듭니다. 검색 준비는 별도 탭에서 실행할 수 있습니다.",
    "connection_test": "검색 준비 서버가 응답하는지 확인합니다. LM Studio 모델을 바꿨거나 서버를 새로 켰을 때 먼저 확인하세요.",
    "run_search_ready": "아직 검색 준비가 안 된 근거를 제한 수량만큼 처리합니다.",
    "top_k": "검색어와 가장 비슷한 근거를 최대 몇 개까지 보여줄지 정합니다. 값이 크면 더 넓게 찾지만 결과가 덜 집중될 수 있습니다.",
    "chat_top_k": "질문에 답할 때 후보로 가져올 소스 근거의 최대 개수입니다.",
    "include_history": "현재 소스뿐 아니라 과거 커밋 이력도 검색 후보에 포함합니다. 현재 코드 사실과 변경 이력은 구분해서 봐야 합니다.",
}

VERIFICATION_LABELS = {
    "verified": "현재 코드 검증됨",
    "stale": "인덱스 오래됨",
    "invalid": "검증 실패",
    "historical": "변경 이력",
    "not_applicable": "검증 대상 아님",
}
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
    col1.metric("근거 조각", chunk_count, help=RAG_HELP["evidence_chunks"])
    col2.metric("검색 데이터", vector_count, help=RAG_HELP["search_data"])
    col3.metric("근거 종류", len(source_counts), help=RAG_HELP["source_types"])
    col4.metric("검색 엔진", settings.embedding_provider, help=RAG_HELP["search_engine"])
    if source_counts:
        st.caption(", ".join(f"{_source_label(key)}: {value}" for key, value in source_counts.items()))


def _selected_source_types(
    label: str,
    default: list[str] | None = None,
    help_text: str | None = None,
    key: str | None = None,
) -> list[str]:
    labels = {SOURCE_TYPE_LABELS[value]: value for value in SOURCE_TYPE_OPTIONS}
    selected = st.multiselect(
        label,
        list(labels.keys()),
        default=[SOURCE_TYPE_LABELS[v] for v in (default or SOURCE_TYPE_OPTIONS)],
        help=help_text,
        key=key,
    )
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


def _embedding_workload(project_id: int, source_types: list[str]) -> tuple[EmbeddingClient, int]:
    with SessionLocal() as db:
        client = EmbeddingClient()
        pending_count = VectorStore(db).count_missing_chunks(
            client.embedding_model_name,
            project_id=project_id,
            source_types=source_types,
        )
        return client, pending_count


def _render_runtime_notice(work_type: str, pending_count: int, limit: int) -> None:
    run_count = min(max(0, int(pending_count or 0)), max(0, int(limit or 0)))
    estimate = estimate_runtime(run_count, work_type)
    st.info(
        f"남은 작업 {pending_count}건 중 이번 실행은 최대 {run_count}건을 처리합니다. "
        f"예상 소요 시간은 {estimate.label}입니다."
    )
    st.caption("실제 시간은 PC 성능, LM Studio 모델 상태, 현재 CPU/GPU 사용량에 따라 달라질 수 있습니다.")


def _render_source_index_status(project: Project) -> None:
    with SessionLocal() as db:
        current_project = db.get(Project, project.id)
        if current_project is None:
            st.error("프로젝트를 찾을 수 없습니다.")
            return
        status = get_source_index_status(db, current_project)

    st.markdown("#### 현재 소스 근거 상태")
    search_ready_count = max(status.source_chunk_count - status.missing_embedding_count, 0)
    code_status = "확인 필요" if status.needs_reindex else "최신"
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("소스 근거", status.source_chunk_count, help=RAG_HELP["source_count"])
    col2.metric("검색 준비", f"{search_ready_count}/{status.source_chunk_count}", help=RAG_HELP["search_ready"])
    col3.metric("코드 반영 상태", code_status, help=RAG_HELP["code_status"])
    col4.metric("추가 준비 필요", status.missing_embedding_count, help=RAG_HELP["missing_ready"])

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
    if status.indexed_head_hashes:
        with st.expander("인덱싱된 HEAD 종류", expanded=False):
            st.write([_short_hash(value) for value in status.indexed_head_hashes])

    for error in status.errors:
        st.warning(error)

    if st.button(
        "최신 변경분 반영",
        type="primary" if status.needs_reindex else "secondary",
        disabled=not bool(project.git_repo_path),
        help=RAG_HELP["refresh_changed"],
        key=project_scoped_key(project.id, "rag_refresh_changed"),
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
            with st.spinner("최신 변경 파일을 소스 근거에 반영하는 중입니다."):
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

    if status.needs_reindex:
        st.warning(
            "코드가 바뀐 뒤 소스 근거가 아직 최신 상태가 아닐 수 있습니다. "
            "최신 코드 기준 검색을 위해 변경분을 먼저 반영하세요."
        )
    elif status.source_chunk_count:
        st.success("현재 소스 근거가 등록된 Git 저장소 기준으로 확인되었습니다.")
    else:
        st.info("현재 소스 근거가 아직 없습니다.")

    embed_after_refresh = st.checkbox(
        "전체 소스 다시 읽은 뒤 검색 준비도 실행",
        value=False,
        help=RAG_HELP["search_after_refresh"],
        key=project_scoped_key(project.id, "rag_embed_after_refresh"),
    )
    refresh_embedding_limit = 0
    if embed_after_refresh:
        refresh_embedding_limit = st.number_input(
            "검색 준비 최대 처리 수",
            min_value=1,
            max_value=500,
            value=50,
            step=25,
            help="큰 저장소에서 PC가 느려지는 것을 막기 위해 한 번에 처리할 수를 제한합니다.",
            key=project_scoped_key(project.id, "rag_refresh_embedding_limit"),
        )
        _render_runtime_notice("embedding", status.source_chunk_count, int(refresh_embedding_limit))

    if st.button(
        "전체 소스 다시 읽기",
        type="secondary",
        disabled=not bool(project.git_repo_path),
        help=RAG_HELP["refresh_all"],
        key=project_scoped_key(project.id, "rag_refresh_all"),
    ):
        with SessionLocal() as db:
            current_project = db.get(Project, project.id)
            if current_project is None:
                st.error("프로젝트를 찾을 수 없습니다.")
                return
            with st.spinner("현재 코드 전체를 다시 읽어 소스 근거를 정리하는 중입니다. 검색 준비는 선택한 경우에만 제한 수량으로 실행합니다."):
                result = refresh_source_file_index(
                    db,
                    current_project,
                    embed_after_refresh=embed_after_refresh,
                    embedding_limit=int(refresh_embedding_limit or 0),
                )
        st.success(
            "전체 소스 다시 읽기 완료: "
            f"새 근거 {result.chunk_result.created_count}건, "
            f"오래된 근거 정리 {result.deleted_unverified_count}건, "
            f"검색 준비 {result.embedding_result.created_count}건, "
            f"실패 {result.embedding_result.failed_count}건"
        )
        if result.embedding_result.errors:
            with st.expander("검색 준비 실패 상세", expanded=False):
                for error in result.embedding_result.errors[:30]:
                    st.error(error)
        st.rerun()


def _render_index_controls(project: Project) -> None:
    st.subheader("한 번에 준비")
    _render_source_index_status(project)
    st.divider()
    col1, col2, col3 = st.columns(3)
    chunk_size = col1.number_input(
        "근거 조각 크기",
        min_value=300,
        max_value=4000,
        value=DEFAULT_CHUNK_SIZE,
        step=100,
        help=RAG_HELP["chunk_size"],
        key=project_scoped_key(project.id, "rag_all_chunk_size"),
    )
    overlap = col2.number_input(
        "겹치는 글자 수",
        min_value=0,
        max_value=500,
        value=DEFAULT_CHUNK_OVERLAP,
        step=50,
        help=RAG_HELP["overlap"],
        key=project_scoped_key(project.id, "rag_all_overlap"),
    )
    limit = col3.number_input(
        "검색 준비 최대 처리 수",
        min_value=1,
        max_value=10000,
        value=50,
        step=25,
        help=RAG_HELP["limit"],
        key=project_scoped_key(project.id, "rag_all_embedding_limit"),
    )
    source_types = _selected_source_types(
        "준비할 근거 종류",
        SOURCE_TYPE_OPTIONS,
        help_text=RAG_HELP["source_filter"],
        key=project_scoped_key(project.id, "rag_all_source_types"),
    )
    _, pending_count = _embedding_workload(project.id, source_types)
    _render_runtime_notice("embedding", pending_count, int(limit))
    if pending_count == 0:
        st.success("선택한 근거 종류의 검색 준비가 완료되어 있습니다. 다시 만들 필요가 있을 때만 실행하세요.")
    if "source_file" in source_types and not project.git_repo_path:
        st.warning("현재 소스 파일을 근거로 준비하려면 프로젝트에 앱 서버 Git 저장소 경로가 필요합니다.")

    if st.button(
        "근거 만들고 검색 준비 실행",
        type="secondary" if pending_count == 0 else "primary",
        help=RAG_HELP["run_all"],
        key=project_scoped_key(project.id, "rag_run_all"),
    ):
        with st.spinner("현재 소스, 프로그램, 커밋, 변경 파일/diff를 질문 검색에 사용할 근거로 준비하는 중입니다."):
            chunk_result = _run_chunking(project, source_types, int(chunk_size), int(overlap))
            client, embedding_result = _run_embedding(project.id, source_types, int(limit))
        st.success(
            "준비 완료: "
            f"새 근거 {chunk_result.created_count}건, 중복 근거 건너뜀 {chunk_result.skipped_count}건, "
            f"검색 준비 {embedding_result.created_count}건, 이미 준비됨 {embedding_result.skipped_count}건, "
            f"실패 {embedding_result.failed_count}건"
        )
        st.caption(f"검색 준비 모델: {client.embedding_model_name}")
        if embedding_result.errors:
            with st.expander("검색 준비 실패 상세", expanded=False):
                for error in embedding_result.errors[:30]:
                    st.error(error)


def _render_chunk_controls(project: Project) -> None:
    st.subheader("근거 만들기")
    col1, col2 = st.columns(2)
    chunk_size = col1.number_input(
        "근거 조각 크기",
        min_value=300,
        max_value=4000,
        value=DEFAULT_CHUNK_SIZE,
        step=100,
        key=project_scoped_key(project.id, "rag_chunk_size_only"),
        help=RAG_HELP["chunk_size"],
    )
    overlap = col2.number_input(
        "겹치는 글자 수",
        min_value=0,
        max_value=500,
        value=DEFAULT_CHUNK_OVERLAP,
        step=50,
        key=project_scoped_key(project.id, "rag_overlap_only"),
        help=RAG_HELP["overlap"],
    )
    source_types = _selected_source_types(
        "근거 대상",
        SOURCE_TYPE_OPTIONS,
        help_text=RAG_HELP["source_filter"],
        key=project_scoped_key(project.id, "rag_chunk_source_types"),
    )
    if "source_file" in source_types and not project.git_repo_path:
        st.warning("현재 소스 파일을 근거로 만들려면 프로젝트에 앱 서버 Git 저장소 경로가 필요합니다.")

    if not st.button(
        "근거 만들기",
        type="primary",
        help=RAG_HELP["run_evidence"],
        key=project_scoped_key(project.id, "rag_run_chunking"),
    ):
        return

    result = _run_chunking(project, source_types, int(chunk_size), int(overlap))
    st.success(f"근거 만들기 완료: 새 근거 {result.created_count}건, 중복 건너뜀 {result.skipped_count}건")


def _render_embedding_controls(project_id: int) -> None:
    st.subheader("검색 준비")
    st.caption(
        f"provider={settings.embedding_provider}, "
        f"base_url={settings.embedding_base_url or settings.llm_base_url or '미설정'}, "
        f"model={settings.embedding_model or '미설정'}, dimension={settings.pgvector_dimension}"
    )
    source_types = _selected_source_types(
        "검색 준비 대상",
        SOURCE_TYPE_OPTIONS,
        help_text=RAG_HELP["source_filter"],
        key=project_scoped_key(project_id, "rag_embedding_source_types"),
    )
    limit = st.number_input(
        "이번 실행에서 처리할 최대 근거 수",
        min_value=1,
        max_value=10000,
        value=50,
        step=25,
        help=RAG_HELP["limit"],
        key=project_scoped_key(project_id, "rag_embedding_limit"),
    )
    client_preview, pending_count = _embedding_workload(project_id, source_types)
    _render_runtime_notice("embedding", pending_count, int(limit))
    st.caption(f"검색 준비 모델: {client_preview.embedding_model_name}")

    col1, col2 = st.columns([1, 2])
    if col1.button(
        "검색 준비 연결 테스트",
        help=RAG_HELP["connection_test"],
        key=project_scoped_key(project_id, "rag_embedding_connection_test"),
    ):
        client = EmbeddingClient()
        ok, message = client.test_connection()
        if ok:
            st.success(message)
        else:
            st.error(message)

    if not col2.button(
        "검색 준비 실행",
        type="primary",
        help=RAG_HELP["run_search_ready"],
        key=project_scoped_key(project_id, "rag_run_embedding"),
    ):
        return

    with st.spinner("아직 검색 준비가 안 된 근거를 처리하는 중입니다."):
        client, result = _run_embedding(project_id, source_types, int(limit))

    st.success(
        f"검색 준비 완료: 신규 {result.created_count}건, 이미 준비됨 {result.skipped_count}건, 실패 {result.failed_count}건"
    )
    st.caption(f"검색 준비 모델: {client.embedding_model_name}")
    if result.errors:
        with st.expander("검색 준비 실패 상세", expanded=False):
            for error in result.errors[:30]:
                st.error(error)


def _render_search(project: Project) -> None:
    st.subheader("검색 품질 확인")
    query_key = project_scoped_key(project.id, "rag_search_query")
    if query_key not in st.session_state:
        st.session_state[query_key] = ""
    query = st.text_area(
        "검색어",
        placeholder="커밋 메시지, 파일 경로, diff 일부 또는 프로그램 설명을 입력하세요.",
        key=query_key,
    )
    col1, col2 = st.columns(2)
    top_k = col1.slider(
        "TOP K",
        min_value=1,
        max_value=50,
        value=10,
        help=RAG_HELP["top_k"],
        key=project_scoped_key(project.id, "rag_search_top_k"),
    )
    source_types = _selected_source_types(
        "근거 종류 필터",
        ["source_file"],
        help_text=RAG_HELP["source_filter"],
        key=project_scoped_key(project.id, "rag_search_source_types"),
    )

    if not st.button("검색", type="primary", key=project_scoped_key(project.id, "rag_search_button")):
        return
    query_text = st.session_state.get(query_key, query).strip()
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
    st.caption(f"검색 준비 모델: {model_name}")
    if not results:
        st.info("검색 결과가 없습니다. 근거 만들기와 검색 준비가 완료되었는지 확인하세요.")
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
                "근거 순번": result["chunk_index"],
                "program_id": metadata.get("program_id"),
                "commit_hash": metadata.get("commit_hash"),
                "file_path": metadata.get("file_path"),
                "line_start": metadata.get("line_start"),
                "line_end": metadata.get("line_end"),
                "preview": result["text"][:300],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("#### 조회된 근거 목록")
    for rank, result in enumerate(results, start=1):
        title = (
            f"#{rank} score={result['similarity']:.4f} "
            f"{_format_source(result)} 근거={result['chunk_index']}"
        )
        with st.expander(title, expanded=rank <= 3):
            st.write(
                {
                    "source_type": result["source_type"],
                    "source_id": result["source_id"],
                    "근거 순번": result["chunk_index"],
                    "similarity": round(result["similarity"], 6),
                    "distance": round(result["distance"], 6),
                    "verification_status": result.get("verification_status"),
                    "verification_reason": result.get("verification_reason"),
                    "metadata": result["metadata"],
                }
            )
            st.text_area(
                "원문 일부",
                value=result["text"][:2000],
                height=220,
                disabled=True,
                key=project_scoped_key(project.id, f"chunk_text_{result['id']}"),
            )


def _render_chat(project: Project) -> None:
    st.subheader("소스 검색 챗")
    st.caption("기본적으로 현재 파일에서 검증된 소스 근거만 사용합니다.")
    question = st.text_area(
        "질문",
        placeholder="예: 매핑 피드백 저장 흐름이 어디에서 처리되는지 알려줘.",
        key=project_scoped_key(project.id, "rag_chat_question"),
    )
    col1, col2 = st.columns([1, 1])
    top_k = col1.slider(
        "검색 TOP K",
        min_value=3,
        max_value=30,
        value=8,
        key=project_scoped_key(project.id, "rag_chat_top_k"),
        help=RAG_HELP["chat_top_k"],
    )
    include_history = col2.checkbox(
        "커밋 이력도 검색 후보에 포함",
        value=False,
        help=RAG_HELP["include_history"],
        key=project_scoped_key(project.id, "rag_chat_include_history"),
    )

    if not st.button("질문하기", type="primary", key=project_scoped_key(project.id, "rag_chat_submit")):
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
        st.caption(f"검증되지 않았거나 현재 코드 근거가 아닌 근거 {answer.excluded_count}건은 답변 근거에서 제외했습니다.")
    if answer.graph_evidence:
        st.markdown("#### 그래프 관계 근거")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "rank": rank,
                        "type": evidence.get("evidence_type") or "-",
                        "path": " -> ".join(str(part) for part in evidence.get("path") or [] if part),
                        "matched": ", ".join(str(seed) for seed in evidence.get("matched_seeds") or []) or "-",
                    }
                    for rank, evidence in enumerate(answer.graph_evidence, start=1)
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

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
    st.caption("현재 소스, 프로그램, 커밋 정보를 질문 검색에 사용할 근거로 준비하고 검색 품질을 확인합니다.")

    context = require_project_context("먼저 프로젝트를 등록하세요.")
    if context is None:
        return
    project_id = context.project_id
    project = Project(id=context.project_id, name=context.project_name, git_repo_path=context.git_repo_path)

    _render_index_stats(project_id)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["한 번에 준비", "근거 만들기", "검색 준비", "검색 확인", "소스 Q&A"])
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

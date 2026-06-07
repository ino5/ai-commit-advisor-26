import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import GitCommit, Program, Project
from src.services.mapping_service import (
    DEFAULT_CANDIDATES_PER_COMMIT,
    DEFAULT_CANDIDATES_PER_PROGRAM,
    CommitMappingProgress,
    MappingService,
)


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _commit_label(commit: GitCommit) -> str:
    short_hash = commit.commit_hash[:12]
    message = (commit.message or "").splitlines()[0]
    status = commit.mapping_analysis_status or "not_analyzed"
    committed_at = commit.committed_at.strftime("%Y-%m-%d %H:%M") if commit.committed_at else "-"
    return f"{short_hash} | {status} | {committed_at} | {message[:80]}"


def _load_commits(project_id: int) -> list[GitCommit]:
    with SessionLocal() as db:
        return (
            db.query(GitCommit)
            .filter(GitCommit.project_id == project_id)
            .order_by(GitCommit.committed_at.desc())
            .all()
        )


def _render_result(result) -> None:
    if result.errors:
        with st.expander("오류 상세", expanded=True):
            for error in result.errors[:20]:
                st.error(error)
            if len(result.errors) > 20:
                st.info(f"추가 오류 {len(result.errors) - 20}건은 analysis_runs 요약과 커밋 상태를 확인하세요.")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("분석 매핑", result.analyzed_count)
    col2.metric("신규 저장", result.created_count)
    col3.metric("업데이트", result.updated_count)
    col4.metric("건너뜀", result.skipped_count)
    col5.metric("실패 커밋", result.failed_count)

    if result.recent_results:
        st.subheader("최근 매핑 결과")
        st.dataframe(pd.DataFrame(result.recent_results), use_container_width=True)
    else:
        st.info("저장된 관련 매핑 결과가 없습니다.")


def _render_commit_based_mode(project_id: int) -> None:
    st.subheader("커밋 기준 분석")

    commits = _load_commits(project_id)
    if not commits:
        st.warning("분석할 Git 커밋이 없습니다.")
        return

    completed_count = sum(1 for commit in commits if commit.mapping_analysis_status == "completed")
    failed_count = sum(1 for commit in commits if commit.mapping_analysis_status == "failed")
    pending_count = len(commits) - completed_count - failed_count

    col1, col2, col3 = st.columns(3)
    col1.metric("미분석 커밋", pending_count)
    col2.metric("완료 커밋", completed_count)
    col3.metric("실패 커밋", failed_count)

    candidates_per_commit = st.slider(
        "커밋당 후보 프로그램 TOP N",
        min_value=3,
        max_value=30,
        value=DEFAULT_CANDIDATES_PER_COMMIT,
        help="커밋 1개마다 규칙/토큰 유사도로 후보 프로그램만 추린 뒤, 이 후보만 LLM에 전달합니다.",
    )

    commit_options = {_commit_label(commit): commit.id for commit in commits}
    selected_commit_label = st.selectbox("분석할 커밋 선택", list(commit_options.keys()))
    selected_commit_id = commit_options[selected_commit_label]

    single_col, batch_col = st.columns(2)
    run_single = single_col.button("선택한 커밋 1개 분석", type="primary")
    run_batch = batch_col.button("아직 완료되지 않은 커밋 일괄 분석")

    if not run_single and not run_batch:
        return

    progress_bar = st.progress(0)
    progress_text = st.empty()

    def update_progress(progress: CommitMappingProgress) -> None:
        ratio = progress.processed_count / progress.total_count if progress.total_count else 1
        progress_bar.progress(min(ratio, 1.0))
        current = progress.current_commit_hash[:12] if progress.current_commit_hash else "-"
        progress_text.write(
            f"진행률: {progress.processed_count}/{progress.total_count}, "
            f"실패: {progress.failed_count}, 현재 커밋: {current}"
        )

    with SessionLocal() as db:
        service = MappingService()
        with st.spinner("커밋 기준 매핑 분석을 실행 중입니다. 완료된 커밋은 재시작 시 건너뜁니다."):
            result = service.analyze_commits(
                db,
                project_id=project_id,
                commit_ids=[selected_commit_id] if run_single else None,
                candidates_per_commit=candidates_per_commit,
                skip_completed=not run_single,
                progress_callback=update_progress,
            )

    progress_bar.progress(1.0)
    progress_text.write("분석이 끝났습니다.")
    _render_result(result)


def _render_program_based_mode(project_id: int) -> None:
    st.subheader("프로그램 기준 분석")
    candidates_per_program = st.slider(
        "프로그램당 분석할 커밋 후보 수",
        min_value=1,
        max_value=30,
        value=min(DEFAULT_CANDIDATES_PER_PROGRAM, 5),
        help="기존 방식입니다. 프로그램별로 후보 커밋을 추리고 각 조합을 LLM으로 분석합니다.",
    )
    related_only = st.checkbox("관련 커밋으로 판단된 결과만 저장", value=False)

    if not st.button("프로그램 기준 매핑 분석 실행", type="primary"):
        return

    with SessionLocal() as db:
        service = MappingService()
        with st.spinner("프로그램별 후보 커밋을 분석하고 저장하는 중입니다."):
            result = service.analyze_project(
                db,
                project_id=project_id,
                candidates_per_program=candidates_per_program,
                related_only=related_only,
            )

    _render_result(result)


def render_mapping_page() -> None:
    st.title("프로그램-커밋 매핑 분석")
    st.caption("커밋 기준 분석을 기본 추천 방식으로 사용합니다. 기존 프로그램 기준 분석도 유지됩니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]

    with SessionLocal() as db:
        program_count = db.query(Program).filter(Program.project_id == project_id).count()
        commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()

    metric1, metric2 = st.columns(2)
    metric1.metric("프로그램 수", program_count)
    metric2.metric("Git 커밋 수", commit_count)

    if program_count == 0 or commit_count == 0:
        st.warning("분석하려면 프로그램 목록과 Git 커밋 데이터가 모두 필요합니다.")
        return

    mode = st.radio(
        "분석 모드",
        ["커밋 기준 분석", "프로그램 기준 분석"],
        index=0,
        horizontal=True,
    )

    if mode == "커밋 기준 분석":
        _render_commit_based_mode(project_id)
    else:
        _render_program_based_mode(project_id)

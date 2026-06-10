import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.git_service import is_git_repository, sync_git_repository


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _render_sync_result(result) -> None:
    if result.errors:
        for error in result.errors:
            st.error(error)
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("신규 저장 커밋", result.saved_commit_count)
    col2.metric("신규 저장 변경 파일", result.saved_file_count)
    col3.metric("건너뛴 중복 커밋", result.skipped_duplicate_count)

    st.write("최근 동기화 대상 커밋:", result.latest_commit_hash or "-")
    if result.recent_commits:
        st.subheader("최근 수집 커밋")
        st.dataframe(pd.DataFrame(result.recent_commits), use_container_width=True)
    else:
        st.info("이번 실행에서 새로 저장된 커밋이 없습니다.")


def render_git_page() -> None:
    st.title("Git")
    st.caption("프로젝트에 등록된 로컬 Git 저장소의 전체 커밋을 수집하고 이후 새 커밋만 증분 동기화합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트/Git 설정에서 프로젝트와 로컬 Git 저장소 경로를 등록해 주세요.")
        return

    options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(options.keys()))
    selected_project_id = options[selected_label]

    init_db()
    with SessionLocal() as db:
        project = db.get(Project, selected_project_id)
        if project is None:
            st.error("선택한 프로젝트를 찾을 수 없습니다.")
            return

        st.text_input("로컬 Git 저장소 경로", value=project.git_repo_path or "", disabled=True)
        st.write("마지막 동기화 커밋:", project.last_synced_commit_hash or "-")
        st.write("마지막 동기화 시각:", project.last_synced_at or "-")

        if not project.git_repo_path:
            st.warning("이 프로젝트에는 Git 저장소 경로가 등록되어 있지 않습니다.")
            return
        if not is_git_repository(project.git_repo_path):
            st.error("등록된 경로가 실제 Git 저장소가 아닙니다. 프로젝트/Git 설정에서 경로를 수정해 주세요.")
            return

        full_col, incremental_col = st.columns(2)
        run_full = full_col.button("전체 수집", type="primary")
        run_incremental = incremental_col.button("증분 동기화")

        if run_full:
            with st.spinner("전체 Git 커밋을 수집하는 중입니다."):
                result = sync_git_repository(db, project, full=True)
            _render_sync_result(result)
        elif run_incremental:
            with st.spinner("새로 추가된 Git 커밋만 동기화하는 중입니다."):
                result = sync_git_repository(db, project, full=False)
            _render_sync_result(result)

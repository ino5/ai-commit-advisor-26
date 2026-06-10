import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.git_service import is_git_repository


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def render_project_page() -> None:
    st.title("프로젝트/Git 설정")
    st.caption("프로젝트와 로컬 Git 저장소 경로를 등록합니다.")

    projects = _load_projects()
    project_options = ["새 프로젝트"] + [f"{project.id} - {project.name}" for project in projects]
    selected = st.selectbox("프로젝트 선택", project_options)
    selected_project = None
    if selected != "새 프로젝트":
        selected_id = int(selected.split(" - ", 1)[0])
        selected_project = next((project for project in projects if project.id == selected_id), None)

    with st.form("project_form"):
        name = st.text_input("프로젝트명", value=selected_project.name if selected_project else "")
        repo_path = st.text_input("로컬 Git 저장소 경로", value=selected_project.git_repo_path if selected_project else "")
        description = st.text_area("설명", value=selected_project.description if selected_project else "")
        submitted = st.form_submit_button("프로젝트 저장", type="primary")

    if not submitted:
        if selected_project:
            st.write("마지막 동기화 커밋:", selected_project.last_synced_commit_hash or "-")
            st.write("마지막 동기화 시각:", selected_project.last_synced_at or "-")
        return

    if not name.strip():
        st.error("프로젝트명을 입력해 주세요.")
        return
    if repo_path.strip() and not is_git_repository(repo_path.strip()):
        st.error("입력한 경로가 실제 Git 저장소가 아닙니다.")
        return

    init_db()
    with SessionLocal() as db:
        if selected_project:
            project = db.get(Project, selected_project.id)
        else:
            project = Project(name=name.strip())
            db.add(project)

        project.name = name.strip()
        project.git_repo_path = repo_path.strip() or None
        project.description = description.strip() or None
        db.commit()

    st.success("프로젝트를 저장했습니다.")

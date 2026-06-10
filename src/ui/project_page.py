import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.git_service import is_git_repository
from src.ui.project_context import CURRENT_PROJECT_ID_KEY, load_projects, set_current_project_id


def render_project_page() -> None:
    st.title("프로젝트/Git 설정")
    st.caption("프로젝트와 로컬 Git 저장소 경로를 등록합니다.")

    projects = load_projects()
    project_options = ["새 프로젝트"] + [f"{project.id} - {project.name}" for project in projects]
    current_project_id = st.session_state.get(CURRENT_PROJECT_ID_KEY)
    default_index = 0
    for index, option in enumerate(project_options):
        if option.startswith(f"{current_project_id} - "):
            default_index = index
            break
    selected = st.selectbox("프로젝트 선택", project_options, index=default_index)
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
        db.refresh(project)
        saved_project_id = int(project.id)

    set_current_project_id(saved_project_id)
    st.success("프로젝트를 저장했습니다.")

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project


CURRENT_PROJECT_ID_KEY = "current_project_id"


@dataclass(frozen=True)
class ProjectContext:
    project_id: int
    project_name: str
    git_repo_path: str | None
    description: str | None = None


def load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def set_current_project_id(project_id: int | None) -> None:
    if project_id is None:
        st.session_state.pop(CURRENT_PROJECT_ID_KEY, None)
    else:
        st.session_state[CURRENT_PROJECT_ID_KEY] = int(project_id)


def _to_context(project: Project) -> ProjectContext:
    return ProjectContext(
        project_id=int(project.id),
        project_name=project.name,
        git_repo_path=project.git_repo_path,
        description=project.description,
    )


def get_current_project_context() -> ProjectContext | None:
    projects = load_projects()
    if not projects:
        set_current_project_id(None)
        return None

    project_by_id = {int(project.id): project for project in projects}
    current_id = st.session_state.get(CURRENT_PROJECT_ID_KEY)
    if current_id not in project_by_id:
        current_id = int(projects[0].id)
        set_current_project_id(current_id)

    return _to_context(project_by_id[int(current_id)])


def require_project_context(message: str = "먼저 프로젝트를 등록하거나 선택해 주세요.") -> ProjectContext | None:
    context = get_current_project_context()
    if context is None:
        st.info(message)
        return None
    st.caption(f"현재 프로젝트: {context.project_name} ({context.project_id})")
    return context


def render_global_project_selector() -> ProjectContext | None:
    projects = load_projects()
    if not projects:
        set_current_project_id(None)
        st.sidebar.info("등록된 프로젝트가 없습니다.")
        return None

    project_ids = [int(project.id) for project in projects]
    labels = {int(project.id): f"{project.name} ({project.id})" for project in projects}
    current_id = st.session_state.get(CURRENT_PROJECT_ID_KEY)
    if current_id not in project_ids:
        current_id = project_ids[0]
        set_current_project_id(current_id)

    selected_id = st.sidebar.selectbox(
        "현재 프로젝트",
        project_ids,
        index=project_ids.index(int(current_id)),
        format_func=lambda project_id: labels[int(project_id)],
    )
    if int(selected_id) != int(current_id):
        set_current_project_id(int(selected_id))

    selected_project = next(project for project in projects if int(project.id) == int(selected_id))
    return _to_context(selected_project)

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project


CURRENT_PROJECT_ID_KEY = "current_project_id"
CURRENT_PROJECT_QUERY_PARAM = "project_id"


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


def _parse_project_id(value) -> int | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_query_project_id() -> int | None:
    query_params = getattr(st, "query_params", None)
    if query_params is None:
        return None
    try:
        return _parse_project_id(query_params.get(CURRENT_PROJECT_QUERY_PARAM))
    except AttributeError:
        return None


def _write_query_project_id(project_id: int | None) -> None:
    query_params = getattr(st, "query_params", None)
    if query_params is None:
        return
    if project_id is None:
        try:
            query_params.pop(CURRENT_PROJECT_QUERY_PARAM, None)
        except AttributeError:
            try:
                del query_params[CURRENT_PROJECT_QUERY_PARAM]
            except (KeyError, TypeError):
                pass
        return
    query_params[CURRENT_PROJECT_QUERY_PARAM] = str(int(project_id))


def set_current_project_id(project_id: int | None) -> None:
    if project_id is None:
        st.session_state.pop(CURRENT_PROJECT_ID_KEY, None)
    else:
        st.session_state[CURRENT_PROJECT_ID_KEY] = int(project_id)
    _write_query_project_id(project_id)


def _resolve_current_project_id(project_ids: list[int]) -> int | None:
    if not project_ids:
        return None

    query_id = _read_query_project_id()
    if query_id in project_ids:
        set_current_project_id(query_id)
        return query_id

    current_id = st.session_state.get(CURRENT_PROJECT_ID_KEY)
    if current_id in project_ids:
        _write_query_project_id(int(current_id))
        return int(current_id)

    current_id = project_ids[0]
    set_current_project_id(current_id)
    return current_id


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
    current_id = _resolve_current_project_id(list(project_by_id.keys()))

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
    current_id = _resolve_current_project_id(project_ids)

    selected_id = st.sidebar.selectbox(
        "현재 프로젝트",
        project_ids,
        index=project_ids.index(int(current_id)),
        format_func=lambda project_id: labels[int(project_id)],
        help="현재 화면에서 조회, 분석, 질문에 사용할 프로젝트입니다. 화면을 바꾸어도 이 선택이 유지됩니다.",
    )
    if int(selected_id) != int(current_id):
        set_current_project_id(int(selected_id))

    selected_project = next(project for project in projects if int(project.id) == int(selected_id))
    return _to_context(selected_project)

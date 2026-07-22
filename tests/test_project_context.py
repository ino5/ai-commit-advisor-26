from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from src.ui import project_context


class FakeSidebar:
    def __init__(self, owner):
        self.owner = owner
        self.next_selection = None

    def info(self, message):
        self.owner.messages.append(("sidebar_info", message))

    def selectbox(self, _label, options, *, key, on_change, **_kwargs):
        if self.next_selection is not None:
            self.owner.session_state[key] = self.next_selection
            self.next_selection = None
            on_change()
        return self.owner.session_state.get(key, options[0])


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.query_params = {}
        self.messages = []
        self.sidebar = FakeSidebar(self)

    def info(self, message):
        self.messages.append(("info", message))

    def caption(self, message):
        self.messages.append(("caption", message))


def _project(project_id: int, name: str):
    return SimpleNamespace(id=project_id, name=name, git_repo_path=None, description=None)


def test_get_current_project_context_keeps_valid_selection(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 2
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [_project(1, "Alpha"), _project(2, "Beta")])

    context = project_context.get_current_project_context()

    assert context is not None
    assert context.project_id == 2
    assert context.project_name == "Beta"
    assert fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] == 2


def test_get_current_project_context_recovers_invalid_selection(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 99
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [_project(1, "Alpha"), _project(2, "Beta")])

    context = project_context.get_current_project_context()

    assert context is not None
    assert context.project_id == 1
    assert context.project_name == "Alpha"
    assert fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] == 1
    assert fake_st.query_params == {}


def test_get_current_project_context_ignores_query_project(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 1
    fake_st.query_params["project_id"] = "2"
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [_project(1, "Alpha"), _project(2, "Beta")])

    context = project_context.get_current_project_context()

    assert context is not None
    assert context.project_id == 1
    assert context.project_name == "Alpha"
    assert fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] == 1
    assert fake_st.query_params["project_id"] == "2"


def test_set_current_project_id_does_not_modify_query_when_cleared(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 2
    fake_st.query_params["project_id"] = "2"
    monkeypatch.setattr(project_context, "st", fake_st)

    project_context.set_current_project_id(None)

    assert project_context.CURRENT_PROJECT_ID_KEY not in fake_st.session_state
    assert fake_st.query_params["project_id"] == "2"


def test_get_current_project_context_clears_selection_when_no_projects(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 2
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [])

    context = project_context.get_current_project_context()

    assert context is None
    assert project_context.CURRENT_PROJECT_ID_KEY not in fake_st.session_state


def test_render_global_project_selector_applies_first_selection(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 1
    fake_st.sidebar.next_selection = 2
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [_project(1, "Alpha"), _project(2, "Beta")])

    context = project_context.render_global_project_selector()

    assert context is not None
    assert context.project_id == 2
    assert context.project_name == "Beta"
    assert fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] == 2
    assert fake_st.session_state[project_context.CURRENT_PROJECT_SELECTOR_KEY] == 2


def test_render_global_project_selector_syncs_programmatic_project_change(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 1
    fake_st.session_state[project_context.CURRENT_PROJECT_SELECTOR_KEY] = 1
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [_project(1, "Alpha"), _project(2, "Beta")])

    project_context.set_current_project_id(2)
    context = project_context.render_global_project_selector()

    assert context is not None
    assert context.project_id == 2
    assert fake_st.session_state[project_context.CURRENT_PROJECT_SELECTOR_KEY] == 2


def test_streamlit_selector_applies_first_selection_without_second_attempt():
    app = AppTest.from_string(
        """
from types import SimpleNamespace
import streamlit as st
from src.ui import project_context

project_context.load_projects = lambda: [
    SimpleNamespace(id=1, name="Alpha", git_repo_path=None, description=None),
    SimpleNamespace(id=2, name="Beta", git_repo_path=None, description=None),
]
context = project_context.render_global_project_selector()
st.caption(f"selected:{context.project_id}")
"""
    )

    app.run()
    app.sidebar.selectbox[0].select(2)
    app.run()

    assert not app.exception
    assert app.sidebar.selectbox[0].value == 2
    assert [caption.value for caption in app.caption] == ["selected:2"]
    assert dict(app.query_params) == {}


def test_project_scoped_key_includes_project_id():
    assert project_context.project_scoped_key(7, "program_select") == "project_7_program_select"
    assert project_context.project_scoped_key("8", "commit_filter") == "project_8_commit_filter"

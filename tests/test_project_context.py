from types import SimpleNamespace

from src.ui import project_context


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.query_params = {}
        self.messages = []

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
    assert fake_st.query_params[project_context.CURRENT_PROJECT_QUERY_PARAM] == "1"


def test_get_current_project_context_restores_query_project(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.query_params[project_context.CURRENT_PROJECT_QUERY_PARAM] = "2"
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [_project(1, "Alpha"), _project(2, "Beta")])

    context = project_context.get_current_project_context()

    assert context is not None
    assert context.project_id == 2
    assert context.project_name == "Beta"
    assert fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] == 2
    assert fake_st.query_params[project_context.CURRENT_PROJECT_QUERY_PARAM] == "2"


def test_set_current_project_id_removes_query_when_cleared(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 2
    fake_st.query_params[project_context.CURRENT_PROJECT_QUERY_PARAM] = "2"
    monkeypatch.setattr(project_context, "st", fake_st)

    project_context.set_current_project_id(None)

    assert project_context.CURRENT_PROJECT_ID_KEY not in fake_st.session_state
    assert project_context.CURRENT_PROJECT_QUERY_PARAM not in fake_st.query_params


def test_get_current_project_context_clears_selection_when_no_projects(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 2
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [])

    context = project_context.get_current_project_context()

    assert context is None
    assert project_context.CURRENT_PROJECT_ID_KEY not in fake_st.session_state
    assert project_context.CURRENT_PROJECT_QUERY_PARAM not in fake_st.query_params


def test_project_scoped_key_includes_project_id():
    assert project_context.project_scoped_key(7, "program_select") == "project_7_program_select"
    assert project_context.project_scoped_key("8", "commit_filter") == "project_8_commit_filter"

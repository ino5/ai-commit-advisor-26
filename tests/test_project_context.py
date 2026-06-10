from types import SimpleNamespace

from src.ui import project_context


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
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


def test_get_current_project_context_clears_selection_when_no_projects(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state[project_context.CURRENT_PROJECT_ID_KEY] = 2
    monkeypatch.setattr(project_context, "st", fake_st)
    monkeypatch.setattr(project_context, "load_projects", lambda: [])

    context = project_context.get_current_project_context()

    assert context is None
    assert project_context.CURRENT_PROJECT_ID_KEY not in fake_st.session_state

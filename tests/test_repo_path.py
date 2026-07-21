from pathlib import Path

from src.utils import repo_path


def test_resolve_repo_path_maps_windows_host_prefix(monkeypatch):
    monkeypatch.setattr(repo_path.settings, "repo_path_host_prefix", r"C:\dev")
    monkeypatch.setattr(repo_path.settings, "repo_path_container_prefix", "/host-dev")

    resolved = repo_path.resolve_repo_path(r"C:\dev\ai-advisor-sample-shop")

    assert resolved == Path("/host-dev/ai-advisor-sample-shop").resolve()


def test_resolve_repo_path_prefers_managed_mapping_over_read_only_parent(monkeypatch):
    monkeypatch.setattr(repo_path.settings, "repo_path_host_prefix", r"C:\dev")
    monkeypatch.setattr(repo_path.settings, "repo_path_container_prefix", "/host-dev")
    monkeypatch.setattr(repo_path.settings, "managed_repo_storage_root", r"C:\dev\managed-repos")
    monkeypatch.setattr(repo_path.settings, "managed_repo_container_prefix", "/managed-repos")

    resolved = repo_path.resolve_repo_path(r"C:\dev\managed-repos\project-7")

    assert resolved == Path("/managed-repos/project-7").resolve()


def test_resolve_repo_path_leaves_unmapped_path(monkeypatch, tmp_path):
    monkeypatch.setattr(repo_path.settings, "repo_path_host_prefix", None)
    monkeypatch.setattr(repo_path.settings, "repo_path_container_prefix", None)

    resolved = repo_path.resolve_repo_path(tmp_path)

    assert resolved == tmp_path.resolve()


def test_repo_path_allowed_when_storage_root_is_unset(monkeypatch, tmp_path):
    monkeypatch.setattr(repo_path.settings, "repo_storage_root", None)

    assert repo_path.is_repo_path_allowed(tmp_path)


def test_repo_path_allowed_under_storage_root(monkeypatch):
    monkeypatch.setattr(repo_path.settings, "repo_storage_root", r"C:\dev\repos")

    assert repo_path.is_repo_path_allowed(r"C:\dev\repos\order-system")


def test_repo_path_rejected_outside_storage_root(monkeypatch):
    monkeypatch.setattr(repo_path.settings, "repo_storage_root", r"C:\dev\repos")

    assert not repo_path.is_repo_path_allowed(r"C:\dev\other-system")


def test_repo_path_rejects_parent_traversal_outside_storage_root(monkeypatch):
    monkeypatch.setattr(repo_path.settings, "repo_storage_root", r"C:\dev")

    assert not repo_path.is_repo_path_allowed(r"C:\dev\..\Windows")


def test_repo_path_allows_separate_managed_storage_root(monkeypatch):
    monkeypatch.setattr(repo_path.settings, "repo_storage_root", "/srv/read-only-repos")
    monkeypatch.setattr(repo_path.settings, "managed_repo_storage_root", "/srv/managed-repos")

    assert repo_path.is_repo_path_allowed("/srv/managed-repos/project-9")
    assert repo_path.is_managed_repo_path("/srv/managed-repos/project-9")


def test_build_managed_repo_path_uses_project_id(monkeypatch):
    monkeypatch.setattr(repo_path.settings, "managed_repo_storage_root", r"C:\dev\managed-repos")

    assert repo_path.build_managed_repo_path(42) == r"C:\dev\managed-repos\project-42"

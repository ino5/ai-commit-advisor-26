from __future__ import annotations

import subprocess
from pathlib import Path

from src.db.models import Project
from src.services.git_repository_status_service import get_repository_status


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _create_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "status@example.local")
    _git(repo, "config", "user.name", "Status Tester")
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")
    return repo, _git(repo, "rev-parse", "HEAD")


def test_repository_status_clean_repo_matches_db_sync(tmp_path: Path):
    repo, head = _create_repo(tmp_path)
    project = Project(name="status", git_repo_path=str(repo), last_synced_commit_hash=head)

    status = get_repository_status(project)

    assert status.is_repository is True
    assert status.head_hash == head
    assert status.db_matches_head is True
    assert status.has_local_changes is False
    assert status.dirty_file_count == 0
    assert status.errors == []


def test_repository_status_reports_dirty_and_db_mismatch(tmp_path: Path):
    repo, _head = _create_repo(tmp_path)
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    project = Project(name="status", git_repo_path=str(repo), last_synced_commit_hash="old")

    status = get_repository_status(project)

    assert status.is_repository is True
    assert status.db_matches_head is False
    assert status.has_local_changes is True
    assert status.dirty_file_count == 1


def test_repository_status_reports_missing_path():
    project = Project(name="missing", git_repo_path="Z:/path/that/does/not/exist")

    status = get_repository_status(project)

    assert status.is_repository is False
    assert status.errors


def test_repository_status_reports_upstream_ahead_behind(tmp_path: Path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
    local = tmp_path / "local"
    subprocess.run(["git", "clone", str(remote), str(local)], check=True, capture_output=True, text=True)
    _git(local, "config", "user.email", "status@example.local")
    _git(local, "config", "user.name", "Status Tester")
    (local / "README.md").write_text("initial\n", encoding="utf-8")
    _git(local, "add", ".")
    _git(local, "commit", "-m", "Initial commit")
    _git(local, "push", "-u", "origin", "main")

    (local / "local.txt").write_text("local\n", encoding="utf-8")
    _git(local, "add", ".")
    _git(local, "commit", "-m", "Local commit")

    project = Project(name="upstream", git_repo_path=str(local), last_synced_commit_hash=None)

    status = get_repository_status(project)

    assert status.upstream == "origin/main"
    assert status.ahead_count == 1
    assert status.behind_count == 0

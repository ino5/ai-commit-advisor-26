from __future__ import annotations

import subprocess
from pathlib import Path

from src.db.models import Project
from src.services.git_remote_service import clone_or_update_project_repository, validate_git_remote_url_for_storage


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _make_remote(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    remote = tmp_path / "remote.git"
    source.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.email", "test@example.local")
    _git(source, "config", "user.name", "Test User")
    (source / "README.md").write_text("one\n", encoding="utf-8")
    _git(source, "add", "README.md")
    _git(source, "commit", "-m", "Initial")
    _git(tmp_path, "clone", "--bare", str(source), str(remote))
    _git(source, "remote", "add", "origin", str(remote))
    return source, remote


def _push_commit(source: Path, text: str, message: str) -> str:
    (source / "README.md").write_text(text, encoding="utf-8")
    _git(source, "add", "README.md")
    _git(source, "commit", "-m", message)
    _git(source, "push", "origin", "main")
    return _git(source, "rev-parse", "HEAD")


def test_clone_or_update_project_repository_clones_and_updates(tmp_path: Path):
    source, remote = _make_remote(tmp_path)
    repo_path = tmp_path / "managed"
    project = Project(
        name="Managed",
        git_repo_path=str(repo_path),
        git_remote_url=str(remote),
        git_branch="main",
    )

    cloned = clone_or_update_project_repository(project)

    assert cloned.status == "cloned"
    assert str(remote) not in "\n".join(cloned.messages)
    assert repo_path.exists()
    assert _git(repo_path, "rev-parse", "--abbrev-ref", "HEAD") == "main"

    expected_head = _push_commit(source, "two\n", "Update")
    updated = clone_or_update_project_repository(project)

    assert updated.status == "updated"
    assert updated.head_after == expected_head
    assert (repo_path / "README.md").read_text(encoding="utf-8") == "two\n"


def test_clone_or_update_project_repository_skips_dirty_reset(tmp_path: Path):
    source, remote = _make_remote(tmp_path)
    repo_path = tmp_path / "managed"
    project = Project(
        name="Managed",
        git_repo_path=str(repo_path),
        git_remote_url=str(remote),
        git_branch="main",
    )
    clone_or_update_project_repository(project)
    (repo_path / "README.md").write_text("local change\n", encoding="utf-8")
    _push_commit(source, "remote change\n", "Remote update")

    result = clone_or_update_project_repository(project)

    assert result.status == "skipped"
    assert result.errors
    assert (repo_path / "README.md").read_text(encoding="utf-8") == "local change\n"


def test_clone_or_update_project_repository_force_resets_dirty_tree(tmp_path: Path):
    source, remote = _make_remote(tmp_path)
    repo_path = tmp_path / "managed"
    project = Project(
        name="Managed",
        git_repo_path=str(repo_path),
        git_remote_url=str(remote),
        git_branch="main",
    )
    clone_or_update_project_repository(project)
    (repo_path / "README.md").write_text("local change\n", encoding="utf-8")
    _push_commit(source, "remote change\n", "Remote update")

    result = clone_or_update_project_repository(project, force_reset=True)

    assert result.status == "updated"
    assert (repo_path / "README.md").read_text(encoding="utf-8") == "remote change\n"


def test_clone_or_update_project_repository_rejects_https_remote_credentials(tmp_path: Path):
    repo_path = tmp_path / "managed"
    secret_remote = "https://token@example.com/org/repo.git"
    project = Project(
        name="Managed",
        git_repo_path=str(repo_path),
        git_remote_url=secret_remote,
        git_branch="main",
    )

    result = clone_or_update_project_repository(project)

    assert result.status == "failed"
    assert result.errors
    assert "token" not in "\n".join(result.errors)
    assert "인증 설정" in result.errors[0]
    assert not repo_path.exists()


def test_validate_git_remote_url_allows_ssh_user_without_password():
    assert validate_git_remote_url_for_storage("git@github.com:org/repo.git") is None
    assert validate_git_remote_url_for_storage("ssh://git@github.com/org/repo.git") is None
    assert validate_git_remote_url_for_storage("ssh://git:secret@github.com/org/repo.git") is not None

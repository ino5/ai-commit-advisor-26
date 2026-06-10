from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from src.db.models import Project
from src.utils.repo_path import is_repo_path_allowed, repo_storage_root_label, resolve_repo_path


@dataclass
class GitRepositoryStatus:
    configured_path: str | None
    resolved_path: str | None = None
    storage_root: str | None = None
    path_allowed: bool = True
    is_repository: bool = False
    branch: str | None = None
    head_hash: str | None = None
    upstream: str | None = None
    ahead_count: int | None = None
    behind_count: int | None = None
    dirty_file_count: int = 0
    has_local_changes: bool = False
    db_last_synced_commit_hash: str | None = None
    db_matches_head: bool | None = None
    errors: list[str] = field(default_factory=list)


def _run_git(repo_path: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={repo_path.as_posix()}", *args],
        cwd=repo_path,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_output(repo_path: Path, args: list[str], *, check: bool = True) -> str | None:
    result = _run_git(repo_path, args, check=check)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _parse_ahead_behind(value: str | None) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    parts = value.split()
    if len(parts) != 2:
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None


def get_repository_status(project: Project) -> GitRepositoryStatus:
    status = GitRepositoryStatus(
        configured_path=project.git_repo_path,
        storage_root=repo_storage_root_label(),
        db_last_synced_commit_hash=project.last_synced_commit_hash,
    )

    if not project.git_repo_path:
        status.errors.append("앱 서버 Git 저장소 경로가 등록되어 있지 않습니다.")
        status.path_allowed = False
        return status

    status.path_allowed = is_repo_path_allowed(project.git_repo_path)
    if not status.path_allowed:
        status.errors.append("등록된 Git 저장소 경로가 허용된 저장소 루트 밖에 있습니다.")

    try:
        resolved_path = resolve_repo_path(project.git_repo_path)
        status.resolved_path = str(resolved_path)
    except Exception as exc:
        status.errors.append(f"저장소 경로 변환 실패: {exc}")
        return status

    if not resolved_path.exists():
        status.errors.append("앱 서버에서 저장소 경로를 찾을 수 없습니다.")
        return status

    inside = _git_output(resolved_path, ["rev-parse", "--is-inside-work-tree"], check=False)
    if inside != "true":
        status.errors.append("앱 서버에서 등록된 경로를 Git 저장소로 확인할 수 없습니다.")
        return status

    status.is_repository = True
    status.branch = _git_output(resolved_path, ["branch", "--show-current"], check=False)
    status.head_hash = _git_output(resolved_path, ["rev-parse", "HEAD"], check=False)
    status.upstream = _git_output(resolved_path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], check=False)

    dirty_output = _git_output(resolved_path, ["status", "--porcelain"], check=False) or ""
    dirty_lines = [line for line in dirty_output.splitlines() if line.strip()]
    status.dirty_file_count = len(dirty_lines)
    status.has_local_changes = bool(dirty_lines)

    if status.upstream:
        counts = _git_output(resolved_path, ["rev-list", "--left-right", "--count", "HEAD...@{u}"], check=False)
        status.ahead_count, status.behind_count = _parse_ahead_behind(counts)

    if status.head_hash and status.db_last_synced_commit_hash:
        status.db_matches_head = status.head_hash == status.db_last_synced_commit_hash
    elif status.head_hash:
        status.db_matches_head = False

    return status

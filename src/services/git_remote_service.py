from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from src.db.models import Project
from src.services.git_service import get_head_commit_hash, is_git_repository
from src.utils.config import settings
from src.utils.repo_path import is_managed_repo_path, is_repo_path_allowed, resolve_repo_path


@dataclass(frozen=True)
class RemoteSyncResult:
    status: str
    repo_path: str
    branch: str | None = None
    head_before: str | None = None
    head_after: str | None = None
    messages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_git_remote_url_for_storage(remote_url: str) -> str | None:
    normalized = remote_url.strip()
    if not normalized:
        return None

    parsed = urlsplit(normalized)
    if parsed.password:
        return "Git remote URL에 password를 포함할 수 없습니다. 서버 OS의 Git 인증 설정을 사용하세요."
    if parsed.scheme in {"http", "https"} and parsed.username:
        return "HTTPS Git remote URL에 인증정보를 포함할 수 없습니다. 서버 OS의 Git 인증 설정을 사용하세요."
    return None


def validate_managed_git_remote_url_for_storage(remote_url: str) -> str | None:
    validation_error = validate_git_remote_url_for_storage(remote_url)
    if validation_error:
        return validation_error

    normalized = remote_url.strip()
    if not normalized:
        return "Git remote URL을 입력해 주세요."

    parsed = urlsplit(normalized)
    if parsed.scheme != "https" or not parsed.hostname:
        return "관리형 저장소는 공개 HTTPS Git URL만 사용할 수 있습니다."
    if parsed.query or parsed.fragment:
        return "관리형 Git remote URL에는 query parameter나 fragment를 포함할 수 없습니다."

    allowed_hosts = {
        host.strip().lower()
        for host in settings.managed_git_allowed_hosts.split(",")
        if host.strip()
    }
    if parsed.hostname.lower() not in allowed_hosts:
        allowed_label = ", ".join(sorted(allowed_hosts)) or "설정된 host 없음"
        return f"관리형 저장소에 허용되지 않은 Git host입니다. 허용 host: {allowed_label}"
    return None


class RepositorySyncLock:
    def __init__(self, repo_path: Path):
        self.lock_path = repo_path.parent / f".{repo_path.name}.sync.lock"
        self._fd: int | None = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self._fd, str(os.getpid()).encode("utf-8"))
        except FileExistsError as exc:
            raise RuntimeError(f"Repository sync is already running: {self.lock_path}") from exc
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def _run_git(repo_path: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", "-c", f"safe.directory={repo_path.as_posix()}", *args],
        cwd=repo_path,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=max(settings.git_operation_timeout_seconds, 1),
    )


def _run_git_parent(parent: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", *args],
        cwd=parent,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=max(settings.git_operation_timeout_seconds, 1),
    )


def _git_output(repo_path: Path, args: list[str], *, check: bool = True) -> str:
    return _run_git(repo_path, args, check=check).stdout.strip()


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def clone_or_update_project_repository(project: Project, *, force_reset: bool = False) -> RemoteSyncResult:
    if not project.git_repo_path:
        return RemoteSyncResult(status="failed", repo_path="", errors=["앱 서버 Git 저장소 경로가 필요합니다."])
    if not project.git_remote_url:
        return RemoteSyncResult(
            status="failed",
            repo_path=project.git_repo_path,
            errors=["Git remote URL이 필요합니다."],
        )
    if not is_repo_path_allowed(project.git_repo_path):
        return RemoteSyncResult(
            status="failed",
            repo_path=project.git_repo_path,
            errors=["Git 저장소 경로가 허용된 저장소 루트 밖에 있습니다."],
        )

    repo_path = resolve_repo_path(project.git_repo_path)
    branch = (project.git_branch or "main").strip() or "main"
    remote_url = project.git_remote_url.strip()
    if is_managed_repo_path(project.git_repo_path):
        validation_error = validate_managed_git_remote_url_for_storage(remote_url)
    else:
        validation_error = validate_git_remote_url_for_storage(remote_url)
    if validation_error:
        return RemoteSyncResult(
            status="failed",
            repo_path=project.git_repo_path,
            branch=branch,
            errors=[validation_error],
        )

    messages: list[str] = []

    try:
        with RepositorySyncLock(repo_path):
            if not repo_path.exists():
                args = ["clone", "--branch", branch, remote_url, str(repo_path)]
                _run_git_parent(repo_path.parent, args)
                head_after = get_head_commit_hash(project.git_repo_path)
                return RemoteSyncResult(
                    status="cloned",
                    repo_path=project.git_repo_path,
                    branch=branch,
                    head_after=head_after,
                    messages=[f"저장소 clone 완료: {project.git_repo_path}", f"HEAD {_short_hash(head_after)}"],
                )

            if not is_git_repository(project.git_repo_path):
                return RemoteSyncResult(
                    status="failed",
                    repo_path=project.git_repo_path,
                    branch=branch,
                    errors=["대상 경로가 이미 존재하지만 Git 저장소가 아닙니다."],
                )

            head_before = get_head_commit_hash(project.git_repo_path)
            _run_git(repo_path, ["remote", "set-url", "origin", remote_url], check=False)
            _run_git(repo_path, ["fetch", "--prune", "origin"])
            messages.append("origin fetch 완료")

            dirty_status = _git_output(repo_path, ["status", "--porcelain"], check=False)
            if dirty_status and not force_reset:
                return RemoteSyncResult(
                    status="skipped",
                    repo_path=project.git_repo_path,
                    branch=branch,
                    head_before=head_before,
                    head_after=head_before,
                    messages=messages,
                    errors=["working tree에 local 변경이 있어 reset을 건너뛰었습니다."],
                )

            checkout = _run_git(repo_path, ["checkout", branch], check=False)
            if checkout.returncode != 0:
                _run_git(repo_path, ["checkout", "-B", branch, f"origin/{branch}"])
            _run_git(repo_path, ["reset", "--hard", f"origin/{branch}"])
            head_after = get_head_commit_hash(project.git_repo_path)
            messages.append(f"{branch} branch를 origin/{branch} 기준으로 reset했습니다.")
            return RemoteSyncResult(
                status="updated",
                repo_path=project.git_repo_path,
                branch=branch,
                head_before=head_before,
                head_after=head_after,
                messages=messages,
            )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        return RemoteSyncResult(
            status="failed",
            repo_path=project.git_repo_path,
            branch=branch,
            messages=messages,
            errors=[stderr or str(exc)],
        )
    except Exception as exc:
        return RemoteSyncResult(
            status="failed",
            repo_path=project.git_repo_path,
            branch=branch,
            messages=messages,
            errors=[str(exc)],
        )

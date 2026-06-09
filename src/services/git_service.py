from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.db.models import CommitFile, GitCommit, Project
from src.utils.repo_path import resolve_repo_path


MAX_DIFF_TEXT_LENGTH = 5000
FIELD_SEPARATOR = "\x1f"


@dataclass
class GitChangedFile:
    file_path: str
    change_type: str
    diff_text: str | None = None


@dataclass
class GitCommitData:
    commit_hash: str
    parent_hashes: list[str]
    message: str
    author_name: str
    author_email: str
    committed_at: datetime
    is_merge_commit: bool
    files: list[GitChangedFile] = field(default_factory=list)


@dataclass
class GitSyncResult:
    saved_commit_count: int = 0
    saved_file_count: int = 0
    skipped_duplicate_count: int = 0
    latest_commit_hash: str | None = None
    recent_commits: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _run_git(repo_path: str | Path, args: list[str]) -> str:
    path = resolve_repo_path(repo_path)
    result = subprocess.run(
        ["git", "-c", f"safe.directory={path.as_posix()}", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def is_git_repository(repo_path: str | Path) -> bool:
    path = resolve_repo_path(repo_path)
    if not path.exists():
        return False
    try:
        output = _run_git(path, ["rev-parse", "--is-inside-work-tree"]).strip()
        return output == "true"
    except Exception:
        return False


def get_head_commit_hash(repo_path: str | Path) -> str | None:
    try:
        return _run_git(repo_path, ["rev-parse", "HEAD"]).strip()
    except Exception:
        return None


def _get_commit_hashes(repo_path: str | Path, since_commit_hash: str | None = None) -> list[str]:
    revision = "HEAD" if not since_commit_hash else f"{since_commit_hash}..HEAD"
    output = _run_git(repo_path, ["rev-list", "--reverse", revision])
    return [line.strip() for line in output.splitlines() if line.strip()]


def _parse_commit(repo_path: str | Path, commit_hash: str) -> GitCommitData:
    output = _run_git(
        repo_path,
        ["show", "-s", f"--format=%H%x1f%P%x1f%an%x1f%ae%x1f%aI%x1f%B", commit_hash],
    )
    commit_hash_value, parents, author_name, author_email, committed_at, message = output.split(FIELD_SEPARATOR, 5)
    parent_hashes = [parent for parent in parents.split() if parent]
    committed_datetime = datetime.fromisoformat(committed_at.strip())

    return GitCommitData(
        commit_hash=commit_hash_value.strip(),
        parent_hashes=parent_hashes,
        message=message.strip(),
        author_name=author_name.strip(),
        author_email=author_email.strip(),
        committed_at=committed_datetime,
        is_merge_commit=len(parent_hashes) > 1,
    )


def _map_change_type(status: str) -> str:
    code = status[:1].upper()
    return {
        "A": "Added",
        "M": "Modified",
        "D": "Deleted",
        "R": "Renamed",
        "C": "Copied",
    }.get(code, "Modified")


def _get_changed_files(repo_path: str | Path, commit_hash: str) -> list[GitChangedFile]:
    output = _run_git(
        repo_path,
        ["diff-tree", "--root", "--no-commit-id", "--name-status", "-r", "-M", commit_hash],
    )
    diff_sections = _get_commit_diff_sections(repo_path, commit_hash)
    files = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue

        status = parts[0]
        file_path = parts[-1]
        files.append(
            GitChangedFile(
                file_path=file_path,
                change_type=_map_change_type(status),
                diff_text=diff_sections.get(file_path),
            )
        )
    return files


def _get_commit_diff_sections(repo_path: str | Path, commit_hash: str) -> dict[str, str | None]:
    try:
        diff = _run_git(
            repo_path,
            ["show", "--format=", "--no-ext-diff", "--no-color", "--find-renames", "--unified=3", commit_hash],
        ).strip()
    except subprocess.CalledProcessError as exc:
        return {"": f"Diff extraction failed: {exc.stderr.strip()}"[:MAX_DIFF_TEXT_LENGTH]}

    if not diff:
        return {}

    sections: dict[str, str | None] = {}
    current_lines: list[str] = []
    current_path: str | None = None

    def flush() -> None:
        if current_path is None:
            return
        text = "\n".join(current_lines).strip()
        if not text:
            sections[current_path] = None
        elif "Binary files " in text or "GIT binary patch" in text:
            sections[current_path] = "Binary file diff omitted."
        else:
            sections[current_path] = text[:MAX_DIFF_TEXT_LENGTH]

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            flush()
            current_lines = [line]
            current_path = _parse_diff_git_path(line)
        else:
            current_lines.append(line)
    flush()
    return sections


def _parse_diff_git_path(line: str) -> str | None:
    parts = line.split()
    if len(parts) < 4:
        return None
    old_path = parts[2][2:] if parts[2].startswith("a/") else parts[2]
    new_path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
    return old_path if new_path == "/dev/null" else new_path


def collect_commits(repo_path: str | Path, since_commit_hash: str | None = None) -> list[GitCommitData]:
    commits = []
    for commit_hash in _get_commit_hashes(repo_path, since_commit_hash):
        commit = _parse_commit(repo_path, commit_hash)
        if not commit.is_merge_commit:
            commit.files = _get_changed_files(repo_path, commit_hash)
        commits.append(commit)
    return commits


def sync_git_repository(db: Session, project: Project, full: bool = False) -> GitSyncResult:
    result = GitSyncResult()
    if not project.git_repo_path:
        result.errors.append("프로젝트에 Git 저장소 경로가 등록되어 있지 않습니다.")
        return result
    if not is_git_repository(project.git_repo_path):
        result.errors.append("등록된 경로가 Git 저장소가 아닙니다.")
        return result

    latest_head = get_head_commit_hash(project.git_repo_path)
    existing_project_commit_count = db.query(GitCommit).filter(GitCommit.project_id == project.id).count()
    since_commit_hash = None if full or existing_project_commit_count == 0 else project.last_synced_commit_hash

    try:
        commit_hashes = _get_commit_hashes(project.git_repo_path, since_commit_hash)
    except subprocess.CalledProcessError as exc:
        result.errors.append(exc.stderr.strip() or str(exc))
        return result
    except Exception as exc:
        result.errors.append(str(exc))
        return result

    for commit_hash in commit_hashes:
        existing = db.query(GitCommit).filter(GitCommit.commit_hash == commit_hash).one_or_none()
        if existing is not None:
            if existing.project_id != project.id:
                existing.project_id = project.id
            result.skipped_duplicate_count += 1
            continue

        try:
            commit = _parse_commit(project.git_repo_path, commit_hash)
            if not commit.is_merge_commit:
                commit.files = _get_changed_files(project.git_repo_path, commit_hash)
        except subprocess.CalledProcessError as exc:
            result.errors.append(exc.stderr.strip() or str(exc))
            continue

        git_commit = GitCommit(
            project_id=project.id,
            commit_hash=commit.commit_hash,
            message=commit.message,
            author=commit.author_name,
            author_name=commit.author_name,
            author_email=commit.author_email,
            committed_at=commit.committed_at,
            is_merge_commit=commit.is_merge_commit,
        )
        db.add(git_commit)
        db.flush()
        result.saved_commit_count += 1

        for changed_file in commit.files:
            db.add(
                CommitFile(
                    commit_id=git_commit.id,
                    git_commit_id=git_commit.id,
                    file_path=changed_file.file_path,
                    change_type=changed_file.change_type,
                    diff_text=changed_file.diff_text,
                )
            )
            result.saved_file_count += 1

        result.recent_commits.append(
            {
                "commit_hash": commit.commit_hash,
                "message": commit.message.splitlines()[0] if commit.message else "",
                "author_name": commit.author_name,
                "author_email": commit.author_email,
                "committed_at": commit.committed_at,
                "is_merge_commit": commit.is_merge_commit,
                "file_count": len(commit.files),
            }
        )

    if latest_head:
        project.last_synced_commit_hash = latest_head
        project.last_synced_at = datetime.now(timezone.utc)
        result.latest_commit_hash = latest_head

    db.commit()
    result.recent_commits = sorted(result.recent_commits, key=lambda item: item["committed_at"], reverse=True)[:20]
    return result

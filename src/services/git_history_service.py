from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from src.db.models import CommitFile, GitCommit, Project
from src.utils.repo_path import resolve_repo_path


FULL_DIFF_MAX_CHARS = 200_000


@dataclass
class GitHistoryCommit:
    commit_db_id: int
    commit_hash: str
    message: str
    author_name: str
    author_email: str | None
    committed_at: datetime | None
    is_merge_commit: bool
    file_count: int


@dataclass
class GitHistoryFile:
    file_path: str
    change_type: str | None
    diff_text: str | None


@dataclass
class GitHistoryDetail:
    commit: GitCommit
    files: list[GitHistoryFile]


@dataclass
class FullDiffResult:
    diff_text: str | None = None
    truncated: bool = False
    errors: list[str] = field(default_factory=list)


def _first_line(value: str | None) -> str:
    return (value or "").splitlines()[0] if value else ""


def list_git_history_commits(
    db: Session,
    *,
    project_id: int,
    message_keyword: str | None = None,
    author_keyword: str | None = None,
    file_keyword: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 300,
) -> list[GitHistoryCommit]:
    query = db.query(GitCommit).options(joinedload(GitCommit.files)).filter(GitCommit.project_id == project_id)

    if message_keyword:
        query = query.filter(GitCommit.message.ilike(f"%{message_keyword}%"))
    if author_keyword:
        keyword = f"%{author_keyword}%"
        query = query.filter(
            (GitCommit.author_name.ilike(keyword))
            | (GitCommit.author.ilike(keyword))
            | (GitCommit.author_email.ilike(keyword))
        )
    if file_keyword:
        query = query.join(CommitFile, CommitFile.commit_id == GitCommit.id).filter(
            CommitFile.file_path.ilike(f"%{file_keyword}%")
        )
    if start_date:
        query = query.filter(GitCommit.committed_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(GitCommit.committed_at <= datetime.combine(end_date, datetime.max.time()))

    commits = (
        query.distinct()
        .order_by(GitCommit.committed_at.desc().nullslast(), GitCommit.id.desc())
        .limit(limit)
        .all()
    )

    return [
        GitHistoryCommit(
            commit_db_id=commit.id,
            commit_hash=commit.commit_hash,
            message=_first_line(commit.message),
            author_name=commit.author_name or commit.author or "미상",
            author_email=commit.author_email,
            committed_at=commit.committed_at,
            is_merge_commit=bool(commit.is_merge_commit),
            file_count=len(commit.files),
        )
        for commit in commits
    ]


def get_git_history_detail(db: Session, *, project_id: int, commit_db_id: int) -> GitHistoryDetail | None:
    commit = (
        db.query(GitCommit)
        .options(joinedload(GitCommit.files))
        .filter(GitCommit.project_id == project_id, GitCommit.id == commit_db_id)
        .one_or_none()
    )
    if commit is None:
        return None

    files = [
        GitHistoryFile(file_path=file.file_path, change_type=file.change_type, diff_text=file.diff_text)
        for file in sorted(commit.files, key=lambda item: item.file_path)
    ]
    return GitHistoryDetail(commit=commit, files=files)


def get_commit_full_diff(
    db: Session,
    *,
    project_id: int,
    commit_db_id: int,
    max_chars: int = FULL_DIFF_MAX_CHARS,
) -> FullDiffResult:
    project = db.get(Project, project_id)
    if project is None:
        return FullDiffResult(errors=["프로젝트를 찾을 수 없습니다."])
    if not project.git_repo_path:
        return FullDiffResult(errors=["프로젝트에 앱 서버 Git 저장소 경로가 등록되어 있지 않습니다."])

    commit = db.query(GitCommit).filter(GitCommit.project_id == project_id, GitCommit.id == commit_db_id).one_or_none()
    if commit is None:
        return FullDiffResult(errors=["선택한 커밋을 찾을 수 없습니다."])

    repo_path = resolve_repo_path(project.git_repo_path)
    try:
        output = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={repo_path.as_posix()}",
                "show",
                "--no-ext-diff",
                "--no-color",
                "--find-renames",
                "--stat",
                "--patch",
                commit.commit_hash,
            ],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout
    except subprocess.CalledProcessError as exc:
        return FullDiffResult(errors=[exc.stderr.strip() or str(exc)])
    except Exception as exc:
        return FullDiffResult(errors=[str(exc)])

    truncated = len(output) > max_chars
    return FullDiffResult(diff_text=output[:max_chars], truncated=truncated)

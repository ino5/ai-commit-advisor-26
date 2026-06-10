from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import CommitFile, GitCommit, Project
from src.services.git_history_service import (
    get_commit_full_diff,
    get_git_history_detail,
    list_git_history_commits,
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _create_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "history-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "history@example.local")
    _git(repo, "config", "user.name", "History Tester")
    (repo / "src").mkdir()
    (repo / "src" / "payment.py").write_text("def pay():\n    return 'ok'\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Add payment flow")
    commit_hash = _git(repo, "rev-parse", "HEAD")
    return repo, commit_hash


def test_list_git_history_commits_filters_by_message_author_and_file(tmp_path: Path):
    init_db()
    repo, commit_hash = _create_repo(tmp_path)

    with SessionLocal() as db:
        project = Project(name=f"git-history-test-{uuid.uuid4()}", git_repo_path=str(repo))
        db.add(project)
        db.flush()
        commit = GitCommit(
            project_id=project.id,
            commit_hash=commit_hash,
            message="Add payment flow",
            author="History Tester",
            author_name="History Tester",
            author_email="history@example.local",
            committed_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
        )
        db.add(commit)
        db.flush()
        db.add(
            CommitFile(
                commit_id=commit.id,
                git_commit_id=commit.id,
                file_path="src/payment.py",
                change_type="Added",
                diff_text="+def pay():",
            )
        )
        db.commit()

        try:
            message_rows = list_git_history_commits(db, project_id=project.id, message_keyword="payment")
            author_rows = list_git_history_commits(db, project_id=project.id, author_keyword="history@example")
            file_rows = list_git_history_commits(db, project_id=project.id, file_keyword="payment.py")
            missing_rows = list_git_history_commits(db, project_id=project.id, file_keyword="inventory")
            detail = get_git_history_detail(db, project_id=project.id, commit_db_id=commit.id)

            assert [row.commit_hash for row in message_rows] == [commit_hash]
            assert [row.commit_hash for row in author_rows] == [commit_hash]
            assert [row.commit_hash for row in file_rows] == [commit_hash]
            assert missing_rows == []
            assert detail is not None
            assert detail.files[0].file_path == "src/payment.py"
        finally:
            db.delete(project)
            db.commit()


def test_get_commit_full_diff_uses_registered_project_commit(tmp_path: Path):
    init_db()
    repo, commit_hash = _create_repo(tmp_path)

    with SessionLocal() as db:
        project = Project(name=f"git-history-diff-test-{uuid.uuid4()}", git_repo_path=str(repo))
        db.add(project)
        db.flush()
        commit = GitCommit(
            project_id=project.id,
            commit_hash=commit_hash,
            message="Add payment flow",
            author_name="History Tester",
            committed_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
        )
        db.add(commit)
        db.commit()

        try:
            result = get_commit_full_diff(db, project_id=project.id, commit_db_id=commit.id)
            missing = get_commit_full_diff(db, project_id=project.id, commit_db_id=commit.id + 999999)

            assert result.errors == []
            assert result.diff_text is not None
            assert "Add payment flow" in result.diff_text
            assert "src/payment.py" in result.diff_text
            assert missing.errors == ["선택한 커밋을 찾을 수 없습니다."]
        finally:
            db.delete(project)
            db.commit()

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.run_local_ai_verification import parse_args
from src.services.code_review_service import (
    ReviewCommitOption,
    get_review_target,
    list_reviewable_commits,
)
from src.ui.code_review_page import TARGET_OPTIONS, _commit_option_label


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_list_reviewable_commits_reads_current_repository_history(tmp_path: Path) -> None:
    repo = tmp_path / "review-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "reviewer@example.local")
    _git(repo, "config", "user.name", "Review Tester")

    source = repo / "payment.py"
    source.write_text("amount = 100\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Add payment amount")
    first_hash = _git(repo, "rev-parse", "HEAD")

    source.write_text("amount = 0\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Allow zero amount")
    second_hash = _git(repo, "rev-parse", "HEAD")

    commits = list_reviewable_commits(repo, limit=2)

    assert [commit.commit_hash for commit in commits] == [second_hash, first_hash]
    assert [commit.message for commit in commits] == ["Allow zero amount", "Add payment amount"]
    assert all(commit.author_name == "Review Tester" for commit in commits)
    assert all(commit.author_email == "reviewer@example.local" for commit in commits)
    assert all(commit.committed_at.tzinfo is not None for commit in commits)


def test_list_reviewable_commits_handles_empty_repository_and_validates_limit(tmp_path: Path) -> None:
    repo = tmp_path / "empty-review-repo"
    repo.mkdir()
    _git(repo, "init")

    assert list_reviewable_commits(repo) == []
    with pytest.raises(ValueError, match="1~200"):
        list_reviewable_commits(repo, limit=0)


def test_commit_option_label_shows_hash_time_author_and_message() -> None:
    option = ReviewCommitOption(
        commit_hash="abcdef1234567890",
        author_name="홍길동",
        author_email="hong@example.local",
        committed_at=datetime(2026, 7, 22, 9, 30, tzinfo=timezone.utc),
        message="결제 승인 경계값 수정",
    )

    assert _commit_option_label(option) == "abcdef123456 · 2026-07-22 09:30 · 홍길동 · 결제 승인 경계값 수정"


def test_code_review_targets_only_offer_commit_history(tmp_path: Path) -> None:
    repo = tmp_path / "review-target-repo"
    repo.mkdir()
    _git(repo, "init")

    assert list(TARGET_OPTIONS.values()) == ["latest_commit", "commit"]
    for removed_target in ("working_tree", "staged"):
        with pytest.raises(ValueError, match="Unsupported review target type"):
            get_review_target(repo, removed_target)


def test_local_ai_verification_rejects_server_local_review_targets() -> None:
    assert parse_args(["--code-review-target", "commit"]).code_review_target == "commit"

    for removed_target in ("working_tree", "staged"):
        with pytest.raises(SystemExit):
            parse_args(["--code-review-target", removed_target])

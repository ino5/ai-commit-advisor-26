from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import AIInvocationLog, CodeReviewResult, Project
from src.services.code_review_service import CodeReviewService
from src.services.llm_client import LLMResponse


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class _EnglishOnlyReviewLLM:
    provider = "local_openai"
    model = "english-only-test-model"

    def __init__(self) -> None:
        self.call_count = 0

    def generate(self, _prompt: str) -> LLMResponse:
        self.call_count += 1
        payload = {
            "summary": "This change updates the payment calculation.",
            "commit_analysis": {
                "change_intent": "Update the payment amount calculation.",
                "impact_scope": "module",
                "risk_level": "medium",
            },
            "bug_findings": [],
            "refactoring_suggestions": [],
        }
        return LLMResponse(
            text=json.dumps(payload),
            raw={"provider": self.provider, "model": self.model},
        )


def test_language_invalid_review_stays_visible_and_logs_completed_telemetry(tmp_path: Path) -> None:
    init_db()
    repo = tmp_path / "english-review-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "review@example.local")
    _git(repo, "config", "user.name", "Review Tester")
    (repo / "payment.py").write_text("amount = total + fee\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Update payment calculation")

    with SessionLocal() as db:
        project = Project(name=f"english-review-{uuid.uuid4()}", git_repo_path=str(repo))
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

        try:
            llm = _EnglishOnlyReviewLLM()
            result = CodeReviewService(llm_client=llm).review_project(
                db,
                project,
                target_type="latest_commit",
            )

            assert result.errors == []
            assert result.review is not None
            assert result.review.status == "completed"
            assert result.review.summary == "This change updates the payment calculation."
            assert result.review.raw_response["language_validation"]["validation_status"] == "language_invalid"
            assert llm.call_count == 2

            invocation = (
                db.query(AIInvocationLog)
                .filter(
                    AIInvocationLog.project_id == project_id,
                    AIInvocationLog.feature == "ai_code_review",
                )
                .one()
            )
            assert invocation.status == "completed"
            assert invocation.validation_status == "language_invalid"
            assert invocation.fallback_used is True
        finally:
            db.query(AIInvocationLog).filter(AIInvocationLog.project_id == project_id).delete(
                synchronize_session=False
            )
            db.query(CodeReviewResult).filter(CodeReviewResult.project_id == project_id).delete(
                synchronize_session=False
            )
            db.query(Project).filter(Project.id == project_id).delete(synchronize_session=False)
            db.commit()

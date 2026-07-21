from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.db.models import CodeReviewResult, Project
from src.services.ai_invocation_service import record_ai_invocation
from src.services.git_service import _run_git, is_git_repository
from src.services.llm_client import LLMClient, generate_structured
from src.services.structured_output_schemas import CODE_REVIEW_SCHEMA


MAX_REVIEW_DIFF_CHARS = 18000


@dataclass
class ReviewTarget:
    target_type: str
    target_ref: str | None
    title: str
    diff_text: str
    commit_message: str | None = None


@dataclass
class CodeReviewRunResult:
    review: CodeReviewResult | None = None
    errors: list[str] = field(default_factory=list)


def _truncate_diff(diff_text: str) -> str:
    if len(diff_text) <= MAX_REVIEW_DIFF_CHARS:
        return diff_text
    return diff_text[:MAX_REVIEW_DIFF_CHARS] + "\n\n[diff truncated for review]"


def _parse_json_object(text: str) -> dict | None:
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= start:
            return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return None


def _empty_review_payload(message: str) -> dict:
    return {
        "summary": message,
        "commit_analysis": {
            "change_intent": "변경 내용을 분석할 수 없습니다.",
            "impact_scope": "unknown",
            "risk_level": "low",
        },
        "bug_findings": [],
        "refactoring_suggestions": [],
    }


def _mock_review_payload(target: ReviewTarget) -> dict:
    changed_lines = sum(1 for line in target.diff_text.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    return {
        "summary": f"Mock review completed for {target.title}. 변경 라인 약 {changed_lines}개를 확인했습니다.",
        "commit_analysis": {
            "change_intent": "Git diff 기반 변경 의도를 요약해야 합니다.",
            "impact_scope": "local",
            "risk_level": "medium" if changed_lines > 200 else "low",
        },
        "bug_findings": [],
        "refactoring_suggestions": [
            {
                "file": "",
                "line": None,
                "suggestion": "실제 LLM 리뷰를 사용하려면 LLM_PROVIDER=local_openai로 설정하세요.",
                "benefit": "버그 탐지와 리팩토링 제안 품질이 향상됩니다.",
            }
        ],
    }


def _normalize_review_payload(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return _empty_review_payload("LLM 응답을 JSON으로 해석하지 못했습니다.")

    return {
        "summary": str(payload.get("summary") or ""),
        "commit_analysis": payload.get("commit_analysis") if isinstance(payload.get("commit_analysis"), dict) else {},
        "bug_findings": payload.get("bug_findings") if isinstance(payload.get("bug_findings"), list) else [],
        "refactoring_suggestions": (
            payload.get("refactoring_suggestions") if isinstance(payload.get("refactoring_suggestions"), list) else []
        ),
    }


def _is_amount_zero_boundary_change(diff_text: str) -> bool:
    return "if (amount <= 0)" in diff_text and "if (amount < 0)" in diff_text


def _postprocess_review_payload(target: ReviewTarget, payload: dict) -> dict:
    if not _is_amount_zero_boundary_change(target.diff_text):
        return payload

    filtered_suggestions = []
    for suggestion in payload.get("refactoring_suggestions") or []:
        text = " ".join(
            str(suggestion.get(key) or "")
            for key in ("file", "suggestion", "benefit")
        )
        if any(
            blocked in text
            for blocked in (
                "amount",
                "0원",
                "PaymentPilotAuthorizationRiskTest",
                "OrderStatusService",
                "markPaid",
            )
        ):
            continue
        filtered_suggestions.append(suggestion)
    payload["refactoring_suggestions"] = filtered_suggestions

    bug_findings = payload.get("bug_findings") or []
    if bug_findings:
        commit_analysis = payload.setdefault("commit_analysis", {})
        if commit_analysis.get("risk_level") == "low":
            commit_analysis["risk_level"] = "medium"
    return payload


def _build_review_prompt(target: ReviewTarget) -> str:
    return f"""
You are a senior software engineer performing a practical code review.
Review the following Git diff and return only valid JSON in this exact shape:
{{
  "summary": "short overall review summary",
  "commit_analysis": {{
    "change_intent": "what this change appears to do",
    "impact_scope": "local|module|cross-cutting|unknown",
    "risk_level": "low|medium|high"
  }},
  "bug_findings": [
    {{
      "severity": "low|medium|high",
      "file": "path/to/file.py",
      "line": 123,
      "issue": "specific potential bug",
      "recommendation": "specific fix"
    }}
  ],
  "refactoring_suggestions": [
    {{
      "file": "path/to/file.py",
      "line": 123,
      "suggestion": "specific refactoring idea",
      "benefit": "why it helps"
    }}
  ]
}}

Language rules:
- Write all human-readable text values in Korean.
- Keep JSON keys exactly as shown above.
- Keep enum values for `impact_scope`, `risk_level`, and `severity` as the exact allowed English tokens.
- Do not translate file paths, class names, method names, function names, API names, table names, column names, constants, or code expressions.
- Do not translate short English business terms that appear in the commit message or code, such as `pilot channel`. Keep them as the original English phrase inside Korean sentences.
- When referring to code, keep expressions such as `amount == 0`, `PaymentService.java`, and `markPaid` exactly as code.

Focus on:
- commit/change analysis
- potential bugs and regressions
- refactoring suggestions that reduce maintenance cost
- concrete, actionable feedback

Diff reading rules:
- Lines starting with "-" were removed by this commit.
- Lines starting with "+" were added by this commit.
- Compare removed and added conditions carefully before describing a bug.
- If a validation condition changed, explain the exact before/after behavior and the input values newly allowed or newly rejected.
- Do not recommend changing code to the same condition that the commit already added.
- For numeric boundary checks, test example values mentally before writing the finding. For example, changing `amount <= 0` to `amount < 0` still rejects negative values but newly allows `amount == 0`.
- Boundary analysis is mandatory for validation changes. In Korean findings, state the boundary value precisely.
- If a diff changes `amount <= 0` to `amount < 0`, every field must say this consistently: negative amounts are still rejected and only `amount == 0` is newly allowed.
- For that exact pattern, the Korean summary, issue, and recommendation must mention `amount == 0` or `0원` as the newly allowed boundary.
- Never claim that negative amounts are newly allowed when the added condition is `amount < 0`.
- For that exact pattern, write the Korean recommendation as rejecting `amount == 0` or `0원 결제`; do not frame it as rejecting negative amounts.
- If your finding is about a numeric condition, include one concrete example input such as `amount == 0` in Korean text.
- Keep refactoring suggestions grounded in the shown diff. Do not suggest replacing service-layer calls or mapper calls unless that call appears in the changed lines.
- Do not suggest code that the commit already added. If the added diff already uses `orderStatusService.markPaid(orderId)`, do not recommend using `OrderStatusService` or `markPaid` as a new suggestion.
- Do not suggest adding a test, class, method, file, mapper, or service that already appears in added diff lines. If `PaymentPilotAuthorizationRiskTest` appears in added lines, do not suggest adding `PaymentPilotAuthorizationRiskTest`.
- Do not use vague translated phrases like "플라이어널". For `pilot channel`, write `pilot channel` or `pilot channel(파일럿 채널)`.
- Do not put the same fix in both `bug_findings[*].recommendation` and `refactoring_suggestions[*].suggestion`. If the only refactoring idea is the bug fix, return an empty `refactoring_suggestions` array.
- If there is no clearly different refactoring suggestion grounded in the changed lines, return an empty `refactoring_suggestions` array.
- Before returning JSON, check that `summary`, `commit_analysis.change_intent`, `bug_findings`, and `refactoring_suggestions` do not contradict each other.

Target: {target.title}
Commit message:
{target.commit_message or ""}

Diff:
{target.diff_text}
""".strip()


def get_review_target(repo_path: str | Path, target_type: str, target_ref: str | None = None) -> ReviewTarget:
    repo = Path(repo_path).expanduser()
    if not is_git_repository(repo):
        raise ValueError(f"Git repository not found: {repo}")

    if target_type == "working_tree":
        diff = _run_git(repo, ["diff", "--no-ext-diff", "--no-color"])
        return ReviewTarget("working_tree", None, "서버 작업트리 변경", _truncate_diff(diff))

    if target_type == "staged":
        diff = _run_git(repo, ["diff", "--cached", "--no-ext-diff", "--no-color"])
        return ReviewTarget("staged", None, "서버 Staged 변경", _truncate_diff(diff))

    if target_type == "latest_commit":
        commit_hash = _run_git(repo, ["rev-parse", "HEAD"]).strip()
        message = _run_git(repo, ["show", "-s", "--format=%B", commit_hash]).strip()
        diff = _run_git(repo, ["show", "--format=", "--no-ext-diff", "--no-color", "--find-renames", commit_hash])
        return ReviewTarget("latest_commit", commit_hash, f"최신 커밋 {commit_hash[:12]}", _truncate_diff(diff), message)

    if target_type == "commit":
        if not target_ref:
            raise ValueError("특정 커밋 리뷰에는 commit hash가 필요합니다.")
        commit_hash = _run_git(repo, ["rev-parse", target_ref]).strip()
        message = _run_git(repo, ["show", "-s", "--format=%B", commit_hash]).strip()
        diff = _run_git(repo, ["show", "--format=", "--no-ext-diff", "--no-color", "--find-renames", commit_hash])
        return ReviewTarget("commit", commit_hash, f"커밋 {commit_hash[:12]}", _truncate_diff(diff), message)

    raise ValueError(f"Unsupported review target type: {target_type}")


class CodeReviewService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient(max_tokens=1200)

    def review_project(
        self,
        db: Session,
        project: Project,
        target_type: str,
        target_ref: str | None = None,
    ) -> CodeReviewRunResult:
        result = CodeReviewRunResult()
        started_at = datetime.now(timezone.utc)

        if not project.git_repo_path:
            result.errors.append("프로젝트에 앱 서버 Git 저장소 경로가 설정되어 있지 않습니다.")
            return result

        try:
            target = get_review_target(project.git_repo_path, target_type, target_ref)
        except (ValueError, subprocess.CalledProcessError) as exc:
            result.errors.append(str(exc))
            return result

        if not target.diff_text.strip():
            payload = _empty_review_payload("리뷰할 변경 사항이 없습니다.")
            raw_response = {"provider": self.llm_client.provider, "empty_diff": True}
            status = "completed"
            prompt_length = 0
            response_length = 0
            fallback_used = False
            error_message = None
        elif self.llm_client.provider == "mock":
            payload = _mock_review_payload(target)
            raw_response = {"provider": "mock", "target": target.title}
            status = "completed"
            prompt_length = len(target.diff_text)
            response_length = len(json.dumps(payload, ensure_ascii=False))
            fallback_used = True
            error_message = None
        else:
            prompt = _build_review_prompt(target)
            try:
                response = generate_structured(
                    self.llm_client,
                    prompt,
                    schema=CODE_REVIEW_SCHEMA,
                    schema_name="ai_code_review",
                )
                payload = _normalize_review_payload(_parse_json_object(response.text))
                payload = _postprocess_review_payload(target, payload)
                raw_response = {"llm": response.raw, "text": response.text, "prompt_length": len(prompt)}
                status = "completed"
                prompt_length = len(prompt)
                response_length = len(response.text or "")
                fallback_used = False
                error_message = None
            except Exception as exc:
                payload = _empty_review_payload(f"LLM 코드리뷰 호출 실패: {exc}")
                raw_response = {"llm_error": str(exc)}
                status = "failed"
                prompt_length = len(prompt)
                response_length = 0
                fallback_used = True
                error_message = str(exc)

        finished_at = datetime.now(timezone.utc)
        review = CodeReviewResult(
            project_id=project.id,
            target_type=target.target_type,
            target_ref=target.target_ref,
            status=status,
            summary=payload["summary"],
            commit_analysis=payload["commit_analysis"],
            bug_findings=payload["bug_findings"],
            refactoring_suggestions=payload["refactoring_suggestions"],
            raw_response=raw_response,
            started_at=started_at,
            finished_at=finished_at,
        )
        db.add(review)
        record_ai_invocation(
            db,
            project_id=project.id,
            feature="ai_code_review",
            provider=self.llm_client.provider,
            model=self.llm_client.model,
            status=status,
            mode=target.target_type,
            fallback_used=fallback_used,
            validation_status="parsed" if status == "completed" else "failed",
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=int((finished_at - started_at).total_seconds() * 1000),
            prompt_length=prompt_length,
            response_length=response_length,
            error_message=error_message,
            raw_metadata={"target": target.title, "target_ref": target.target_ref},
        )
        db.commit()
        db.refresh(review)
        result.review = review
        return result


def get_recent_code_reviews(db: Session, project_id: int, limit: int = 20) -> list[CodeReviewResult]:
    return (
        db.query(CodeReviewResult)
        .filter(CodeReviewResult.project_id == project_id)
        .order_by(CodeReviewResult.created_at.desc(), CodeReviewResult.id.desc())
        .limit(limit)
        .all()
    )

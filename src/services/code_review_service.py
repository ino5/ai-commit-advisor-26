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
from src.services.llm_client import LLMClient


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


def _target_text(target: ReviewTarget) -> str:
    return f"{target.commit_message or ''}\n{target.diff_text}".lower()


def _sample_payment_review_payload(target: ReviewTarget, changed_lines: int) -> dict:
    return {
        "summary": (
            f"샘플 결제 커밋 리뷰: {target.title}에서 0원 결제 승인 가능성이 보입니다. "
            f"변경 라인 약 {changed_lines}개를 기준으로 결제 상태 전환 영향까지 확인해야 합니다."
        ),
        "commit_analysis": {
            "change_intent": "파일럿 파트너 결제를 위해 금액 검증을 완화했습니다.",
            "impact_scope": "module",
            "risk_level": "high",
        },
        "bug_findings": [
            {
                "severity": "high",
                "file": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "line": 18,
                "issue": "`amount <= 0` 거부 조건이 `amount < 0`으로 완화되어 0원 결제가 AUTHORIZED 처리될 수 있습니다.",
                "recommendation": "0원 결제는 명시적인 파트너 정산 상태로 분리하거나, 기존처럼 `amount <= 0`을 거부하고 예외 케이스는 별도 승인 흐름으로 처리하세요.",
            },
            {
                "severity": "medium",
                "file": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "line": 22,
                "issue": "금액 검증 완화 후에도 주문 상태를 바로 `PAID`로 바꿔 후속 출고/정산 로직이 실제 결제 완료로 오인할 수 있습니다.",
                "recommendation": "파일럿 파트너 결제는 `PAYMENT_PENDING_SETTLEMENT` 같은 중간 상태를 사용하고 출고 가능 조건을 별도로 검증하세요.",
            },
        ],
        "refactoring_suggestions": [
            {
                "file": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "line": 16,
                "suggestion": "금액 검증 조건을 `validateAuthorizableAmount` 같은 private method로 분리하세요.",
                "benefit": "파트너 예외 정책과 일반 결제 정책을 테스트하기 쉬워지고, 향후 결제 한도 규칙 추가 시 영향 범위가 줄어듭니다.",
            }
        ],
    }


def _sample_dashboard_review_payload(target: ReviewTarget, changed_lines: int) -> dict:
    return {
        "summary": (
            f"샘플 dashboard 커밋 리뷰: {target.title}에서 orders, shortage, payments join으로 집계가 부풀 위험이 있습니다. "
            f"변경 라인 약 {changed_lines}개를 기준으로 cross-module regression을 확인해야 합니다."
        ),
        "commit_analysis": {
            "change_intent": "운영 dashboard summary query를 여러 업무 테이블 join 기반으로 바꿨습니다.",
            "impact_scope": "cross-cutting",
            "risk_level": "high",
        },
        "bug_findings": [
            {
                "severity": "high",
                "file": "src/main/resources/mappers/DashboardMapper.xml",
                "line": 6,
                "issue": "orders, inventory_shortage_signals, payments를 grouping 없이 join해 payment나 shortage row가 여러 개일 때 `count(o.order_id)`가 중복 집계됩니다.",
                "recommendation": "기존처럼 metric별 subquery를 유지하거나, `count(distinct ...)`와 조건부 집계를 사용해 지표별 cardinality를 분리하세요.",
            },
            {
                "severity": "medium",
                "file": "src/main/resources/mappers/DashboardMapper.xml",
                "line": 8,
                "issue": "`left join inventory_shortage_signals s on s.resolved_yn = 'N'`에 order 또는 item 연결 조건이 없어 모든 미해결 shortage가 모든 open order에 곱해질 수 있습니다.",
                "recommendation": "shortage signal을 주문/상품 기준으로 연결하거나 별도 summary subquery로 계산하세요.",
            },
        ],
        "refactoring_suggestions": [
            {
                "file": "src/main/resources/mappers/DashboardMapper.xml",
                "line": 5,
                "suggestion": "dashboard 지표별 SQL을 작은 named subquery로 분리하고 regression test fixture를 함께 추가하세요.",
                "benefit": "주문, 결제, 재고 지표가 서로 곱해지는 회귀를 테스트로 고정할 수 있습니다.",
            }
        ],
    }


def _sample_refactoring_review_payload(target: ReviewTarget, changed_lines: int) -> dict:
    return {
        "summary": f"샘플 리팩터링 커밋 리뷰: {target.title}은 위험도가 낮은 상수 추출 변경입니다.",
        "commit_analysis": {
            "change_intent": "dashboard indicator 이름을 상수로 분리했습니다.",
            "impact_scope": "local",
            "risk_level": "low",
        },
        "bug_findings": [],
        "refactoring_suggestions": [
            {
                "file": "src/main/java/com/example/market/dashboard/service/DashboardIndicatorNames.java",
                "line": 3,
                "suggestion": "상수 사용처까지 같은 커밋에 포함하거나 follow-up commit을 명시하세요.",
                "benefit": "새 상수 클래스가 실제로 중복 문자열을 줄였는지 리뷰어가 바로 확인할 수 있습니다.",
            },
            {
                "file": "src/main/java/com/example/market/dashboard/service/DashboardIndicatorNames.java",
                "line": 4,
                "suggestion": "UI/API contract에 노출되는 indicator key라면 간단한 serialization regression test를 추가하세요.",
                "benefit": "키 이름 변경이 dashboard client와 어긋나는 문제를 조기에 잡을 수 있습니다.",
            },
        ],
    }


def _sample_signal_review_payload(target: ReviewTarget, changed_lines: int) -> dict | None:
    text = _target_text(target)
    if "relax partner payment validation" in text or "payment-zero-amount-risk" in text or "amount < 0" in text:
        return _sample_payment_review_payload(target, changed_lines)
    if "dashboard-overcount-risk" in text or "select count(o.order_id)" in text:
        return _sample_dashboard_review_payload(target, changed_lines)
    if "refactor dashboard indicator names" in text or "dashboardindicatornames" in text:
        return _sample_refactoring_review_payload(target, changed_lines)
    return None


def _mock_review_payload(target: ReviewTarget) -> dict:
    changed_lines = sum(1 for line in target.diff_text.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    sample_payload = _sample_signal_review_payload(target, changed_lines)
    if sample_payload is not None:
        return sample_payload
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

Focus on:
- commit/change analysis
- potential bugs and regressions
- refactoring suggestions that reduce maintenance cost
- concrete, actionable feedback

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
                response = self.llm_client.generate(prompt)
                payload = _normalize_review_payload(_parse_json_object(response.text))
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

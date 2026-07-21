from types import SimpleNamespace

import json
from unittest.mock import patch

from src.services.code_review_service import (
    ReviewTarget,
    _build_korean_repair_prompt,
    _build_review_prompt,
    _postprocess_review_payload,
    _repair_review_language,
    _review_language_metrics,
)
from src.services.llm_client import LLMResponse
from src.ui.code_review_page import (
    _commit_analysis_display_rows,
    _review_metadata_display_rows,
    _severity_label,
    _status_label,
)


def test_code_review_prompt_requests_korean_human_readable_values() -> None:
    prompt = _build_review_prompt(
        ReviewTarget(
            target_type="commit",
            target_ref="abc123",
            title="커밋 abc123",
            diff_text="+ if (amount < 0) { throw new IllegalArgumentException(); }",
            commit_message="Relax validation",
        )
    )

    assert "Write all human-readable text values in Korean." in prompt
    assert "Keep JSON keys exactly as shown above." in prompt
    assert "Keep enum values for `impact_scope`, `risk_level`, and `severity`" in prompt
    assert "Do not translate file paths, class names, method names" in prompt
    assert "such as `pilot channel`" in prompt
    assert "`amount == 0`" in prompt
    assert "only `amount == 0` is newly allowed" in prompt
    assert "Never claim that negative amounts are newly allowed" in prompt
    assert "do not frame it as rejecting negative amounts" in prompt
    assert "include one concrete example input such as `amount == 0` in Korean text" in prompt
    assert "Do not suggest replacing service-layer calls or mapper calls" in prompt
    assert "do not recommend using `OrderStatusService` or `markPaid` as a new suggestion" in prompt
    assert "do not suggest adding `PaymentPilotAuthorizationRiskTest`" in prompt
    assert "Do not use vague translated phrases like \"플라이어널\"" in prompt
    assert "Do not put the same fix in both `bug_findings[*].recommendation`" in prompt
    assert "return an empty `refactoring_suggestions` array" in prompt
    assert "`summary`, `commit_analysis.change_intent`, `bug_findings`, and `refactoring_suggestions`" in prompt


def test_code_review_page_labels_saved_status_and_review_enums_in_korean() -> None:
    assert _status_label("completed") == "완료"
    assert _status_label("failed") == "실패"
    assert _status_label("custom") == "custom"
    assert _severity_label("high") == "높음"

    rows = _commit_analysis_display_rows(
        {
            "risk_level": "medium",
            "impact_scope": "module",
            "change_intent": "결제 검증 조건을 완화합니다.",
        }
    )

    assert rows == [
        ("위험도", "보통"),
        ("영향 범위", "모듈"),
        ("변경 의도", "결제 검증 조건을 완화합니다."),
    ]


def test_review_metadata_rows_are_compact_key_values() -> None:
    review = SimpleNamespace(
        status="completed",
        target_type="commit",
        target_ref="2325182ecf5cb054",
        raw_response={"llm": {"provider": "local_openai", "model": "qwen2.5-coder-7b-instruct"}},
    )

    assert _review_metadata_display_rows(review) == [
        ("상태", "완료"),
        ("Provider", "local_openai / qwen2.5-coder-7b-instruct"),
        ("대상", "커밋 목록에서 선택"),
        ("참조", "2325182ecf5c"),
    ]


def test_postprocess_removes_ungrounded_amount_boundary_refactoring() -> None:
    target = ReviewTarget(
        target_type="commit",
        target_ref="abc123",
        title="커밋 abc123",
        diff_text="""
-        if (amount <= 0) {
+        if (amount < 0) {
+class PaymentPilotAuthorizationRiskTest {
""",
    )
    payload = {
        "summary": "0원 결제가 허용됩니다.",
        "commit_analysis": {"risk_level": "low", "impact_scope": "module"},
        "bug_findings": [
            {
                "severity": "medium",
                "file": "PaymentService.java",
                "line": 18,
                "issue": "0원 결제가 허용됩니다.",
                "recommendation": "amount == 0일 때 거절하세요.",
            }
        ],
        "refactoring_suggestions": [
            {
                "file": "PaymentService.java",
                "line": 18,
                "suggestion": "amount < 0 && amount == 0을 분리하세요.",
                "benefit": "명확성",
            },
            {
                "file": "PaymentPilotAuthorizationRiskTest.java",
                "line": 1,
                "suggestion": "PaymentPilotAuthorizationRiskTest를 추가하세요.",
                "benefit": "테스트",
            },
            {
                "file": "PaymentService.java",
                "line": 20,
                "suggestion": "변수명을 더 명확히 하세요.",
                "benefit": "가독성",
            },
        ],
    }

    postprocessed = _postprocess_review_payload(target, payload)

    assert postprocessed["commit_analysis"]["risk_level"] == "medium"
    assert postprocessed["refactoring_suggestions"] == [
        {
            "file": "PaymentService.java",
            "line": 20,
            "suggestion": "변수명을 더 명확히 하세요.",
            "benefit": "가독성",
        }
    ]


def _english_review_payload() -> dict:
    return {
        "summary": "This change relaxes payment validation.",
        "commit_analysis": {
            "change_intent": "Allow zero amount payments in the pilot channel.",
            "impact_scope": "module",
            "risk_level": "medium",
        },
        "bug_findings": [
            {
                "severity": "medium",
                "file": "PaymentService.java",
                "line": 18,
                "issue": "A zero amount payment can be approved.",
                "recommendation": "Reject amount == 0 before approval.",
            }
        ],
        "refactoring_suggestions": [],
    }


class _QueuedReviewLLM:
    provider = "local_openai"
    model = "test-model"

    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = list(payloads)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> LLMResponse:
        self.prompts.append(prompt)
        payload = self.payloads.pop(0)
        text = json.dumps(payload, ensure_ascii=False)
        return LLMResponse(text=text, raw={"provider": self.provider, "model": self.model})


def test_review_language_metrics_allow_korean_sentences_with_code_identifiers() -> None:
    payload = _english_review_payload()
    payload["summary"] = "PaymentService의 결제 검증 조건을 수정했습니다."
    payload["commit_analysis"]["change_intent"] = "pilot channel에서 amount == 0을 허용합니다."
    payload["bug_findings"][0]["issue"] = "amount == 0 결제가 승인될 수 있습니다."
    payload["bug_findings"][0]["recommendation"] = "승인 전에 amount == 0을 거부하세요."

    metrics = _review_language_metrics(payload)

    assert metrics["is_korean"] is True
    assert metrics["hangul_char_count"] >= 3


def test_review_language_repair_translates_descriptions_and_preserves_structure() -> None:
    original = _english_review_payload()
    repaired = {
        "summary": "결제 검증 조건을 완화한 변경입니다.",
        "commit_analysis": {
            "change_intent": "pilot channel에서 0원 결제를 허용합니다.",
            "impact_scope": "module",
            "risk_level": "medium",
        },
        "bug_findings": [
            {
                "severity": "medium",
                "file": "PaymentService.java",
                "line": 18,
                "issue": "amount == 0인 결제가 승인될 수 있습니다.",
                "recommendation": "승인 전에 amount == 0을 거부하세요.",
            }
        ],
        "refactoring_suggestions": [],
    }
    llm = _QueuedReviewLLM([repaired])
    target = ReviewTarget("commit", "abc123", "커밋 abc123", "+ amount == 0")

    result = _repair_review_language(llm, target, original)

    assert result.validation_status == "language_repaired"
    assert result.repair_attempted is True
    assert result.fallback_used is True
    assert result.payload == repaired
    assert result.final_metrics["structure_preserved"] is True
    assert "사용자 설명 필드만 자연스러운 한국어" in llm.prompts[0]
    assert "PaymentService.java" in _build_korean_repair_prompt(original)


def test_review_language_repair_failure_preserves_english_result_and_logs_warning() -> None:
    original = _english_review_payload()
    changed_structure = _english_review_payload()
    changed_structure["bug_findings"] = []
    llm = _QueuedReviewLLM([changed_structure])
    target = ReviewTarget("commit", "abc123", "커밋 abc123", "+ amount == 0")

    with patch("src.services.code_review_service.logger.warning") as warning:
        result = _repair_review_language(llm, target, original)

    assert result.validation_status == "language_invalid"
    assert result.repair_attempted is True
    assert result.fallback_used is True
    assert result.payload == original
    warning.assert_called_once()
    assert "preserving original review" in warning.call_args.args[0]

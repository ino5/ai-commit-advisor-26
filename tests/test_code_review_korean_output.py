from types import SimpleNamespace

from src.services.code_review_service import ReviewTarget, _build_review_prompt, _postprocess_review_payload
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
        ("대상", "특정 커밋"),
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

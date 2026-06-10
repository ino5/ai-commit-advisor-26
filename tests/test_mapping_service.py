from types import SimpleNamespace

from src.services.mapping_service import (
    _candidate_score,
    _fallback_commit_based_results,
    _normalize_implementation_status,
    _parse_commit_based_result,
)


def test_candidate_score_uses_program_text_and_file_paths():
    program = SimpleNamespace(
        program_id="P001",
        program_name="Login API",
        module="auth",
        screen_name="Login",
        description="사용자 로그인 인증 처리",
    )
    commit = SimpleNamespace(
        message="Implement login token validation",
        committed_at=None,
        files=[
            SimpleNamespace(
                file_path="src/auth/login_service.py",
                diff_text="+ validate login token\n+ authenticate user",
            )
        ],
    )

    assert _candidate_score(program, commit) >= 30


def test_parse_commit_based_result_accepts_only_known_candidates():
    program = SimpleNamespace(
        id=1,
        program_id="P001",
        program_name="Login API",
    )
    text = """
    {
      "related_programs": [
        {
          "program_id": "P001",
          "relevance_score": 120,
          "implementation_status": "구현완료",
          "reason": "관련 파일 변경"
        },
        {
          "program_id": "UNKNOWN",
          "relevance_score": 80,
          "implementation_status": "일부구현",
          "reason": "후보에 없음"
        }
      ]
    }
    """

    parsed = _parse_commit_based_result(text, [program])

    assert parsed is not None
    assert len(parsed) == 1
    assert parsed[0]["program"] is program
    assert parsed[0]["relevance_score"] == 100
    assert parsed[0]["implementation_status"] == "구현완료"


def test_commit_based_fallback_uses_token_similarity_for_related_candidates():
    payment = SimpleNamespace(
        id=1,
        program_id="SMP-PAY-001",
        program_name="결제 승인",
        module="payment",
        screen_name="/payments/authorize",
        description="payment authorization validates payment amount and updates order status.",
    )
    coupon = SimpleNamespace(
        id=2,
        program_id="SMP-CPN-001",
        program_name="쿠폰 할인",
        module="coupon",
        screen_name="/coupons/apply",
        description="쿠폰 할인 가능 여부와 할인 금액을 계산합니다.",
    )
    commit = SimpleNamespace(
        message="Reject zero and negative payment amounts",
        committed_at=None,
        files=[
            SimpleNamespace(
                file_path="src/main/java/com/example/market/payment/service/PaymentService.java",
                diff_text="+ if (amount <= 0) return REJECTED;",
            )
        ],
    )

    fallback = _fallback_commit_based_results(commit, [payment, coupon], "invalid json")

    assert [item["program_id"] for item in fallback] == ["SMP-PAY-001"]
    assert fallback[0]["relevance_score"] >= 30
    assert fallback[0]["implementation_status"] in {"구현됨", "일부구현", "판단불가"}
    assert "token" not in fallback[0]["reason"].lower()
    assert "fallback" in fallback[0]["reason"]


def test_normalize_implementation_status_falls_back_to_unknown():
    assert _normalize_implementation_status("일부구현") == "일부구현"
    assert _normalize_implementation_status("unexpected") == "판단불가"

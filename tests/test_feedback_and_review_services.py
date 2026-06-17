from src.services.code_review_service import ReviewTarget, _mock_review_payload, _parse_json_object
from src.services.git_service import _parse_diff_git_path
from src.services.mapping_feedback_service import (
    MappingFeedbackRow,
    apply_mapping_feedback,
    filter_mapping_review_queue_rows,
    normalize_feedback_status,
    summarize_mapping_feedback_quality_rows,
)
from src.services.risk_service import normalize_implementation_status


def test_parse_json_object_extracts_json_from_llm_text():
    parsed = _parse_json_object('prefix {"summary": "ok", "bug_findings": []} suffix')

    assert parsed == {"summary": "ok", "bug_findings": []}


def test_mock_review_payload_surfaces_sample_payment_risk():
    payload = _mock_review_payload(
        ReviewTarget(
            target_type="commit",
            target_ref="abc",
            title="커밋 abc",
            commit_message="Relax partner payment validation for pilot channel",
            diff_text="""
diff --git a/src/main/java/com/example/market/payment/service/PaymentService.java b/src/main/java/com/example/market/payment/service/PaymentService.java
-                        if (amount <= 0) {
+                            if (amount < 0) {
+                            orderMapper.updateOrderStatus(orderId, "PAID");
""",
        )
    )

    assert payload["commit_analysis"]["risk_level"] == "high"
    assert payload["bug_findings"]
    assert "0원 결제" in payload["bug_findings"][0]["issue"]
    assert "PaymentService.java" in payload["bug_findings"][0]["file"]


def test_mock_review_payload_surfaces_sample_dashboard_overcount_risk():
    payload = _mock_review_payload(
        ReviewTarget(
            target_type="commit",
            target_ref="abc",
            title="커밋 abc",
            commit_message="Change dashboard summary query across operations modules",
            diff_text="""
diff --git a/src/main/resources/mappers/DashboardMapper.xml b/src/main/resources/mappers/DashboardMapper.xml
+                            select count(o.order_id) as open_orders,
+                            left join inventory_shortage_signals s on s.resolved_yn = 'N'
+                            left join payments p on p.order_id = o.order_id
""",
        )
    )

    assert payload["commit_analysis"]["impact_scope"] == "cross-cutting"
    assert payload["bug_findings"]
    assert "중복 집계" in payload["bug_findings"][0]["issue"]


def test_parse_diff_git_path_prefers_new_path_and_handles_delete():
    assert _parse_diff_git_path("diff --git a/src/old.py b/src/new.py") == "src/new.py"
    assert _parse_diff_git_path("diff --git a/src/old.py /dev/null") == "src/old.py"


def test_feedback_status_normalization_allows_known_values_only():
    assert normalize_feedback_status("구현됨") == "구현됨"
    assert normalize_feedback_status("done") == "판단불가"


def _feedback_row(
    mapping_id: int,
    *,
    program_id: str = "P001",
    program_name: str = "로그인",
    commit_hash: str = "abcdef1234567890",
    commit_message: str = "로그인 화면 수정",
    relevance_score: float = 50,
    is_related: bool | None = None,
    implementation_status: str = "판단불가",
    reason: str = "",
    has_feedback: bool = False,
) -> MappingFeedbackRow:
    row = MappingFeedbackRow(
        mapping_id=mapping_id,
        program_id=program_id,
        program_name=program_name,
        commit_hash=commit_hash,
        commit_message=commit_message,
        author_name="dev",
        relevance_score=relevance_score,
        is_related=is_related,
        implementation_status=implementation_status,
        reason=reason,
        has_feedback=has_feedback,
        feedback_updated_at=None,
    )
    from src.services.mapping_feedback_service import mapping_review_reasons

    row.review_reasons = mapping_review_reasons(row)
    row.review_needed = bool(row.review_reasons)
    return row


def test_mapping_feedback_quality_summary_counts_feedback_and_review_candidates():
    rows = [
        _feedback_row(1, has_feedback=False, implementation_status="판단불가", relevance_score=50),
        _feedback_row(
            2,
            has_feedback=True,
            is_related=True,
            implementation_status="구현됨",
            relevance_score=85,
            reason="프로그램 기능과 커밋 변경 내용이 충분히 연결되어 있습니다.",
        ),
        _feedback_row(3, has_feedback=False, implementation_status="일부구현", relevance_score=20),
    ]

    summary = summarize_mapping_feedback_quality_rows(rows)

    assert summary.total_count == 3
    assert summary.feedback_completed_count == 1
    assert summary.feedback_pending_count == 2
    assert summary.review_needed_count == 2
    assert summary.unknown_status_count == 1
    assert summary.low_relevance_count == 1


def test_mapping_review_queue_filters_unknown_and_low_relevance_candidates():
    rows = [
        _feedback_row(1, implementation_status="판단불가", relevance_score=85),
        _feedback_row(2, implementation_status="구현됨", relevance_score=45, reason="낮은 관련도 후보입니다."),
        _feedback_row(
            3,
            implementation_status="구현됨",
            relevance_score=90,
            reason="프로그램 기능과 커밋 변경 내용이 충분히 연결되어 있습니다.",
            has_feedback=True,
            is_related=True,
        ),
    ]

    unknown_rows = filter_mapping_review_queue_rows(rows, queue_filter="판단불가")
    low_score_rows = filter_mapping_review_queue_rows(rows, queue_filter="낮은 관련도")

    assert [row.mapping_id for row in unknown_rows] == [1]
    assert [row.mapping_id for row in low_score_rows] == [2]


def test_mapping_review_queue_keyword_searches_program_and_commit_fields():
    rows = [
        _feedback_row(1, program_id="P-LOGIN", program_name="로그인", commit_message="세션 처리"),
        _feedback_row(2, program_id="P-PAY", program_name="결제", commit_hash="ffff11112222", commit_message="PG 승인"),
    ]

    by_program = filter_mapping_review_queue_rows(rows, keyword="LOGIN")
    by_commit = filter_mapping_review_queue_rows(rows, keyword="ffff1111")

    assert [row.mapping_id for row in by_program] == [1]
    assert [row.mapping_id for row in by_commit] == [2]


class _FakeQuery:
    def __init__(self, mapping):
        self.mapping = mapping

    def filter(self, *_args, **_kwargs):
        return self

    def one(self):
        return self.mapping


class _FakeDb:
    def __init__(self, mapping):
        self.mapping = mapping
        self.committed = False
        self.refreshed = False

    def query(self, _model):
        return _FakeQuery(self.mapping)

    def commit(self):
        self.committed = True

    def refresh(self, mapping):
        assert mapping is self.mapping
        self.refreshed = True


def test_apply_mapping_feedback_updates_existing_mapping_fields():
    class Mapping:
        id = 1

    mapping = Mapping()
    db = _FakeDb(mapping)

    result = apply_mapping_feedback(
        db,
        1,
        is_related=True,
        relevance_score=120,
        implementation_status="done",
        reason="  사람이 확인한 근거입니다.  ",
    )

    assert result is mapping
    assert mapping.is_related is True
    assert mapping.relevance_score == 100.0
    assert mapping.implementation_status == "판단불가"
    assert mapping.reason == "사람이 확인한 근거입니다."
    assert mapping.feedback_updated_at is not None
    assert db.committed is True
    assert db.refreshed is True


def test_risk_status_normalization_supports_common_aliases():
    assert normalize_implementation_status("completed") == "구현됨"
    assert normalize_implementation_status("partial") == "일부구현"
    assert normalize_implementation_status("") == "판단불가"

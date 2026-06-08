from src.services.code_review_service import _parse_json_object
from src.services.git_service import _parse_diff_git_path
from src.services.mapping_feedback_service import normalize_feedback_status
from src.services.risk_service import normalize_implementation_status


def test_parse_json_object_extracts_json_from_llm_text():
    parsed = _parse_json_object('prefix {"summary": "ok", "bug_findings": []} suffix')

    assert parsed == {"summary": "ok", "bug_findings": []}


def test_parse_diff_git_path_prefers_new_path_and_handles_delete():
    assert _parse_diff_git_path("diff --git a/src/old.py b/src/new.py") == "src/new.py"
    assert _parse_diff_git_path("diff --git a/src/old.py /dev/null") == "src/old.py"


def test_feedback_status_normalization_allows_known_values_only():
    assert normalize_feedback_status("구현됨") == "구현됨"
    assert normalize_feedback_status("done") == "판단불가"


def test_risk_status_normalization_supports_common_aliases():
    assert normalize_implementation_status("completed") == "구현됨"
    assert normalize_implementation_status("partial") == "일부구현"
    assert normalize_implementation_status("") == "판단불가"

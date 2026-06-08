from src.services.progress_service import implementation_analysis_status_label, implementation_evidence_count


def test_implementation_analysis_status_label_maps_saved_statuses():
    assert implementation_analysis_status_label("NOT_STARTED") == "구현전 추정"
    assert implementation_analysis_status_label("IN_PROGRESS") == "진행중 추정"
    assert implementation_analysis_status_label("COMPLETED") == "구현완료 추정"
    assert implementation_analysis_status_label("UNKNOWN") == "판단불가"


def test_implementation_analysis_status_label_handles_missing_or_unknown_values():
    assert implementation_analysis_status_label(None) == "분석없음"
    assert implementation_analysis_status_label("") == "분석없음"
    assert implementation_analysis_status_label("unexpected") == "판단불가"


def test_implementation_evidence_count_counts_only_lists():
    assert implementation_evidence_count([{"commit_hash": "a"}, {"commit_hash": "b"}]) == 2
    assert implementation_evidence_count(None) == 0
    assert implementation_evidence_count({"commit_hash": "a"}) == 0

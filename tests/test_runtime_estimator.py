from src.utils.runtime_estimator import estimate_runtime, format_runtime_range


def test_estimate_embedding_runtime_uses_conservative_range():
    estimate = estimate_runtime(50, "embedding")

    assert estimate.item_count == 50
    assert estimate.min_seconds == 50
    assert estimate.max_seconds == 250
    assert estimate.label == "약 1-5분"


def test_estimate_runtime_handles_zero_count():
    estimate = estimate_runtime(0, "mapping")

    assert estimate.item_count == 0
    assert estimate.label == "약 0분"


def test_format_runtime_range_uses_seconds_for_short_jobs():
    assert format_runtime_range(5, 30) == "약 5-30초"

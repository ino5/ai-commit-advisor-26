from types import SimpleNamespace

from src.services.program_implementation_analyzer import (
    STATUS_IN_PROGRESS,
    STATUS_NOT_STARTED,
    STATUS_UNKNOWN,
    _fallback_payload,
    _normalize_payload,
)


def _mapping(
    commit_hash: str = "a" * 40,
    relevance_score: float = 80,
    implementation_status: str = "일부구현",
    reason: str = "로그인 화면 변경과 관련된 커밋입니다.",
):
    commit = SimpleNamespace(commit_hash=commit_hash)
    return SimpleNamespace(
        commit=commit,
        relevance_score=relevance_score,
        implementation_status=implementation_status,
        reason=reason,
    )


def test_fallback_without_mappings_returns_not_started_with_korean_summary():
    result = _fallback_payload([])

    assert result["status"] == STATUS_NOT_STARTED
    assert "관련 커밋이 없어 구현 근거를 찾지 못했습니다" in result["summary"]
    assert "담당자 확인" in result["incomplete_features"][0]


def test_fallback_with_partial_or_high_relevance_returns_in_progress():
    result = _fallback_payload([_mapping(relevance_score=85, implementation_status="일부구현")])

    assert result["status"] == STATUS_IN_PROGRESS
    assert "전체 범위 완료 여부는 확인이 필요" in result["summary"]
    assert any("테스트/배포 여부" in item for item in result["incomplete_features"])


def test_normalize_payload_excludes_unknown_evidence_commit_hash():
    known_hash = "b" * 40
    unknown_hash = "c" * 40
    payload = {
        "status": STATUS_IN_PROGRESS,
        "summary": "관련 구현은 있으나 검증이 필요합니다.",
        "completed_features": ["일부 화면 연결"],
        "incomplete_features": ["테스트 여부 확인 필요"],
        "evidence_commits": [
            {"commit_hash": known_hash, "reason": "입력에 있는 커밋입니다."},
            {"commit_hash": unknown_hash, "reason": "입력에 없는 커밋입니다."},
        ],
    }

    result = _normalize_payload(payload, [_mapping(commit_hash=known_hash)])

    evidence_hashes = [item["commit_hash"] for item in result["evidence_commits"]]
    assert known_hash in evidence_hashes
    assert unknown_hash not in evidence_hashes


def test_fallback_result_contains_korean_incomplete_guidance():
    result = _fallback_payload([_mapping(relevance_score=10, implementation_status="판단불가")])

    assert result["status"] == STATUS_UNKNOWN
    assert "구현 의미가 불명확" in result["summary"]
    assert any("테스트/배포 여부" in item for item in result["incomplete_features"])


def test_normalize_payload_converts_invalid_status_to_unknown():
    known_hash = "d" * 40
    payload = {
        "status": "DONE",
        "summary": "완료라고 단정할 수 없습니다.",
        "completed_features": [],
        "incomplete_features": ["근거 부족"],
        "evidence_commits": [{"commit_hash": known_hash, "reason": "근거 커밋입니다."}],
    }

    result = _normalize_payload(payload, [_mapping(commit_hash=known_hash)])

    assert result["status"] == STATUS_UNKNOWN

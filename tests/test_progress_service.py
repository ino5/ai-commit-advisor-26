from __future__ import annotations

import uuid

from src.db.models import GitCommit, ProgramCommitMapping, ProgramImplementationStatus
from src.services.progress_service import (
    implementation_analysis_signature,
    implementation_analysis_status_label,
    implementation_evidence_count,
    resolve_ai_progress,
)


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


def _mapping(status: str, *, commit_hash: str | None = None) -> ProgramCommitMapping:
    commit = GitCommit(commit_hash=commit_hash or uuid.uuid4().hex, message=status)
    return ProgramCommitMapping(
        commit=commit,
        relevance_score=80,
        is_related=True,
        implementation_status=status,
        reason=status,
    )


def test_resolve_ai_progress_requires_current_program_implementation_analysis():
    partial_mapping = _mapping("일부구현")

    missing = resolve_ai_progress([partial_mapping], None)
    assert missing.ai_progress_rate is None
    assert missing.ai_progress_state_label == "분석 필요"
    assert missing.mapping_ai_progress_rate == 50.0

    current_status = ProgramImplementationStatus(
        status="COMPLETED",
        commit_hash_signature=implementation_analysis_signature([partial_mapping]),
    )
    current = resolve_ai_progress([partial_mapping], current_status)
    assert current.ai_progress_rate == 100.0
    assert current.ai_progress_state_label == "최신 분석"
    assert current.mapping_ai_progress_rate == 50.0

    completed_mapping = _mapping("구현완료")
    stale = resolve_ai_progress([partial_mapping, completed_mapping], current_status)
    assert stale.ai_progress_rate is None
    assert stale.ai_progress_state_label == "재분석 필요"
    assert stale.mapping_ai_progress_rate == 100.0

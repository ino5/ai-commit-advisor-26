from src.rag.source_index_service import count_head_mismatch_chunks, source_index_needs_refresh
from src.rag.source_verifier import verify_source_file_chunk


def test_source_index_needs_refresh_when_index_is_empty_for_repo():
    assert (
        source_index_needs_refresh(
            repo_path="C:/repo",
            current_head_hash="abc123",
            indexed_head_hashes=[],
            source_chunk_count=0,
            stale_chunk_count=0,
            invalid_chunk_count=0,
        )
        is True
    )


def test_source_index_needs_refresh_when_head_changed():
    assert (
        source_index_needs_refresh(
            repo_path="C:/repo",
            current_head_hash="new-head",
            indexed_head_hashes=["old-head"],
            source_chunk_count=10,
            stale_chunk_count=0,
            invalid_chunk_count=0,
        )
        is True
    )


def test_source_index_needs_refresh_when_any_chunk_is_unverified():
    assert (
        source_index_needs_refresh(
            repo_path="C:/repo",
            current_head_hash="same-head",
            indexed_head_hashes=["same-head"],
            source_chunk_count=10,
            stale_chunk_count=1,
            invalid_chunk_count=0,
        )
        is True
    )


def test_source_index_is_current_when_head_and_chunks_match():
    assert (
        source_index_needs_refresh(
            repo_path="C:/repo",
            current_head_hash="same-head",
            indexed_head_hashes=["same-head"],
            source_chunk_count=10,
            stale_chunk_count=0,
            invalid_chunk_count=0,
        )
        is False
    )


def test_source_index_without_repo_does_not_request_refresh():
    assert (
        source_index_needs_refresh(
            repo_path=None,
            current_head_hash=None,
            indexed_head_hashes=[],
            source_chunk_count=10,
            stale_chunk_count=10,
            invalid_chunk_count=0,
        )
        is False
    )


def test_count_head_mismatch_chunks_when_indexed_head_differs():
    count = count_head_mismatch_chunks(
        "current-head",
        [
            {"indexed_head_hash": "current-head"},
            {"indexed_head_hash": "old-head"},
            {"indexed_head_hash": "old-head"},
            {},
        ],
    )

    assert count == 2


def test_count_head_mismatch_chunks_is_zero_when_heads_match():
    count = count_head_mismatch_chunks(
        "same-head",
        [
            {"indexed_head_hash": "same-head"},
            {"indexed_head_hash": "same-head"},
        ],
    )

    assert count == 0


def test_source_file_chunk_with_incomplete_metadata_is_invalid(tmp_path):
    verification = verify_source_file_chunk(str(tmp_path), {"file_path": "src/app.py"})

    assert verification.status == "invalid"

from src.rag.source_index_service import source_index_needs_refresh


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

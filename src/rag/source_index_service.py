from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import DocumentChunk, Project, VectorItem
from src.rag.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    SOURCE_FILE_TYPE,
    ChunkBuildResult,
    build_source_file_chunks,
)
from src.rag.embedding_client import EmbeddingClient
from src.rag.source_verifier import SourceVerification, hash_text
from src.rag.vector_store import EmbeddingBuildResult, VectorStore
from src.services.git_service import get_head_commit_hash


@dataclass
class SourceIndexStatus:
    repo_path: str | None
    current_head_hash: str | None
    latest_indexed_head_hash: str | None
    indexed_head_hashes: list[str]
    source_chunk_count: int
    source_vector_count: int
    head_mismatch_chunk_count: int
    stale_chunk_count: int
    invalid_chunk_count: int
    needs_reindex: bool
    errors: list[str]


@dataclass
class SourceIndexRefreshResult:
    chunk_result: ChunkBuildResult
    embedding_result: EmbeddingBuildResult
    status: SourceIndexStatus
    deleted_unverified_count: int = 0


def source_index_needs_refresh(
    *,
    repo_path: str | None,
    current_head_hash: str | None,
    indexed_head_hashes: list[str],
    source_chunk_count: int,
    stale_chunk_count: int,
    invalid_chunk_count: int,
) -> bool:
    if not repo_path:
        return False
    if source_chunk_count == 0:
        return True
    if current_head_hash and current_head_hash not in indexed_head_hashes:
        return True
    return stale_chunk_count > 0 or invalid_chunk_count > 0


def count_head_mismatch_chunks(current_head_hash: str | None, metadata_rows: list[dict]) -> int:
    if not current_head_hash:
        return 0
    return sum(
        1
        for metadata in metadata_rows
        if metadata.get("indexed_head_hash") and metadata.get("indexed_head_hash") != current_head_hash
    )


def _verify_source_file_chunk_at_head(
    repo_path: str,
    metadata: dict,
    current_head_hash: str | None,
) -> SourceVerification:
    file_path = metadata.get("file_path")
    line_start = metadata.get("line_start")
    line_end = metadata.get("line_end")
    expected_chunk_hash = metadata.get("chunk_content_hash")
    indexed_head_hash = metadata.get("indexed_head_hash")

    if not file_path or not line_start or not line_end or not expected_chunk_hash:
        return SourceVerification("invalid", "source_file metadata is incomplete", current_head_hash)
    if indexed_head_hash and current_head_hash and indexed_head_hash != current_head_hash:
        return SourceVerification("stale", "repository HEAD changed since indexing", current_head_hash)

    repo_root = Path(repo_path).expanduser().resolve()
    target = (repo_root / str(file_path)).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError:
        return SourceVerification("invalid", "file_path escapes repository root", current_head_hash)
    if not target.exists() or not target.is_file():
        return SourceVerification("invalid", "source file no longer exists", current_head_hash)

    try:
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = int(line_start)
        end = int(line_end)
    except (OSError, TypeError, ValueError):
        return SourceVerification("invalid", "source file or line metadata could not be read", current_head_hash)
    if start < 1 or end < start or end > len(lines):
        return SourceVerification("invalid", "source line range no longer exists", current_head_hash)

    current_hash = hash_text("\n".join(lines[start - 1 : end]))
    if current_hash != expected_chunk_hash:
        return SourceVerification("stale", "source line range changed since indexing", current_head_hash)
    return SourceVerification("verified", "source chunk matches current file", current_head_hash)


def get_source_index_status(db: Session, project: Project) -> SourceIndexStatus:
    repo_path = project.git_repo_path
    errors: list[str] = []
    current_head_hash: str | None = None

    if repo_path:
        try:
            current_head_hash = get_head_commit_hash(Path(repo_path).expanduser().resolve())
        except Exception as exc:
            errors.append(f"Git HEAD 확인 실패: {exc}")
    else:
        errors.append("프로젝트에 Git 저장소 경로가 등록되지 않았습니다.")

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.project_id == project.id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
        .order_by(DocumentChunk.id)
        .all()
    )
    source_chunk_count = len(chunks)
    source_vector_count = (
        db.query(VectorItem)
        .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
        .filter(DocumentChunk.project_id == project.id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
        .count()
    )

    indexed_head_hashes = sorted(
        {
            str((chunk.raw_metadata or {}).get("indexed_head_hash") or "")
            for chunk in chunks
            if (chunk.raw_metadata or {}).get("indexed_head_hash")
        }
    )
    latest_indexed_head_hash = indexed_head_hashes[-1] if indexed_head_hashes else None
    metadata_rows = [chunk.raw_metadata or {} for chunk in chunks]
    head_mismatch_chunk_count = count_head_mismatch_chunks(current_head_hash, metadata_rows)

    stale_chunk_count = 0
    invalid_chunk_count = 0
    if repo_path:
        for chunk in chunks:
            verification = _verify_source_file_chunk_at_head(repo_path, chunk.raw_metadata or {}, current_head_hash)
            if verification.status == "stale":
                stale_chunk_count += 1
            elif verification.status == "invalid":
                invalid_chunk_count += 1
    elif chunks:
        invalid_chunk_count = source_chunk_count

    needs_reindex = source_index_needs_refresh(
        repo_path=repo_path,
        current_head_hash=current_head_hash,
        indexed_head_hashes=indexed_head_hashes,
        source_chunk_count=source_chunk_count,
        stale_chunk_count=stale_chunk_count,
        invalid_chunk_count=invalid_chunk_count,
    )

    return SourceIndexStatus(
        repo_path=repo_path,
        current_head_hash=current_head_hash,
        latest_indexed_head_hash=latest_indexed_head_hash,
        indexed_head_hashes=indexed_head_hashes,
        source_chunk_count=source_chunk_count,
        source_vector_count=source_vector_count,
        head_mismatch_chunk_count=head_mismatch_chunk_count,
        stale_chunk_count=stale_chunk_count,
        invalid_chunk_count=invalid_chunk_count,
        needs_reindex=needs_reindex,
        errors=errors,
    )


def clear_source_file_index(db: Session, project_id: int) -> int:
    chunk_ids = select(DocumentChunk.id).where(
        DocumentChunk.project_id == project_id,
        DocumentChunk.source_type == SOURCE_FILE_TYPE,
    )
    db.query(VectorItem).filter(VectorItem.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
    deleted_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(deleted_chunks or 0)


def remove_unverified_source_file_chunks(
    db: Session,
    project: Project,
    current_head_hash: str | None = None,
) -> int:
    if not project.git_repo_path:
        return 0
    if current_head_hash is None:
        current_head_hash = get_head_commit_hash(Path(project.git_repo_path).expanduser().resolve())

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.project_id == project.id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
        .all()
    )
    delete_ids = [
        chunk.id
        for chunk in chunks
        if not _verify_source_file_chunk_at_head(project.git_repo_path, chunk.raw_metadata or {}, current_head_hash).is_verified
    ]
    if not delete_ids:
        return 0

    db.query(VectorItem).filter(VectorItem.chunk_id.in_(delete_ids)).delete(synchronize_session=False)
    deleted_count = db.query(DocumentChunk).filter(DocumentChunk.id.in_(delete_ids)).delete(synchronize_session=False)
    db.commit()
    return int(deleted_count or 0)


def refresh_source_file_index(
    db: Session,
    project: Project,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    embed_after_refresh: bool = False,
    embedding_limit: int = 100,
) -> SourceIndexRefreshResult:
    if not project.git_repo_path:
        raise ValueError("Git 저장소 경로가 등록된 프로젝트만 source_file 인덱스를 갱신할 수 있습니다.")

    current_head_hash = get_head_commit_hash(Path(project.git_repo_path).expanduser().resolve())
    chunk_result = build_source_file_chunks(
        db=db,
        project_id=project.id,
        repo_path=project.git_repo_path,
        chunk_size=chunk_size,
        overlap=overlap,
    )
    deleted_unverified_count = remove_unverified_source_file_chunks(db, project, current_head_hash)
    embedding_result = EmbeddingBuildResult()
    if embed_after_refresh:
        client = EmbeddingClient()
        embedding_result = VectorStore(db).embed_missing_chunks(
            client,
            project_id=project.id,
            source_types=[SOURCE_FILE_TYPE],
            limit=embedding_limit,
        )
    status = get_source_index_status(db, project)
    return SourceIndexRefreshResult(
        chunk_result=chunk_result,
        embedding_result=embedding_result,
        status=status,
        deleted_unverified_count=deleted_unverified_count,
    )

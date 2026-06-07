from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from src.db.models import CommitFile, DocumentChunk, GitCommit, Program


DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 100
MAX_DIFF_TEXT_LENGTH = 4000


@dataclass
class ChunkBuildResult:
    created_count: int = 0
    skipped_count: int = 0


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into simple overlapping chunks for future RAG indexing."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be greater than or equal to 0 and smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    clean_text = text.strip()
    while start < len(clean_text):
        end = start + chunk_size
        chunks.append(clean_text[start:end])
        start = end - overlap
    return chunks


def _chunk_exists(db: Session, source_type: str, source_id: str, chunk_index: int) -> bool:
    return (
        db.query(DocumentChunk.id)
        .filter(
            DocumentChunk.source_type == source_type,
            DocumentChunk.source_id == source_id,
            DocumentChunk.chunk_index == chunk_index,
        )
        .first()
        is not None
    )


def _save_source_chunks(
    db: Session,
    project_id: int,
    source_type: str,
    source_id: str,
    text: str,
    metadata: dict,
    chunk_size: int,
    overlap: int,
) -> ChunkBuildResult:
    result = ChunkBuildResult()
    for index, chunk in enumerate(chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
        if _chunk_exists(db, source_type, source_id, index):
            result.skipped_count += 1
            continue

        db.add(
            DocumentChunk(
                project_id=project_id,
                source_type=source_type,
                source_id=source_id,
                chunk_index=index,
                chunk_text=chunk,
                raw_metadata={**metadata, "embedding_status": "pending"},
            )
        )
        result.created_count += 1
    return result


def _program_chunk_text(program: Program) -> str:
    return "\n".join(
        [
            f"program_id: {program.program_id or ''}",
            f"program_name: {program.program_name or ''}",
            f"screen_name: {program.screen_name or ''}",
            f"module: {program.module or ''}",
            f"description: {program.description or ''}",
        ]
    ).strip()


def _commit_chunk_text(commit: GitCommit) -> str:
    return "\n".join(
        [
            f"commit_hash: {commit.commit_hash}",
            f"message: {commit.message or ''}",
            f"author: {commit.author_name or commit.author or ''}",
        ]
    ).strip()


def _commit_file_chunk_text(file: CommitFile) -> str:
    diff_text = (file.diff_text or "")[:MAX_DIFF_TEXT_LENGTH]
    return "\n".join(
        [
            f"file_path: {file.file_path}",
            f"change_type: {file.change_type or ''}",
            "diff_text:",
            diff_text,
        ]
    ).strip()


def build_project_chunks(
    db: Session,
    project_id: int,
    include_programs: bool = True,
    include_commits: bool = True,
    include_commit_files: bool = True,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ChunkBuildResult:
    result = ChunkBuildResult()

    if include_programs:
        programs = db.query(Program).filter(Program.project_id == project_id).all()
        for program in programs:
            partial = _save_source_chunks(
                db=db,
                project_id=project_id,
                source_type="program",
                source_id=str(program.id),
                text=_program_chunk_text(program),
                metadata={
                    "program_db_id": program.id,
                    "program_id": program.program_id,
                    "program_name": program.program_name,
                },
                chunk_size=chunk_size,
                overlap=overlap,
            )
            result.created_count += partial.created_count
            result.skipped_count += partial.skipped_count

    if include_commits or include_commit_files:
        commits = (
            db.query(GitCommit)
            .options(joinedload(GitCommit.files))
            .filter(GitCommit.project_id == project_id)
            .all()
        )
        for commit in commits:
            if include_commits:
                partial = _save_source_chunks(
                    db=db,
                    project_id=project_id,
                    source_type="commit",
                    source_id=str(commit.id),
                    text=_commit_chunk_text(commit),
                    metadata={"commit_id": commit.id, "commit_hash": commit.commit_hash},
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
                result.created_count += partial.created_count
                result.skipped_count += partial.skipped_count

            if include_commit_files:
                for file in commit.files:
                    partial = _save_source_chunks(
                        db=db,
                        project_id=project_id,
                        source_type="commit_file",
                        source_id=str(file.id),
                        text=_commit_file_chunk_text(file),
                        metadata={
                            "commit_file_id": file.id,
                            "commit_id": commit.id,
                            "commit_hash": commit.commit_hash,
                            "file_path": file.file_path,
                        },
                        chunk_size=chunk_size,
                        overlap=overlap,
                    )
                    result.created_count += partial.created_count
                    result.skipped_count += partial.skipped_count

    db.commit()
    return result

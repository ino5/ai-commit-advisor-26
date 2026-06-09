from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from src.db.models import CommitFile, DocumentChunk, GitCommit, Program
from src.services.git_service import get_head_commit_hash


DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 100
MAX_DIFF_TEXT_LENGTH = 4000
SOURCE_FILE_TYPE = "source_file"
MAX_SOURCE_FILE_BYTES = 300_000
SOURCE_FILE_EXTENSIONS = {
    ".cfg",
    ".css",
    ".csv",
    ".dockerfile",
    ".env",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsp",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
SOURCE_FILE_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}
SOURCE_FILE_EXCLUDED_SUFFIXES = {
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".pyc",
    ".svg",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}


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


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line_range_hash(lines: list[str], line_start: int, line_end: int) -> str:
    selected = "\n".join(lines[line_start - 1 : line_end])
    return _content_hash(selected)


def _is_source_file(path: Path, repo_root: Path) -> bool:
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        return False
    parts = set(relative.parts)
    if parts & SOURCE_FILE_EXCLUDED_DIRS:
        return False
    if path.suffix.lower() in SOURCE_FILE_EXCLUDED_SUFFIXES:
        return False
    if path.name.lower() in {"dockerfile", "makefile"}:
        return True
    return path.suffix.lower() in SOURCE_FILE_EXTENSIONS


def _read_text_file(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_SOURCE_FILE_BYTES:
            return None
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def chunk_lines(lines: list[str], chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    current_lines: list[str] = []
    current_start = 1

    for line_number, line in enumerate(lines, start=1):
        current_lines.append(line)
        if len("\n".join(current_lines)) < chunk_size:
            continue

        line_end = line_number
        chunks.append((current_start, line_end, "\n".join(current_lines)))
        if len(current_lines) == 1:
            current_lines = []
            current_start = line_number + 1
            continue
        overlap_lines = _overlap_lines(current_lines, overlap)
        current_lines = overlap_lines
        current_start = max(1, line_end - len(overlap_lines) + 1)

    if current_lines:
        chunks.append((current_start, current_start + len(current_lines) - 1, "\n".join(current_lines)))
    return chunks


def _overlap_lines(lines: list[str], overlap_chars: int) -> list[str]:
    if overlap_chars <= 0:
        return []
    selected: list[str] = []
    total = 0
    for line in reversed(lines):
        selected.append(line)
        total += len(line) + 1
        if total >= overlap_chars:
            break
    return list(reversed(selected))


def _chunk_exists(db: Session, project_id: int, source_type: str, source_id: str, chunk_index: int) -> bool:
    return (
        db.query(DocumentChunk.id)
        .filter(
            DocumentChunk.project_id == project_id,
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
        if _chunk_exists(db, project_id, source_type, source_id, index):
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


def _delete_source_file_chunks_for_path(db: Session, project_id: int, file_path: str) -> int:
    return (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.project_id == project_id,
            DocumentChunk.source_type == SOURCE_FILE_TYPE,
            DocumentChunk.raw_metadata["file_path"].astext == file_path,
        )
        .delete(synchronize_session=False)
    )


def build_source_file_chunks(
    db: Session,
    project_id: int,
    repo_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ChunkBuildResult:
    result = ChunkBuildResult()
    repo_root = Path(repo_path).expanduser().resolve()
    if not repo_root.exists():
        raise ValueError(f"Repository path does not exist: {repo_root}")

    indexed_head_hash = get_head_commit_hash(repo_root)
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or not _is_source_file(path, repo_root):
            continue

        text = _read_text_file(path)
        if text is None:
            result.skipped_count += 1
            continue

        relative_path = path.relative_to(repo_root).as_posix()
        file_hash = _content_hash(text)
        existing = (
            db.query(DocumentChunk.id)
            .filter(
                DocumentChunk.project_id == project_id,
                DocumentChunk.source_type == SOURCE_FILE_TYPE,
                DocumentChunk.raw_metadata["file_path"].astext == relative_path,
                DocumentChunk.raw_metadata["content_hash"].astext == file_hash,
                DocumentChunk.raw_metadata["indexed_head_hash"].astext == (indexed_head_hash or ""),
            )
            .first()
        )
        if existing is not None:
            result.skipped_count += 1
            continue

        _delete_source_file_chunks_for_path(db, project_id, relative_path)
        lines = text.splitlines()
        if not lines:
            result.skipped_count += 1
            continue

        for index, (line_start, line_end, chunk) in enumerate(chunk_lines(lines, chunk_size, overlap)):
            db.add(
                DocumentChunk(
                    project_id=project_id,
                    source_type=SOURCE_FILE_TYPE,
                    source_id=relative_path,
                    chunk_index=index,
                    chunk_text=chunk,
                    raw_metadata={
                        "source_snapshot": "HEAD",
                        "repo_path": str(repo_root),
                        "file_path": relative_path,
                        "extension": path.suffix.lower(),
                        "line_start": line_start,
                        "line_end": line_end,
                        "content_hash": file_hash,
                        "chunk_content_hash": _line_range_hash(lines, line_start, line_end),
                        "indexed_head_hash": indexed_head_hash or "",
                        "embedding_status": "pending",
                    },
                )
            )
            result.created_count += 1

    db.commit()
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
    include_source_files: bool = False,
    repo_path: str | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ChunkBuildResult:
    result = ChunkBuildResult()

    if include_source_files:
        if not repo_path:
            raise ValueError("repo_path is required when include_source_files=True")
        partial = build_source_file_chunks(
            db=db,
            project_id=project_id,
            repo_path=repo_path,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        result.created_count += partial.created_count
        result.skipped_count += partial.skipped_count

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

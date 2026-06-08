from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.services.git_service import get_head_commit_hash


@dataclass
class SourceVerification:
    status: str
    reason: str
    current_head_hash: str | None = None

    @property
    def is_verified(self) -> bool:
        return self.status == "verified"


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_source_file_chunk(repo_path: str, metadata: dict) -> SourceVerification:
    file_path = metadata.get("file_path")
    line_start = metadata.get("line_start")
    line_end = metadata.get("line_end")
    expected_chunk_hash = metadata.get("chunk_content_hash")
    indexed_head_hash = metadata.get("indexed_head_hash")

    if not file_path or not line_start or not line_end or not expected_chunk_hash:
        return SourceVerification("invalid", "source_file metadata is incomplete")

    repo_root = Path(repo_path).expanduser().resolve()
    target = (repo_root / str(file_path)).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError:
        return SourceVerification("invalid", "file_path escapes repository root")

    current_head_hash = get_head_commit_hash(repo_root)
    if indexed_head_hash and current_head_hash and indexed_head_hash != current_head_hash:
        return SourceVerification("stale", "repository HEAD changed since indexing", current_head_hash)

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


def annotate_retrieval_result(result: dict, repo_path: str | None) -> dict:
    annotated = dict(result)
    if result.get("source_type") != "source_file":
        annotated["verification_status"] = "historical" if result.get("source_type") in {"commit", "commit_file"} else "not_applicable"
        annotated["verification_reason"] = "not a current source file chunk"
        return annotated

    if not repo_path:
        annotated["verification_status"] = "invalid"
        annotated["verification_reason"] = "project has no git_repo_path"
        return annotated

    verification = verify_source_file_chunk(repo_path, result.get("metadata") or {})
    annotated["verification_status"] = verification.status
    annotated["verification_reason"] = verification.reason
    annotated["current_head_hash"] = verification.current_head_hash
    return annotated

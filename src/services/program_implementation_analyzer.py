from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, Program, ProgramCommitMapping, ProgramImplementationStatus
from src.services.llm_client import LLMClient


STATUS_NOT_STARTED = "NOT_STARTED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
STATUS_UNKNOWN = "UNKNOWN"
IMPLEMENTATION_STATUS_VALUES = {
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_UNKNOWN,
}

MAX_EVIDENCE_COMMITS = 10
MAX_FILES_PER_COMMIT = 12


@dataclass
class ProgramImplementationAnalysisResult:
    analyzed_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    results: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _parse_json(text: str) -> dict | None:
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= start:
            payload = json.loads(text[start : end + 1])
            return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        return None
    return None


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _commit_signature(commits: Iterable[GitCommit]) -> str:
    hashes = sorted(commit.commit_hash for commit in commits if commit.commit_hash)
    joined = "\n".join(hashes)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _commit_summary(mapping: ProgramCommitMapping) -> dict:
    commit = mapping.commit
    files = [
        {
            "path": file.file_path,
            "change_type": file.change_type,
        }
        for file in (commit.files or [])[:MAX_FILES_PER_COMMIT]
    ]
    return {
        "commit_hash": commit.commit_hash,
        "short_hash": commit.commit_hash[:12],
        "message": (commit.message or "").splitlines()[0],
        "author": commit.author_name or commit.author,
        "committed_at": commit.committed_at.isoformat() if commit.committed_at else None,
        "relevance_score": float(mapping.relevance_score or 0),
        "mapping_status": mapping.implementation_status,
        "mapping_reason": mapping.reason,
        "changed_files": files,
    }


def _build_prompt(program: Program, mappings: list[ProgramCommitMapping]) -> str:
    commits = [_commit_summary(mapping) for mapping in mappings[:MAX_EVIDENCE_COMMITS]]
    program_info = {
        "program_db_id": program.id,
        "program_id": program.program_id,
        "program_name": program.program_name,
        "screen_name": program.screen_name,
        "module": program.module,
        "description": program.description,
        "developer": program.developer,
        "planned_start_date": program.planned_start_date.isoformat() if program.planned_start_date else None,
        "planned_end_date": program.planned_end_date.isoformat() if program.planned_end_date else None,
        "plan_status": program.status,
        "plan_progress_rate": float(program.progress_rate or 0),
        "raw_metadata": program.raw_metadata,
    }
    return f"""
Analyze the implementation status of one development-plan program from its related Git commits.
Use the program plan, description, commit messages, changed files, and existing commit mapping analysis.
Do not decide from commit count alone.

Return only valid JSON in this shape:
{{
  "status": "NOT_STARTED | IN_PROGRESS | COMPLETED | UNKNOWN",
  "summary": "short Korean summary explaining the judgment",
  "completed_features": ["feature that appears implemented"],
  "incomplete_features": ["feature that appears incomplete or uncertain"],
  "evidence_commits": [
    {{
      "commit_hash": "full hash from input",
      "reason": "why this commit supports the judgment"
    }}
  ]
}}

Status rules:
- NOT_STARTED: no related implementation evidence exists.
- IN_PROGRESS: implementation evidence exists but completion is partial or still uncertain.
- COMPLETED: commits and analysis strongly indicate the described program is implemented.
- UNKNOWN: evidence is insufficient or contradictory.

[Program]
{json.dumps(program_info, ensure_ascii=False, default=str)}

[Related commits]
{json.dumps(commits, ensure_ascii=False, default=str)}
""".strip()


def _normalize_payload(payload: dict | None, mappings: list[ProgramCommitMapping]) -> dict:
    if not payload:
        return _fallback_payload(mappings)

    status = str(payload.get("status") or "").strip().upper()
    if status not in IMPLEMENTATION_STATUS_VALUES:
        status = STATUS_UNKNOWN

    evidence = payload.get("evidence_commits")
    if not isinstance(evidence, list):
        evidence = []
    normalized_evidence = []
    known_hashes = {mapping.commit.commit_hash for mapping in mappings if mapping.commit}
    for item in evidence:
        if not isinstance(item, dict):
            continue
        commit_hash = str(item.get("commit_hash") or "").strip()
        if commit_hash not in known_hashes:
            continue
        normalized_evidence.append(
            {
                "commit_hash": commit_hash,
                "short_hash": commit_hash[:12],
                "reason": str(item.get("reason") or "").strip(),
            }
        )

    if not normalized_evidence:
        normalized_evidence = _fallback_evidence(mappings)

    return {
        "status": status,
        "summary": str(payload.get("summary") or "").strip() or "No summary was returned by the analyzer.",
        "completed_features": _as_string_list(payload.get("completed_features")),
        "incomplete_features": _as_string_list(payload.get("incomplete_features")),
        "evidence_commits": normalized_evidence[:MAX_EVIDENCE_COMMITS],
    }


def _fallback_evidence(mappings: list[ProgramCommitMapping]) -> list[dict]:
    sorted_mappings = sorted(mappings, key=lambda mapping: float(mapping.relevance_score or 0), reverse=True)
    return [
        {
            "commit_hash": mapping.commit.commit_hash,
            "short_hash": mapping.commit.commit_hash[:12],
            "reason": mapping.reason or "Related commit mapping evidence.",
        }
        for mapping in sorted_mappings[:MAX_EVIDENCE_COMMITS]
        if mapping.commit
    ]


def _fallback_payload(mappings: list[ProgramCommitMapping]) -> dict:
    if not mappings:
        return {
            "status": STATUS_NOT_STARTED,
            "summary": "No related commits are mapped to this program.",
            "completed_features": [],
            "incomplete_features": ["Implementation evidence has not been found."],
            "evidence_commits": [],
        }

    mapping_statuses = {str(mapping.implementation_status or "").lower() for mapping in mappings}
    high_score_count = sum(1 for mapping in mappings if float(mapping.relevance_score or 0) >= 70)
    has_completion_hint = any(
        keyword in status
        for status in mapping_statuses
        for keyword in ("complete", "completed", "implemented", "done", "완료")
    )
    has_partial_hint = any(keyword in status for status in mapping_statuses for keyword in ("partial", "progress", "일부"))

    if has_completion_hint and high_score_count > 0:
        status = STATUS_COMPLETED
        summary = "Mapped commit analysis contains completion signals for this program."
        completed_features = ["Implementation appears complete based on mapped commit analysis."]
        incomplete_features = []
    elif has_partial_hint or high_score_count > 0 or len(mappings) > 1:
        status = STATUS_IN_PROGRESS
        summary = "Related commits exist, but the available evidence does not prove full completion."
        completed_features = ["Some implementation work is visible in related commits."]
        incomplete_features = ["Completion of the full program scope is still uncertain."]
    else:
        status = STATUS_UNKNOWN
        summary = "Related commits exist, but their implementation meaning is unclear."
        completed_features = []
        incomplete_features = ["The mapped commits are not enough to judge implementation status."]

    return {
        "status": status,
        "summary": summary,
        "completed_features": completed_features,
        "incomplete_features": incomplete_features,
        "evidence_commits": _fallback_evidence(mappings),
    }


class ProgramImplementationAnalyzer:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient(max_tokens=900)

    def analyze_program(
        self,
        db: Session,
        program_id: int,
        skip_unchanged: bool = True,
    ) -> tuple[ProgramImplementationStatus, bool]:
        program = (
            db.query(Program)
            .options(
                joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit).joinedload(GitCommit.files),
                joinedload(Program.implementation_status_result),
            )
            .filter(Program.id == program_id)
            .one()
        )
        mappings = [
            mapping
            for mapping in (program.mappings or [])
            if mapping.commit is not None and mapping.is_related is not False
        ]
        mappings.sort(
            key=lambda mapping: (
                float(mapping.relevance_score or 0),
                mapping.commit.committed_at or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        )
        signature = _commit_signature(mapping.commit for mapping in mappings if mapping.commit)
        saved = program.implementation_status_result
        if saved and skip_unchanged and saved.commit_hash_signature == signature:
            return saved, False

        payload = None
        raw_response = None
        if mappings:
            prompt = _build_prompt(program, mappings)
            try:
                response = self.llm_client.generate(prompt)
                payload = _parse_json(response.text)
                raw_response = {
                    "llm": response.raw,
                    "text": response.text,
                    "prompt_length": len(prompt),
                }
            except Exception as exc:
                raw_response = {"llm_error": str(exc)}

        normalized = _normalize_payload(payload, mappings)
        if saved is None:
            saved = ProgramImplementationStatus(program_id=program.id)
            db.add(saved)

        saved.status = normalized["status"]
        saved.summary = normalized["summary"]
        saved.completed_features = normalized["completed_features"]
        saved.incomplete_features = normalized["incomplete_features"]
        saved.evidence_commits = normalized["evidence_commits"]
        saved.commit_hash_signature = signature
        saved.analyzed_at = datetime.now(timezone.utc)
        saved.raw_response = raw_response or {"fallback": True}
        db.flush()
        return saved, True

    def analyze_project(self, db: Session, project_id: int, skip_unchanged: bool = True) -> ProgramImplementationAnalysisResult:
        result = ProgramImplementationAnalysisResult()
        program_ids = [
            row[0]
            for row in db.query(Program.id)
            .filter(Program.project_id == project_id)
            .order_by(Program.program_name)
            .all()
        ]
        for program_id in program_ids:
            try:
                status_result, analyzed = self.analyze_program(db, program_id, skip_unchanged=skip_unchanged)
                if analyzed:
                    result.analyzed_count += 1
                else:
                    result.skipped_count += 1
                result.results.append(
                    {
                        "program_id": program_id,
                        "status": status_result.status,
                        "summary": status_result.summary,
                        "analyzed": analyzed,
                    }
                )
            except Exception as exc:
                result.failed_count += 1
                result.errors.append(f"program_id={program_id}: {exc}")
        db.commit()
        return result


def get_program_implementation_status(db: Session, program_id: int) -> ProgramImplementationStatus | None:
    return (
        db.query(ProgramImplementationStatus)
        .filter(ProgramImplementationStatus.program_id == program_id)
        .one_or_none()
    )

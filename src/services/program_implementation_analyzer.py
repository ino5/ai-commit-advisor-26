from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, Program, ProgramCommitMapping, ProgramImplementationStatus
from src.services.llm_client import LLMClient, generate_structured
from src.services.structured_output_schemas import PROGRAM_IMPLEMENTATION_SCHEMA


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
개발계획에 등록된 단일 프로그램의 구현상태를 보수적으로 분석하세요.

입력 데이터는 프로그램 계획/설명, 관련 커밋 메시지, 변경 파일, 기존 프로그램-커밋 매핑 근거입니다.
커밋 수만으로 구현상태를 판단하지 마세요.
커밋만으로 실제 배포 완료, 테스트 완료, 검증 완료를 확정할 수 없습니다.
완료 신호가 있어도 근거가 약하거나 범위가 불명확하면 IN_PROGRESS 또는 UNKNOWN을 선택하세요.
테스트, 예외처리, 화면 연결, 배포 여부가 확인되지 않으면 incomplete_features에 불확실성으로 남기세요.

반드시 valid JSON만 반환하세요. JSON 밖의 설명 문장을 쓰지 마세요.
summary, completed_features, incomplete_features, evidence_commits.reason은 모두 한국어로 작성하세요.

JSON 형식:
{{
  "status": "NOT_STARTED | IN_PROGRESS | COMPLETED | UNKNOWN",
  "summary": "판단 근거를 짧게 설명하는 한국어 요약",
  "completed_features": ["완료된 것으로 보이는 기능"],
  "incomplete_features": ["미완료 또는 확인이 필요한 기능/불확실성"],
  "evidence_commits": [
    {{
      "commit_hash": "입력에 있는 full commit hash",
      "reason": "이 커밋이 판단 근거가 되는 이유"
    }}
  ]
}}

상태 판단 기준:
- NOT_STARTED: 관련 구현 근거가 없음.
- IN_PROGRESS: 구현 근거는 있으나 전체 범위 완료를 확정할 수 없음.
- COMPLETED: 프로그램 설명/계획 범위와 관련된 핵심 구현 근거가 충분하고, 미완료 신호가 뚜렷하지 않은 경우에만 선택.
- UNKNOWN: 근거가 부족하거나 충돌하거나 의미가 불명확함.

COMPLETED 선택 주의:
- 단순히 관련 커밋이 많거나 관련도 점수가 높다는 이유만으로 COMPLETED를 선택하지 마세요.
- 테스트 완료, 예외처리, 화면 연결, 배포/검증 여부가 입력에서 확인되지 않으면 해당 내용을 incomplete_features에 남기세요.
- 완료로 보이는 커밋이 있어도 프로그램 전체 범위를 덮는지 불명확하면 IN_PROGRESS 또는 UNKNOWN을 선택하세요.

[프로그램 정보]
{json.dumps(program_info, ensure_ascii=False, default=str)}

[관련 커밋 및 기존 매핑 근거]
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
        "summary": str(payload.get("summary") or "").strip() or "분석 요약이 반환되지 않았습니다.",
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
            "reason": mapping.reason or "관련 커밋 매핑 근거입니다.",
        }
        for mapping in sorted_mappings[:MAX_EVIDENCE_COMMITS]
        if mapping.commit
    ]


def _fallback_payload(mappings: list[ProgramCommitMapping]) -> dict:
    if not mappings:
        return {
            "status": STATUS_NOT_STARTED,
            "summary": "관련 커밋이 없어 구현 근거를 찾지 못했습니다.",
            "completed_features": [],
            "incomplete_features": ["관련 구현 근거가 없어 실제 구현 여부는 담당자 확인이 필요합니다."],
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
        status = STATUS_IN_PROGRESS
        summary = "매핑 결과에 완료 신호가 있으나 실제 완료 여부는 담당자 검증이 필요합니다."
        completed_features = ["관련 커밋과 매핑 근거에서 구현 완료 신호가 일부 확인됩니다."]
        incomplete_features = [
            "프로그램 전체 범위 완료 여부는 추가 확인이 필요합니다.",
            "변경 파일과 커밋 메시지만으로 테스트/배포 여부는 확인할 수 없습니다.",
        ]
    elif has_partial_hint or high_score_count > 0 or len(mappings) > 1:
        status = STATUS_IN_PROGRESS
        summary = "관련 커밋은 있으나 전체 범위 완료 여부는 확인이 필요합니다."
        completed_features = ["관련 커밋에서 일부 구현 작업이 확인됩니다."]
        incomplete_features = [
            "전체 프로그램 범위의 완료 여부는 아직 불확실합니다.",
            "변경 파일과 커밋 메시지만으로 테스트/배포 여부는 확인할 수 없습니다.",
        ]
    else:
        status = STATUS_UNKNOWN
        summary = "관련 커밋은 있으나 구현 의미가 불명확해 판단할 수 없습니다."
        completed_features = []
        incomplete_features = [
            "매핑된 커밋만으로 구현상태를 판단하기 어렵습니다.",
            "변경 파일과 커밋 메시지만으로 테스트/배포 여부는 확인할 수 없습니다.",
        ]

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
                response = generate_structured(
                    self.llm_client,
                    prompt,
                    schema=PROGRAM_IMPLEMENTATION_SCHEMA,
                    schema_name="program_implementation_status",
                )
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

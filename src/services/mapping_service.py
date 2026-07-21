from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session, joinedload

from src.db.models import AnalysisRun, GitCommit, Program, ProgramCommitMapping
from src.rag.retriever import Retriever
from src.services.ai_invocation_service import record_ai_invocation
from src.services.llm_client import LLMClient, generate_structured
from src.services.structured_output_schemas import COMMIT_MAPPING_SCHEMA, PAIR_MAPPING_SCHEMA


MAX_COMMIT_TEXT_LENGTH = 2200
MAX_CHANGED_FILES = 20
MAX_DIFF_FILES = 3
MAX_DIFF_CHARS_PER_FILE = 400
DEFAULT_CANDIDATES_PER_PROGRAM = 10
DEFAULT_CANDIDATES_PER_COMMIT = 10

IMPLEMENTATION_STATUS_VALUES = {"구현완료", "일부구현", "판단불가"}


@dataclass
class MappingRunResult:
    analyzed_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    recent_results: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class CommitMappingProgress:
    total_count: int
    processed_count: int
    failed_count: int
    current_commit_hash: str | None = None


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    tokens = re.findall(r"[A-Za-z0-9가-힣]{2,}", text.lower())
    stop_words = {"src", "main", "java", "html", "class", "public", "private", "return", "null"}
    return {token for token in tokens if token not in stop_words}


def _program_text(program: Program) -> str:
    return "\n".join(
        [
            f"program_id: {program.program_id or ''}",
            f"program_name: {program.program_name or ''}",
            f"module: {program.module or ''}",
            f"screen_name: {program.screen_name or ''}",
            f"description: {program.description or ''}",
        ]
    )


def _program_identifier(program: Program) -> str:
    return program.program_id or f"internal-{program.id}"


def _commit_text(commit: GitCommit) -> str:
    file_lines = []
    diff_parts = []
    for file in commit.files[:MAX_CHANGED_FILES]:
        file_lines.append(f"- {file.change_type or ''}: {file.file_path}")
        if file.diff_text and len(diff_parts) < MAX_DIFF_FILES:
            diff_parts.append(f"### {file.file_path}\n{file.diff_text[:MAX_DIFF_CHARS_PER_FILE]}")

    text = "\n".join(
        [
            f"commit_hash: {commit.commit_hash}",
            f"message: {commit.message or ''}",
            f"author: {commit.author_name or commit.author or ''} <{commit.author_email or ''}>",
            "changed_files:",
            "\n".join(file_lines),
            "diff_text_snippets:",
            "\n\n".join(diff_parts),
        ]
    )
    return text[:MAX_COMMIT_TEXT_LENGTH]


def _candidate_score(program: Program, commit: GitCommit) -> int:
    program_tokens = _tokens(_program_text(program))
    commit_tokens = _tokens(commit.message)
    for file in commit.files:
        commit_tokens.update(_tokens(file.file_path))
        if file.diff_text:
            commit_tokens.update(_tokens(file.diff_text[:3000]))

    if not program_tokens or not commit_tokens:
        return 0
    overlap = program_tokens & commit_tokens
    score = min(100, int((len(overlap) / max(len(program_tokens), 1)) * 100))

    program_name = (program.program_name or "").lower()
    module = (program.module or "").lower()
    for file in commit.files:
        path = (file.file_path or "").lower()
        if module and module in path:
            score += 20
        if program_name and any(part in path for part in program_name.split()):
            score += 10
    return min(score, 100)


def _select_candidate_commits(program: Program, commits: list[GitCommit], limit: int) -> list[GitCommit]:
    scored = [(_candidate_score(program, commit), commit) for commit in commits]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: (item[0], item[1].committed_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return [commit for _, commit in scored[:limit]]


def _select_candidate_programs(commit: GitCommit, programs: list[Program], limit: int) -> list[Program]:
    scored = [(_candidate_score(program, commit), program) for program in programs]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: (item[0], item[1].program_id or "", item[1].program_name or ""), reverse=True)
    return [program for _, program in scored[:limit]]


def _build_commit_query_text(commit: GitCommit) -> str:
    return _commit_text(commit)


def _select_candidate_programs_with_rag(
    db: Session,
    commit: GitCommit,
    programs: list[Program],
    limit: int,
) -> list[Program]:
    token_candidates = _select_candidate_programs(commit, programs, limit)
    programs_by_id = {program.id: program for program in programs}
    merged: list[Program] = []
    seen = set()

    try:
        retriever = Retriever(db)
        rag_program_ids = retriever.retrieve_program_ids(
            _build_commit_query_text(commit),
            project_id=commit.project_id,
            limit=limit,
        )
    except Exception:
        rag_program_ids = []

    for program_id in rag_program_ids:
        program = programs_by_id.get(program_id)
        if program is not None and program.id not in seen:
            merged.append(program)
            seen.add(program.id)

    for program in token_candidates:
        if program.id not in seen:
            merged.append(program)
            seen.add(program.id)

    return merged[:limit]


def _build_commit_based_prompt(commit: GitCommit, programs: list[Program]) -> str:
    program_blocks = []
    for index, program in enumerate(programs, start=1):
        program_blocks.append(
            "\n".join(
                [
                    f"## Candidate {index}",
                    f"program_id: {_program_identifier(program)}",
                    f"program_name: {program.program_name or ''}",
                    f"module: {program.module or ''}",
                    f"screen_name: {program.screen_name or ''}",
                    f"description: {program.description or ''}",
                ]
            )
        )

    return f"""
You are a precise software analysis assistant.
Analyze one Git commit and choose zero or more related programs from the candidate list.
Return only valid JSON in this exact shape:
{{
  "related_programs": [
    {{
      "program_id": "P001",
      "relevance_score": 85,
      "implementation_status": "일부구현",
      "reason": "커밋 메시지와 변경 파일이 해당 프로그램의 서비스/화면과 관련됨"
    }}
  ]
}}

Rules:
- Choose only programs from the candidate list.
- If no candidate is related, return {{"related_programs": []}}.
- relevance_score must be 0-100.
- implementation_status must be one of: 구현완료, 일부구현, 판단불가.
- Keep each reason short.

[Git commit]
{_commit_text(commit)}

[Candidate programs]
{chr(10).join(program_blocks)}
""".strip()


def _build_prompt(program: Program, commit: GitCommit) -> str:
    return f"""
너는 프로그램 목록과 Git 커밋 정보를 비교해 관련 커밋을 추천하는 분석가다.

아래 JSON 형식으로만 답하라.
{{
  "relevance_score": 0-100 숫자,
  "is_related": true 또는 false,
  "reason": "판단 근거",
  "implementation_status": "구현됨" 또는 "일부구현" 또는 "판단불가"
}}

[프로그램]
{_program_text(program)}

[커밋]
{_commit_text(commit)}
""".strip()


def _parse_llm_result(text: str) -> dict | None:
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= start:
            return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return None


def _normalize_implementation_status(value: str | None) -> str:
    if value in IMPLEMENTATION_STATUS_VALUES:
        return value
    return "판단불가"


def _parse_commit_based_result(text: str, candidate_programs: list[Program]) -> list[dict] | None:
    payload = _parse_llm_result(text)
    if not isinstance(payload, dict):
        return None

    related_programs = payload.get("related_programs")
    if not isinstance(related_programs, list):
        return None

    candidates_by_program_id = {_program_identifier(program): program for program in candidate_programs}
    normalized: list[dict] = []
    for item in related_programs:
        if not isinstance(item, dict):
            continue

        program_id = item.get("program_id")
        program = candidates_by_program_id.get(program_id)
        if program is None:
            continue

        score = float(item.get("relevance_score") or 0)
        normalized.append(
            {
                "program": program,
                "program_id": program_id,
                "relevance_score": min(max(score, 0), 100),
                "implementation_status": _normalize_implementation_status(item.get("implementation_status")),
                "reason": str(item.get("reason") or ""),
            }
        )
    return normalized


def _fallback_result(program: Program, commit: GitCommit) -> dict:
    score = _candidate_score(program, commit)
    is_related = score >= 30
    if score >= 70:
        status = "구현됨"
    elif score >= 30:
        status = "일부구현"
    else:
        status = "판단불가"
    return {
        "relevance_score": score,
        "is_related": is_related,
        "reason": "LLM 응답을 구조화하지 못해 프로그램명/설명과 커밋 메시지, 변경 파일, diff 토큰 유사도로 판단했습니다.",
        "implementation_status": status,
    }


def _fallback_commit_based_results(commit: GitCommit, candidate_programs: list[Program], error: str) -> list[dict]:
    fallback_results: list[dict] = []
    for program in candidate_programs:
        parsed = _fallback_result(program, commit)
        if not parsed["is_related"]:
            continue
        parsed["reason"] = (
            "LLM 응답을 commit-based JSON으로 구조화하지 못해 "
            f"토큰 유사도 fallback을 사용했습니다. 오류: {error}"
        )
        fallback_results.append(
            {
                "program": program,
                "program_id": _program_identifier(program),
                "relevance_score": parsed["relevance_score"],
                "implementation_status": parsed["implementation_status"],
                "reason": parsed["reason"],
            }
        )
    return fallback_results


class MappingService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def analyze_commit(
        self,
        db: Session,
        commit: GitCommit,
        programs: list[Program],
        analysis_run: AnalysisRun,
        candidates_per_commit: int = DEFAULT_CANDIDATES_PER_COMMIT,
    ) -> MappingRunResult:
        result = MappingRunResult()
        candidate_programs = _select_candidate_programs_with_rag(db, commit, programs, candidates_per_commit)
        now = datetime.now(timezone.utc)

        if not candidate_programs:
            commit.mapping_analysis_status = "completed"
            commit.mapping_analyzed_at = now
            result.skipped_count = 1
            return result

        prompt = _build_commit_based_prompt(commit, candidate_programs)
        fallback_used = False
        raw_response: dict
        invocation_started_at = datetime.now(timezone.utc)
        invocation_finished_at: datetime
        response_length = 0
        invocation_error: str | None = None
        try:
            response = generate_structured(
                self.llm_client,
                prompt,
                schema=COMMIT_MAPPING_SCHEMA,
                schema_name="commit_mapping",
            )
            response_length = len(response.text or "")
            related_programs = _parse_commit_based_result(response.text, candidate_programs)
            if related_programs is None:
                raise ValueError("LLM response did not match commit-based mapping JSON format.")
        except Exception as exc:
            invocation_finished_at = datetime.now(timezone.utc)
            invocation_error = str(exc)
            fallback_used = True
            related_programs = _fallback_commit_based_results(commit, candidate_programs, str(exc))
            raw_response = {
                "llm_error": str(exc),
                "fallback": "token_similarity",
                "prompt_length": len(prompt),
                "candidate_program_ids": [_program_identifier(program) for program in candidate_programs],
            }
            if not related_programs:
                commit.mapping_analysis_status = "completed"
                commit.mapping_analyzed_at = now
                result.skipped_count = 1
                return result
        else:
            invocation_finished_at = datetime.now(timezone.utc)
            raw_response = {
                "llm": response.raw,
                "text": response.text,
                "prompt_length": len(prompt),
                "candidate_program_ids": [_program_identifier(program) for program in candidate_programs],
            }
        record_ai_invocation(
            db,
            project_id=commit.project_id,
            feature="commit_mapping",
            provider=self.llm_client.provider,
            model=self.llm_client.model,
            status="completed",
            mode="commit_based",
            fallback_used=fallback_used,
            validation_status="fallback" if fallback_used else "parsed",
            started_at=invocation_started_at,
            finished_at=invocation_finished_at,
            duration_ms=int((invocation_finished_at - invocation_started_at).total_seconds() * 1000),
            prompt_length=len(prompt),
            response_length=response_length,
            error_message=invocation_error,
            raw_metadata={
                "commit_hash": commit.commit_hash[:12],
                "candidate_program_count": len(candidate_programs),
                "analysis_run_id": analysis_run.id,
            },
        )

        for related in related_programs:
            program = related["program"]
            mapping = (
                db.query(ProgramCommitMapping)
                .filter(
                    ProgramCommitMapping.program_id == program.id,
                    ProgramCommitMapping.commit_id == commit.id,
                )
                .one_or_none()
            )
            if mapping is None:
                mapping = ProgramCommitMapping(program_id=program.id, commit_id=commit.id)
                db.add(mapping)
                result.created_count += 1
            else:
                result.updated_count += 1

            mapping.analysis_run_id = analysis_run.id
            mapping.relevance_score = related["relevance_score"]
            mapping.is_related = True
            mapping.implementation_status = related["implementation_status"]
            mapping.reason = related["reason"]
            mapping.raw_response = raw_response
            result.analyzed_count += 1
            result.recent_results.append(
                {
                    "program_id": _program_identifier(program),
                    "program_name": program.program_name,
                    "commit_hash": commit.commit_hash[:12],
                    "message": (commit.message or "").splitlines()[0],
                    "relevance_score": related["relevance_score"],
                    "is_related": True,
                    "implementation_status": related["implementation_status"],
                    "reason": related["reason"],
                    "fallback_used": fallback_used,
                }
            )

        commit.mapping_analysis_status = "completed"
        commit.mapping_analyzed_at = now
        return result

    def analyze_commits(
        self,
        db: Session,
        project_id: int,
        commit_ids: list[int] | None = None,
        candidates_per_commit: int = DEFAULT_CANDIDATES_PER_COMMIT,
        skip_completed: bool = True,
        progress_callback: Callable[[CommitMappingProgress], None] | None = None,
    ) -> MappingRunResult:
        result = MappingRunResult()
        query = (
            db.query(GitCommit)
            .options(joinedload(GitCommit.files))
            .filter(GitCommit.project_id == project_id)
            .order_by(GitCommit.committed_at.desc())
        )
        if commit_ids is not None:
            query = query.filter(GitCommit.id.in_(commit_ids))
        if skip_completed:
            query = query.filter(GitCommit.mapping_analysis_status.is_distinct_from("completed"))

        commits = query.all()
        programs = db.query(Program).filter(Program.project_id == project_id).all()
        analysis_run = AnalysisRun(
            project_id=project_id,
            run_type="commit_based_mapping",
            analysis_type="commit_based_mapping",
            status="running",
            total_count=len(commits),
            processed_count=0,
            failed_count=0,
            started_at=datetime.now(timezone.utc),
            parameters={
                "candidates_per_commit": candidates_per_commit,
                "skip_completed": skip_completed,
                "llm_provider": self.llm_client.provider,
                "llm_model": self.llm_client.model,
            },
        )
        db.add(analysis_run)
        db.flush()

        try:
            for commit in commits:
                partial = self.analyze_commit(
                    db,
                    commit=commit,
                    programs=programs,
                    analysis_run=analysis_run,
                    candidates_per_commit=candidates_per_commit,
                )
                result.analyzed_count += partial.analyzed_count
                result.created_count += partial.created_count
                result.updated_count += partial.updated_count
                result.skipped_count += partial.skipped_count
                result.failed_count += partial.failed_count
                result.errors.extend(partial.errors)
                result.recent_results.extend(partial.recent_results)

                analysis_run.processed_count = (analysis_run.processed_count or 0) + 1
                analysis_run.failed_count = result.failed_count
                db.commit()

                if progress_callback is not None:
                    progress_callback(
                        CommitMappingProgress(
                            total_count=len(commits),
                            processed_count=analysis_run.processed_count or 0,
                            failed_count=result.failed_count,
                            current_commit_hash=commit.commit_hash,
                        )
                    )

            analysis_run.status = "completed" if result.failed_count == 0 else "completed_with_errors"
            analysis_run.finished_at = datetime.now(timezone.utc)
            analysis_run.summary = (
                f"commits={len(commits)}, processed={analysis_run.processed_count or 0}, "
                f"failed={result.failed_count}, created={result.created_count}, updated={result.updated_count}"
            )
            db.add(analysis_run)
            db.commit()

            try:
                from src.services.program_implementation_analyzer import ProgramImplementationAnalyzer

                implementation_result = ProgramImplementationAnalyzer(self.llm_client).analyze_project(
                    db,
                    project_id=project_id,
                    skip_unchanged=True,
                )
                result.recent_results.append(
                    {
                        "stage": "program_implementation_status",
                        "analyzed": implementation_result.analyzed_count,
                        "skipped": implementation_result.skipped_count,
                        "failed": implementation_result.failed_count,
                    }
                )
                if implementation_result.errors:
                    result.errors.extend(implementation_result.errors)
            except Exception as exc:
                result.errors.append(f"Program implementation status analysis failed: {exc}")
        except Exception as exc:
            db.rollback()
            result.errors.append(str(exc))
            analysis_run.status = "failed"
            analysis_run.finished_at = datetime.now(timezone.utc)
            analysis_run.failed_count = (analysis_run.failed_count or 0) + 1
            analysis_run.summary = str(exc)
            db.add(analysis_run)
            db.commit()

        result.recent_results = result.recent_results[:100]
        return result

    def analyze_pair(self, program: Program, commit: GitCommit) -> dict:
        prompt = _build_prompt(program, commit)
        try:
            response = generate_structured(
                self.llm_client,
                prompt,
                schema=PAIR_MAPPING_SCHEMA,
                schema_name="program_commit_mapping",
            )
            parsed = _parse_llm_result(response.text) or _fallback_result(program, commit)
            raw_response = {
                "llm": response.raw,
                "text": response.text,
                "parsed": parsed,
                "prompt_length": len(prompt),
            }
        except Exception as exc:
            parsed = _fallback_result(program, commit)
            parsed["reason"] = f"LLM 호출 실패로 규칙 기반 fallback을 사용했습니다. 오류: {exc}"
            raw_response = {
                "llm_error": str(exc),
                "parsed": parsed,
                "prompt_length": len(prompt),
            }

        score = float(parsed.get("relevance_score") or 0)
        score = min(max(score, 0), 100)
        is_related = bool(parsed.get("is_related", score >= 30))
        implementation_status = parsed.get("implementation_status") or "판단불가"
        if implementation_status not in {"구현됨", "일부구현", "판단불가"}:
            implementation_status = "판단불가"

        return {
            "relevance_score": score,
            "is_related": is_related,
            "reason": str(parsed.get("reason") or ""),
            "implementation_status": implementation_status,
            "raw_response": raw_response,
        }

    def analyze_project(
        self,
        db: Session,
        project_id: int,
        candidates_per_program: int = DEFAULT_CANDIDATES_PER_PROGRAM,
        related_only: bool = False,
    ) -> MappingRunResult:
        result = MappingRunResult()
        analysis_run = AnalysisRun(
            project_id=project_id,
            run_type="program_commit_mapping",
            status="running",
            started_at=datetime.now(timezone.utc),
            parameters={
                "candidates_per_program": candidates_per_program,
                "related_only": related_only,
                "llm_provider": self.llm_client.provider,
                "llm_model": self.llm_client.model,
            },
        )
        db.add(analysis_run)
        db.flush()

        try:
            programs = db.query(Program).filter(Program.project_id == project_id).all()
            commits = (
                db.query(GitCommit)
                .options(joinedload(GitCommit.files))
                .filter(GitCommit.project_id == project_id)
                .order_by(GitCommit.committed_at.desc())
                .all()
            )

            for program in programs:
                candidates = _select_candidate_commits(program, commits, candidates_per_program)
                if not candidates:
                    result.skipped_count += 1
                    continue

                for commit in candidates:
                    analysis = self.analyze_pair(program, commit)
                    if related_only and not analysis["is_related"]:
                        result.skipped_count += 1
                        continue

                    mapping = (
                        db.query(ProgramCommitMapping)
                        .filter(
                            ProgramCommitMapping.program_id == program.id,
                            ProgramCommitMapping.commit_id == commit.id,
                        )
                        .one_or_none()
                    )
                    if mapping is None:
                        mapping = ProgramCommitMapping(program_id=program.id, commit_id=commit.id)
                        db.add(mapping)
                        result.created_count += 1
                    else:
                        result.updated_count += 1

                    mapping.analysis_run_id = analysis_run.id
                    mapping.relevance_score = analysis["relevance_score"]
                    mapping.is_related = analysis["is_related"]
                    mapping.implementation_status = analysis["implementation_status"]
                    mapping.reason = analysis["reason"]
                    mapping.raw_response = analysis["raw_response"]
                    result.analyzed_count += 1

                    result.recent_results.append(
                        {
                            "program_id": program.program_id,
                            "program_name": program.program_name,
                            "commit_hash": commit.commit_hash[:12],
                            "message": (commit.message or "").splitlines()[0],
                            "relevance_score": analysis["relevance_score"],
                            "is_related": analysis["is_related"],
                            "implementation_status": analysis["implementation_status"],
                            "reason": analysis["reason"],
                        }
                    )

            analysis_run.status = "completed"
            analysis_run.finished_at = datetime.now(timezone.utc)
            analysis_run.summary = (
                f"analyzed={result.analyzed_count}, created={result.created_count}, "
                f"updated={result.updated_count}, skipped={result.skipped_count}"
            )
            db.commit()

            try:
                from src.services.program_implementation_analyzer import ProgramImplementationAnalyzer

                implementation_result = ProgramImplementationAnalyzer(self.llm_client).analyze_project(
                    db,
                    project_id=project_id,
                    skip_unchanged=True,
                )
                result.recent_results.append(
                    {
                        "stage": "program_implementation_status",
                        "analyzed": implementation_result.analyzed_count,
                        "skipped": implementation_result.skipped_count,
                        "failed": implementation_result.failed_count,
                    }
                )
                if implementation_result.errors:
                    result.errors.extend(implementation_result.errors)
            except Exception as exc:
                result.errors.append(f"Program implementation status analysis failed: {exc}")
        except Exception as exc:
            db.rollback()
            result.errors.append(str(exc))
            analysis_run.status = "failed"
            analysis_run.finished_at = datetime.now(timezone.utc)
            analysis_run.summary = str(exc)
            db.add(analysis_run)
            db.commit()

        result.recent_results = result.recent_results[:100]
        return result

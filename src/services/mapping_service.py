from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from src.db.models import AnalysisRun, GitCommit, Program, ProgramCommitMapping
from src.services.llm_client import LLMClient


MAX_COMMIT_TEXT_LENGTH = 2200
MAX_CHANGED_FILES = 20
MAX_DIFF_FILES = 3
MAX_DIFF_CHARS_PER_FILE = 400
DEFAULT_CANDIDATES_PER_PROGRAM = 10


@dataclass
class MappingRunResult:
    analyzed_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    recent_results: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


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


class MappingService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def analyze_pair(self, program: Program, commit: GitCommit) -> dict:
        prompt = _build_prompt(program, commit)
        try:
            response = self.llm_client.generate(prompt)
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

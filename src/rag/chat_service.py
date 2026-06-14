from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.db.models import Project
from src.rag.query_expander import expand_query_with_standard_terms
from src.rag.retriever import Retriever
from src.rag.source_verifier import annotate_retrieval_result
from src.services.ai_invocation_service import record_ai_invocation
from src.services.llm_client import LLMClient


INSUFFICIENT_EVIDENCE_ANSWER = (
    "현재 검증된 소스 근거만으로는 답변하기 어렵습니다.\n"
    "추가 인덱싱 또는 검색어 조정이 필요합니다."
)


@dataclass
class RagChatAnswer:
    answer: str
    sources: list[dict] = field(default_factory=list)
    expanded_queries: list[str] = field(default_factory=list)
    matched_terms: list[dict] = field(default_factory=list)
    excluded_count: int = 0
    used_source_count: int = 0
    insufficient_evidence: bool = False
    errors: list[str] = field(default_factory=list)


def _format_context_block(index: int, source: dict, *, heading: str) -> str:
    metadata = source.get("metadata") or {}
    return "\n".join(
        [
            f"[{heading} {index}]",
            f"source_type: {source.get('source_type')}",
            f"file_path: {metadata.get('file_path') or source.get('source_id')}",
            f"line_start: {metadata.get('line_start')}",
            f"line_end: {metadata.get('line_end')}",
            f"verification_status: {source.get('verification_status')}",
            f"indexed_head_hash: {metadata.get('indexed_head_hash')}",
            f"commit_hash: {metadata.get('commit_hash')}",
            "text:",
            source.get("text") or "",
        ]
    )


def _build_prompt(question: str, current_sources: list[dict], historical_sources: list[dict]) -> str:
    current_blocks = [
        _format_context_block(index, source, heading="Verified current source")
        for index, source in enumerate(current_sources, start=1)
    ]
    historical_blocks = [
        _format_context_block(index, source, heading="Historical/reference evidence")
        for index, source in enumerate(historical_sources, start=1)
    ]
    historical_context = "\n\n".join(historical_blocks) if historical_blocks else "None"

    return f"""
You answer questions about the current source code.
Use verified source_file context as the only basis for statements about the current code.
If the verified source_file context does not contain enough evidence, answer exactly:
{INSUFFICIENT_EVIDENCE_ANSWER}
Do not speculate or fill gaps from general knowledge.
Do not describe commit history or deleted diff lines as current source code.
Commit and commit_file evidence, when present, is historical/reference evidence only.
Always mention file path and line range for claims about code.
Answer in Korean.
For normal answers, use Markdown prose and bullets.
Do not wrap the answer in JSON.
Do not use a fenced code block unless the user explicitly asks for code or JSON.
Copy file paths and line ranges only from the provided context metadata. Do not infer narrower line numbers.

[Question]
{question}

[Verified current source context]
{chr(10).join(current_blocks)}

[Historical/reference context]
{historical_context}
""".strip()


def _summarize_source(source: dict) -> str:
    metadata = source.get("metadata") or {}
    file_path = metadata.get("file_path") or source.get("source_id") or "-"
    line_start = metadata.get("line_start")
    line_end = metadata.get("line_end")
    line_range = f"{line_start}-{line_end}" if line_start and line_end else "-"
    source_type = source.get("source_type") or "-"
    status = source.get("verification_status") or "-"
    return f"- {file_path}:{line_range} ({source_type}, {status})"


def _expand_question(db: Session | None, project: Project, question: str):
    if db is None or project.id is None:
        return type(
            "QueryExpansionFallback",
            (),
            {"expanded_queries": [question], "matched_terms": [], "original_query": question},
        )()
    return expand_query_with_standard_terms(db, project.id, question)


def _retrieve_with_expansion(retriever: Retriever, expansion, *, top_k: int, project_id: int, source_types: list[str]) -> list[dict]:
    if hasattr(retriever, "retrieve_multi_query"):
        return retriever.retrieve_multi_query(
            expansion.expanded_queries,
            limit=top_k,
            project_id=project_id,
            source_types=source_types,
        )
    return retriever.retrieve(
        expansion.original_query,
        limit=top_k,
        project_id=project_id,
        source_types=source_types,
    )


def clean_llm_answer(text: str) -> str:
    stripped = text.strip()
    fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    payload = fence_match.group(1).strip() if fence_match else stripped
    if payload.startswith("{") and payload.endswith("}"):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return stripped
        for key in ("response", "answer", "content", "message"):
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                return _normalize_korean_answer_text(value.strip())
    return _normalize_korean_answer_text(stripped)


def _normalize_korean_answer_text(text: str) -> str:
    replacements = {
        "具体적으로": "구체적으로",
        "具体的으로": "구체적으로",
        "具体的": "구체적으로",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def ensure_answer_citations(answer: str, verified_sources: list[dict], *, max_sources: int = 3) -> str:
    if re.search(r"`?[\w./\\-]+\.[A-Za-z0-9]+:\d+-\d+`?", answer):
        return answer

    citation_lines = []
    for source in verified_sources[:max_sources]:
        metadata = source.get("metadata") or {}
        file_path = metadata.get("file_path") or source.get("source_id")
        line_start = metadata.get("line_start")
        line_end = metadata.get("line_end")
        if file_path and line_start and line_end:
            citation_lines.append(f"- `{file_path}:{line_start}-{line_end}`")

    if not citation_lines:
        return answer
    return answer.rstrip() + "\n\n근거:\n" + "\n".join(citation_lines)


def _log_project_chat_invocation(
    db: Session | None,
    project: Project,
    llm_client: LLMClient,
    *,
    started_at: datetime,
    status: str,
    mode: str,
    prompt_length: int = 0,
    response_length: int = 0,
    fallback_used: bool = False,
    error_message: str | None = None,
    raw_metadata: dict | None = None,
) -> None:
    if db is None or project.id is None:
        return
    finished_at = datetime.now(timezone.utc)
    record_ai_invocation(
        db,
        project_id=project.id,
        feature="project_chat",
        provider=getattr(llm_client, "provider", "unknown"),
        model=getattr(llm_client, "model", None),
        status=status,
        mode=mode,
        fallback_used=fallback_used,
        validation_status="not_applicable",
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=int((finished_at - started_at).total_seconds() * 1000),
        prompt_length=prompt_length,
        response_length=response_length,
        error_message=error_message,
        raw_metadata=raw_metadata,
    )


def answer_source_question(
    db: Session,
    project: Project,
    question: str,
    *,
    top_k: int = 8,
    include_history: bool = False,
    retriever: Retriever | None = None,
    llm_client: LLMClient | None = None,
) -> RagChatAnswer:
    retriever = retriever or Retriever(db)
    llm_client = llm_client or LLMClient(max_tokens=900)
    started_at = datetime.now(timezone.utc)
    source_types = ["source_file"]
    if include_history:
        source_types.extend(["commit", "commit_file"])

    try:
        expansion = _expand_question(db, project, question)
        results = _retrieve_with_expansion(
            retriever,
            expansion,
            top_k=top_k,
            project_id=project.id,
            source_types=source_types,
        )
    except Exception as exc:
        _log_project_chat_invocation(
            db,
            project,
            llm_client,
            started_at=started_at,
            status="failed",
            mode="retrieval",
            fallback_used=True,
            error_message=str(exc),
        )
        return RagChatAnswer(answer="", errors=[f"retrieval failed: {exc}"])

    annotated = [annotate_retrieval_result(result, project.git_repo_path) for result in results]
    verified_sources = [
        result
        for result in annotated
        if result.get("source_type") == "source_file" and result.get("verification_status") == "verified"
    ]
    historical_sources = [
        result
        for result in annotated
        if result.get("source_type") in {"commit", "commit_file", "program"}
        and result.get("verification_status") in {"historical", "not_applicable"}
    ]
    excluded_count = len(annotated) - len(verified_sources)

    if not verified_sources:
        _log_project_chat_invocation(
            db,
            project,
            llm_client,
            started_at=started_at,
            status="completed",
            mode="insufficient_evidence",
            fallback_used=True,
            raw_metadata={"retrieved_count": len(annotated), "excluded_count": excluded_count},
        )
        return RagChatAnswer(
            answer=INSUFFICIENT_EVIDENCE_ANSWER,
            sources=annotated,
            expanded_queries=expansion.expanded_queries,
            matched_terms=expansion.matched_terms,
            excluded_count=excluded_count,
            used_source_count=0,
            insufficient_evidence=True,
        )

    prompt = _build_prompt(question, verified_sources, historical_sources)
    if llm_client.provider == "mock":
        mock_answer = "Mock answer. 검증된 현재 소스 근거:\n" + "\n".join(
            _summarize_source(source) for source in verified_sources[:3]
        )
        _log_project_chat_invocation(
            db,
            project,
            llm_client,
            started_at=started_at,
            status="completed",
            mode="mock",
            prompt_length=len(prompt),
            response_length=len(mock_answer),
            fallback_used=True,
            raw_metadata={"used_source_count": len(verified_sources), "include_history": include_history},
        )
        return RagChatAnswer(
            answer=mock_answer,
            sources=annotated,
            expanded_queries=expansion.expanded_queries,
            matched_terms=expansion.matched_terms,
            excluded_count=excluded_count,
            used_source_count=len(verified_sources),
        )

    try:
        response = llm_client.generate(prompt)
    except Exception as exc:
        _log_project_chat_invocation(
            db,
            project,
            llm_client,
            started_at=started_at,
            status="failed",
            mode="llm_generation",
            prompt_length=len(prompt),
            fallback_used=True,
            error_message=str(exc),
            raw_metadata={"used_source_count": len(verified_sources), "include_history": include_history},
        )
        return RagChatAnswer(
            answer="",
            sources=annotated,
            expanded_queries=expansion.expanded_queries,
            matched_terms=expansion.matched_terms,
            excluded_count=excluded_count,
            used_source_count=len(verified_sources),
            errors=[f"LLM generation failed: {exc}"],
        )

    final_answer = ensure_answer_citations(clean_llm_answer(response.text), verified_sources)
    _log_project_chat_invocation(
        db,
        project,
        llm_client,
        started_at=started_at,
        status="completed",
        mode="llm_generation",
        prompt_length=len(prompt),
        response_length=len(response.text or ""),
        fallback_used=False,
        raw_metadata={"used_source_count": len(verified_sources), "include_history": include_history},
    )
    return RagChatAnswer(
        answer=final_answer,
        sources=annotated,
        expanded_queries=expansion.expanded_queries,
        matched_terms=expansion.matched_terms,
        excluded_count=excluded_count,
        used_source_count=len(verified_sources),
    )

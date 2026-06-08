from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.db.models import Project
from src.rag.retriever import Retriever
from src.rag.source_verifier import annotate_retrieval_result
from src.services.llm_client import LLMClient


@dataclass
class RagChatAnswer:
    answer: str
    sources: list[dict] = field(default_factory=list)
    excluded_count: int = 0
    errors: list[str] = field(default_factory=list)


def _build_prompt(question: str, sources: list[dict]) -> str:
    context_blocks = []
    for index, source in enumerate(sources, start=1):
        metadata = source.get("metadata") or {}
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"file_path: {metadata.get('file_path') or source.get('source_id')}",
                    f"line_start: {metadata.get('line_start')}",
                    f"line_end: {metadata.get('line_end')}",
                    f"indexed_head_hash: {metadata.get('indexed_head_hash')}",
                    "text:",
                    source.get("text") or "",
                ]
            )
        )

    return f"""
You answer questions about the current source code.
Use only the verified source_file context below.
If the context does not contain enough evidence, say that the current indexed source does not provide enough evidence.
Do not use commit history or deleted diff lines as current source code.
Always mention file path and line range for claims about code.

[Question]
{question}

[Verified current source context]
{chr(10).join(context_blocks)}
""".strip()


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
    source_types = ["source_file"]
    if include_history:
        source_types.extend(["commit", "commit_file"])

    try:
        results = retriever.retrieve(question, limit=top_k, project_id=project.id, source_types=source_types)
    except Exception as exc:
        return RagChatAnswer(answer="", errors=[f"retrieval failed: {exc}"])

    annotated = [annotate_retrieval_result(result, project.git_repo_path) for result in results]
    verified_sources = [
        result
        for result in annotated
        if result.get("source_type") == "source_file" and result.get("verification_status") == "verified"
    ]
    excluded_count = len(annotated) - len(verified_sources)
    if not verified_sources:
        return RagChatAnswer(
            answer="현재 검증된 source_file 근거가 부족해서 답변할 수 없습니다. Source file 인덱싱을 다시 실행하세요.",
            sources=annotated,
            excluded_count=excluded_count,
        )

    prompt = _build_prompt(question, verified_sources)
    if llm_client.provider == "mock":
        source_lines = []
        for source in verified_sources[:3]:
            metadata = source.get("metadata") or {}
            source_lines.append(
                f"- {metadata.get('file_path')}:{metadata.get('line_start')}-{metadata.get('line_end')}"
            )
        return RagChatAnswer(
            answer="Mock answer. 검증된 현재 소스 근거:\n" + "\n".join(source_lines),
            sources=annotated,
            excluded_count=excluded_count,
        )

    try:
        response = llm_client.generate(prompt)
    except Exception as exc:
        return RagChatAnswer(
            answer="",
            sources=annotated,
            excluded_count=excluded_count,
            errors=[f"LLM generation failed: {exc}"],
        )

    return RagChatAnswer(answer=response.text.strip(), sources=annotated, excluded_count=excluded_count)

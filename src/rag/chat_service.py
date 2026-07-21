from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.db.models import DocumentChunk, Project
from src.rag.query_expander import expand_query_with_standard_terms
from src.rag.retriever import Retriever
from src.rag.source_verifier import annotate_retrieval_result
from src.services.ai_invocation_service import record_ai_invocation
from src.services.llm_client import LLMClient
from src.services.neo4j_graph_service import find_project_graph_evidence
from src.utils.repo_path import resolve_repo_path


INSUFFICIENT_EVIDENCE_ANSWER = (
    "현재 검증된 소스 근거만으로는 답변하기 어렵습니다.\n"
    "추가 인덱싱 또는 검색어 조정이 필요합니다."
)

MAX_PROMPT_CURRENT_SOURCES = 6
MAX_PROMPT_HISTORICAL_SOURCES = 2
MAX_PROMPT_GRAPH_EVIDENCE = 4


@dataclass(frozen=True)
class _JavaDirectCall:
    caller: str
    callee: str
    expression: str
    line: int


@dataclass(frozen=True)
class _JavaConditionOutcome:
    condition: str
    outcome: str
    line: int


@dataclass(frozen=True)
class _JavaMethodEvidence:
    owner: str
    file_path: str
    line_start: int
    line_end: int
    source: str
    direct_calls: tuple[_JavaDirectCall, ...] = ()
    condition_outcomes: tuple[_JavaConditionOutcome, ...] = ()
    kind: str = "method"


@dataclass
class RagChatAnswer:
    answer: str
    sources: list[dict] = field(default_factory=list)
    expanded_queries: list[str] = field(default_factory=list)
    matched_terms: list[dict] = field(default_factory=list)
    excluded_count: int = 0
    used_source_count: int = 0
    insufficient_evidence: bool = False
    graph_evidence: list[dict] = field(default_factory=list)
    graph_evidence_metadata: dict = field(default_factory=dict)
    provider: str | None = None
    model: str | None = None
    fallback_used: bool = False
    validation_status: str = "not_applicable"
    repair_attempted: bool = False
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


def _format_graph_context_block(index: int, evidence: dict) -> str:
    path = " -> ".join(str(part) for part in evidence.get("path") or [] if part)
    matched_seeds = ", ".join(str(seed) for seed in evidence.get("matched_seeds") or [])
    lines = [
        f"[Graph relationship {index}]",
        f"evidence_type: {evidence.get('evidence_type')}",
        f"title: {evidence.get('title')}",
        f"path: {path or '-'}",
        f"matched_seeds: {matched_seeds or '-'}",
    ]
    for key in (
        "program",
        "program_id",
        "commit",
        "commit_message",
        "file_path",
        "class_name",
        "domain",
        "source_class",
        "target_class",
        "source_file",
        "target_file",
        "source_domain",
        "target_domain",
        "program_count",
        "file_count",
        "class_count",
    ):
        if evidence.get(key) is not None:
            lines.append(f"{key}: {evidence.get(key)}")
    return "\n".join(lines)


def _format_identifier_focus_block(question: str, current_sources: list[dict], graph_evidence: list[dict] | None) -> str:
    identifiers = _query_code_identifiers(question)
    lines: list[str] = []
    for source in current_sources:
        score = _source_identifier_score(source, identifiers)
        if score <= 0:
            continue
        metadata = source.get("metadata") or {}
        file_path = metadata.get("file_path") or source.get("source_id") or "-"
        line_start = metadata.get("line_start")
        line_end = metadata.get("line_end")
        text = source.get("text") or ""
        imports = sorted(set(re.findall(r"import\s+([A-Za-z0-9_.]+);", text)))
        details = []
        if imports:
            details.append("imports=" + ", ".join(imports[:5]))
        details.append("matched named identifier; call ownership is defined only in method-level evidence")
        detail_text = "; ".join(details)
        lines.append(f"- `{file_path}:{line_start}-{line_end}` {detail_text}")

    for index, evidence in enumerate(graph_evidence or [], start=1):
        if evidence.get("evidence_type") != "class_import":
            continue
        source_class = evidence.get("source_class")
        target_class = evidence.get("target_class")
        if source_class and target_class:
            lines.append(f"- Graph {index}: `{source_class}` imports `{target_class}`")

    return "\n".join(lines) if lines else "None"


def _format_method_evidence(method_evidence: list[_JavaMethodEvidence]) -> str:
    if not method_evidence:
        return "None"
    blocks: list[str] = []
    for index, evidence in enumerate(method_evidence, start=1):
        calls = [
            f"- {call.caller} → {call.callee} at line {call.line}; expression={call.expression}"
            for call in evidence.direct_calls
        ]
        outcomes = [
            f"- condition `{item.condition}` → `{item.outcome}` at line {item.line}"
            for item in evidence.condition_outcomes
        ]
        blocks.append(
            "\n".join(
                [
                    f"[Verified method evidence {index}]",
                    f"kind: {evidence.kind}",
                    f"owner: {evidence.owner}",
                    f"file_path: {evidence.file_path}",
                    f"line_start: {evidence.line_start}",
                    f"line_end: {evidence.line_end}",
                    "direct_calls:",
                    *(calls or ["- None"]),
                    "condition_outcomes:",
                    *(outcomes or ["- None"]),
                    "numbered_source:",
                    evidence.source,
                ]
            )
        )
    return "\n\n".join(blocks)


def _build_prompt(
    question: str,
    current_sources: list[dict],
    historical_sources: list[dict],
    graph_evidence: list[dict] | None = None,
    method_evidence: list[_JavaMethodEvidence] | None = None,
) -> str:
    prompt_current_sources = current_sources[:MAX_PROMPT_CURRENT_SOURCES]
    prompt_historical_sources = historical_sources[:MAX_PROMPT_HISTORICAL_SOURCES]
    prompt_graph_evidence = list(graph_evidence or [])[:MAX_PROMPT_GRAPH_EVIDENCE]
    method_evidence_paths = {item.file_path for item in method_evidence or []}
    context_current_sources = [
        source
        for source in prompt_current_sources
        if str((source.get("metadata") or {}).get("file_path") or source.get("source_id") or "").replace("\\", "/")
        not in method_evidence_paths
    ]
    current_blocks = [
        _format_context_block(index, source, heading="Verified current source")
        for index, source in enumerate(context_current_sources, start=1)
    ]
    historical_blocks = [
        _format_context_block(index, source, heading="Historical/reference evidence")
        for index, source in enumerate(prompt_historical_sources, start=1)
    ]
    graph_blocks = [
        _format_graph_context_block(index, evidence)
        for index, evidence in enumerate(prompt_graph_evidence, start=1)
    ]
    current_context = (
        "\n\n".join(current_blocks)
        if current_blocks
        else "Named Java files are represented by verified method-level evidence above."
    )
    historical_context = "\n\n".join(historical_blocks) if historical_blocks else "None"
    graph_context = "\n\n".join(graph_blocks) if graph_blocks else "None"
    identifier_focus = _format_identifier_focus_block(question, prompt_current_sources, prompt_graph_evidence)
    method_context = _format_method_evidence(list(method_evidence or []))

    return f"""
You answer questions about the current source code.
Use verified source_file context as the only basis for statements about the current code.
The application has already blocked questions with no verified source_file context before this prompt.
If one requested detail is not covered by the verified source_file context, say that specific detail lacks evidence and still answer the parts that are covered.
Do not speculate or fill gaps from general knowledge.
Do not describe commit history or deleted diff lines as current source code.
Commit and commit_file evidence, when present, is historical/reference evidence only.
Graph relationship evidence, when present, is supporting evidence for relationships among programs, commits, files, classes, and domains.
Do not use graph relationship evidence as a substitute for verified current source code.
When using graph relationship evidence, separate it from source-code claims and cite it as Graph 1, Graph 2, etc.
Always mention file path and line range for claims about code.
When the question names classes, files, or methods, start with those named identifiers before related helper classes.
For relationship questions, use the method-level direct_calls ledger below as the authority for direct calls.
Never collapse a transitive chain into one direct call. If A calls B and B calls C, describe two separate steps and do not say A directly calls C.
Write every verified direct-call step with the exact `Owner.method → Target.method` notation from the ledger.
Preserve comparison operators, constants, status strings, and return values exactly as shown in method-level evidence.
Explicitly distinguish a direct method call from an import-only or transitive relationship.
Answer in Korean.
For normal answers, use Markdown prose and bullets.
Do not wrap the answer in JSON.
Do not use a fenced code block unless the user explicitly asks for code or JSON.
Copy file paths and line ranges only from the provided context metadata. Do not infer narrower line numbers.

[Question]
{question}

[Named identifier focus]
{identifier_focus}

[Verified method-level evidence]
{method_context}

[Verified current source context]
{current_context}

[Historical/reference context]
{historical_context}

[Graph relationship context]
{graph_context}
""".strip()


def _query_code_identifiers(question: str) -> set[str]:
    identifiers: set[str] = set()
    file_extensions = {"java", "py", "js", "jsx", "ts", "tsx", "kt", "kts", "go", "rs", "cs", "cpp", "c", "h", "xml", "sql"}
    for match in re.findall(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)?", question):
        token = match.strip(".,:;()[]{}\"'")
        if len(token) < 3:
            continue
        lowered = token.lower()
        identifiers.add(lowered)
        if "." in token:
            left, right = lowered.rsplit(".", 1)
            if right in file_extensions:
                identifiers.add(left.rsplit("/", 1)[-1])
            else:
                identifiers.add(left.rsplit(".", 1)[-1])
                identifiers.add(right)
    return identifiers


def _source_identifier_score(source: dict, identifiers: set[str]) -> int:
    if not identifiers:
        return 0
    metadata = source.get("metadata") or {}
    file_path = str(metadata.get("file_path") or source.get("source_id") or "").lower()
    file_name = file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    file_stem = file_name.rsplit(".", 1)[0]
    text = str(source.get("text") or "").lower()
    score = 0
    for identifier in identifiers:
        if identifier in {file_name, file_stem}:
            score += 100
        elif identifier in file_path:
            score += 10
        if identifier in text:
            score += 1
    return score


def _sort_verified_sources_for_prompt(sources: list[dict], question: str) -> list[dict]:
    identifiers = _query_code_identifiers(question)

    def sort_key(item: dict) -> tuple[int, int, int, float]:
        metadata = item.get("metadata") or {}
        file_path = str(metadata.get("file_path") or item.get("source_id") or "")
        path_priority = 0 if file_path.startswith(("src/main/", "src/test/")) else 1
        identifier_score = _source_identifier_score(item, identifiers)
        line_start = int(metadata.get("line_start") or 0)
        return (-identifier_score, path_priority, line_start, -float(item.get("similarity") or 0))

    return sorted(sources, key=sort_key)


def _named_java_classes(question: str, sources: list[dict]) -> set[str]:
    lowered_question = question.lower()
    names: set[str] = set()
    for source in sources:
        metadata = source.get("metadata") or {}
        file_path = str(metadata.get("file_path") or source.get("source_id") or "")
        if not file_path.lower().endswith(".java"):
            continue
        class_name = Path(file_path).stem
        if class_name.lower() in lowered_question:
            names.add(class_name)
    return names


def _java_variable_types(text: str) -> dict[str, str]:
    variable_types: dict[str, str] = {}
    field_pattern = re.compile(
        r"\b(?:public\s+|protected\s+|private\s+)?(?:static\s+)?(?:final\s+)?"
        r"(?P<type>[A-Z][A-Za-z0-9_]*)\s+(?P<name>[a-z][A-Za-z0-9_]*)\s*(?:[;=,])"
    )
    parameter_pattern = re.compile(r"\b(?P<type>[A-Z][A-Za-z0-9_]*)\s+(?P<name>[a-z][A-Za-z0-9_]*)\b")
    for pattern in (field_pattern, parameter_pattern):
        for match in pattern.finditer(text):
            variable_types.setdefault(match.group("name"), match.group("type"))
    return variable_types


def _method_declaration_name(line: str, class_name: str) -> str | None:
    if "(" not in line or "{" not in line or ";" in line.split("{", 1)[0]:
        return None
    prefix = line.split("(", 1)[0].strip()
    match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", prefix)
    if not match:
        return None
    name = match.group(1)
    if name in {"if", "for", "while", "switch", "catch", "try", "synchronized", "do", "else"}:
        return None
    if re.search(r"\b(?:class|interface|enum|record)\s+" + re.escape(name) + r"$", prefix):
        return None
    if name == class_name:
        return None
    return name


def _interface_method_name(line: str, class_name: str) -> str | None:
    stripped = line.strip()
    if "(" not in stripped or not stripped.endswith(";"):
        return None
    prefix = stripped.split("(", 1)[0]
    match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", prefix)
    if not match:
        return None
    name = match.group(1)
    if name == class_name or name in {"if", "for", "while", "switch", "return", "throw", "new"}:
        return None
    return name


def _method_end_index(lines: list[str], start_index: int) -> int:
    depth = 0
    opened = False
    for index in range(start_index, len(lines)):
        line = re.sub(r'"(?:\\.|[^"\\])*"', '""', lines[index])
        for char in line:
            if char == "{":
                depth += 1
                opened = True
            elif char == "}":
                depth -= 1
                if opened and depth == 0:
                    return index
    return start_index


def _method_direct_calls(
    class_name: str,
    method_name: str,
    lines: list[str],
    start_index: int,
    end_index: int,
    variable_types: dict[str, str],
) -> tuple[_JavaDirectCall, ...]:
    calls: list[_JavaDirectCall] = []
    seen: set[tuple[str, str, int]] = set()
    object_call_pattern = re.compile(
        r"\b(?P<object>[A-Za-z_][A-Za-z0-9_]*)\.(?P<method>[A-Za-z_][A-Za-z0-9_]*)\s*"
        r"\((?P<args>[^)]*)\)"
    )
    unqualified_call_pattern = re.compile(r"(?<![.\w])(?P<method>[a-z][A-Za-z0-9_]*)\s*\((?P<args>[^)]*)\)")
    ignored = {"if", "for", "while", "switch", "catch", "return", "throw", "new", "super", "this"}

    for index in range(start_index + 1, end_index + 1):
        line = lines[index]
        for match in object_call_pattern.finditer(line):
            object_name = match.group("object")
            target_method = match.group("method")
            target_class = class_name if object_name == "this" else variable_types.get(object_name)
            if target_class is None and object_name[:1].isupper():
                target_class = object_name
            if target_class is None:
                target_class = object_name
            caller = f"{class_name}.{method_name}"
            callee = f"{target_class}.{target_method}"
            key = (caller, callee, index + 1)
            if key in seen:
                continue
            seen.add(key)
            calls.append(
                _JavaDirectCall(
                    caller=caller,
                    callee=callee,
                    expression=match.group(0).strip(),
                    line=index + 1,
                )
            )

        for match in unqualified_call_pattern.finditer(line):
            target_method = match.group("method")
            if target_method in ignored:
                continue
            if match.start() > 0 and line[match.start() - 1] == ".":
                continue
            caller = f"{class_name}.{method_name}"
            callee = f"{class_name}.{target_method}"
            key = (caller, callee, index + 1)
            if key in seen:
                continue
            seen.add(key)
            calls.append(
                _JavaDirectCall(
                    caller=caller,
                    callee=callee,
                    expression=match.group(0).strip(),
                    line=index + 1,
                )
            )
    return tuple(calls)


def _method_condition_outcomes(
    source: str,
    *,
    line_start: int,
) -> tuple[_JavaConditionOutcome, ...]:
    outcomes: list[_JavaConditionOutcome] = []
    condition_pattern = re.compile(r"if\s*\((?P<condition>[^)]*)\)\s*\{(?P<body>.*?)\n\s*}", re.DOTALL)
    for match in condition_pattern.finditer(source):
        body = match.group("body")
        return_match = re.search(r"return\s+(?P<value>\"[^\"]*\"|[^;]+)\s*;", body)
        throw_match = re.search(r"throw\s+new\s+(?P<value>[A-Za-z_][A-Za-z0-9_]*)", body)
        if return_match:
            outcome = f"return {return_match.group('value').strip()}"
        elif throw_match:
            outcome = f"throw {throw_match.group('value').strip()}"
        else:
            continue
        outcomes.append(
            _JavaConditionOutcome(
                condition=" ".join(match.group("condition").split()),
                outcome=outcome,
                line=line_start + source[: match.start()].count("\n"),
            )
        )
    return tuple(outcomes)


def _collect_verified_java_method_evidence(
    repo_path: str | None,
    question: str,
    verified_sources: list[dict],
    *,
    max_files: int = 4,
) -> list[_JavaMethodEvidence]:
    if not repo_path:
        return []
    identifiers = _query_code_identifiers(question)
    candidate_paths: list[str] = []
    for source in verified_sources:
        if source.get("verification_status") != "verified" or _source_identifier_score(source, identifiers) <= 0:
            continue
        metadata = source.get("metadata") or {}
        file_path = str(metadata.get("file_path") or source.get("source_id") or "").replace("\\", "/")
        if file_path.lower().endswith(".java") and file_path not in candidate_paths:
            candidate_paths.append(file_path)
    if not candidate_paths:
        return []

    try:
        repo_root = resolve_repo_path(repo_path)
    except Exception:
        return []

    evidence: list[_JavaMethodEvidence] = []
    verified_coverage = _citation_coverage(verified_sources)
    for file_path in candidate_paths[:max_files]:
        target = (repo_root / file_path).resolve()
        try:
            target.relative_to(repo_root)
            text = target.read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            continue
        lines = text.splitlines()
        class_match = re.search(r"\b(?:class|interface|enum|record)\s+([A-Za-z_][A-Za-z0-9_]*)", text)
        class_name = class_match.group(1) if class_match else Path(file_path).stem
        variable_types = _java_variable_types(text)
        index = 0
        while index < len(lines):
            method_name = _method_declaration_name(lines[index], class_name)
            if method_name:
                end_index = _method_end_index(lines, index)
                method_lines = set(range(index + 1, end_index + 2))
                if not method_lines.issubset(verified_coverage.get(file_path, set())):
                    index = end_index + 1
                    continue
                numbered_source = "\n".join(
                    f"{line_number}: {lines[line_number - 1]}"
                    for line_number in range(index + 1, end_index + 2)
                )
                raw_source = "\n".join(lines[index : end_index + 1])
                evidence.append(
                    _JavaMethodEvidence(
                        owner=f"{class_name}.{method_name}",
                        file_path=file_path,
                        line_start=index + 1,
                        line_end=end_index + 1,
                        source=numbered_source,
                        direct_calls=_method_direct_calls(
                            class_name,
                            method_name,
                            lines,
                            index,
                            end_index,
                            variable_types,
                        ),
                        condition_outcomes=_method_condition_outcomes(raw_source, line_start=index + 1),
                    )
                )
                index = end_index + 1
                continue

            contract_name = _interface_method_name(lines[index], class_name)
            if contract_name:
                if index + 1 not in verified_coverage.get(file_path, set()):
                    index += 1
                    continue
                evidence.append(
                    _JavaMethodEvidence(
                        owner=f"{class_name}.{contract_name}",
                        file_path=file_path,
                        line_start=index + 1,
                        line_end=index + 1,
                        source=f"{index + 1}: {lines[index]}",
                        kind="contract",
                    )
                )
            index += 1
    return evidence


def _relevant_method_calls(
    question: str,
    method_evidence: list[_JavaMethodEvidence],
) -> list[_JavaDirectCall]:
    named_classes = {
        evidence.owner.split(".", 1)[0]
        for evidence in method_evidence
        if evidence.owner.split(".", 1)[0].lower() in question.lower()
    }
    calls: list[_JavaDirectCall] = []
    seen: set[tuple[str, str]] = set()
    for evidence in method_evidence:
        for call in evidence.direct_calls:
            caller_class = call.caller.split(".", 1)[0]
            callee_class = call.callee.split(".", 1)[0]
            if caller_class not in named_classes or callee_class not in named_classes:
                continue
            key = (call.caller, call.callee)
            if key in seen:
                continue
            seen.add(key)
            calls.append(call)

    adjacency: dict[str, list[_JavaDirectCall]] = {}
    for call in calls:
        adjacency.setdefault(call.caller, []).append(call)
    callee_methods = {call.callee for call in calls}
    roots = [caller for caller in adjacency if caller not in callee_methods]
    ordered: list[_JavaDirectCall] = []
    visited: set[tuple[str, str]] = set()

    def visit(caller: str) -> None:
        for call in adjacency.get(caller, []):
            key = (call.caller, call.callee)
            if key in visited:
                continue
            visited.add(key)
            ordered.append(call)
            visit(call.callee)

    for root in roots:
        visit(root)
    for call in calls:
        if (call.caller, call.callee) not in visited:
            visit(call.caller)
    return ordered


def _citation_coverage(verified_sources: list[dict]) -> dict[str, set[int]]:
    coverage: dict[str, set[int]] = {}
    for source in verified_sources:
        metadata = source.get("metadata") or {}
        file_path = str(metadata.get("file_path") or source.get("source_id") or "").replace("\\", "/")
        try:
            line_start = int(metadata.get("line_start"))
            line_end = int(metadata.get("line_end"))
        except (TypeError, ValueError):
            continue
        coverage.setdefault(file_path, set()).update(range(line_start, line_end + 1))
    return coverage


def _validate_method_answer(
    question: str,
    answer: str,
    method_evidence: list[_JavaMethodEvidence],
    verified_sources: list[dict],
) -> list[str]:
    if not method_evidence:
        return []
    relationship_question = any(token in question.lower() for token in ("관계", "연결", "호출", "흐름", "어떻게", "영향", "relationship", "flow"))
    condition_question = any(token in question.lower() for token in ("금액", "조건", "거절", "실패", "amount", "reject", "condition"))
    errors: list[str] = []
    normalized_answer = answer.replace("`", "")
    relevant_calls = _relevant_method_calls(question, method_evidence)
    allowed_edges = {(call.caller, call.callee) for call in relevant_calls}

    if relationship_question:
        for call in relevant_calls:
            pattern = re.compile(
                re.escape(call.caller) + r"\s*(?:→|->|⇒)\s*" + re.escape(call.callee),
                re.IGNORECASE,
            )
            if not pattern.search(normalized_answer):
                errors.append(f"직접 호출 단계 누락: {call.caller} → {call.callee}")

        arrow_pattern = re.compile(
            r"\b([A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\s*(?:→|->|⇒)\s*"
            r"([A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)"
        )
        for caller, callee in arrow_pattern.findall(normalized_answer):
            if (caller, callee) not in allowed_edges:
                errors.append(f"검증되지 않은 직접 호출 단계: {caller} → {callee}")

        cited_paths = {
            path.replace("\\", "/")
            for path in re.findall(r"([\w./\\-]+\.[A-Za-z0-9]+):\d+-\d+", answer)
        }
        required_paths = {
            evidence.file_path
            for evidence in method_evidence
            if evidence.owner.split(".", 1)[0].lower() in question.lower()
        }
        for path in sorted(required_paths - cited_paths):
            errors.append(f"파일 근거 인용 누락: {path}")

    if condition_question:
        for evidence in method_evidence:
            if evidence.owner.split(".", 1)[0].lower() not in question.lower():
                continue
            for outcome in evidence.condition_outcomes:
                compact_condition = re.sub(r"\s+", "", outcome.condition)
                compact_answer = re.sub(r"\s+", "", normalized_answer)
                if compact_condition not in compact_answer or outcome.outcome.replace('"', "") not in normalized_answer.replace('"', ""):
                    errors.append(f"조건 결과 누락 또는 불일치: {outcome.condition} → {outcome.outcome}")

    coverage = _citation_coverage(verified_sources)
    citation_pattern = re.compile(r"([\w./\\-]+\.[A-Za-z0-9]+):(\d+)-(\d+)")
    for path, start_text, end_text in citation_pattern.findall(answer):
        normalized_path = path.replace("\\", "/")
        start = int(start_text)
        end = int(end_text)
        covered_lines = coverage.get(normalized_path, set())
        if start > end or not set(range(start, end + 1)).issubset(covered_lines):
            errors.append(f"검증 범위를 벗어난 인용: {normalized_path}:{start}-{end}")
    return list(dict.fromkeys(errors))


def _build_verified_method_fallback(
    question: str,
    method_evidence: list[_JavaMethodEvidence],
) -> str:
    calls = _relevant_method_calls(question, method_evidence)
    lines = ["검증된 현재 소스에서 확인되는 호출 흐름은 다음과 같습니다."]
    for call in calls:
        evidence = next((item for item in method_evidence if item.owner == call.caller), None)
        if evidence is None:
            continue
        lines.append(
            f"- `{call.caller} → {call.callee}`: `{call.expression}`을 직접 호출합니다. "
            f"(`{evidence.file_path}:{call.line}-{call.line}`)"
        )

    if any(token in question.lower() for token in ("금액", "조건", "거절", "실패", "amount", "reject", "condition")):
        for evidence in method_evidence:
            for outcome in evidence.condition_outcomes:
                lines.append(
                    f"- `{evidence.owner}`의 `{outcome.condition}` 조건 결과는 `{outcome.outcome}`입니다. "
                    f"(`{evidence.file_path}:{outcome.line}-{evidence.line_end}`)"
                )

    cited_paths = {call.caller.split(".", 1)[0] for call in calls}
    for evidence in method_evidence:
        owner_class = evidence.owner.split(".", 1)[0]
        if evidence.kind != "contract" or owner_class in cited_paths or owner_class.lower() not in question.lower():
            continue
        lines.append(
            f"- `{evidence.owner}` 계약이 선언되어 있습니다. "
            f"(`{evidence.file_path}:{evidence.line_start}-{evidence.line_end}`)"
        )
    lines.append("따라서 각 단계는 위 순서의 직접 호출이며, 앞 단계가 뒤쪽 mapper를 바로 호출하는 것으로 합치면 안 됩니다.")
    return "\n".join(lines)


def _order_sources_for_answer(annotated: list[dict], used_sources: list[dict]) -> list[dict]:
    ordered = list(used_sources)
    used_ids = {id(source) for source in used_sources}
    ordered.extend(source for source in annotated if id(source) not in used_ids and source not in used_sources)
    return ordered


def _file_paths_for_query_identifiers(db: Session, project_id: int, identifiers: set[str]) -> list[str]:
    if not identifiers:
        return []
    rows = (
        db.query(DocumentChunk.raw_metadata)
        .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == "source_file")
        .all()
    )
    scored_paths: list[tuple[int, str]] = []
    seen: set[str] = set()
    for (metadata,) in rows:
        file_path = str((metadata or {}).get("file_path") or "")
        if not file_path or file_path in seen:
            continue
        lowered = file_path.lower()
        file_name = lowered.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        stem = file_name.rsplit(".", 1)[0]
        score = 0
        for identifier in identifiers:
            if identifier in {file_name, stem}:
                score += 100
            elif identifier in lowered:
                score += 10
        if score:
            seen.add(file_path)
            scored_paths.append((score, file_path))
    return [file_path for _, file_path in sorted(scored_paths, key=lambda item: (-item[0], item[1]))]


def _add_identifier_source_chunks(
    db: Session | None,
    project: Project,
    question: str,
    annotated: list[dict],
    verified_sources: list[dict],
    *,
    max_extra_files: int = 4,
) -> list[dict]:
    if db is None or project.id is None:
        return verified_sources
    identifiers = _query_code_identifiers(question)
    file_paths = _file_paths_for_query_identifiers(db, project.id, identifiers)[:max_extra_files]
    if not file_paths:
        return verified_sources

    existing_ids = {int(source["id"]) for source in verified_sources if source.get("id") is not None}
    existing_annotated_ids = {int(source["id"]) for source in annotated if source.get("id") is not None}
    rows = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.project_id == project.id, DocumentChunk.source_type == "source_file")
        .all()
    )
    extra_sources: list[dict] = []
    for chunk in rows:
        metadata = chunk.raw_metadata or {}
        if metadata.get("file_path") not in file_paths:
            continue
        raw_source = {
            "id": chunk.id,
            "source_type": chunk.source_type,
            "source_id": chunk.source_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.chunk_text,
            "metadata": metadata,
            "similarity": 1.0,
            "distance": 0.0,
        }
        annotated_source = annotate_retrieval_result(raw_source, project.git_repo_path)
        if annotated_source.get("verification_status") != "verified":
            continue
        chunk_id = int(chunk.id)
        if chunk_id not in existing_annotated_ids:
            annotated.append(annotated_source)
            existing_annotated_ids.add(chunk_id)
        if chunk_id not in existing_ids:
            extra_sources.append(annotated_source)
            existing_ids.add(chunk_id)

    if not extra_sources:
        return verified_sources
    return [*verified_sources, *extra_sources]


def _summarize_source(source: dict) -> str:
    metadata = source.get("metadata") or {}
    file_path = metadata.get("file_path") or source.get("source_id") or "-"
    line_start = metadata.get("line_start")
    line_end = metadata.get("line_end")
    line_range = f"{line_start}-{line_end}" if line_start and line_end else "-"
    source_type = source.get("source_type") or "-"
    status = source.get("verification_status") or "-"
    return f"- {file_path}:{line_range} ({source_type}, {status})"


def _summarize_graph_evidence(evidence: dict) -> str:
    path = " -> ".join(str(part) for part in evidence.get("path") or [] if part)
    evidence_type = evidence.get("evidence_type") or "-"
    return f"- {path or evidence.get('title') or '-'} ({evidence_type})"


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


def _collect_graph_evidence(
    db: Session | None,
    project: Project,
    question: str,
    sources: list[dict],
    expanded_queries: list[str],
    *,
    top_k: int,
    provider: Callable[..., object] | None = None,
) -> tuple[list[dict], dict]:
    if project.id is None:
        return [], {"status": "skipped", "summary": "project id가 없어 graph evidence를 조회하지 않았습니다."}
    if db is None and provider is None:
        return [], {"status": "skipped", "summary": "db가 없어 기본 graph evidence 조회를 건너뜁니다."}

    graph_provider = provider or find_project_graph_evidence
    try:
        result = graph_provider(
            project.id,
            question,
            sources,
            expanded_queries=expanded_queries,
            limit=max(3, min(int(top_k), 8)),
        )
    except Exception as exc:
        return [], {"status": "failed", "summary": "Project Chat graph evidence 조회 실패", "errors": [str(exc)]}

    evidence = list(getattr(result, "evidence", []) or [])
    metadata = {
        "status": getattr(result, "status", "unknown"),
        "summary": getattr(result, "summary", ""),
        "seed_count": len(getattr(result, "seeds", []) or []),
        "seeds": list(getattr(result, "seeds", []) or [])[:20],
        "errors": list(getattr(result, "errors", []) or []),
        "evidence_count": len(evidence),
    }
    return evidence, metadata


def clean_llm_answer(text: str) -> str:
    stripped = text.strip()
    fence_match = re.fullmatch(r"```(?:json|markdown|md)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
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
    if fence_match:
        return _normalize_korean_answer_text(payload)
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
    validation_status: str = "not_applicable",
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
        validation_status=validation_status,
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
    graph_evidence_provider: Callable[..., object] | None = None,
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
    verified_sources = _add_identifier_source_chunks(db, project, question, annotated, verified_sources)
    verified_sources = _sort_verified_sources_for_prompt(verified_sources, question)
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
            provider=getattr(llm_client, "provider", None),
            model=getattr(llm_client, "model", None),
            fallback_used=True,
        )

    graph_evidence, graph_metadata = _collect_graph_evidence(
        db,
        project,
        question,
        [*verified_sources, *historical_sources],
        list(expansion.expanded_queries),
        top_k=top_k,
        provider=graph_evidence_provider,
    )
    prompt_current_sources = verified_sources[:MAX_PROMPT_CURRENT_SOURCES]
    prompt_historical_sources = historical_sources[:MAX_PROMPT_HISTORICAL_SOURCES]
    prompt_graph_evidence = graph_evidence[:MAX_PROMPT_GRAPH_EVIDENCE]
    graph_metadata = {
        **graph_metadata,
        "retrieved_evidence_count": len(graph_evidence),
        "evidence_count": len(prompt_graph_evidence),
    }
    method_evidence = _collect_verified_java_method_evidence(
        project.git_repo_path,
        question,
        prompt_current_sources,
    )
    answer_sources = _order_sources_for_answer(annotated, prompt_current_sources)
    prompt = _build_prompt(
        question,
        prompt_current_sources,
        prompt_historical_sources,
        prompt_graph_evidence,
        method_evidence,
    )
    if llm_client.provider == "mock":
        mock_answer = "Mock answer. 검증된 현재 소스 근거:\n" + "\n".join(
            _summarize_source(source) for source in prompt_current_sources[:3]
        )
        if prompt_graph_evidence:
            mock_answer += "\n\n그래프 관계 근거:\n" + "\n".join(
                _summarize_graph_evidence(evidence) for evidence in prompt_graph_evidence[:3]
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
            raw_metadata={
                "used_source_count": len(prompt_current_sources),
                "include_history": include_history,
                "graph_evidence_count": len(prompt_graph_evidence),
                "graph_status": graph_metadata.get("status"),
                "graph_errors": graph_metadata.get("errors", []),
                "method_evidence_count": len(method_evidence),
            },
        )
        return RagChatAnswer(
            answer=mock_answer,
            sources=answer_sources,
            expanded_queries=expansion.expanded_queries,
            matched_terms=expansion.matched_terms,
            excluded_count=excluded_count,
            used_source_count=len(prompt_current_sources),
            graph_evidence=prompt_graph_evidence,
            graph_evidence_metadata=graph_metadata,
            provider=getattr(llm_client, "provider", None),
            model=getattr(llm_client, "model", None),
            fallback_used=True,
            validation_status="not_applicable",
        )

    try:
        response = llm_client.generate(prompt)
    except Exception as exc:
        if method_evidence:
            fallback_answer = _build_verified_method_fallback(question, method_evidence)
            _log_project_chat_invocation(
                db,
                project,
                llm_client,
                started_at=started_at,
                status="completed",
                mode="verified_method_fallback",
                prompt_length=len(prompt),
                response_length=len(fallback_answer),
                fallback_used=True,
                validation_status="deterministic_repair",
                error_message=str(exc),
                raw_metadata={
                    "used_source_count": len(prompt_current_sources),
                    "include_history": include_history,
                    "graph_evidence_count": len(prompt_graph_evidence),
                    "graph_status": graph_metadata.get("status"),
                    "graph_errors": graph_metadata.get("errors", []),
                    "method_evidence_count": len(method_evidence),
                    "generation_error": str(exc),
                },
            )
            return RagChatAnswer(
                answer=fallback_answer,
                sources=answer_sources,
                expanded_queries=expansion.expanded_queries,
                matched_terms=expansion.matched_terms,
                excluded_count=excluded_count,
                used_source_count=len(prompt_current_sources),
                graph_evidence=prompt_graph_evidence,
                graph_evidence_metadata=graph_metadata,
                provider=getattr(llm_client, "provider", None),
                model=getattr(llm_client, "model", None),
                fallback_used=True,
                validation_status="deterministic_repair",
                repair_attempted=True,
            )
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
            raw_metadata={
                "used_source_count": len(prompt_current_sources),
                "include_history": include_history,
                "graph_evidence_count": len(prompt_graph_evidence),
                "graph_status": graph_metadata.get("status"),
                "graph_errors": graph_metadata.get("errors", []),
                "method_evidence_count": len(method_evidence),
            },
        )
        return RagChatAnswer(
            answer="",
            sources=answer_sources,
            expanded_queries=expansion.expanded_queries,
            matched_terms=expansion.matched_terms,
            excluded_count=excluded_count,
            used_source_count=len(prompt_current_sources),
            graph_evidence=prompt_graph_evidence,
            graph_evidence_metadata=graph_metadata,
            provider=getattr(llm_client, "provider", None),
            model=getattr(llm_client, "model", None),
            fallback_used=True,
            validation_status="failed",
            errors=[f"LLM generation failed: {exc}"],
        )

    final_answer = clean_llm_answer(response.text)
    initial_validation_errors = _validate_method_answer(
        question,
        final_answer,
        method_evidence,
        prompt_current_sources,
    )
    repair_attempted = False
    repair_errors: list[str] = []
    repair_error_message: str | None = None
    validation_status = "valid" if method_evidence else "not_applicable"
    fallback_used = False
    prompt_length = len(prompt)
    response_length = len(response.text or "")

    if initial_validation_errors:
        repair_attempted = True
        final_answer = _build_verified_method_fallback(question, method_evidence)
        validation_status = "deterministic_repair"
        fallback_used = True

    final_answer = ensure_answer_citations(final_answer, prompt_current_sources)
    _log_project_chat_invocation(
        db,
        project,
        llm_client,
        started_at=started_at,
        status="completed",
        mode="llm_generation",
        prompt_length=prompt_length,
        response_length=response_length,
        fallback_used=fallback_used,
        validation_status=validation_status,
        raw_metadata={
            "used_source_count": len(prompt_current_sources),
            "include_history": include_history,
            "graph_evidence_count": len(prompt_graph_evidence),
            "graph_status": graph_metadata.get("status"),
            "graph_errors": graph_metadata.get("errors", []),
            "method_evidence_count": len(method_evidence),
            "validation_status": validation_status,
            "validation_errors": initial_validation_errors,
            "repair_attempted": repair_attempted,
            "repair_errors": repair_errors,
            "repair_error": repair_error_message,
        },
    )
    return RagChatAnswer(
        answer=final_answer,
        sources=answer_sources,
        expanded_queries=expansion.expanded_queries,
        matched_terms=expansion.matched_terms,
        excluded_count=excluded_count,
        used_source_count=len(prompt_current_sources),
        graph_evidence=prompt_graph_evidence,
        graph_evidence_metadata=graph_metadata,
        provider=getattr(llm_client, "provider", None),
        model=getattr(llm_client, "model", None),
        fallback_used=fallback_used,
        validation_status=validation_status,
        repair_attempted=repair_attempted,
    )

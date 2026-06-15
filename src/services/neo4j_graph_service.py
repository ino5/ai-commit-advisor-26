from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.db.models import CommitFile, GitCommit, Program, ProgramCommitMapping, Project, ProjectGraphSyncState
from src.rag.chunker import _is_source_file, _read_text_file
from src.services.git_service import get_head_commit_hash
from src.utils.config import settings
from src.utils.repo_path import resolve_repo_path

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover - exercised when dependency is not installed locally.
    GraphDatabase = None


PACKAGE_RE = re.compile(r"(?m)^\s*package\s+([A-Za-z_][\w.]*)\s*;")
IMPORT_RE = re.compile(r"(?m)^\s*import\s+(?:static\s+)?([A-Za-z_][\w.]*)(?:\.\*)?\s*;")
TYPE_RE = re.compile(r"\b(class|interface|enum|record)\s+([A-Z][A-Za-z0-9_]*)\b")
GRAPH_SEED_RE = re.compile(r"[A-Za-z가-힣][A-Za-z0-9가-힣_.$:/\\-]{1,}")
GRAPH_SEED_STOPWORDS = {
    "about",
    "answer",
    "class",
    "code",
    "current",
    "file",
    "where",
    "with",
    "가능",
    "근거",
    "기준",
    "뭐야",
    "무엇",
    "변경",
    "설명",
    "알려",
    "어디",
    "어떤",
    "영향",
    "있나",
    "있는",
    "있어",
}
SOURCE_GRAPH_CHANGE_TYPES = {"Added", "Modified", "Copied", "Renamed"}
SOURCE_GRAPH_CLEAR_TYPES = {"Added", "Modified", "Copied", "Deleted", "Renamed"}


@dataclass(frozen=True)
class JavaSymbol:
    file_path: str
    package: str | None
    class_name: str
    qualified_name: str
    kind: str
    domain: str
    imports: tuple[str, ...] = ()


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_neo4j(self, project_id: int) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "project_id": project_id,
            "node_type": self.node_type,
            "label": self.label,
            **_neo4j_properties(self.properties),
        }


@dataclass(frozen=True)
class GraphEdge:
    from_node_id: str
    to_node_id: str
    edge_type: str
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def edge_id(self) -> str:
        return f"{self.from_node_id}|{self.edge_type}|{self.to_node_id}"

    def to_neo4j(self, project_id: int) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "project_id": project_id,
            "edge_type": self.edge_type,
            "graph_scope": self.properties.get("graph_scope") or _graph_scope_for_edge(self.edge_type),
            "weight": float(self.weight),
            **_neo4j_properties(self.properties),
        }


@dataclass(frozen=True)
class DomainSummaryRow:
    domain: str
    program_count: int
    file_count: int
    class_count: int
    commit_count: int


@dataclass(frozen=True)
class ImpactPathRow:
    commit: str
    program: str
    file_path: str
    class_name: str
    domain: str


@dataclass(frozen=True)
class GraphPayload:
    project_id: int
    project_name: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    domain_rows: list[DomainSummaryRow]
    impact_rows: list[ImpactPathRow]
    class_import_rows: list[dict[str, str]]
    errors: list[str] = field(default_factory=list)

    @property
    def node_counts(self) -> Counter:
        return Counter(node.node_type for node in self.nodes)

    @property
    def edge_counts(self) -> Counter:
        return Counter(edge.edge_type for edge in self.edges)


@dataclass(frozen=True)
class Neo4jConnectionStatus:
    enabled: bool
    connected: bool
    message: str
    uri: str
    database: str | None


@dataclass(frozen=True)
class Neo4jSyncResult:
    status: str
    summary: str
    node_count: int = 0
    edge_count: int = 0
    node_counts: dict[str, int] = field(default_factory=dict)
    edge_counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Neo4jGraphFreshness:
    status: str
    summary: str
    repo_head_hash: str | None = None
    db_sync_head_hash: str | None = None
    graph_sync_head_hash: str | None = None
    synced_at: datetime | None = None
    sync_mode: str | None = None
    node_count: int = 0
    edge_count: int = 0
    last_commit_db_id: int | None = None
    last_mapping_updated_at: datetime | None = None
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Neo4jGraphPreview:
    status: str
    summary: str
    class_import_rows: list[dict[str, str]] = field(default_factory=list)
    impact_rows: list[ImpactPathRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GraphEvidenceSearchResult:
    status: str
    summary: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    seeds: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _node_id(project_id: int, node_type: str, key: str | int) -> str:
    return f"p{project_id}:{node_type}:{str(key).strip()}"


def _edge_key(edge: GraphEdge) -> tuple[str, str, str]:
    return edge.from_node_id, edge.edge_type, edge.to_node_id


def _graph_scope_for_edge(edge_type: str) -> str:
    if edge_type in {"CONTAINS_CLASS", "IMPORTS_CLASS"}:
        return "current_source"
    if edge_type in {"HAS_COMMIT", "TOUCHES_FILE", "TOUCHES_DOMAIN"}:
        return "historical_git"
    if edge_type == "MAPPED_TO_COMMIT":
        return "analysis"
    return "project_structure"


def _clean_key(value: str | None, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9가-힣_.:/-]+", "-", (value or "").strip())
    return cleaned.strip("-") or fallback


def _short_commit(commit_hash: str | None) -> str:
    return (commit_hash or "-")[:12]


def _normalize_graph_seed(value: Any) -> str:
    seed = str(value or "").strip().replace("\\", "/").lower()
    seed = re.sub(r"^[^\w가-힣]+|[^\w가-힣]+$", "", seed)
    return seed


def _add_graph_seed(seeds: list[str], seen: set[str], value: Any) -> None:
    seed = _normalize_graph_seed(value)
    if len(seed) < 2 or seed in seen or seed in GRAPH_SEED_STOPWORDS:
        return
    seen.add(seed)
    seeds.append(seed)


def _add_graph_seed_variants(seeds: list[str], seen: set[str], value: Any) -> None:
    raw = str(value or "").strip()
    if not raw:
        return
    normalized = raw.replace("\\", "/")
    _add_graph_seed(seeds, seen, normalized)
    path = Path(normalized)
    if path.name:
        _add_graph_seed(seeds, seen, path.name)
        _add_graph_seed(seeds, seen, path.stem)
    for part in re.split(r"[/.\s:_-]+", normalized):
        _add_graph_seed(seeds, seen, part)


def build_graph_evidence_seeds(
    question: str,
    sources: list[dict],
    *,
    expanded_queries: list[str] | None = None,
    limit: int = 30,
) -> list[str]:
    seeds: list[str] = []
    seen: set[str] = set()

    for text in [question, *(expanded_queries or [])]:
        for match in GRAPH_SEED_RE.finditer(text or ""):
            _add_graph_seed_variants(seeds, seen, match.group(0))
            if len(seeds) >= limit:
                return seeds[:limit]

    for source in sources:
        metadata = source.get("metadata") or {}
        for key in (
            "file_path",
            "commit_hash",
            "program_id",
            "program_name",
            "screen_name",
            "module",
            "class_name",
            "qualified_name",
            "domain",
        ):
            _add_graph_seed_variants(seeds, seen, metadata.get(key))
        _add_graph_seed_variants(seeds, seen, source.get("source_id"))

        file_path = metadata.get("file_path") or source.get("source_id") or ""
        text = source.get("text") or ""
        if file_path and text and str(file_path).endswith(".java"):
            for symbol in extract_java_symbols(str(file_path).replace("\\", "/"), text):
                _add_graph_seed_variants(seeds, seen, symbol.file_path)
                _add_graph_seed_variants(seeds, seen, symbol.class_name)
                _add_graph_seed_variants(seeds, seen, symbol.qualified_name)
                _add_graph_seed_variants(seeds, seen, symbol.domain)
                for imported in symbol.imports:
                    _add_graph_seed_variants(seeds, seen, imported)
        if len(seeds) >= limit:
            return seeds[:limit]
    return seeds[:limit]


def _neo4j_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, list | tuple | set):
        result = []
        for item in value:
            converted = _neo4j_value(item)
            if isinstance(converted, (bool, int, float, str)):
                result.append(converted)
        return result
    return str(value)


def _neo4j_properties(properties: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, raw in properties.items() if (value := _neo4j_value(raw)) is not None}


def _domain_from_package(package: str | None) -> str | None:
    if not package:
        return None
    parts = package.split(".")
    for marker in ("market", "domain", "app"):
        if marker in parts:
            index = parts.index(marker)
            if index + 1 < len(parts):
                return parts[index + 1]
    if len(parts) >= 3:
        return parts[-2]
    return parts[0] if parts else None


def _domain_from_path(file_path: str) -> str:
    ignored = {"src", "main", "test", "java", "resources", "com", "example", "market"}
    for part in Path(file_path.replace("\\", "/")).parts:
        normalized = part.strip().lower()
        if normalized and normalized not in ignored and "." not in normalized:
            return normalized
    return "unknown"


def extract_java_symbols(file_path: str, text: str) -> list[JavaSymbol]:
    package_match = PACKAGE_RE.search(text)
    package = package_match.group(1) if package_match else None
    imports = tuple(sorted({match.group(1) for match in IMPORT_RE.finditer(text)}))
    domain = _domain_from_package(package) or _domain_from_path(file_path)
    symbols: list[JavaSymbol] = []
    for match in TYPE_RE.finditer(text):
        kind = match.group(1)
        class_name = match.group(2)
        qualified_name = f"{package}.{class_name}" if package else class_name
        symbols.append(
            JavaSymbol(
                file_path=file_path,
                package=package,
                class_name=class_name,
                qualified_name=qualified_name,
                kind=kind,
                domain=domain,
                imports=imports,
            )
        )
    return symbols


def _source_java_symbols(repo_path: str | None) -> tuple[list[JavaSymbol], list[str]]:
    if not repo_path:
        return [], ["프로젝트에 앱 서버 Git 저장소 경로가 등록되지 않았습니다."]
    errors: list[str] = []
    symbols: list[JavaSymbol] = []
    try:
        repo_root = resolve_repo_path(repo_path)
    except Exception as exc:
        return [], [f"Git 저장소 경로 확인 실패: {exc}"]
    if not repo_root.exists():
        return [], [f"Git 저장소 경로가 존재하지 않습니다: {repo_root}"]

    for path in sorted(repo_root.rglob("*.java")):
        if not path.is_file() or not _is_source_file(path, repo_root):
            continue
        text = _read_text_file(path)
        if text is None:
            errors.append(f"읽을 수 없는 Java 파일: {path}")
            continue
        relative_path = path.relative_to(repo_root).as_posix()
        symbols.extend(extract_java_symbols(relative_path, text))
    return symbols, errors


def _normalize_file_path(file_path: str | None) -> str:
    return (file_path or "").replace("\\", "/").strip()


def _is_java_path(file_path: str | None) -> bool:
    return _normalize_file_path(file_path).lower().endswith(".java")


def _renamed_old_path(file: CommitFile) -> str | None:
    diff_text = file.diff_text or ""
    match = re.search(r"(?m)^rename from\s+(.+)$", diff_text)
    if match:
        return _normalize_file_path(match.group(1))
    diff_match = re.search(r"(?m)^diff --git a/(.+?) b/(.+)$", diff_text)
    if diff_match:
        old_path = _normalize_file_path(diff_match.group(1))
        new_path = _normalize_file_path(diff_match.group(2))
        if old_path and old_path != new_path:
            return old_path
    return None


def _changed_source_clear_paths(files: list[CommitFile]) -> list[str]:
    paths: set[str] = set()
    for file in files:
        change_type = file.change_type or "Modified"
        if change_type not in SOURCE_GRAPH_CLEAR_TYPES:
            continue
        file_path = _normalize_file_path(file.file_path)
        if _is_java_path(file_path):
            paths.add(file_path)
        if change_type == "Renamed":
            old_path = _renamed_old_path(file)
            if _is_java_path(old_path):
                paths.add(_normalize_file_path(old_path))
    return sorted(paths)


def _changed_source_parse_paths(files: list[CommitFile]) -> list[str]:
    paths: set[str] = set()
    for file in files:
        change_type = file.change_type or "Modified"
        if change_type not in SOURCE_GRAPH_CHANGE_TYPES:
            continue
        file_path = _normalize_file_path(file.file_path)
        if _is_java_path(file_path):
            paths.add(file_path)
    return sorted(paths)


def _source_java_symbols_for_paths(repo_path: str | None, file_paths: list[str]) -> tuple[list[JavaSymbol], list[str]]:
    if not file_paths:
        return [], []
    if not repo_path:
        return [], ["프로젝트에 앱 서버 Git 저장소 경로가 등록되지 않았습니다."]
    try:
        repo_root = resolve_repo_path(repo_path)
    except Exception as exc:
        return [], [f"Git 저장소 경로 확인 실패: {exc}"]
    if not repo_root.exists():
        return [], [f"Git 저장소 경로가 존재하지 않습니다: {repo_root}"]

    symbols: list[JavaSymbol] = []
    errors: list[str] = []
    for file_path in file_paths:
        absolute_path = repo_root / file_path
        if not absolute_path.exists():
            continue
        if not absolute_path.is_file() or not _is_source_file(absolute_path, repo_root):
            continue
        text = _read_text_file(absolute_path)
        if text is None:
            errors.append(f"읽을 수 없는 Java 파일: {absolute_path}")
            continue
        symbols.extend(extract_java_symbols(file_path, text))
    return symbols, errors


def _project_repo_head(project: Project) -> str | None:
    if not project.git_repo_path:
        return None
    return get_head_commit_hash(project.git_repo_path)


def _max_project_commit_id(db: Session, project_id: int) -> int | None:
    return db.query(func.max(GitCommit.id)).filter(GitCommit.project_id == project_id).scalar()


def _max_project_mapping_updated_at(db: Session, project_id: int) -> datetime | None:
    return (
        db.query(func.max(ProgramCommitMapping.updated_at))
        .join(Program, ProgramCommitMapping.program_id == Program.id)
        .filter(Program.project_id == project_id)
        .scalar()
    )


def _get_graph_sync_state(db: Session, project_id: int) -> ProjectGraphSyncState | None:
    return db.query(ProjectGraphSyncState).filter(ProjectGraphSyncState.project_id == project_id).one_or_none()


def _get_or_create_graph_sync_state(db: Session, project_id: int) -> ProjectGraphSyncState:
    state = _get_graph_sync_state(db, project_id)
    if state is not None:
        return state
    state = ProjectGraphSyncState(project_id=project_id)
    db.add(state)
    db.flush()
    return state


def _is_after(left: datetime | None, right: datetime | None) -> bool:
    if left is None:
        return False
    if right is None:
        return True
    try:
        return left > right
    except TypeError:
        return left.replace(tzinfo=None) > right.replace(tzinfo=None)


def _record_graph_sync_attempt(
    db: Session,
    project_id: int,
    mode: str,
    result: Neo4jSyncResult,
    *,
    raw_metadata: dict[str, Any] | None = None,
) -> None:
    if result.status == "skipped":
        return
    project = db.get(Project, project_id)
    if project is None:
        return

    state = _get_or_create_graph_sync_state(db, project_id)
    now = datetime.now(timezone.utc)
    repo_head = _project_repo_head(project)
    db_sync_head = project.last_synced_commit_hash
    last_commit_db_id = _max_project_commit_id(db, project_id)
    last_mapping_updated_at = _max_project_mapping_updated_at(db, project_id)

    if result.status == "completed":
        state.repo_head_hash = repo_head
        state.db_sync_head_hash = db_sync_head
        state.synced_at = now
        state.node_count = int(result.node_count or 0)
        state.edge_count = int(result.edge_count or 0)
        state.last_commit_db_id = last_commit_db_id
        state.last_mapping_updated_at = last_mapping_updated_at
        state.error_summary = None
    else:
        state.error_summary = "\n".join(result.errors[:3]) or result.summary

    state.sync_mode = mode
    state.status = result.status
    state.raw_metadata = {
        **(state.raw_metadata or {}),
        "last_attempted_at": now.isoformat(),
        "last_attempt_mode": mode,
        "last_attempt_status": result.status,
        "last_attempt_summary": result.summary,
        "last_attempt_errors": result.errors,
        "last_attempt_node_count": int(result.node_count or 0),
        "last_attempt_edge_count": int(result.edge_count or 0),
        **(raw_metadata or {}),
    }
    db.commit()


def get_project_graph_freshness(db: Session, project_id: int) -> Neo4jGraphFreshness:
    project = db.get(Project, project_id)
    if project is None:
        return Neo4jGraphFreshness("failed", "프로젝트를 찾을 수 없습니다.")

    repo_head = _project_repo_head(project)
    db_sync_head = project.last_synced_commit_hash
    state = _get_graph_sync_state(db, project_id)
    if not settings.neo4j_enabled:
        return Neo4jGraphFreshness(
            "skipped",
            "Neo4j가 비활성화되어 graph 상태를 확인하지 않습니다.",
            repo_head_hash=repo_head,
            db_sync_head_hash=db_sync_head,
            graph_sync_head_hash=state.repo_head_hash if state else None,
            synced_at=state.synced_at if state else None,
            sync_mode=state.sync_mode if state else None,
            node_count=state.node_count if state else 0,
            edge_count=state.edge_count if state else 0,
            last_commit_db_id=state.last_commit_db_id if state else None,
            last_mapping_updated_at=state.last_mapping_updated_at if state else None,
        )

    if state is None:
        return Neo4jGraphFreshness(
            "missing",
            "Neo4j graph를 아직 저장하지 않았습니다. 전체 재동기화를 먼저 실행하세요.",
            repo_head_hash=repo_head,
            db_sync_head_hash=db_sync_head,
        )

    if state.status == "failed":
        return Neo4jGraphFreshness(
            "failed",
            f"마지막 graph sync가 실패했습니다: {state.error_summary or '오류 내용을 확인하세요.'}",
            repo_head_hash=repo_head,
            db_sync_head_hash=db_sync_head,
            graph_sync_head_hash=state.repo_head_hash,
            synced_at=state.synced_at,
            sync_mode=state.sync_mode,
            node_count=state.node_count,
            edge_count=state.edge_count,
            last_commit_db_id=state.last_commit_db_id,
            last_mapping_updated_at=state.last_mapping_updated_at,
            errors=[state.error_summary] if state.error_summary else [],
        )

    current_mapping_updated_at = _max_project_mapping_updated_at(db, project_id)
    stale_reasons: list[str] = []
    if repo_head and state.repo_head_hash != repo_head:
        stale_reasons.append("Repo HEAD가 graph sync 이후 변경되었습니다.")
    if db_sync_head and state.db_sync_head_hash != db_sync_head:
        stale_reasons.append("DB Git Sync HEAD가 graph sync 이후 변경되었습니다.")
    if _is_after(current_mapping_updated_at, state.last_mapping_updated_at):
        stale_reasons.append("프로그램-커밋 매핑이 graph sync 이후 변경되었습니다.")
    if project.git_repo_path and repo_head is None:
        stale_reasons.append("앱 서버 Git 저장소의 현재 HEAD를 확인하지 못했습니다.")

    status = "stale" if stale_reasons else "latest"
    summary = " / ".join(stale_reasons) if stale_reasons else "Neo4j graph가 현재 DB/Git 기준과 일치합니다."
    return Neo4jGraphFreshness(
        status,
        summary,
        repo_head_hash=repo_head,
        db_sync_head_hash=db_sync_head,
        graph_sync_head_hash=state.repo_head_hash,
        synced_at=state.synced_at,
        sync_mode=state.sync_mode,
        node_count=state.node_count,
        edge_count=state.edge_count,
        last_commit_db_id=state.last_commit_db_id,
        last_mapping_updated_at=current_mapping_updated_at or state.last_mapping_updated_at,
    )


def build_project_graph_payload(db: Session, project_id: int) -> GraphPayload:
    project = db.get(Project, project_id)
    if project is None:
        return GraphPayload(project_id, "-", [], [], [], [], [], ["프로젝트를 찾을 수 없습니다."])

    nodes: dict[str, GraphNode] = {}
    edges: dict[tuple[str, str, str], GraphEdge] = {}
    errors: list[str] = []

    def add_node(node: GraphNode) -> None:
        nodes[node.node_id] = node

    def add_edge(edge: GraphEdge) -> None:
        edges[_edge_key(edge)] = edge

    def ensure_domain(domain: str) -> str:
        domain_key = _clean_key(domain.lower(), "unknown")
        node_id = _node_id(project_id, "domain", domain_key)
        add_node(GraphNode(node_id, "domain", domain_key, {"domain": domain_key}))
        add_edge(GraphEdge(project_node_id, node_id, "HAS_DOMAIN"))
        return node_id

    project_node_id = _node_id(project_id, "project", project.id)
    add_node(GraphNode(project_node_id, "project", project.name, {"project_id": project.id, "git_repo_path": project.git_repo_path}))

    programs = (
        db.query(Program)
        .options(joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit))
        .filter(Program.project_id == project_id)
        .all()
    )
    commits = (
        db.query(GitCommit)
        .options(joinedload(GitCommit.files))
        .filter(GitCommit.project_id == project_id)
        .all()
    )

    commit_nodes: dict[int, str] = {}
    program_nodes: dict[int, str] = {}
    file_nodes: dict[str, str] = {}
    file_domains: dict[str, str] = {}

    for program in programs:
        program_node_id = _node_id(project_id, "program", program.id)
        program_nodes[int(program.id)] = program_node_id
        domain = _clean_key(program.module or program.screen_name or program.program_name, f"program-{program.id}").lower()
        domain_node_id = ensure_domain(domain)
        add_node(
            GraphNode(
                program_node_id,
                "program",
                f"{program.program_id or '-'} {program.program_name}".strip(),
                {
                    "program_db_id": program.id,
                    "program_id": program.program_id,
                    "program_name": program.program_name,
                    "module": program.module,
                    "status": program.status,
                    "progress_rate": program.progress_rate,
                },
            )
        )
        add_edge(GraphEdge(project_node_id, program_node_id, "HAS_PROGRAM"))
        add_edge(GraphEdge(domain_node_id, program_node_id, "OWNS_PROGRAM"))

    for commit in commits:
        commit_node_id = _node_id(project_id, "commit", commit.commit_hash)
        commit_nodes[int(commit.id)] = commit_node_id
        add_node(
            GraphNode(
                commit_node_id,
                "commit",
                f"{_short_commit(commit.commit_hash)} {commit.message or ''}".strip(),
                {
                    "commit_db_id": commit.id,
                    "commit_hash": commit.commit_hash,
                    "message": commit.message,
                    "author": commit.author_name or commit.author,
                    "committed_at": commit.committed_at,
                    "mapping_analysis_status": commit.mapping_analysis_status,
                },
            )
        )
        add_edge(GraphEdge(project_node_id, commit_node_id, "HAS_COMMIT"))
        for file in commit.files:
            file_path = (file.file_path or "").replace("\\", "/")
            if not file_path:
                continue
            file_node_id = file_nodes.setdefault(file_path, _node_id(project_id, "file", file_path))
            file_domain = _domain_from_path(file_path)
            file_domains[file_path] = file_domain
            domain_node_id = ensure_domain(file_domain)
            add_node(GraphNode(file_node_id, "file", file_path, {"file_path": file_path, "domain": file_domain}))
            add_edge(GraphEdge(project_node_id, file_node_id, "HAS_FILE"))
            add_edge(GraphEdge(domain_node_id, file_node_id, "HAS_FILE"))
            add_edge(
                GraphEdge(
                    commit_node_id,
                    file_node_id,
                    "TOUCHES_FILE",
                    properties={"change_type": file.change_type, "commit_file_id": file.id},
                )
            )
            add_edge(GraphEdge(commit_node_id, domain_node_id, "TOUCHES_DOMAIN"))

    for program in programs:
        program_node_id = program_nodes.get(int(program.id))
        if not program_node_id:
            continue
        for mapping in program.mappings:
            if mapping.is_related is False:
                continue
            commit_node_id = commit_nodes.get(int(mapping.commit_id))
            if not commit_node_id:
                continue
            add_edge(
                GraphEdge(
                    program_node_id,
                    commit_node_id,
                    "MAPPED_TO_COMMIT",
                    weight=float(mapping.relevance_score or 0),
                    properties={
                        "relevance_score": mapping.relevance_score,
                        "implementation_status": mapping.implementation_status,
                        "reason": mapping.reason,
                    },
                )
            )

    symbols, symbol_errors = _source_java_symbols(project.git_repo_path)
    errors.extend(symbol_errors)
    classes_by_fqn = {symbol.qualified_name: symbol for symbol in symbols}
    classes_by_simple = defaultdict(list)
    for symbol in symbols:
        classes_by_simple[symbol.class_name].append(symbol)
        file_path = symbol.file_path.replace("\\", "/")
        file_node_id = file_nodes.setdefault(file_path, _node_id(project_id, "file", file_path))
        class_node_id = _node_id(project_id, "class", symbol.qualified_name)
        domain_node_id = ensure_domain(symbol.domain)
        file_domains[file_path] = symbol.domain
        add_node(GraphNode(file_node_id, "file", file_path, {"file_path": file_path, "domain": symbol.domain}))
        add_node(
            GraphNode(
                class_node_id,
                "class",
                symbol.qualified_name,
                {
                    "class_name": symbol.class_name,
                    "qualified_name": symbol.qualified_name,
                    "kind": symbol.kind,
                    "package": symbol.package,
                    "file_path": file_path,
                    "domain": symbol.domain,
                },
            )
        )
        add_edge(GraphEdge(project_node_id, file_node_id, "HAS_FILE"))
        add_edge(GraphEdge(domain_node_id, file_node_id, "HAS_FILE"))
        add_edge(GraphEdge(domain_node_id, class_node_id, "CONTAINS_CLASS"))
        add_edge(GraphEdge(file_node_id, class_node_id, "CONTAINS_CLASS"))

    class_import_rows: list[dict[str, str]] = []
    for symbol in symbols:
        source_node_id = _node_id(project_id, "class", symbol.qualified_name)
        for imported in symbol.imports:
            targets = []
            direct = classes_by_fqn.get(imported)
            if direct is not None:
                targets = [direct]
            else:
                targets = classes_by_simple.get(imported.split(".")[-1], [])
            for target in targets:
                if target.qualified_name == symbol.qualified_name:
                    continue
                target_node_id = _node_id(project_id, "class", target.qualified_name)
                add_edge(GraphEdge(source_node_id, target_node_id, "IMPORTS_CLASS"))
                class_import_rows.append({"source": symbol.qualified_name, "target": target.qualified_name})

    file_classes = defaultdict(list)
    for symbol in symbols:
        file_classes[symbol.file_path.replace("\\", "/")].append(symbol)
    commit_programs = defaultdict(list)
    for edge in edges.values():
        if edge.edge_type == "MAPPED_TO_COMMIT":
            commit_programs[edge.to_node_id].append(nodes[edge.from_node_id].label)
    impact_rows: list[ImpactPathRow] = []
    for commit in sorted(commits, key=lambda row: row.committed_at or datetime.min, reverse=True):
        commit_node_id = commit_nodes.get(int(commit.id))
        if not commit_node_id:
            continue
        programs_for_commit = commit_programs.get(commit_node_id, ["-"])
        for file in commit.files:
            file_path = (file.file_path or "").replace("\\", "/")
            for symbol in file_classes.get(file_path, []):
                for program_label in programs_for_commit:
                    impact_rows.append(
                        ImpactPathRow(
                            commit=_short_commit(commit.commit_hash),
                            program=program_label,
                            file_path=file_path,
                            class_name=symbol.qualified_name,
                            domain=symbol.domain,
                        )
                    )
                    if len(impact_rows) >= 100:
                        break
                if len(impact_rows) >= 100:
                    break
            if len(impact_rows) >= 100:
                break
        if len(impact_rows) >= 100:
            break

    domain_programs = defaultdict(set)
    domain_files = defaultdict(set)
    domain_classes = defaultdict(set)
    domain_commits = defaultdict(set)
    for edge in edges.values():
        if edge.edge_type == "OWNS_PROGRAM":
            domain_programs[nodes[edge.from_node_id].label].add(edge.to_node_id)
        elif edge.edge_type == "HAS_FILE" and nodes.get(edge.from_node_id, GraphNode("", "", "")).node_type == "domain":
            domain_files[nodes[edge.from_node_id].label].add(edge.to_node_id)
        elif edge.edge_type == "CONTAINS_CLASS" and nodes.get(edge.from_node_id, GraphNode("", "", "")).node_type == "domain":
            domain_classes[nodes[edge.from_node_id].label].add(edge.to_node_id)
        elif edge.edge_type == "TOUCHES_DOMAIN":
            domain_commits[nodes[edge.to_node_id].label].add(edge.from_node_id)

    domain_names = sorted(set(domain_programs) | set(domain_files) | set(domain_classes) | set(domain_commits))
    domain_rows = [
        DomainSummaryRow(
            domain=domain,
            program_count=len(domain_programs[domain]),
            file_count=len(domain_files[domain]),
            class_count=len(domain_classes[domain]),
            commit_count=len(domain_commits[domain]),
        )
        for domain in domain_names
    ]
    domain_rows.sort(key=lambda row: (row.class_count + row.file_count + row.commit_count, row.domain), reverse=True)

    return GraphPayload(
        project_id=int(project.id),
        project_name=project.name,
        nodes=list(nodes.values()),
        edges=list(edges.values()),
        domain_rows=domain_rows,
        impact_rows=impact_rows,
        class_import_rows=class_import_rows,
        errors=errors,
    )


def _changed_file_stats(files: list[CommitFile], source_clear_paths: list[str]) -> dict[str, Any]:
    change_counts = Counter(file.change_type or "Modified" for file in files)
    java_file_count = sum(1 for file in files if _is_java_path(file.file_path))
    return {
        "changed_file_count": len(files),
        "java_file_count": java_file_count,
        "non_source_file_count": max(0, len(files) - java_file_count),
        "source_clear_path_count": len(source_clear_paths),
        "change_counts": dict(change_counts),
    }


def _build_incremental_project_graph_payload(
    db: Session,
    project: Project,
    changed_commits: list[GitCommit],
) -> tuple[GraphPayload, list[str], dict[str, Any]]:
    nodes: dict[str, GraphNode] = {}
    edges: dict[tuple[str, str, str], GraphEdge] = {}
    errors: list[str] = []
    project_id = int(project.id)

    def add_node(node: GraphNode) -> None:
        nodes[node.node_id] = node

    def add_edge(edge: GraphEdge) -> None:
        edges[_edge_key(edge)] = edge

    project_node_id = _node_id(project_id, "project", project.id)
    add_node(GraphNode(project_node_id, "project", project.name, {"project_id": project.id, "git_repo_path": project.git_repo_path}))

    def ensure_domain(domain: str) -> str:
        domain_key = _clean_key(domain.lower(), "unknown")
        node_id = _node_id(project_id, "domain", domain_key)
        add_node(GraphNode(node_id, "domain", domain_key, {"domain": domain_key}))
        add_edge(GraphEdge(project_node_id, node_id, "HAS_DOMAIN"))
        return node_id

    programs = (
        db.query(Program)
        .options(joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit))
        .filter(Program.project_id == project_id)
        .all()
    )
    changed_files = [file for commit in changed_commits for file in (commit.files or [])]
    clear_source_paths = _changed_source_clear_paths(changed_files)
    parse_source_paths = _changed_source_parse_paths(changed_files)
    stats = _changed_file_stats(changed_files, clear_source_paths)
    stats["changed_commit_count"] = len(changed_commits)

    program_nodes: dict[int, str] = {}
    commit_nodes: dict[int, str] = {}
    file_nodes: dict[str, str] = {}

    for program in programs:
        program_node_id = _node_id(project_id, "program", program.id)
        program_nodes[int(program.id)] = program_node_id
        domain = _clean_key(program.module or program.screen_name or program.program_name, f"program-{program.id}").lower()
        domain_node_id = ensure_domain(domain)
        add_node(
            GraphNode(
                program_node_id,
                "program",
                f"{program.program_id or '-'} {program.program_name}".strip(),
                {
                    "program_db_id": program.id,
                    "program_id": program.program_id,
                    "program_name": program.program_name,
                    "module": program.module,
                    "status": program.status,
                    "progress_rate": program.progress_rate,
                },
            )
        )
        add_edge(GraphEdge(project_node_id, program_node_id, "HAS_PROGRAM"))
        add_edge(GraphEdge(domain_node_id, program_node_id, "OWNS_PROGRAM"))

    def add_commit_node(commit: GitCommit) -> str:
        commit_node_id = _node_id(project_id, "commit", commit.commit_hash)
        commit_nodes[int(commit.id)] = commit_node_id
        add_node(
            GraphNode(
                commit_node_id,
                "commit",
                f"{_short_commit(commit.commit_hash)} {commit.message or ''}".strip(),
                {
                    "commit_db_id": commit.id,
                    "commit_hash": commit.commit_hash,
                    "message": commit.message,
                    "author": commit.author_name or commit.author,
                    "committed_at": commit.committed_at,
                    "mapping_analysis_status": commit.mapping_analysis_status,
                },
            )
        )
        add_edge(GraphEdge(project_node_id, commit_node_id, "HAS_COMMIT"))
        return commit_node_id

    for commit in changed_commits:
        commit_node_id = add_commit_node(commit)
        for file in commit.files or []:
            file_path = _normalize_file_path(file.file_path)
            if not file_path:
                continue
            file_node_id = file_nodes.setdefault(file_path, _node_id(project_id, "file", file_path))
            file_domain = _domain_from_path(file_path)
            domain_node_id = ensure_domain(file_domain)
            add_node(GraphNode(file_node_id, "file", file_path, {"file_path": file_path, "domain": file_domain}))
            add_edge(GraphEdge(project_node_id, file_node_id, "HAS_FILE"))
            add_edge(GraphEdge(domain_node_id, file_node_id, "HAS_FILE"))
            add_edge(
                GraphEdge(
                    commit_node_id,
                    file_node_id,
                    "TOUCHES_FILE",
                    properties={"change_type": file.change_type, "commit_file_id": file.id},
                )
            )
            add_edge(GraphEdge(commit_node_id, domain_node_id, "TOUCHES_DOMAIN"))

    for program in programs:
        program_node_id = program_nodes.get(int(program.id))
        if not program_node_id:
            continue
        for mapping in program.mappings:
            if mapping.is_related is False or mapping.commit is None:
                continue
            commit_node_id = commit_nodes.get(int(mapping.commit_id)) or add_commit_node(mapping.commit)
            add_edge(
                GraphEdge(
                    program_node_id,
                    commit_node_id,
                    "MAPPED_TO_COMMIT",
                    weight=float(mapping.relevance_score or 0),
                    properties={
                        "relevance_score": mapping.relevance_score,
                        "implementation_status": mapping.implementation_status,
                        "reason": mapping.reason,
                    },
                )
            )

    symbols, symbol_errors = _source_java_symbols_for_paths(project.git_repo_path, parse_source_paths)
    errors.extend(symbol_errors)
    for symbol in symbols:
        file_path = _normalize_file_path(symbol.file_path)
        file_node_id = file_nodes.setdefault(file_path, _node_id(project_id, "file", file_path))
        class_node_id = _node_id(project_id, "class", symbol.qualified_name)
        domain_node_id = ensure_domain(symbol.domain)
        add_node(GraphNode(file_node_id, "file", file_path, {"file_path": file_path, "domain": symbol.domain}))
        add_node(
            GraphNode(
                class_node_id,
                "class",
                symbol.qualified_name,
                {
                    "class_name": symbol.class_name,
                    "qualified_name": symbol.qualified_name,
                    "kind": symbol.kind,
                    "package": symbol.package,
                    "file_path": file_path,
                    "domain": symbol.domain,
                },
            )
        )
        add_edge(GraphEdge(project_node_id, file_node_id, "HAS_FILE"))
        add_edge(GraphEdge(domain_node_id, file_node_id, "HAS_FILE"))
        add_edge(GraphEdge(domain_node_id, class_node_id, "CONTAINS_CLASS"))
        add_edge(GraphEdge(file_node_id, class_node_id, "CONTAINS_CLASS"))
        for imported in symbol.imports:
            add_edge(GraphEdge(class_node_id, _node_id(project_id, "class", imported), "IMPORTS_CLASS"))

    return (
        GraphPayload(
            project_id=project_id,
            project_name=project.name,
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            domain_rows=[],
            impact_rows=[],
            class_import_rows=[],
            errors=errors,
        ),
        clear_source_paths,
        stats,
    )


def _driver():
    if GraphDatabase is None:
        raise RuntimeError("neo4j Python driver is not installed. Run pip install -r requirements.txt.")
    return GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))


def _session_kwargs() -> dict[str, str]:
    return {"database": settings.neo4j_database} if settings.neo4j_database else {}


def get_neo4j_connection_status() -> Neo4jConnectionStatus:
    if not settings.neo4j_enabled:
        return Neo4jConnectionStatus(False, False, "NEO4J_ENABLED=false", settings.neo4j_uri, settings.neo4j_database)
    if GraphDatabase is None:
        return Neo4jConnectionStatus(True, False, "neo4j Python driver가 설치되지 않았습니다.", settings.neo4j_uri, settings.neo4j_database)
    try:
        with _driver() as driver:
            driver.verify_connectivity()
    except Exception as exc:
        return Neo4jConnectionStatus(True, False, f"Neo4j 연결 실패: {exc}", settings.neo4j_uri, settings.neo4j_database)
    return Neo4jConnectionStatus(True, True, "Neo4j 연결됨", settings.neo4j_uri, settings.neo4j_database)


def clear_project_graph(project_id: int) -> Neo4jSyncResult:
    if not settings.neo4j_enabled:
        return Neo4jSyncResult("skipped", "Neo4j가 비활성화되어 graph cleanup을 건너뜁니다.")
    try:
        with _driver() as driver:
            with driver.session(**_session_kwargs()) as session:
                deleted = session.execute_write(_clear_project_graph_tx, project_id)
    except Exception as exc:
        return Neo4jSyncResult("failed", "Neo4j graph cleanup 실패", errors=[str(exc)])
    return Neo4jSyncResult("completed", f"Neo4j graph node {deleted}개를 삭제했습니다.", node_count=int(deleted or 0))


def _clear_project_graph_tx(tx, project_id: int) -> int:
    result = tx.run(
        """
        MATCH (n:KnowledgeNode {project_id: $project_id})
        WITH collect(n) AS nodes, count(n) AS deleted_count
        FOREACH (node IN nodes | DETACH DELETE node)
        RETURN deleted_count
        """,
        project_id=int(project_id),
    )
    row = result.single()
    return int(row["deleted_count"] if row else 0)


def sync_project_graph_to_neo4j(db: Session, project_id: int) -> Neo4jSyncResult:
    payload = build_project_graph_payload(db, project_id)
    if payload.errors and not payload.nodes:
        result = Neo4jSyncResult("failed", "Neo4j 동기화 payload 생성 실패", errors=payload.errors)
        _record_graph_sync_attempt(db, project_id, "full", result, raw_metadata={"payload_errors": payload.errors})
        return result
    if not settings.neo4j_enabled:
        return Neo4jSyncResult(
            "skipped",
            "Neo4j가 비활성화되어 동기화하지 않았습니다. NEO4J_ENABLED=true로 설정하세요.",
            node_count=len(payload.nodes),
            edge_count=len(payload.edges),
            node_counts=dict(payload.node_counts),
            edge_counts=dict(payload.edge_counts),
            errors=payload.errors,
        )

    nodes = [node.to_neo4j(project_id) for node in payload.nodes]
    edges = [edge.to_neo4j(project_id) for edge in payload.edges]
    try:
        with _driver() as driver:
            with driver.session(**_session_kwargs()) as session:
                _ensure_neo4j_schema(session)
                session.execute_write(_sync_project_graph_tx, project_id, nodes, edges)
    except Exception as exc:
        result = Neo4jSyncResult(
            "failed",
            "Neo4j graph 동기화 실패",
            node_count=len(nodes),
            edge_count=len(edges),
            node_counts=dict(payload.node_counts),
            edge_counts=dict(payload.edge_counts),
            errors=[*payload.errors, str(exc)],
        )
        _record_graph_sync_attempt(db, project_id, "full", result, raw_metadata={"payload_errors": payload.errors})
        return result

    result = Neo4jSyncResult(
        "completed",
        f"Neo4j에 node {len(nodes)}개, edge {len(edges)}개를 동기화했습니다.",
        node_count=len(nodes),
        edge_count=len(edges),
        node_counts=dict(payload.node_counts),
        edge_counts=dict(payload.edge_counts),
        errors=payload.errors,
    )
    _record_graph_sync_attempt(db, project_id, "full", result, raw_metadata={"payload_errors": payload.errors})
    return result


def sync_project_graph_incrementally_to_neo4j(db: Session, project_id: int) -> Neo4jSyncResult:
    project = db.get(Project, project_id)
    if project is None:
        return Neo4jSyncResult("failed", "프로젝트를 찾을 수 없습니다.")
    if not settings.neo4j_enabled:
        return Neo4jSyncResult("skipped", "Neo4j가 비활성화되어 증분 동기화하지 않았습니다. NEO4J_ENABLED=true로 설정하세요.")

    state = _get_graph_sync_state(db, project_id)
    if state is None or state.last_commit_db_id is None:
        return Neo4jSyncResult("skipped", "증분 동기화 기준이 없습니다. 먼저 전체 Neo4j 동기화를 실행하세요.")

    repo_head = _project_repo_head(project)
    db_sync_head = project.last_synced_commit_hash
    if repo_head and db_sync_head and repo_head != db_sync_head:
        return Neo4jSyncResult(
            "skipped",
            "앱 서버 저장소 HEAD와 DB Git Sync HEAD가 다릅니다. 먼저 Git 동기화를 실행한 뒤 graph를 갱신하세요.",
        )

    changed_commits = (
        db.query(GitCommit)
        .options(joinedload(GitCommit.files))
        .filter(GitCommit.project_id == project_id, GitCommit.id > state.last_commit_db_id)
        .order_by(GitCommit.id.asc())
        .all()
    )
    current_mapping_updated_at = _max_project_mapping_updated_at(db, project_id)
    mapping_changed = _is_after(current_mapping_updated_at, state.last_mapping_updated_at)
    if (
        not changed_commits
        and not mapping_changed
        and (not repo_head or state.repo_head_hash == repo_head)
        and (not db_sync_head or state.db_sync_head_hash == db_sync_head)
    ):
        return Neo4jSyncResult(
            "skipped",
            "Neo4j graph가 이미 최신 상태입니다.",
            node_count=state.node_count,
            edge_count=state.edge_count,
        )

    payload, clear_source_paths, stats = _build_incremental_project_graph_payload(db, project, changed_commits)
    if payload.errors and stats.get("source_clear_path_count", 0) > 0:
        result = Neo4jSyncResult(
            "failed",
            "Neo4j 증분 동기화 payload 생성 실패",
            node_count=len(payload.nodes),
            edge_count=len(payload.edges),
            node_counts=dict(payload.node_counts),
            edge_counts=dict(payload.edge_counts),
            errors=payload.errors,
        )
        _record_graph_sync_attempt(db, project_id, "incremental", result, raw_metadata=stats)
        return result

    nodes = [node.to_neo4j(project_id) for node in payload.nodes]
    edges = [edge.to_neo4j(project_id) for edge in payload.edges]
    try:
        with _driver() as driver:
            with driver.session(**_session_kwargs()) as session:
                _ensure_neo4j_schema(session)
                write_counts = session.execute_write(
                    _sync_project_graph_incremental_tx,
                    project_id,
                    clear_source_paths,
                    nodes,
                    edges,
                )
                node_counts, edge_counts = session.execute_read(_read_project_summary_tx, project_id)
    except Exception as exc:
        result = Neo4jSyncResult(
            "failed",
            "Neo4j graph 증분 동기화 실패. 전체 재동기화를 실행해 복구할 수 있습니다.",
            node_count=len(nodes),
            edge_count=len(edges),
            node_counts=dict(payload.node_counts),
            edge_counts=dict(payload.edge_counts),
            errors=[*payload.errors, str(exc)],
        )
        _record_graph_sync_attempt(db, project_id, "incremental", result, raw_metadata=stats)
        return result

    stats = {
        **stats,
        **write_counts,
        "mapping_changed": mapping_changed,
    }
    result = Neo4jSyncResult(
        "completed",
        (
            "Neo4j 최신 변경분 반영 완료: "
            f"commit {stats['changed_commit_count']}개, file {stats['changed_file_count']}개, "
            f"current source class {write_counts.get('deleted_class_count', 0)}개 제거, "
            f"node {len(nodes)}개/edge {len(edges)}개 upsert."
        ),
        node_count=sum(node_counts.values()),
        edge_count=sum(edge_counts.values()),
        node_counts=node_counts,
        edge_counts=edge_counts,
        errors=payload.errors,
    )
    _record_graph_sync_attempt(db, project_id, "incremental", result, raw_metadata=stats)
    return result


def _ensure_neo4j_schema(session) -> None:
    session.run(
        "CREATE CONSTRAINT knowledge_node_id IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id IS UNIQUE"
    ).consume()


def _sync_project_graph_tx(tx, project_id: int, nodes: list[dict], edges: list[dict]) -> None:
    _clear_project_graph_tx(tx, project_id)
    tx.run(
        """
        UNWIND $nodes AS row
        MERGE (n:KnowledgeNode {node_id: row.node_id})
        SET n = row
        """,
        nodes=nodes,
    )
    tx.run(
        """
        UNWIND $edges AS row
        MATCH (source:KnowledgeNode {node_id: row.from_node_id})
        MATCH (target:KnowledgeNode {node_id: row.to_node_id})
        MERGE (source)-[rel:RELATED {edge_id: row.edge_id}]->(target)
        SET rel = row
        """,
        edges=edges,
    )


def _sync_project_graph_incremental_tx(
    tx,
    project_id: int,
    clear_source_paths: list[str],
    nodes: list[dict],
    edges: list[dict],
) -> dict[str, int]:
    deleted_class_count = 0
    if clear_source_paths:
        result = tx.run(
            """
            MATCH (class_node:KnowledgeNode {project_id: $project_id, node_type: 'class'})
            WHERE class_node.file_path IN $file_paths
            WITH collect(class_node) AS class_nodes, count(class_node) AS deleted_class_count
            FOREACH (node IN class_nodes | DETACH DELETE node)
            RETURN deleted_class_count
            """,
            project_id=int(project_id),
            file_paths=clear_source_paths,
        )
        row = result.single()
        deleted_class_count = int(row["deleted_class_count"] if row else 0)

    mapping_result = tx.run(
        """
        MATCH (:KnowledgeNode {project_id: $project_id})-[rel:RELATED {project_id: $project_id, edge_type: 'MAPPED_TO_COMMIT'}]->
              (:KnowledgeNode {project_id: $project_id})
        WITH collect(rel) AS rels, count(rel) AS deleted_mapping_count
        FOREACH (rel IN rels | DELETE rel)
        RETURN deleted_mapping_count
        """,
        project_id=int(project_id),
    )
    mapping_row = mapping_result.single()
    deleted_mapping_count = int(mapping_row["deleted_mapping_count"] if mapping_row else 0)

    tx.run(
        """
        UNWIND $nodes AS row
        MERGE (n:KnowledgeNode {node_id: row.node_id})
        SET n = row
        """,
        nodes=nodes,
    )
    tx.run(
        """
        UNWIND $edges AS row
        MATCH (source:KnowledgeNode {node_id: row.from_node_id})
        MATCH (target:KnowledgeNode {node_id: row.to_node_id})
        MERGE (source)-[rel:RELATED {edge_id: row.edge_id}]->(target)
        SET rel = row
        """,
        edges=edges,
    )
    return {
        "deleted_class_count": deleted_class_count,
        "deleted_mapping_count": deleted_mapping_count,
        "upsert_node_count": len(nodes),
        "upsert_edge_count": len(edges),
    }


def get_neo4j_project_summary(project_id: int) -> Neo4jSyncResult:
    if not settings.neo4j_enabled:
        return Neo4jSyncResult("skipped", "Neo4j가 비활성화되어 summary를 읽지 않았습니다.")
    try:
        with _driver() as driver:
            with driver.session(**_session_kwargs()) as session:
                node_counts, edge_counts = session.execute_read(_read_project_summary_tx, project_id)
    except Exception as exc:
        return Neo4jSyncResult("failed", "Neo4j summary 조회 실패", errors=[str(exc)])
    return Neo4jSyncResult(
        "completed",
        "Neo4j summary 조회 완료",
        node_count=sum(node_counts.values()),
        edge_count=sum(edge_counts.values()),
        node_counts=node_counts,
        edge_counts=edge_counts,
    )


def _read_project_summary_tx(tx, project_id: int) -> tuple[dict[str, int], dict[str, int]]:
    node_rows = tx.run(
        """
        MATCH (n:KnowledgeNode {project_id: $project_id})
        RETURN n.node_type AS node_type, count(n) AS count
        ORDER BY node_type
        """,
        project_id=int(project_id),
    )
    edge_rows = tx.run(
        """
        MATCH (:KnowledgeNode {project_id: $project_id})-[rel:RELATED]->(:KnowledgeNode {project_id: $project_id})
        RETURN rel.edge_type AS edge_type, count(rel) AS count
        ORDER BY edge_type
        """,
        project_id=int(project_id),
    )
    node_counts = {str(row["node_type"]): int(row["count"]) for row in node_rows}
    edge_counts = {str(row["edge_type"]): int(row["count"]) for row in edge_rows}
    return node_counts, edge_counts


def find_project_graph_evidence(
    project_id: int,
    question: str,
    sources: list[dict],
    *,
    expanded_queries: list[str] | None = None,
    limit: int = 8,
) -> GraphEvidenceSearchResult:
    seeds = build_graph_evidence_seeds(question, sources, expanded_queries=expanded_queries)
    if not seeds:
        return GraphEvidenceSearchResult("skipped", "GraphRAG seed 후보가 없어 graph evidence 조회를 건너뜁니다.")
    if not settings.neo4j_enabled:
        return GraphEvidenceSearchResult(
            "skipped",
            "Neo4j가 비활성화되어 Project Chat graph evidence를 조회하지 않았습니다.",
            seeds=seeds,
        )

    safe_limit = max(1, min(int(limit), 20))
    try:
        with _driver() as driver:
            with driver.session(**_session_kwargs()) as session:
                evidence = session.execute_read(_read_project_graph_evidence_tx, project_id, seeds, safe_limit)
    except Exception as exc:
        return GraphEvidenceSearchResult(
            "failed",
            "Project Chat graph evidence 조회 실패",
            seeds=seeds,
            errors=[str(exc)],
        )

    return GraphEvidenceSearchResult(
        "completed",
        f"Project Chat graph evidence {len(evidence)}건 조회",
        evidence=evidence,
        seeds=seeds,
    )


def _read_project_graph_evidence_tx(tx, project_id: int, seeds: list[str], limit: int) -> list[dict[str, Any]]:
    impact_rows = tx.run(
        """
        MATCH (program:KnowledgeNode {project_id: $project_id, node_type: 'program'})
              -[mapping:RELATED {edge_type: 'MAPPED_TO_COMMIT'}]->
              (commit_node:KnowledgeNode {project_id: $project_id, node_type: 'commit'})
        MATCH (commit_node)
              -[touch:RELATED {edge_type: 'TOUCHES_FILE'}]->
              (file:KnowledgeNode {project_id: $project_id, node_type: 'file'})
        OPTIONAL MATCH (file)
              -[contains:RELATED {edge_type: 'CONTAINS_CLASS'}]->
              (class_node:KnowledgeNode {project_id: $project_id, node_type: 'class'})
        WITH program, commit_node, file, class_node,
             [seed IN $seeds WHERE
                toLower(coalesce(program.label, '')) CONTAINS seed OR
                toLower(coalesce(program.program_id, '')) CONTAINS seed OR
                toLower(coalesce(program.program_name, '')) CONTAINS seed OR
                toLower(coalesce(commit_node.label, '')) CONTAINS seed OR
                toLower(coalesce(commit_node.commit_hash, '')) CONTAINS seed OR
                toLower(coalesce(commit_node.message, '')) CONTAINS seed OR
                toLower(coalesce(file.label, '')) CONTAINS seed OR
                toLower(coalesce(file.file_path, '')) CONTAINS seed OR
                toLower(coalesce(file.domain, '')) CONTAINS seed OR
                toLower(coalesce(class_node.label, '')) CONTAINS seed OR
                toLower(coalesce(class_node.class_name, '')) CONTAINS seed OR
                toLower(coalesce(class_node.file_path, '')) CONTAINS seed OR
                toLower(coalesce(class_node.domain, '')) CONTAINS seed
             ] AS matched_seeds
        WHERE size(matched_seeds) > 0
        RETURN matched_seeds,
               program.label AS program,
               coalesce(program.program_id, '-') AS program_id,
               coalesce(commit_node.commit_hash, commit_node.label) AS commit_hash,
               coalesce(commit_node.message, '-') AS commit_message,
               coalesce(file.file_path, file.label) AS file_path,
               coalesce(class_node.label, '-') AS class_name,
               coalesce(class_node.domain, file.domain, '-') AS domain,
               coalesce(commit_node.committed_at, '') AS committed_at
        ORDER BY size(matched_seeds) DESC, committed_at DESC, commit_hash, program, file_path, class_name
        LIMIT $limit
        """,
        project_id=int(project_id),
        seeds=seeds,
        limit=limit,
    )
    evidence: list[dict[str, Any]] = []
    for row in impact_rows:
        commit_hash = str(row["commit_hash"] or "-")
        path = [
            str(row["program"] or "-"),
            _short_commit(commit_hash),
            str(row["file_path"] or "-"),
        ]
        class_name = str(row["class_name"] or "-")
        if class_name != "-":
            path.append(class_name)
        evidence.append(
            {
                "evidence_type": "impact_path",
                "title": "program -> commit -> file -> class",
                "matched_seeds": list(row["matched_seeds"] or []),
                "program": str(row["program"] or "-"),
                "program_id": str(row["program_id"] or "-"),
                "commit": _short_commit(commit_hash),
                "commit_hash": commit_hash,
                "commit_message": str(row["commit_message"] or "-"),
                "file_path": str(row["file_path"] or "-"),
                "class_name": class_name,
                "domain": str(row["domain"] or "-"),
                "path": path,
            }
        )

    import_rows = tx.run(
        """
        MATCH (source:KnowledgeNode {project_id: $project_id, node_type: 'class'})
              -[rel:RELATED {edge_type: 'IMPORTS_CLASS'}]->
              (target:KnowledgeNode {project_id: $project_id, node_type: 'class'})
        WITH source, target,
             [seed IN $seeds WHERE
                toLower(coalesce(source.label, '')) CONTAINS seed OR
                toLower(coalesce(source.class_name, '')) CONTAINS seed OR
                toLower(coalesce(source.file_path, '')) CONTAINS seed OR
                toLower(coalesce(source.domain, '')) CONTAINS seed OR
                toLower(coalesce(target.label, '')) CONTAINS seed OR
                toLower(coalesce(target.class_name, '')) CONTAINS seed OR
                toLower(coalesce(target.file_path, '')) CONTAINS seed OR
                toLower(coalesce(target.domain, '')) CONTAINS seed
             ] AS matched_seeds
        WHERE size(matched_seeds) > 0
        RETURN matched_seeds,
               source.label AS source_class,
               target.label AS target_class,
               coalesce(source.file_path, '-') AS source_file,
               coalesce(target.file_path, '-') AS target_file,
               coalesce(source.domain, '-') AS source_domain,
               coalesce(target.domain, '-') AS target_domain
        ORDER BY size(matched_seeds) DESC, source_class, target_class
        LIMIT $limit
        """,
        project_id=int(project_id),
        seeds=seeds,
        limit=limit,
    )
    for row in import_rows:
        evidence.append(
            {
                "evidence_type": "class_import",
                "title": "class -> imports -> class",
                "matched_seeds": list(row["matched_seeds"] or []),
                "source_class": str(row["source_class"] or "-"),
                "target_class": str(row["target_class"] or "-"),
                "source_file": str(row["source_file"] or "-"),
                "target_file": str(row["target_file"] or "-"),
                "source_domain": str(row["source_domain"] or "-"),
                "target_domain": str(row["target_domain"] or "-"),
                "path": [str(row["source_class"] or "-"), str(row["target_class"] or "-")],
            }
        )

    domain_rows = tx.run(
        """
        MATCH (domain:KnowledgeNode {project_id: $project_id, node_type: 'domain'})
        WITH domain,
             [seed IN $seeds WHERE
                toLower(coalesce(domain.label, '')) CONTAINS seed OR
                toLower(coalesce(domain.domain, '')) CONTAINS seed
             ] AS matched_seeds
        WHERE size(matched_seeds) > 0
        OPTIONAL MATCH (domain)-[:RELATED {edge_type: 'OWNS_PROGRAM'}]->
                       (program:KnowledgeNode {project_id: $project_id, node_type: 'program'})
        WITH domain, matched_seeds, count(DISTINCT program) AS program_count
        OPTIONAL MATCH (domain)-[:RELATED {edge_type: 'HAS_FILE'}]->
                       (file:KnowledgeNode {project_id: $project_id, node_type: 'file'})
        WITH domain, matched_seeds, program_count, count(DISTINCT file) AS file_count
        OPTIONAL MATCH (domain)-[:RELATED {edge_type: 'CONTAINS_CLASS'}]->
                       (class_node:KnowledgeNode {project_id: $project_id, node_type: 'class'})
        RETURN matched_seeds,
               domain.label AS domain,
               program_count,
               file_count,
               count(DISTINCT class_node) AS class_count
        ORDER BY size(matched_seeds) DESC, class_count DESC, file_count DESC, domain
        LIMIT $limit
        """,
        project_id=int(project_id),
        seeds=seeds,
        limit=limit,
    )
    for row in domain_rows:
        evidence.append(
            {
                "evidence_type": "domain_summary",
                "title": "domain summary",
                "matched_seeds": list(row["matched_seeds"] or []),
                "domain": str(row["domain"] or "-"),
                "program_count": int(row["program_count"] or 0),
                "file_count": int(row["file_count"] or 0),
                "class_count": int(row["class_count"] or 0),
                "path": [str(row["domain"] or "-")],
            }
        )

    deduped: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for item in evidence:
        key = (
            item.get("evidence_type"),
            item.get("program"),
            item.get("commit_hash"),
            item.get("file_path"),
            item.get("class_name"),
            item.get("source_class"),
            item.get("target_class"),
            item.get("domain"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def get_neo4j_project_preview(project_id: int, limit: int = 100) -> Neo4jGraphPreview:
    if not settings.neo4j_enabled:
        return Neo4jGraphPreview("skipped", "Neo4j가 비활성화되어 graph preview를 읽지 않았습니다.")
    try:
        with _driver() as driver:
            with driver.session(**_session_kwargs()) as session:
                class_rows, impact_rows = session.execute_read(_read_project_preview_tx, project_id, limit)
    except Exception as exc:
        return Neo4jGraphPreview("failed", "Neo4j graph preview 조회 실패", errors=[str(exc)])
    return Neo4jGraphPreview(
        "completed",
        f"Neo4j graph preview 조회 완료: class 관계 {len(class_rows)}개, 영향 경로 {len(impact_rows)}개",
        class_import_rows=class_rows,
        impact_rows=impact_rows,
    )


def _read_project_preview_tx(tx, project_id: int, limit: int) -> tuple[list[dict[str, str]], list[ImpactPathRow]]:
    safe_limit = max(1, min(int(limit), 500))
    class_result = tx.run(
        """
        MATCH (source:KnowledgeNode {project_id: $project_id, node_type: 'class'})
              -[rel:RELATED {edge_type: 'IMPORTS_CLASS'}]->
              (target:KnowledgeNode {project_id: $project_id, node_type: 'class'})
        RETURN source.label AS source, target.label AS target
        ORDER BY source, target
        LIMIT $limit
        """,
        project_id=int(project_id),
        limit=safe_limit,
    )
    class_rows = [
        {"source": str(row["source"] or "-"), "target": str(row["target"] or "-")}
        for row in class_result
    ]

    impact_result = tx.run(
        """
        MATCH (program:KnowledgeNode {project_id: $project_id, node_type: 'program'})
              -[mapping:RELATED {edge_type: 'MAPPED_TO_COMMIT'}]->
              (commit_node:KnowledgeNode {project_id: $project_id, node_type: 'commit'})
        MATCH (commit_node)
              -[touch:RELATED {edge_type: 'TOUCHES_FILE'}]->
              (file:KnowledgeNode {project_id: $project_id, node_type: 'file'})
        MATCH (file)
              -[contains:RELATED {edge_type: 'CONTAINS_CLASS'}]->
              (class_node:KnowledgeNode {project_id: $project_id, node_type: 'class'})
        WITH program, commit_node, file, class_node, coalesce(commit_node.committed_at, '') AS committed_at
        RETURN coalesce(commit_node.commit_hash, commit_node.label) AS commit,
               program.label AS program,
               coalesce(file.file_path, file.label) AS file_path,
               class_node.label AS class_name,
               coalesce(class_node.domain, file.domain, '-') AS domain
        ORDER BY committed_at DESC, commit, program, file_path, class_name
        LIMIT $limit
        """,
        project_id=int(project_id),
        limit=safe_limit,
    )
    impact_rows = [
        ImpactPathRow(
            commit=_short_commit(str(row["commit"] or "-")),
            program=str(row["program"] or "-"),
            file_path=str(row["file_path"] or "-"),
            class_name=str(row["class_name"] or "-"),
            domain=str(row["domain"] or "-"),
        )
        for row in impact_result
    ]
    return class_rows, impact_rows

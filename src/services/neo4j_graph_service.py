from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, joinedload

from src.db.models import CommitFile, GitCommit, Program, ProgramCommitMapping, Project
from src.rag.chunker import _is_source_file, _read_text_file
from src.utils.config import settings
from src.utils.repo_path import resolve_repo_path

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover - exercised when dependency is not installed locally.
    GraphDatabase = None


PACKAGE_RE = re.compile(r"(?m)^\s*package\s+([A-Za-z_][\w.]*)\s*;")
IMPORT_RE = re.compile(r"(?m)^\s*import\s+(?:static\s+)?([A-Za-z_][\w.]*)(?:\.\*)?\s*;")
TYPE_RE = re.compile(r"\b(class|interface|enum|record)\s+([A-Z][A-Za-z0-9_]*)\b")


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
class Neo4jGraphPreview:
    status: str
    summary: str
    class_import_rows: list[dict[str, str]] = field(default_factory=list)
    impact_rows: list[ImpactPathRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _node_id(project_id: int, node_type: str, key: str | int) -> str:
    return f"p{project_id}:{node_type}:{str(key).strip()}"


def _edge_key(edge: GraphEdge) -> tuple[str, str, str]:
    return edge.from_node_id, edge.edge_type, edge.to_node_id


def _clean_key(value: str | None, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9가-힣_.:/-]+", "-", (value or "").strip())
    return cleaned.strip("-") or fallback


def _short_commit(commit_hash: str | None) -> str:
    return (commit_hash or "-")[:12]


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
        return Neo4jSyncResult("failed", "Neo4j 동기화 payload 생성 실패", errors=payload.errors)
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
        return Neo4jSyncResult(
            "failed",
            "Neo4j graph 동기화 실패",
            node_count=len(nodes),
            edge_count=len(edges),
            node_counts=dict(payload.node_counts),
            edge_counts=dict(payload.edge_counts),
            errors=[*payload.errors, str(exc)],
        )

    return Neo4jSyncResult(
        "completed",
        f"Neo4j에 node {len(nodes)}개, edge {len(edges)}개를 동기화했습니다.",
        node_count=len(nodes),
        edge_count=len(edges),
        node_counts=dict(payload.node_counts),
        edge_counts=dict(payload.edge_counts),
        errors=payload.errors,
    )


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

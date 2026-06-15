from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import CommitFile, GitCommit, Program, ProgramCommitMapping, Project, ProjectGraphSyncState
from src.services import neo4j_graph_service
from src.services.neo4j_graph_service import (
    _changed_source_clear_paths,
    build_graph_evidence_seeds,
    build_project_graph_payload,
    explore_neo4j_project_graph,
    extract_java_symbols,
    find_project_graph_evidence,
    get_neo4j_graph_explore_options,
    get_neo4j_project_preview,
    get_project_graph_freshness,
    sync_project_graph_incrementally_to_neo4j,
    sync_project_graph_to_neo4j,
)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def test_extract_java_symbols_detects_package_class_domain_and_imports() -> None:
    text = """
        package com.example.market.payment.service;

        import com.example.market.order.mapper.OrderMapper;
        import org.springframework.stereotype.Service;

        public class PaymentService {
        }
    """

    symbols = extract_java_symbols("src/main/java/com/example/market/payment/service/PaymentService.java", text)

    assert len(symbols) == 1
    symbol = symbols[0]
    assert symbol.qualified_name == "com.example.market.payment.service.PaymentService"
    assert symbol.domain == "payment"
    assert "com.example.market.order.mapper.OrderMapper" in symbol.imports


def test_build_graph_evidence_seeds_uses_question_expansion_and_source_symbols() -> None:
    seeds = build_graph_evidence_seeds(
        "결제 변경이 주문 쪽에 영향을 줄 수 있는 근거가 뭐야?",
        [
            {
                "source_type": "source_file",
                "source_id": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "text": """
                    package com.example.market.payment.service;
                    import com.example.market.order.mapper.OrderMapper;
                    public class PaymentService {}
                """,
                "metadata": {
                    "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                },
            }
        ],
        expanded_queries=["payment service order mapper"],
    )

    assert "결제" in seeds
    assert "paymentservice" in seeds
    assert "payment" in seeds
    assert "ordermapper" in seeds


def test_build_project_graph_payload_links_program_commit_file_class_and_domain(tmp_path) -> None:
    init_db()
    repo = tmp_path / "repo"
    payment_dir = repo / "src" / "main" / "java" / "com" / "example" / "market" / "payment" / "service"
    order_dir = repo / "src" / "main" / "java" / "com" / "example" / "market" / "order" / "mapper"
    payment_dir.mkdir(parents=True)
    order_dir.mkdir(parents=True)
    payment_file = payment_dir / "PaymentService.java"
    payment_file.write_text(
        """
        package com.example.market.payment.service;

        import com.example.market.order.mapper.OrderMapper;

        public class PaymentService {
        }
        """,
        encoding="utf-8",
    )
    order_file = order_dir / "OrderMapper.java"
    order_file.write_text(
        """
        package com.example.market.order.mapper;

        public interface OrderMapper {
        }
        """,
        encoding="utf-8",
    )

    with SessionLocal() as db:
        project = Project(name=_unique("graph-project"), git_repo_path=str(repo))
        db.add(project)
        db.flush()
        program = Program(
            project_id=project.id,
            program_id=_unique("PAY"),
            program_name="Payment Program",
            module="payment",
        )
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="Update payment service",
        )
        db.add_all([program, commit])
        db.flush()
        db.add_all(
            [
                CommitFile(
                    commit_id=commit.id,
                    git_commit_id=commit.id,
                    file_path="src/main/java/com/example/market/payment/service/PaymentService.java",
                    change_type="Modified",
                    diff_text="+ payment",
                ),
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=commit.id,
                    relevance_score=95,
                    is_related=True,
                    implementation_status="일부구현",
                    reason="payment service change",
                ),
            ]
        )
        db.commit()

        try:
            payload = build_project_graph_payload(db, project.id)

            assert payload.node_counts["project"] == 1
            assert payload.node_counts["program"] == 1
            assert payload.node_counts["commit"] == 1
            assert payload.node_counts["class"] == 2
            assert payload.edge_counts["MAPPED_TO_COMMIT"] == 1
            assert payload.edge_counts["CONTAINS_CLASS"] >= 2
            assert payload.edge_counts["IMPORTS_CLASS"] == 1
            assert any(row.domain == "payment" for row in payload.domain_rows)
            assert any(row.class_name.endswith("PaymentService") for row in payload.impact_rows)
        finally:
            remaining = db.get(Project, project.id)
            if remaining is not None:
                db.delete(remaining)
            db.commit()


def test_sync_project_graph_prepares_schema_outside_write_transaction(monkeypatch, tmp_path) -> None:
    init_db()
    repo = tmp_path / "repo"
    repo.mkdir()
    calls: list[str] = []

    class FakeResult:
        def consume(self):
            calls.append("schema_consumed")

        def single(self):
            return {"deleted_count": 0}

    class FakeTx:
        def run(self, query, **params):
            normalized = " ".join(query.split())
            if normalized.startswith("MATCH (n:KnowledgeNode"):
                calls.append("clear_project_graph")
            elif normalized.startswith("UNWIND $nodes"):
                calls.append("write_nodes")
            elif normalized.startswith("UNWIND $edges"):
                calls.append("write_edges")
            return FakeResult()

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def run(self, query):
            assert "CREATE CONSTRAINT" in query
            calls.append("ensure_schema")
            return FakeResult()

        def execute_write(self, fn, *args):
            calls.append("execute_write")
            return fn(FakeTx(), *args)

    class FakeDriver:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def session(self, **kwargs):
            return FakeSession()

    monkeypatch.setattr(neo4j_graph_service.settings, "neo4j_enabled", True)
    monkeypatch.setattr(neo4j_graph_service, "_driver", lambda: FakeDriver())
    monkeypatch.setattr(neo4j_graph_service, "get_head_commit_hash", lambda repo_path: "head123")

    with SessionLocal() as db:
        project = Project(name=_unique("graph-sync-project"), git_repo_path=str(repo), last_synced_commit_hash="head123")
        db.add(project)
        db.flush()
        program = Program(project_id=project.id, program_id=_unique("PAY"), program_name="Payment Program")
        commit = GitCommit(project_id=project.id, commit_hash=uuid.uuid4().hex, message="Update payment")
        db.add_all([program, commit])
        db.flush()
        db.add(ProgramCommitMapping(program_id=program.id, commit_id=commit.id, relevance_score=80, is_related=True))
        db.commit()

        try:
            result = sync_project_graph_to_neo4j(db, project.id)

            assert result.status == "completed"
            assert calls[:3] == ["ensure_schema", "schema_consumed", "execute_write"]
            assert "clear_project_graph" in calls
            assert "write_nodes" in calls
            assert "write_edges" in calls
            state = db.query(ProjectGraphSyncState).filter(ProjectGraphSyncState.project_id == project.id).one()
            assert state.status == "completed"
            assert state.sync_mode == "full"
            assert state.repo_head_hash == "head123"
            assert state.db_sync_head_hash == "head123"
            assert state.last_commit_db_id == commit.id
        finally:
            remaining = db.get(Project, project.id)
            if remaining is not None:
                db.delete(remaining)
            db.commit()


def test_get_project_graph_freshness_detects_repo_head_stale(monkeypatch, tmp_path) -> None:
    init_db()
    repo = tmp_path / "repo"
    repo.mkdir()
    synced_at = datetime(2026, 6, 15, tzinfo=timezone.utc)

    monkeypatch.setattr(neo4j_graph_service.settings, "neo4j_enabled", True)
    monkeypatch.setattr(neo4j_graph_service, "get_head_commit_hash", lambda repo_path: "new-head")

    with SessionLocal() as db:
        project = Project(
            name=_unique("graph-freshness-project"),
            git_repo_path=str(repo),
            last_synced_commit_hash="old-head",
        )
        db.add(project)
        db.flush()
        db.add(
            ProjectGraphSyncState(
                project_id=project.id,
                repo_head_hash="old-head",
                db_sync_head_hash="old-head",
                synced_at=synced_at,
                sync_mode="full",
                status="completed",
                node_count=10,
                edge_count=20,
                last_commit_db_id=1,
            )
        )
        db.commit()

        try:
            freshness = get_project_graph_freshness(db, project.id)

            assert freshness.status == "stale"
            assert freshness.repo_head_hash == "new-head"
            assert freshness.graph_sync_head_hash == "old-head"
            assert "Repo HEAD" in freshness.summary
        finally:
            remaining = db.get(Project, project.id)
            if remaining is not None:
                db.delete(remaining)
            db.commit()


def test_changed_source_clear_paths_handles_deleted_renamed_and_non_source() -> None:
    paths = _changed_source_clear_paths(
        [
            CommitFile(file_path="src/main/java/NewService.java", change_type="Renamed", diff_text="rename from src/main/java/OldService.java\nrename to src/main/java/NewService.java"),
            CommitFile(file_path="src/main/java/DeletedService.java", change_type="Deleted"),
            CommitFile(file_path="README.md", change_type="Modified"),
        ]
    )

    assert paths == [
        "src/main/java/DeletedService.java",
        "src/main/java/NewService.java",
        "src/main/java/OldService.java",
    ]


def test_incremental_sync_refreshes_changed_source_and_mapping_edges(monkeypatch, tmp_path) -> None:
    init_db()
    repo = tmp_path / "repo"
    service_dir = repo / "src" / "main" / "java" / "com" / "example" / "market" / "payment" / "service"
    service_dir.mkdir(parents=True)
    service_file = service_dir / "PaymentService.java"
    service_file.write_text(
        """
        package com.example.market.payment.service;

        import com.example.market.order.mapper.OrderMapper;

        public class PaymentService {
        }
        """,
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    class FakeResult:
        def __init__(self, rows=None, single_row=None):
            self.rows = rows or []
            self.single_row = single_row

        def consume(self):
            return None

        def single(self):
            if self.single_row is not None:
                return self.single_row
            return self.rows[0] if self.rows else None

        def __iter__(self):
            return iter(self.rows)

    class FakeTx:
        def run(self, query, **params):
            normalized = " ".join(query.split())
            if "deleted_class_count" in normalized:
                captured["clear_source_paths"] = params["file_paths"]
                return FakeResult(single_row={"deleted_class_count": 1})
            if "deleted_mapping_count" in normalized:
                captured["mapping_refresh"] = True
                return FakeResult(single_row={"deleted_mapping_count": 1})
            if normalized.startswith("UNWIND $nodes"):
                captured["nodes"] = params["nodes"]
                return FakeResult()
            if normalized.startswith("UNWIND $edges"):
                captured["edges"] = params["edges"]
                return FakeResult()
            if "RETURN n.node_type AS node_type" in normalized:
                return FakeResult(rows=[{"node_type": "project", "count": 1}, {"node_type": "class", "count": 1}])
            if "RETURN rel.edge_type AS edge_type" in normalized:
                return FakeResult(rows=[{"edge_type": "TOUCHES_FILE", "count": 1}, {"edge_type": "CONTAINS_CLASS", "count": 2}])
            return FakeResult()

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def run(self, query):
            assert "CREATE CONSTRAINT" in query
            return FakeResult()

        def execute_write(self, fn, *args):
            return fn(FakeTx(), *args)

        def execute_read(self, fn, *args):
            return fn(FakeTx(), *args)

    class FakeDriver:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def session(self, **kwargs):
            return FakeSession()

    monkeypatch.setattr(neo4j_graph_service.settings, "neo4j_enabled", True)
    monkeypatch.setattr(neo4j_graph_service, "_driver", lambda: FakeDriver())
    monkeypatch.setattr(neo4j_graph_service, "get_head_commit_hash", lambda repo_path: "head456")

    with SessionLocal() as db:
        project = Project(name=_unique("graph-incremental-project"), git_repo_path=str(repo), last_synced_commit_hash="head456")
        db.add(project)
        db.flush()
        program = Program(project_id=project.id, program_id=_unique("PAY"), program_name="Payment Program", module="payment")
        old_commit = GitCommit(project_id=project.id, commit_hash=uuid.uuid4().hex, message="Previous payment")
        db.add_all([program, old_commit])
        db.flush()
        new_commit = GitCommit(project_id=project.id, commit_hash=uuid.uuid4().hex, message="Update payment service")
        db.add(new_commit)
        db.flush()
        db.add_all(
            [
                CommitFile(
                    commit_id=new_commit.id,
                    git_commit_id=new_commit.id,
                    file_path="src/main/java/com/example/market/payment/service/PaymentService.java",
                    change_type="Modified",
                    diff_text="+ import order mapper",
                ),
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=old_commit.id,
                    relevance_score=90,
                    is_related=False,
                    updated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
                ),
                ProjectGraphSyncState(
                    project_id=project.id,
                    repo_head_hash="old-head",
                    db_sync_head_hash="old-head",
                    synced_at=datetime(2026, 6, 15, tzinfo=timezone.utc) - timedelta(hours=1),
                    sync_mode="full",
                    status="completed",
                    node_count=8,
                    edge_count=12,
                    last_commit_db_id=old_commit.id,
                    last_mapping_updated_at=datetime(2026, 6, 15, tzinfo=timezone.utc) - timedelta(hours=1),
                ),
            ]
        )
        db.commit()

        try:
            result = sync_project_graph_incrementally_to_neo4j(db, project.id)

            assert result.status == "completed"
            assert captured["clear_source_paths"] == [
                "src/main/java/com/example/market/payment/service/PaymentService.java"
            ]
            edges = captured["edges"]
            edge_types = {edge["edge_type"] for edge in edges}
            assert "TOUCHES_FILE" in edge_types
            assert "CONTAINS_CLASS" in edge_types
            assert "IMPORTS_CLASS" in edge_types
            assert "MAPPED_TO_COMMIT" not in edge_types
            assert captured["mapping_refresh"] is True

            state = db.query(ProjectGraphSyncState).filter(ProjectGraphSyncState.project_id == project.id).one()
            assert state.status == "completed"
            assert state.sync_mode == "incremental"
            assert state.repo_head_hash == "head456"
            assert state.db_sync_head_hash == "head456"
            assert state.last_commit_db_id == new_commit.id
            assert state.raw_metadata["deleted_class_count"] == 1
        finally:
            remaining = db.get(Project, project.id)
            if remaining is not None:
                db.delete(remaining)
            db.commit()


def test_get_neo4j_project_preview_reads_saved_class_and_impact_paths(monkeypatch) -> None:
    class FakeTx:
        def run(self, query, **params):
            if "IMPORTS_CLASS" in query:
                return [
                    {
                        "source": "com.example.market.payment.service.PaymentService",
                        "target": "com.example.market.order.mapper.OrderMapper",
                    }
                ]
            if "MAPPED_TO_COMMIT" in query:
                return [
                    {
                        "commit": "abcdef1234567890",
                        "program": "PAY Payment Program",
                        "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                        "class_name": "com.example.market.payment.service.PaymentService",
                        "domain": "payment",
                    }
                ]
            return []

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute_read(self, fn, *args):
            return fn(FakeTx(), *args)

    class FakeDriver:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def session(self, **kwargs):
            return FakeSession()

    monkeypatch.setattr(neo4j_graph_service.settings, "neo4j_enabled", True)
    monkeypatch.setattr(neo4j_graph_service, "_driver", lambda: FakeDriver())

    result = get_neo4j_project_preview(123)

    assert result.status == "completed"
    assert result.class_import_rows == [
        {
            "source": "com.example.market.payment.service.PaymentService",
            "target": "com.example.market.order.mapper.OrderMapper",
        }
    ]
    assert len(result.impact_rows) == 1
    assert result.impact_rows[0].commit == "abcdef123456"
    assert result.impact_rows[0].class_name.endswith("PaymentService")


def test_get_neo4j_graph_explore_options_groups_focus_nodes(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeTx:
        def run(self, query, **params):
            captured["query"] = " ".join(query.split())
            captured["params"] = params
            return [
                {
                    "node_type": "program",
                    "node_id": "p123:program:PAY-001",
                    "label": "PAY-001 Payment Program",
                    "key": "PAY-001",
                    "description": "Payment Program",
                },
                {
                    "node_type": "program",
                    "node_id": "p123:program:PAY-002",
                    "label": "PAY-002 Payment Batch",
                    "key": "PAY-002",
                    "description": "Payment Batch",
                },
                {
                    "node_type": "class",
                    "node_id": "p123:class:PaymentService",
                    "label": "com.example.market.payment.service.PaymentService",
                    "key": "com.example.market.payment.service.PaymentService",
                    "description": "PaymentService",
                },
                {
                    "node_type": "domain",
                    "node_id": "p123:domain:payment",
                    "label": "payment",
                    "key": "payment",
                    "description": "payment",
                },
                {
                    "node_type": "commit",
                    "node_id": "p123:commit:abcdef",
                    "label": "abcdef123456",
                    "key": "abcdef1234567890",
                    "description": "Update payment service",
                },
            ]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute_read(self, fn, *args):
            return fn(FakeTx(), *args)

    class FakeDriver:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def session(self, **kwargs):
            return FakeSession()

    monkeypatch.setattr(neo4j_graph_service.settings, "neo4j_enabled", True)
    monkeypatch.setattr(neo4j_graph_service, "_driver", lambda: FakeDriver())

    result = get_neo4j_graph_explore_options(123, limit_per_type=1)

    assert result.status == "completed"
    assert "MATCH (n:KnowledgeNode" in captured["query"]
    assert captured["params"] == {"project_id": 123, "limit": 4}
    assert [row.key for row in result.options_by_type["program"]] == ["PAY-001"]
    assert result.options_by_type["class"][0].label.endswith("PaymentService")
    assert result.options_by_type["domain"][0].key == "payment"
    assert result.options_by_type["commit"][0].description == "Update payment service"


def test_explore_neo4j_project_graph_reads_node_detail_and_paths(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResult:
        def __init__(self, rows=None, single_row=None):
            self.rows = rows or []
            self.single_row = single_row

        def single(self):
            return self.single_row

        def __iter__(self):
            return iter(self.rows)

    class FakeTx:
        def run(self, query, **params):
            normalized = " ".join(query.split())
            if "properties(focus)" in normalized:
                return FakeResult(
                    single_row={
                        "node_id": "p123:program:PAY-001",
                        "node_type": "program",
                        "label": "PAY-001 Payment Program",
                        "related_count": 3,
                        "properties": {"program_id": "PAY-001", "program_name": "Payment Program"},
                    }
                )

            captured["path_query"] = normalized
            captured["path_params"] = params
            return FakeResult(
                rows=[
                    {
                        "node_labels": [
                            "PAY-001 Payment Program",
                            "abcdef123456",
                            "src/main/java/com/example/market/payment/service/PaymentService.java",
                        ],
                        "node_types": ["program", "commit", "file"],
                        "edge_types": ["MAPPED_TO_COMMIT", "TOUCHES_FILE"],
                        "target_node_id": "p123:file:PaymentService.java",
                        "target_type": "file",
                        "target_label": "PaymentService.java",
                        "depth": 2,
                    }
                ]
            )

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute_read(self, fn, *args):
            return fn(FakeTx(), *args)

    class FakeDriver:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def session(self, **kwargs):
            return FakeSession()

    monkeypatch.setattr(neo4j_graph_service.settings, "neo4j_enabled", True)
    monkeypatch.setattr(neo4j_graph_service, "_driver", lambda: FakeDriver())

    result = explore_neo4j_project_graph(
        123,
        "p123:program:PAY-001",
        relationship_types=["TOUCHES_FILE", "MAPPED_TO_COMMIT", "TOUCHES_FILE"],
        depth=5,
        limit=500,
    )

    assert result.status == "completed"
    assert result.node_detail is not None
    assert result.node_detail.related_count == 3
    assert result.node_detail.properties["program_name"] == "Payment Program"
    assert "*1..3" in captured["path_query"]
    assert captured["path_params"]["relationship_types"] == ["MAPPED_TO_COMMIT", "TOUCHES_FILE"]
    assert captured["path_params"]["limit"] == 300
    assert result.rows[0].target_label == "PaymentService.java"
    assert result.rows[0].path == (
        "program:PAY-001 Payment Program -> [MAPPED_TO_COMMIT] -> "
        "commit:abcdef123456 -> [TOUCHES_FILE] -> "
        "file:src/main/java/com/example/market/payment/service/PaymentService.java"
    )


def test_find_project_graph_evidence_reads_impact_import_and_domain_paths(monkeypatch) -> None:
    class FakeTx:
        def run(self, query, **params):
            if "MAPPED_TO_COMMIT" in query:
                return [
                    {
                        "matched_seeds": ["paymentservice", "payment"],
                        "program": "PAY Payment Program",
                        "program_id": "PAY-001",
                        "commit_hash": "abcdef1234567890",
                        "commit_message": "Update payment service",
                        "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                        "class_name": "com.example.market.payment.service.PaymentService",
                        "domain": "payment",
                        "committed_at": "2026-06-15T00:00:00",
                    }
                ]
            if "IMPORTS_CLASS" in query:
                return [
                    {
                        "matched_seeds": ["paymentservice", "ordermapper"],
                        "source_class": "com.example.market.payment.service.PaymentService",
                        "target_class": "com.example.market.order.mapper.OrderMapper",
                        "source_file": "src/main/java/com/example/market/payment/service/PaymentService.java",
                        "target_file": "src/main/java/com/example/market/order/mapper/OrderMapper.java",
                        "source_domain": "payment",
                        "target_domain": "order",
                    }
                ]
            if "OWNS_PROGRAM" in query:
                return [
                    {
                        "matched_seeds": ["payment"],
                        "domain": "payment",
                        "program_count": 1,
                        "file_count": 2,
                        "class_count": 2,
                    }
                ]
            return []

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute_read(self, fn, *args):
            return fn(FakeTx(), *args)

    class FakeDriver:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def session(self, **kwargs):
            return FakeSession()

    monkeypatch.setattr(neo4j_graph_service.settings, "neo4j_enabled", True)
    monkeypatch.setattr(neo4j_graph_service, "_driver", lambda: FakeDriver())

    result = find_project_graph_evidence(
        123,
        "결제 변경이 주문 쪽에 영향을 줄 수 있는 근거가 뭐야?",
        [
            {
                "source_type": "source_file",
                "source_id": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "text": "package com.example.market.payment.service; public class PaymentService {}",
                "metadata": {
                    "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                },
            }
        ],
        expanded_queries=["payment service order mapper"],
    )

    assert result.status == "completed"
    assert [row["evidence_type"] for row in result.evidence] == [
        "impact_path",
        "class_import",
        "domain_summary",
    ]
    assert result.evidence[0]["commit"] == "abcdef123456"
    assert result.evidence[1]["target_class"].endswith("OrderMapper")

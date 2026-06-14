from __future__ import annotations

import uuid

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import CommitFile, GitCommit, Program, ProgramCommitMapping, Project
from src.services import neo4j_graph_service
from src.services.neo4j_graph_service import (
    build_graph_evidence_seeds,
    build_project_graph_payload,
    extract_java_symbols,
    find_project_graph_evidence,
    get_neo4j_project_preview,
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

    with SessionLocal() as db:
        project = Project(name=_unique("graph-sync-project"), git_repo_path=str(repo))
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

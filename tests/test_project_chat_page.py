from dataclasses import replace
from datetime import datetime, timezone

from src.db.models import Project
from src.rag.source_index_service import SourceIndexStatus, SourceIndexSummary
from src.services.neo4j_graph_service import Neo4jGraphFreshness
from src.ui import project_chat_page
from src.ui.project_chat_page import (
    GRAPH_AWARE_QUESTION_TEMPLATES,
    _cache_source_verification,
    _get_cached_source_verification,
    _graph_template_status,
    _load_initial_source_summary,
    _run_source_file_verification,
    build_source_verification_cache_key,
    build_graph_evidence_display,
)


def _summary(**overrides) -> SourceIndexSummary:
    values = {
        "repo_path": "C:/repo",
        "current_head_hash": "head-a",
        "latest_indexed_head_hash": "head-a",
        "indexed_head_hashes": ["head-a"],
        "source_chunk_count": 3,
        "source_vector_count": 3,
        "missing_embedding_count": 0,
        "head_mismatch_chunk_count": 0,
        "needs_refresh": False,
        "head_matches_index": True,
        "last_indexed_at": datetime(2026, 7, 21, tzinfo=timezone.utc),
        "checked_at": datetime(2026, 7, 21, tzinfo=timezone.utc),
        "index_signature": "3:9:2026-07-21T00:00:00+00:00",
        "errors": [],
    }
    values.update(overrides)
    return SourceIndexSummary(**values)


def _verified_status() -> SourceIndexStatus:
    return SourceIndexStatus(
        repo_path="C:/repo",
        current_head_hash="head-a",
        latest_indexed_head_hash="head-a",
        indexed_head_hashes=["head-a"],
        source_chunk_count=3,
        source_vector_count=3,
        missing_embedding_count=0,
        head_mismatch_chunk_count=0,
        stale_chunk_count=0,
        invalid_chunk_count=0,
        needs_reindex=False,
        errors=[],
    )


def test_initial_project_chat_status_uses_summary_without_expensive_file_verification(monkeypatch) -> None:
    expected = _summary()
    monkeypatch.setattr(project_chat_page, "get_source_index_summary", lambda db, project: expected)
    monkeypatch.setattr(
        project_chat_page,
        "get_source_index_status",
        lambda db, project: (_ for _ in ()).throw(AssertionError("full source verification must not run")),
    )

    assert _load_initial_source_summary(object(), Project(id=1, name="project")) is expected


def test_explicit_project_chat_status_refresh_runs_file_verification(monkeypatch) -> None:
    expected = _verified_status()
    calls = []
    monkeypatch.setattr(
        project_chat_page,
        "get_source_index_status",
        lambda db, project: calls.append((db, project.id)) or expected,
    )

    db = object()
    assert _run_source_file_verification(db, Project(id=1, name="project")) is expected
    assert calls == [(db, 1)]


def test_source_verification_cache_isolated_by_project_head_model_and_index_signature() -> None:
    project = Project(id=1, name="project", last_synced_commit_hash="sync-a")
    summary = _summary()
    base_key = build_source_verification_cache_key(
        project,
        summary,
        embedding_provider="local_openai",
        embedding_model="model-a",
        embedding_dimension=768,
    )
    state = {}
    cached = _cache_source_verification(base_key, _verified_status(), state)

    assert _get_cached_source_verification(base_key, state) is cached
    assert _get_cached_source_verification(
        build_source_verification_cache_key(
            Project(id=2, name="other", last_synced_commit_hash="sync-a"),
            summary,
            embedding_provider="local_openai",
            embedding_model="model-a",
            embedding_dimension=768,
        ),
        state,
    ) is None
    assert _get_cached_source_verification(
        build_source_verification_cache_key(
            project,
            replace(summary, current_head_hash="head-b"),
            embedding_provider="local_openai",
            embedding_model="model-a",
            embedding_dimension=768,
        ),
        state,
    ) is None
    assert _get_cached_source_verification(
        build_source_verification_cache_key(
            project,
            summary,
            embedding_provider="local_openai",
            embedding_model="model-b",
            embedding_dimension=768,
        ),
        state,
    ) is None
    assert _get_cached_source_verification(
        build_source_verification_cache_key(
            project,
            replace(summary, index_signature="4:10:2026-07-21T01:00:00+00:00"),
            embedding_provider="local_openai",
            embedding_model="model-a",
            embedding_dimension=768,
        ),
        state,
    ) is None


def test_graph_question_templates_cover_project_commit_class_domain_relationships() -> None:
    questions = " ".join(template["question"] for template in GRAPH_AWARE_QUESTION_TEMPLATES)

    assert len(GRAPH_AWARE_QUESTION_TEMPLATES) >= 5
    assert "프로그램" in questions
    assert "commit" in questions
    assert "file" in questions
    assert "class" in questions
    assert "domain" in questions


def test_graph_template_status_enables_only_latest_graph() -> None:
    enabled, message = _graph_template_status(Neo4jGraphFreshness("latest", "최신"))

    assert enabled is True
    assert "graph 관계 근거" in message


def test_graph_template_status_blocks_missing_or_stale_graph() -> None:
    missing_enabled, missing_message = _graph_template_status(Neo4jGraphFreshness("missing", "저장 필요"))
    stale_enabled, stale_message = _graph_template_status(Neo4jGraphFreshness("stale", "갱신 필요"))

    assert missing_enabled is False
    assert "전체 재동기화" in missing_message
    assert stale_enabled is False
    assert "최신 변경분 반영" in stale_message


def test_build_graph_evidence_display_renders_class_import_relationships() -> None:
    nodes, edges = build_graph_evidence_display(
        [
            {
                "evidence_type": "class_import",
                "source_class": "com.example.market.payment.service.PaymentService",
                "target_class": "com.example.market.order.mapper.OrderMapper",
                "matched_seeds": ["paymentservice"],
            }
        ]
    )

    assert {node.label for node in nodes} == {"PaymentService", "OrderMapper"}
    assert any(node.label == "PaymentService" and node.highlighted for node in nodes)
    assert [(edge.label, edge.source, edge.target) for edge in edges] == [
        (
            "IMPORTS_CLASS",
            "class:com.example.market.payment.service.PaymentService",
            "class:com.example.market.order.mapper.OrderMapper",
        )
    ]


def test_build_graph_evidence_display_renders_impact_path_context() -> None:
    nodes, edges = build_graph_evidence_display(
        [
            {
                "evidence_type": "impact_path",
                "program": "Payment Checkout",
                "commit": "abcdef123456",
                "commit_hash": "abcdef1234567890",
                "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "class_name": "com.example.market.payment.service.PaymentService",
                "matched_seeds": ["paymentcheckout"],
            }
        ]
    )

    assert {node.label for node in nodes} == {"Payment Checkout", "abcdef123456", "PaymentService"}
    assert any(node.label == "Payment Checkout" and node.highlighted for node in nodes)
    assert any(
        node.label == "PaymentService"
        and "PaymentService.java" in node.title
        and "com.example.market.payment.service.PaymentService" in node.title
        for node in nodes
    )
    assert [(edge.label, edge.source, edge.target) for edge in edges] == [
        ("MAPPED_COMMIT", "program:Payment Checkout", "commit:abcdef123456"),
        (
            "TOUCHES_FILE",
            "commit:abcdef123456",
            "class:com.example.market.payment.service.PaymentService",
        ),
    ]


def test_build_graph_evidence_display_keeps_domain_summary_out_of_default_graph() -> None:
    nodes, edges = build_graph_evidence_display(
        [
            {
                "evidence_type": "domain_summary",
                "domain": "Order",
                "program": "Order status",
                "class_name": "com.example.market.order.service.OrderStatusService",
                "matched_seeds": ["order", "status"],
            }
        ]
    )

    assert nodes == []
    assert edges == []


def test_build_graph_evidence_display_deduplicates_and_limits_graph() -> None:
    evidence = [
        {
            "evidence_type": "class_import",
            "source_class": f"com.example.Source{i}",
            "target_class": f"com.example.Target{i}",
            "matched_seeds": [],
        }
        for i in range(10)
    ]

    nodes, edges = build_graph_evidence_display(evidence, max_nodes=4, max_edges=3)

    assert len(nodes) == 4
    assert len(edges) == 3

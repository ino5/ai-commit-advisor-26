from src.services.neo4j_graph_service import Neo4jGraphFreshness
from src.ui.project_chat_page import (
    GRAPH_AWARE_QUESTION_TEMPLATES,
    _graph_template_status,
    build_graph_evidence_display,
)


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


def test_build_graph_evidence_display_keeps_impact_path_out_of_default_graph() -> None:
    nodes, edges = build_graph_evidence_display(
        [
            {
                "evidence_type": "impact_path",
                "program": "Payment Checkout",
                "commit_hash": "abcdef1234567890",
                "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "class_name": "com.example.market.payment.service.PaymentService",
                "matched_seeds": ["payment"],
            }
        ]
    )

    assert nodes == []
    assert edges == []


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

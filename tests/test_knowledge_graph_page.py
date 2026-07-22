from src.services.neo4j_graph_service import (
    GraphNodeDetail,
    GraphPathEdge,
    GraphPathNode,
    GraphPathRow,
    Neo4jGraphExploreResult,
)
from src.ui.knowledge_graph_page import build_graph_exploration_display


def _row(
    *,
    target_node_id: str,
    nodes: list[GraphPathNode],
    edges: list[GraphPathEdge],
) -> GraphPathRow:
    return GraphPathRow(
        depth=len(edges),
        path="path",
        edge_types=[edge.edge_type for edge in edges],
        target_node_id=target_node_id,
        target_type=nodes[-1].node_type,
        target_label=nodes[-1].label,
        nodes=nodes,
        edges=edges,
    )


def _result(rows: list[GraphPathRow]) -> Neo4jGraphExploreResult:
    return Neo4jGraphExploreResult(
        status="completed",
        summary="조회 완료",
        node_detail=GraphNodeDetail(
            node_id="p1:program:PAY-001",
            node_type="program",
            label="PAY-001 Payment Program",
            related_count=3,
            properties={"program_id": "PAY-001"},
        ),
        rows=rows,
    )


def test_build_graph_exploration_display_deduplicates_and_keeps_stored_direction() -> None:
    focus = GraphPathNode("p1:program:PAY-001", "program", "PAY-001 Payment Program")
    commit = GraphPathNode("p1:commit:abc", "commit", "abcdef123456")
    file_node = GraphPathNode(
        "p1:file:PaymentService.java",
        "file",
        "src/main/java/com/example/market/payment/service/PaymentService.java",
    )
    class_node = GraphPathNode(
        "p1:class:PaymentService",
        "class",
        "com.example.market.payment.service.PaymentService",
    )
    mapping_edge = GraphPathEdge(focus.node_id, commit.node_id, "MAPPED_TO_COMMIT")
    result = _result(
        [
            _row(
                target_node_id=file_node.node_id,
                nodes=[focus, commit, file_node],
                edges=[mapping_edge, GraphPathEdge(commit.node_id, file_node.node_id, "TOUCHES_FILE")],
            ),
            _row(
                target_node_id=class_node.node_id,
                nodes=[focus, commit, file_node, class_node],
                edges=[
                    mapping_edge,
                    GraphPathEdge(commit.node_id, file_node.node_id, "TOUCHES_FILE"),
                    GraphPathEdge(file_node.node_id, class_node.node_id, "CONTAINS_CLASS"),
                ],
            ),
        ]
    )

    nodes, edges, truncated = build_graph_exploration_display(result)

    assert truncated is False
    assert {node.id for node in nodes} == {focus.node_id, commit.node_id, file_node.node_id, class_node.node_id}
    assert [node.id for node in nodes if node.highlighted] == [focus.node_id]
    assert next(node for node in nodes if node.id == file_node.node_id).label == "PaymentService.java"
    assert {
        (edge.source, edge.target, edge.label)
        for edge in edges
    } == {
        (focus.node_id, commit.node_id, "MAPPED_TO_COMMIT"),
        (commit.node_id, file_node.node_id, "TOUCHES_FILE"),
        (file_node.node_id, class_node.node_id, "CONTAINS_CLASS"),
    }


def test_build_graph_exploration_display_limits_whole_paths_without_breaking_edges() -> None:
    focus = GraphPathNode("p1:program:PAY-001", "program", "PAY-001 Payment Program")
    commit = GraphPathNode("p1:commit:abc", "commit", "abcdef123456")
    file_node = GraphPathNode("p1:file:PaymentService.java", "file", "PaymentService.java")
    result = _result(
        [
            _row(
                target_node_id=commit.node_id,
                nodes=[focus, commit],
                edges=[GraphPathEdge(focus.node_id, commit.node_id, "MAPPED_TO_COMMIT")],
            ),
            _row(
                target_node_id=file_node.node_id,
                nodes=[focus, commit, file_node],
                edges=[
                    GraphPathEdge(focus.node_id, commit.node_id, "MAPPED_TO_COMMIT"),
                    GraphPathEdge(commit.node_id, file_node.node_id, "TOUCHES_FILE"),
                ],
            ),
        ]
    )

    nodes, edges, truncated = build_graph_exploration_display(result, max_nodes=2, max_edges=1)

    assert truncated is True
    assert [node.id for node in nodes] == [focus.node_id, commit.node_id]
    assert [(edge.source, edge.target) for edge in edges] == [(focus.node_id, commit.node_id)]

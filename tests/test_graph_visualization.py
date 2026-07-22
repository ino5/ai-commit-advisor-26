from src.ui import graph_visualization
from src.ui.graph_visualization import GraphDisplayEdge, GraphDisplayNode, render_node_edge_graph, short_graph_label


def test_short_graph_label_compacts_file_and_qualified_class_names() -> None:
    assert short_graph_label("src/main/java/com/example/PaymentService.java") == "PaymentService.java"
    assert short_graph_label("com.example.market.payment.PaymentService") == "PaymentService"


def test_render_node_edge_graph_shows_relationship_labels_when_requested(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_agraph(*, nodes, edges, config):
        captured["nodes"] = nodes
        captured["edges"] = edges
        captured["config"] = config
        return "selected"

    monkeypatch.setattr(graph_visualization, "agraph", fake_agraph)

    selected = render_node_edge_graph(
        [
            GraphDisplayNode("program:1", "Payment", "program", "program", highlighted=True),
            GraphDisplayNode("commit:1", "abcdef123456", "commit", "commit"),
        ],
        [GraphDisplayEdge("program:1", "commit:1", "MAPPED_TO_COMMIT")],
        show_edge_labels=True,
        use_component_variants=False,
        physics=False,
        hierarchical=True,
    )

    assert selected == "selected"
    assert captured["nodes"][0].borderWidth == 3
    assert captured["edges"][0].label == "MAPPED_TO_COMMIT"
    assert captured["edges"][0].source == "program:1"
    assert captured["edges"][0].to == "commit:1"
    assert captured["config"].physics["enabled"] is False
    assert captured["config"].layout["hierarchical"]["enabled"] is True

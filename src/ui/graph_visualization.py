from __future__ import annotations

from dataclasses import dataclass

from streamlit_agraph import Config, Edge, Node, agraph


GRAPH_NODE_STYLE = {
    "project": {
        "color": "#F1F5F9",
        "highlight": "#E2E8F0",
        "border": "#64748B",
        "shape": "star",
        "size": 30,
    },
    "program": {
        "color": "#DCEBFF",
        "highlight": "#C8DDFF",
        "border": "#6EA1E8",
        "shape": "box",
        "size": 28,
    },
    "commit": {
        "color": "#EADFFF",
        "highlight": "#DCCBFF",
        "border": "#9B7BE8",
        "shape": "diamond",
        "size": 24,
    },
    "file": {
        "color": "#D8F7DF",
        "highlight": "#C5EDCF",
        "border": "#62B879",
        "shape": "box",
        "size": 24,
    },
    "class": {
        "color": "#FFE6BF",
        "highlight": "#FFD8A3",
        "border": "#E89A3C",
        "shape": "dot",
        "size": 30,
    },
    "domain": {
        "color": "#CFF5EF",
        "highlight": "#B8ECE4",
        "border": "#43ADA4",
        "shape": "hexagon",
        "size": 26,
    },
}

GRAPH_NODE_VARIANT_STYLES = (
    {"color": "#DCEBFF", "highlight": "#C8DDFF", "border": "#6EA1E8"},
    {"color": "#EADFFF", "highlight": "#DCCBFF", "border": "#9B7BE8"},
    {"color": "#D8F7DF", "highlight": "#C5EDCF", "border": "#62B879"},
    {"color": "#FFE6BF", "highlight": "#FFD8A3", "border": "#E89A3C"},
    {"color": "#CFF5EF", "highlight": "#B8ECE4", "border": "#43ADA4"},
    {"color": "#FDE2F3", "highlight": "#FBCBE8", "border": "#E879C1"},
    {"color": "#E0F2FE", "highlight": "#BAE6FD", "border": "#38A6D9"},
    {"color": "#ECFCCB", "highlight": "#D9F99D", "border": "#84B93F"},
)

GRAPH_HIGHLIGHT_COLOR = "#60A5FA"
GRAPH_HIGHLIGHT_BORDER_COLOR = "#2563EB"
GRAPH_EDGE_COLOR = "#94A3B8"
GRAPH_EDGE_HIGHLIGHT_COLOR = "#64748B"


@dataclass(frozen=True)
class GraphDisplayNode:
    id: str
    label: str
    node_type: str
    title: str
    highlighted: bool = False


@dataclass(frozen=True)
class GraphDisplayEdge:
    source: str
    target: str
    label: str


def short_graph_label(value: str, *, max_length: int = 34) -> str:
    if not value:
        label = "-"
    elif "/" in value or "\\" in value:
        label = value.replace("\\", "/").rsplit("/", 1)[-1]
    else:
        label = value.rsplit(".", 1)[-1]
    if len(label) > max_length:
        return label[: max_length - 1].rstrip() + "..."
    return label


def _graph_component_variant_indexes(
    nodes: list[GraphDisplayNode],
    edges: list[GraphDisplayEdge],
) -> dict[str, int]:
    adjacency: dict[str, set[str]] = {node.id: set() for node in nodes}
    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)

    component_indexes: dict[str, int] = {}
    visited: set[str] = set()
    component_count = 0
    for node in nodes:
        if node.id in visited:
            continue
        stack = [node.id]
        component: list[str] = []
        visited.add(node.id)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        variant_index = component_count % len(GRAPH_NODE_VARIANT_STYLES)
        component_count += 1
        for node_id in component:
            component_indexes[node_id] = variant_index
    return component_indexes


def render_node_edge_graph(
    nodes: list[GraphDisplayNode],
    edges: list[GraphDisplayEdge],
    *,
    height: int | None = None,
    show_edge_labels: bool = False,
    use_component_variants: bool = True,
    physics: bool | None = None,
    hierarchical: bool | None = None,
) -> object | None:
    if not nodes or not edges:
        return None

    single_type_graph = len({node.node_type for node in nodes}) == 1
    component_variant_indexes = (
        _graph_component_variant_indexes(nodes, edges)
        if single_type_graph and use_component_variants
        else {}
    )
    agraph_nodes: list[Node] = []
    for node in nodes:
        style = GRAPH_NODE_STYLE.get(
            node.node_type,
            {"color": "#F3F4F6", "highlight": "#E5E7EB", "border": "#D1D5DB", "shape": "dot", "size": 22},
        )
        color_style = (
            GRAPH_NODE_VARIANT_STYLES[component_variant_indexes.get(node.id, 0)]
            if component_variant_indexes
            else style
        )
        border = GRAPH_HIGHLIGHT_COLOR if node.highlighted else color_style["border"]
        highlight_border = GRAPH_HIGHLIGHT_BORDER_COLOR if node.highlighted else color_style["border"]
        agraph_nodes.append(
            Node(
                id=node.id,
                label=node.label,
                title=node.title,
                color={
                    "background": color_style["color"],
                    "border": border,
                    "highlight": {
                        "background": color_style["highlight"],
                        "border": highlight_border,
                    },
                    "hover": {
                        "background": color_style["highlight"],
                        "border": highlight_border,
                    },
                },
                shape=style["shape"],
                size=style["size"] + (3 if node.highlighted else 0),
                borderWidth=3 if node.highlighted else 2,
                font={"color": "#111827", "face": "Inter, Arial", "size": 14},
            )
        )

    edge_font = {
        "color": "#475569",
        "face": "Inter, Arial",
        "size": 11,
        "background": "rgba(255,255,255,0.82)",
    }
    agraph_edges = [
        Edge(
            source=edge.source,
            target=edge.target,
            label=edge.label if show_edge_labels else "",
            title=edge.label,
            color={"color": GRAPH_EDGE_COLOR, "highlight": GRAPH_EDGE_HIGHLIGHT_COLOR},
            smooth={"type": "dynamic"},
            width=2.4,
            font=edge_font,
        )
        for edge in edges
    ]
    resolved_hierarchical = single_type_graph if hierarchical is None else bool(hierarchical)
    resolved_physics = not resolved_hierarchical if physics is None else bool(physics)
    config = Config(
        height=height or (480 if single_type_graph else 560),
        width="100%",
        directed=True,
        physics=resolved_physics,
        hierarchical=resolved_hierarchical,
        groups={},
    )
    return agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)

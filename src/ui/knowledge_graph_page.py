from __future__ import annotations

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.services.neo4j_graph_service import (
    GraphExploreOption,
    GraphPathRow,
    GraphPayload,
    ImpactPathRow,
    Neo4jGraphFreshness,
    Neo4jGraphExploreResult,
    Neo4jGraphPreview,
    Neo4jSyncResult,
    build_project_graph_payload,
    explore_neo4j_project_graph,
    get_neo4j_connection_status,
    get_neo4j_graph_explore_options,
    get_neo4j_project_preview,
    get_neo4j_project_summary,
    get_project_graph_freshness,
    sync_project_graph_incrementally_to_neo4j,
    sync_project_graph_to_neo4j,
)
from src.ui.graph_visualization import (
    GraphDisplayEdge,
    GraphDisplayNode,
    render_node_edge_graph,
    short_graph_label,
)
from src.ui.project_context import require_project_context


NODE_TYPE_LABELS = {
    "program": "프로그램",
    "class": "클래스",
    "domain": "도메인",
    "commit": "커밋",
}

RELATIONSHIP_TYPE_LABELS = {
    "HAS_PROGRAM": "프로젝트-프로그램",
    "HAS_COMMIT": "프로젝트-커밋",
    "HAS_FILE": "프로젝트-파일",
    "HAS_DOMAIN": "프로젝트-도메인",
    "OWNS_PROGRAM": "도메인-프로그램",
    "MAPPED_TO_COMMIT": "프로그램-커밋",
    "TOUCHES_FILE": "커밋-파일",
    "TOUCHES_DOMAIN": "커밋-도메인",
    "CONTAINS_CLASS": "파일-클래스",
    "IMPORTS_CLASS": "클래스 import",
}

GRAPH_EXPLORER_MAX_NODES = 12
GRAPH_EXPLORER_MAX_EDGES = 16


def _counter_df(counter) -> pd.DataFrame:
    rows = [{"종류": key, "개수": value} for key, value in sorted(counter.items())]
    return pd.DataFrame(rows, columns=["종류", "개수"])


def _domain_df(payload: GraphPayload) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "도메인": row.domain,
                "프로그램": row.program_count,
                "파일": row.file_count,
                "클래스": row.class_count,
                "커밋": row.commit_count,
            }
            for row in payload.domain_rows
        ]
    )


def _impact_rows_df(rows: list[ImpactPathRow]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "커밋": row.commit,
                "프로그램": row.program,
                "파일": row.file_path,
                "클래스": row.class_name,
                "도메인": row.domain,
            }
            for row in rows
        ]
    )


def _impact_df(payload: GraphPayload) -> pd.DataFrame:
    return _impact_rows_df(payload.impact_rows)


def _explore_path_df(rows: list[GraphPathRow]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "깊이": row.depth,
                "대상 종류": NODE_TYPE_LABELS.get(row.target_type, row.target_type),
                "대상": row.target_label,
                "관계": " > ".join(row.edge_types),
                "경로": row.path,
            }
            for row in rows
        ],
        columns=["깊이", "대상 종류", "대상", "관계", "경로"],
    )


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def _format_datetime(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _class_graph_dot_from_rows(rows: list[dict[str, str]], limit: int = 24) -> str:
    rows = rows[:limit]
    lines = ["digraph G {", '  rankdir="LR";', '  node [shape=box, style="rounded,filled", fillcolor="#eef6ff"];']
    for row in rows:
        source = _dot_escape(row["source"].split(".")[-1])
        target = _dot_escape(row["target"].split(".")[-1])
        lines.append(f'  "{source}" -> "{target}";')
    lines.append("}")
    return "\n".join(lines)


def _class_graph_dot(payload: GraphPayload, limit: int = 24) -> str:
    rows = payload.class_import_rows[:limit]
    if not rows:
        class_edges = [
            edge
            for edge in payload.edges
            if edge.edge_type == "CONTAINS_CLASS"
            and edge.from_node_id in {node.node_id for node in payload.nodes if node.node_type == "file"}
        ][:limit]
        labels = {node.node_id: node.label for node in payload.nodes}
        rows = [{"source": labels.get(edge.from_node_id, edge.from_node_id), "target": labels.get(edge.to_node_id, edge.to_node_id)} for edge in class_edges]

    return _class_graph_dot_from_rows(rows)


def _render_sync_result(result) -> None:
    if result.status == "completed":
        st.success(result.summary)
    elif result.status == "skipped":
        st.warning(result.summary)
    else:
        st.error(result.summary)
    if result.node_counts:
        st.dataframe(_counter_df(result.node_counts), hide_index=True, use_container_width=True)
    if result.edge_counts:
        st.dataframe(_counter_df(result.edge_counts), hide_index=True, use_container_width=True)
    if result.raw_metadata:
        keys = [
            "neo4j_write_batch_size",
            "node_batch_count",
            "completed_node_batch_count",
            "edge_batch_count",
            "completed_edge_batch_count",
            "written_node_count",
            "written_edge_count",
            "retry_count",
            "failed_operation",
        ]
        metadata_rows = [
            {"항목": key, "값": result.raw_metadata.get(key)}
            for key in keys
            if key in result.raw_metadata
        ]
        if metadata_rows:
            with st.expander("Neo4j 동기화 실행 세부", expanded=result.status == "failed"):
                st.dataframe(pd.DataFrame(metadata_rows), hide_index=True, use_container_width=True)
    for error in result.errors:
        st.warning(error)
    for warning in getattr(result, "warnings", []):
        st.warning(warning)


def _render_neo4j_saved_summary(project_id: int) -> Neo4jSyncResult:
    summary = get_neo4j_project_summary(project_id)
    if summary.status != "completed":
        _render_sync_result(summary)
        return summary

    st.success(f"Neo4j 저장 확인: node {summary.node_count}개, edge {summary.edge_count}개를 조회했습니다.")
    left, right = st.columns(2)
    left.markdown("##### Neo4j 저장 Node")
    left.dataframe(_counter_df(summary.node_counts), hide_index=True, use_container_width=True)
    right.markdown("##### Neo4j 저장 Edge")
    right.dataframe(_counter_df(summary.edge_counts), hide_index=True, use_container_width=True)
    return summary


def _render_graph_freshness(freshness: Neo4jGraphFreshness) -> None:
    status_labels = {
        "latest": "최신",
        "stale": "갱신 필요",
        "missing": "저장 필요",
        "failed": "실패",
        "skipped": "미사용",
    }
    st.markdown("#### Graph 상태")
    cols = st.columns(6)
    cols[0].metric("상태", status_labels.get(freshness.status, freshness.status))
    cols[1].metric("Repo HEAD", _short_hash(freshness.repo_head_hash))
    cols[2].metric("DB Sync HEAD", _short_hash(freshness.db_sync_head_hash))
    cols[3].metric("Graph HEAD", _short_hash(freshness.graph_sync_head_hash))
    cols[4].metric("마지막 반영", _format_datetime(freshness.synced_at))
    cols[5].metric("방식", freshness.sync_mode or "-")

    if freshness.status == "latest":
        st.success(freshness.summary)
    elif freshness.status == "failed":
        st.error(freshness.summary)
    elif freshness.status in {"stale", "missing"}:
        st.warning(freshness.summary)
    else:
        st.info(freshness.summary)


def _format_explore_option(option: GraphExploreOption) -> str:
    suffix = option.key if option.key and option.key != option.label else option.description
    return f"{option.label} · {suffix}" if suffix and suffix != "-" else option.label


def _format_relationship_type(value: str) -> str:
    label = RELATIONSHIP_TYPE_LABELS.get(value, value)
    return f"{label} ({value})"


def _render_node_detail(result) -> None:
    detail = result.node_detail
    if detail is None:
        return

    st.markdown("##### 선택 node")
    cols = st.columns(4)
    cols[0].metric("종류", NODE_TYPE_LABELS.get(detail.node_type, detail.node_type))
    cols[1].metric("Label", detail.label)
    cols[2].metric("연결 수", detail.related_count)
    cols[3].metric("Node ID", detail.node_id)

    property_rows = [
        {"속성": key, "값": str(value)}
        for key, value in sorted(detail.properties.items())
        if value not in (None, "")
    ]
    if property_rows:
        with st.expander("Node properties", expanded=False):
            st.dataframe(pd.DataFrame(property_rows), hide_index=True, use_container_width=True)


def build_graph_exploration_display(
    result: Neo4jGraphExploreResult,
    *,
    max_nodes: int = GRAPH_EXPLORER_MAX_NODES,
    max_edges: int = GRAPH_EXPLORER_MAX_EDGES,
) -> tuple[list[GraphDisplayNode], list[GraphDisplayEdge], bool]:
    detail = result.node_detail
    if detail is None:
        return [], [], False

    safe_max_nodes = max(2, int(max_nodes))
    safe_max_edges = max(1, int(max_edges))
    nodes: dict[str, GraphDisplayNode] = {
        detail.node_id: GraphDisplayNode(
            id=detail.node_id,
            label=short_graph_label(detail.label),
            node_type=detail.node_type,
            title=f"{NODE_TYPE_LABELS.get(detail.node_type, detail.node_type)}: {detail.label}\nNode ID: {detail.node_id}",
            highlighted=True,
        )
    }
    edges: dict[tuple[str, str, str], GraphDisplayEdge] = {}
    truncated = False

    for row in result.rows:
        path_nodes = {
            node.node_id: GraphDisplayNode(
                id=node.node_id,
                label=short_graph_label(node.label),
                node_type=node.node_type,
                title=f"{NODE_TYPE_LABELS.get(node.node_type, node.node_type)}: {node.label}\nNode ID: {node.node_id}",
                highlighted=node.node_id == detail.node_id,
            )
            for node in row.nodes
            if node.node_id and node.node_id != "-"
        }
        path_edges = {
            (edge.source_node_id, edge.target_node_id, edge.edge_type): GraphDisplayEdge(
                source=edge.source_node_id,
                target=edge.target_node_id,
                label=edge.edge_type,
            )
            for edge in row.edges
            if edge.source_node_id in path_nodes
            and edge.target_node_id in path_nodes
            and edge.source_node_id != edge.target_node_id
        }
        new_node_ids = [node_id for node_id in path_nodes if node_id not in nodes]
        new_edge_keys = [edge_key for edge_key in path_edges if edge_key not in edges]
        if len(nodes) + len(new_node_ids) > safe_max_nodes or len(edges) + len(new_edge_keys) > safe_max_edges:
            truncated = True
            continue

        for node_id, node in path_nodes.items():
            existing = nodes.get(node_id)
            if existing is None or (node.highlighted and not existing.highlighted):
                nodes[node_id] = node
        edges.update(path_edges)

    return list(nodes.values()), list(edges.values()), truncated


def _render_graph_exploration_visualization(result: Neo4jGraphExploreResult) -> None:
    nodes, edges, truncated = build_graph_exploration_display(result)
    if not nodes or not edges:
        st.info("선택한 조건에서 관계도로 표시할 node와 edge가 없습니다. 아래 path 표를 확인하세요.")
        return

    st.markdown("##### 선택 node 관계도")
    st.caption(
        "파란 테두리는 선택 node이며 화살표는 Neo4j에 저장된 관계 방향입니다. "
        "프로그램·커밋·파일·클래스·도메인은 종류별 색과 모양으로 구분하고, 선 위에 마우스를 올리면 관계 이름을 확인할 수 있습니다."
    )
    render_node_edge_graph(
        nodes,
        edges,
        height=520,
        show_edge_labels=False,
        use_component_variants=False,
    )
    st.caption(f"관계도 표시: node {len(nodes)}개 · edge {len(edges)}개")
    st.caption("표시 관계: " + ", ".join(sorted({edge.label for edge in edges})))
    if truncated:
        st.caption(
            f"화면 가독성을 위해 최대 node {GRAPH_EXPLORER_MAX_NODES}개, edge {GRAPH_EXPLORER_MAX_EDGES}개까지만 그립니다. "
            "조회된 경로는 아래 표에서 계속 확인할 수 있습니다."
        )


def _render_graph_explorer(project_id: int, status_connected: bool) -> None:
    st.markdown("#### 관계 탐색")
    st.caption("Neo4j에 저장된 graph에서 선택한 프로그램, 클래스, 도메인, 커밋 주변 path만 좁혀 봅니다.")
    if not status_connected:
        st.warning("Neo4j 연결이 준비되면 저장 graph 기준 관계 탐색을 사용할 수 있습니다.")
        return

    options_result = get_neo4j_graph_explore_options(project_id)
    if options_result.status != "completed":
        st.warning(options_result.summary)
        for error in options_result.errors:
            st.warning(error)
        return

    available_types = [node_type for node_type in NODE_TYPE_LABELS if options_result.options_by_type.get(node_type)]
    if not available_types:
        st.info("Neo4j에 탐색할 프로그램, 클래스, 도메인, 커밋 node가 아직 없습니다. 먼저 전체 재동기화를 실행하세요.")
        return

    selector_cols = st.columns([1, 3])
    selected_type = selector_cols[0].selectbox(
        "탐색 기준",
        available_types,
        format_func=lambda value: NODE_TYPE_LABELS.get(value, value),
        key=f"kg_explore_type_{project_id}",
    )
    selected_option = selector_cols[1].selectbox(
        "탐색 node",
        options_result.options_by_type[selected_type],
        format_func=_format_explore_option,
        key=f"kg_explore_node_{project_id}_{selected_type}",
    )

    filter_cols = st.columns([3, 1, 1])
    relationship_types = filter_cols[0].multiselect(
        "관계 필터",
        list(RELATIONSHIP_TYPE_LABELS),
        format_func=_format_relationship_type,
        placeholder="전체 관계",
        key=f"kg_explore_relationships_{project_id}_{selected_type}",
    )
    depth = filter_cols[1].slider("깊이", min_value=1, max_value=3, value=2, key=f"kg_explore_depth_{project_id}")
    limit = filter_cols[2].number_input(
        "최대 path",
        min_value=10,
        max_value=300,
        value=80,
        step=10,
        key=f"kg_explore_limit_{project_id}",
    )

    result = explore_neo4j_project_graph(
        project_id,
        selected_option.node_id,
        relationship_types=relationship_types,
        depth=depth,
        limit=int(limit),
    )
    if result.status == "failed":
        st.error(result.summary)
        for error in result.errors:
            st.warning(error)
        return
    if result.status == "skipped":
        st.info(result.summary)
        return

    _render_node_detail(result)
    if result.rows:
        _render_graph_exploration_visualization(result)
        st.markdown("##### 주변 path")
        st.dataframe(_explore_path_df(result.rows), hide_index=True, use_container_width=True)
    else:
        st.info("선택한 조건에 맞는 주변 path가 없습니다. 깊이를 늘리거나 관계 필터를 비워 보세요.")


def _read_neo4j_preview(status_connected: bool, project_id: int) -> tuple[Neo4jSyncResult | None, Neo4jGraphPreview | None]:
    if not status_connected:
        return None, None
    return get_neo4j_project_summary(project_id), get_neo4j_project_preview(project_id)


def _uses_saved_graph(preview: Neo4jGraphPreview | None, rows: list) -> bool:
    return bool(preview and preview.status == "completed" and rows)


def render_knowledge_graph_page() -> None:
    st.title("Knowledge Graph")
    st.caption("Neo4j에 프로젝트, 프로그램, 커밋, 파일, 클래스, 도메인 관계를 동기화하고 영향 경로를 확인합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return

    status = get_neo4j_connection_status()
    cols = st.columns(4)
    cols[0].metric("Neo4j", "연결" if status.connected else "미연결")
    cols[1].metric("사용 설정", "ON" if status.enabled else "OFF")
    cols[2].metric("URI", status.uri)
    cols[3].metric("Database", status.database or "default")
    if status.connected:
        st.success(status.message)
    else:
        st.warning(status.message)

    with SessionLocal() as db:
        payload = build_project_graph_payload(db, context.project_id)
        freshness = get_project_graph_freshness(db, context.project_id)

    _render_graph_freshness(freshness)

    st.markdown("#### 동기화 대상 요약")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Nodes", len(payload.nodes))
    metric_cols[1].metric("Edges", len(payload.edges))
    metric_cols[2].metric("Classes", payload.node_counts.get("class", 0))
    metric_cols[3].metric("Domains", payload.node_counts.get("domain", 0))

    action_cols = st.columns(3)
    incremental_disabled = not status.connected or freshness.status == "missing"
    if action_cols[0].button(
        "최신 변경분만 Neo4j 반영",
        use_container_width=True,
        disabled=incremental_disabled,
    ):
        with SessionLocal() as db:
            result = sync_project_graph_incrementally_to_neo4j(db, context.project_id)
        _render_sync_result(result)
        if result.status == "completed":
            _render_neo4j_saved_summary(context.project_id)
    if action_cols[1].button("전체 재동기화", use_container_width=True, disabled=not status.connected):
        with SessionLocal() as db:
            result = sync_project_graph_to_neo4j(db, context.project_id)
        _render_sync_result(result)
        if result.status == "completed":
            _render_neo4j_saved_summary(context.project_id)
    if action_cols[2].button("Neo4j 저장 상태 조회", use_container_width=True, disabled=not status.connected):
        _render_neo4j_saved_summary(context.project_id)

    neo4j_summary, neo4j_preview = _read_neo4j_preview(status.connected, context.project_id)
    if neo4j_preview and neo4j_preview.status == "failed":
        st.warning(neo4j_preview.summary)
        for error in neo4j_preview.errors:
            st.warning(error)

    if payload.errors or payload.warnings:
        with st.expander("동기화 준비 경고", expanded=True):
            for error in payload.errors:
                st.warning(error)
            for warning in payload.warnings:
                st.warning(warning)

    graph_views = ["도메인 묶음", "관계 탐색", "클래스 관계도", "영향 경로", "노드/엣지"]
    selected_view = st.segmented_control(
        "Knowledge Graph 보기",
        graph_views,
        default="도메인 묶음",
        selection_mode="single",
        key=f"knowledge_graph_view_{context.project_id}",
        label_visibility="collapsed",
    )
    selected_view = selected_view or "도메인 묶음"

    if selected_view == "도메인 묶음":
        st.dataframe(_domain_df(payload), hide_index=True, use_container_width=True)
    elif selected_view == "관계 탐색":
        _render_graph_explorer(context.project_id, status.connected)
    elif selected_view == "클래스 관계도":
        neo4j_class_rows = neo4j_preview.class_import_rows if neo4j_preview else []
        if _uses_saved_graph(neo4j_preview, neo4j_class_rows):
            st.caption("Neo4j 저장 그래프 기준")
            st.graphviz_chart(_class_graph_dot_from_rows(neo4j_class_rows), use_container_width=True)
            st.dataframe(pd.DataFrame(neo4j_class_rows), hide_index=True, use_container_width=True)
        elif payload.class_import_rows:
            st.caption("동기화 대상 preview 기준")
            st.graphviz_chart(_class_graph_dot(payload), use_container_width=True)
            st.dataframe(pd.DataFrame(payload.class_import_rows), hide_index=True, use_container_width=True)
        else:
            st.caption("동기화 대상 preview 기준")
            st.graphviz_chart(_class_graph_dot(payload), use_container_width=True)
            st.info("프로젝트 내부 import 관계가 아직 충분히 추출되지 않아 파일-클래스 관계를 표시했습니다.")
    elif selected_view == "영향 경로":
        neo4j_impact_rows = neo4j_preview.impact_rows if neo4j_preview else []
        if _uses_saved_graph(neo4j_preview, neo4j_impact_rows):
            st.caption("Neo4j 저장 그래프 기준")
            st.dataframe(_impact_rows_df(neo4j_impact_rows), hide_index=True, use_container_width=True)
        else:
            st.caption("동기화 대상 preview 기준")
            st.dataframe(_impact_df(payload), hide_index=True, use_container_width=True)
    elif selected_view == "노드/엣지":
        if neo4j_summary and neo4j_summary.status == "completed" and (neo4j_summary.node_count or neo4j_summary.edge_count):
            st.caption("Neo4j에서 조회한 저장 상태입니다.")
            left, right = st.columns(2)
            left.markdown("##### Neo4j 저장 Node")
            left.table(_counter_df(neo4j_summary.node_counts))
            right.markdown("##### Neo4j 저장 Edge")
            right.table(_counter_df(neo4j_summary.edge_counts))
        else:
            st.caption("동기화 대상 preview 기준")
            left, right = st.columns(2)
            left.markdown("##### Node")
            left.table(_counter_df(payload.node_counts))
            right.markdown("##### Edge")
            right.table(_counter_df(payload.edge_counts))

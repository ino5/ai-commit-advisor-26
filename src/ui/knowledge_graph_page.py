from __future__ import annotations

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.services.neo4j_graph_service import (
    GraphPayload,
    build_project_graph_payload,
    get_neo4j_connection_status,
    get_neo4j_project_summary,
    sync_project_graph_to_neo4j,
)
from src.ui.project_context import require_project_context


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


def _impact_df(payload: GraphPayload) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "커밋": row.commit,
                "프로그램": row.program,
                "파일": row.file_path,
                "클래스": row.class_name,
                "도메인": row.domain,
            }
            for row in payload.impact_rows
        ]
    )


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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

    lines = ["digraph G {", '  rankdir="LR";', '  node [shape=box, style="rounded,filled", fillcolor="#eef6ff"];']
    for row in rows:
        source = _dot_escape(row["source"].split(".")[-1])
        target = _dot_escape(row["target"].split(".")[-1])
        lines.append(f'  "{source}" -> "{target}";')
    lines.append("}")
    return "\n".join(lines)


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
    for error in result.errors:
        st.warning(error)


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

    st.markdown("#### 동기화 대상 요약")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Nodes", len(payload.nodes))
    metric_cols[1].metric("Edges", len(payload.edges))
    metric_cols[2].metric("Classes", payload.node_counts.get("class", 0))
    metric_cols[3].metric("Domains", payload.node_counts.get("domain", 0))

    action_cols = st.columns(2)
    if action_cols[0].button("Neo4j 동기화", use_container_width=True):
        with SessionLocal() as db:
            result = sync_project_graph_to_neo4j(db, context.project_id)
        _render_sync_result(result)
    if action_cols[1].button("Neo4j 저장 상태 조회", use_container_width=True):
        _render_sync_result(get_neo4j_project_summary(context.project_id))

    if payload.errors:
        with st.expander("동기화 준비 경고", expanded=True):
            for error in payload.errors:
                st.warning(error)

    domain_tab, class_tab, impact_tab, count_tab = st.tabs(["도메인 묶음", "클래스 관계도", "영향 경로", "노드/엣지"])
    with domain_tab:
        st.dataframe(_domain_df(payload), hide_index=True, use_container_width=True)
    with class_tab:
        st.graphviz_chart(_class_graph_dot(payload), use_container_width=True)
        if payload.class_import_rows:
            st.dataframe(pd.DataFrame(payload.class_import_rows), hide_index=True, use_container_width=True)
        else:
            st.info("프로젝트 내부 import 관계가 아직 충분히 추출되지 않아 파일-클래스 관계를 표시했습니다.")
    with impact_tab:
        st.dataframe(_impact_df(payload), hide_index=True, use_container_width=True)
    with count_tab:
        left, right = st.columns(2)
        left.markdown("##### Node")
        left.dataframe(_counter_df(payload.node_counts), hide_index=True, use_container_width=True)
        right.markdown("##### Edge")
        right.dataframe(_counter_df(payload.edge_counts), hide_index=True, use_container_width=True)

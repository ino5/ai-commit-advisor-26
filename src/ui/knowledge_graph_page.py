from __future__ import annotations

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.services.neo4j_graph_service import (
    GraphPayload,
    ImpactPathRow,
    Neo4jGraphFreshness,
    Neo4jGraphPreview,
    Neo4jSyncResult,
    build_project_graph_payload,
    get_neo4j_connection_status,
    get_neo4j_project_preview,
    get_neo4j_project_summary,
    get_project_graph_freshness,
    sync_project_graph_incrementally_to_neo4j,
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
    for error in result.errors:
        st.warning(error)


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

    if payload.errors:
        with st.expander("동기화 준비 경고", expanded=True):
            for error in payload.errors:
                st.warning(error)

    domain_tab, class_tab, impact_tab, count_tab = st.tabs(["도메인 묶음", "클래스 관계도", "영향 경로", "노드/엣지"])
    with domain_tab:
        st.dataframe(_domain_df(payload), hide_index=True, use_container_width=True)
    with class_tab:
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
    with impact_tab:
        neo4j_impact_rows = neo4j_preview.impact_rows if neo4j_preview else []
        if _uses_saved_graph(neo4j_preview, neo4j_impact_rows):
            st.caption("Neo4j 저장 그래프 기준")
            st.dataframe(_impact_rows_df(neo4j_impact_rows), hide_index=True, use_container_width=True)
        else:
            st.caption("동기화 대상 preview 기준")
            st.dataframe(_impact_df(payload), hide_index=True, use_container_width=True)
    with count_tab:
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

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.services.ai_evidence_service import (
    generate_weekly_ai_report,
    get_ai_evaluation_scorecard,
    get_evidence_trace,
    get_poc_readiness_rows,
)
from src.services.ai_invocation_service import list_ai_invocations, summarize_ai_invocations
from src.ui.project_context import require_project_context


def _rows_to_df(rows) -> pd.DataFrame:
    return pd.DataFrame([row.__dict__ for row in rows]).rename(
        columns={"area": "영역", "status": "상태", "value": "현재 값", "action": "다음 조치"}
    )


def _json_block(label: str, payload: dict | list) -> None:
    with st.expander(label, expanded=False):
        st.json(payload)


def _render_readiness(project_id: int) -> None:
    with SessionLocal() as db:
        rows = get_poc_readiness_rows(db, project_id)
    st.dataframe(_rows_to_df(rows), use_container_width=True, hide_index=True)


def _render_scorecard(project_id: int) -> None:
    with SessionLocal() as db:
        rows = get_ai_evaluation_scorecard(db, project_id)
    st.dataframe(_rows_to_df(rows), use_container_width=True, hide_index=True)


def _render_trace(project_id: int) -> None:
    with SessionLocal() as db:
        trace = get_evidence_trace(db, project_id, limit=10)

    st.subheader("PL Briefing")
    if trace.latest_pl_briefing:
        briefing = trace.latest_pl_briefing
        st.table(
            {
                "항목": ["generated_at", "provider", "model", "mode", "validation_status", "repair_attempted"],
                "값": [
                    briefing["generated_at"],
                    briefing["provider"],
                    briefing["model"],
                    briefing["mode"],
                    briefing.get("validation_status") or "-",
                    str(briefing.get("repair_attempted")),
                ],
            }
        )
        st.markdown(briefing["summary"])
        _json_block("PL Briefing evidence payload", briefing["evidence_payload"])
        _json_block("PL Briefing raw response metadata", briefing["raw_response"])
    else:
        st.info("저장된 PL Briefing이 없습니다.")

    st.subheader("Mapping")
    if trace.recent_mappings:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "program": row["program"],
                        "commit": row["commit"],
                        "score": row["score"],
                        "status": row["status"],
                        "fallback": row["fallback"],
                        "reason": row["reason"],
                    }
                    for row in trace.recent_mappings
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        _json_block("최근 Mapping raw response", [row["raw_response"] for row in trace.recent_mappings[:3]])
    else:
        st.info("Mapping evidence가 없습니다.")

    st.subheader("Project Chat")
    if trace.recent_chat_answers:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "session": row["session"],
                        "message_index": row["message_index"],
                        "used_sources": row["used_sources"],
                        "excluded_sources": row["excluded_sources"],
                        "insufficient_evidence": row["insufficient_evidence"],
                        "answer": row["answer"],
                    }
                    for row in trace.recent_chat_answers
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        _json_block("최근 Project Chat source metadata", [row["sources"] for row in trace.recent_chat_answers[:3]])
    else:
        st.info("Project Chat 답변 evidence가 없습니다.")

    st.subheader("AI Code Review")
    if trace.recent_code_reviews:
        st.dataframe(pd.DataFrame(trace.recent_code_reviews).drop(columns=["raw_response"]), use_container_width=True, hide_index=True)
        _json_block("최근 AI Code Review raw response", [row["raw_response"] for row in trace.recent_code_reviews[:3]])
    else:
        st.info("AI Code Review evidence가 없습니다.")


def _render_telemetry(project_id: int) -> None:
    with SessionLocal() as db:
        summary = summarize_ai_invocations(db, project_id)
        rows = list_ai_invocations(db, project_id, limit=50)

    cols = st.columns(5)
    cols[0].metric("총 호출", summary.total_count)
    cols[1].metric("성공", summary.success_count)
    cols[2].metric("실패", summary.failed_count)
    cols[3].metric("fallback", summary.fallback_count)
    cols[4].metric("평균 지연", f"{summary.average_duration_ms}ms")

    if rows:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "feature": row.feature,
                        "provider": row.provider,
                        "model": row.model or "-",
                        "status": row.status,
                        "mode": row.mode or "-",
                        "fallback": row.fallback_used,
                        "validation": row.validation_status or "-",
                        "duration_ms": row.duration_ms,
                        "prompt_length": row.prompt_length,
                        "response_length": row.response_length,
                        "error": row.error_message or "-",
                    }
                    for row in rows
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        _json_block("최근 telemetry metadata", [row.raw_metadata or {} for row in rows[:10]])
    else:
        st.info("아직 저장된 AI 호출 telemetry가 없습니다.")


def _render_report(project_id: int) -> None:
    with SessionLocal() as db:
        report = generate_weekly_ai_report(db, project_id)
    st.download_button(
        "주간 점검 보고서 다운로드",
        data=report.encode("utf-8"),
        file_name=f"weekly-ai-report-project-{project_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.text_area("보고서 미리보기", value=report, height=520)


def render_ai_evidence_page() -> None:
    st.title("AI Evidence")
    st.caption("AX PoC 시연을 위한 AI 준비 상태, 근거 추적, 품질 점검, 보고서, 호출 telemetry를 확인합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return

    readiness_tab, trace_tab, scorecard_tab, report_tab, telemetry_tab = st.tabs(
        ["시연 준비", "Evidence Trace", "AI Scorecard", "주간 보고서", "Telemetry"]
    )
    with readiness_tab:
        _render_readiness(context.project_id)
    with trace_tab:
        _render_trace(context.project_id)
    with scorecard_tab:
        _render_scorecard(context.project_id)
    with report_tab:
        _render_report(context.project_id)
    with telemetry_tab:
        _render_telemetry(context.project_id)

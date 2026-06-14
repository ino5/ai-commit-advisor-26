from __future__ import annotations

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.services.ai_evidence_service import (
    EvidenceActionResult,
    FAIL,
    WARN,
    generate_weekly_ai_report,
    get_ai_evaluation_scorecard,
    get_ai_operations_status_rows,
    get_evidence_trace,
    get_ai_readiness_rows,
    priority_status_rows,
    run_mapping_shortcut,
    run_pl_briefing_shortcut,
    run_risk_analysis_shortcut,
    run_search_ready_shortcut,
    summarize_status_rows,
)
from src.services.ai_invocation_service import list_ai_invocations, summarize_ai_invocations
from src.ui.project_context import ProjectContext, project_scoped_key, require_project_context


def _rows_to_df(rows) -> pd.DataFrame:
    columns = {"area": "영역", "status": "상태", "value": "현재 값", "action": "다음 조치"}
    if not rows:
        return pd.DataFrame(columns=columns.values())
    return pd.DataFrame([row.__dict__ for row in rows]).rename(
        columns=columns
    )


def _json_block(label: str, payload: dict | list) -> None:
    with st.expander(label, expanded=False):
        st.json(payload)


def _render_action_result(result: EvidenceActionResult) -> None:
    if result.status == "failed":
        st.error(result.summary)
    elif result.status == "completed_with_warnings":
        st.warning(result.summary)
    else:
        st.success(result.summary)

    if result.details or result.errors:
        with st.expander(f"{result.title} 상세", expanded=bool(result.errors)):
            if result.details:
                st.json(result.details)
            for error in result.errors:
                st.error(error)


def _run_shortcut(title: str, action) -> None:
    try:
        with st.spinner(f"{title} 중입니다."):
            with SessionLocal() as db:
                result = action(db)
    except Exception as exc:
        st.error(f"{title} 실패: {exc}")
        return
    _render_action_result(result)


def _render_action_shortcuts(context: ProjectContext) -> None:
    st.markdown("#### AI 실행 바로가기")
    cols = st.columns(4)
    if cols[0].button(
        "Mapping 실행",
        key=project_scoped_key(context.project_id, "ai_evidence_run_mapping"),
        use_container_width=True,
    ):
        _run_shortcut("Mapping 실행", lambda db: run_mapping_shortcut(db, context.project_id))

    if cols[1].button(
        "Risk Analysis 실행",
        key=project_scoped_key(context.project_id, "ai_evidence_run_risk"),
        use_container_width=True,
    ):
        _run_shortcut("Risk Analysis 실행", lambda db: run_risk_analysis_shortcut(db, context.project_id))

    if cols[2].button(
        "PL Briefing 생성",
        key=project_scoped_key(context.project_id, "ai_evidence_run_pl_briefing"),
        use_container_width=True,
    ):
        _run_shortcut("PL Briefing 생성", lambda db: run_pl_briefing_shortcut(db, context.project_id))

    if cols[3].button(
        "검색 준비 생성",
        disabled=not bool(context.git_repo_path),
        key=project_scoped_key(context.project_id, "ai_evidence_run_search_ready"),
        use_container_width=True,
    ):
        _run_shortcut(
            "검색 준비 생성",
            lambda db: run_search_ready_shortcut(db, context.project_id, embedding_limit=50),
        )


def _render_status_focus(title: str, rows) -> None:
    summary = summarize_status_rows(rows)
    st.markdown(f"#### {title}")
    cols = st.columns(4)
    cols[0].metric("전체", summary.total_count)
    cols[1].metric("통과", summary.pass_count)
    cols[2].metric("주의", summary.warn_count)
    cols[3].metric("실패", summary.fail_count)

    focused_rows = priority_status_rows(rows)
    st.markdown("##### 주의/실패 우선 확인")
    if focused_rows:
        for row in focused_rows:
            message = f"**{row.area}** · `{row.value}`\n\n{row.action}"
            if row.status == FAIL:
                st.error(message)
            elif row.status == WARN:
                st.warning(message)
            else:
                st.info(message)
    else:
        st.success("주의/실패 항목이 없습니다.")

    with st.expander("전체 항목", expanded=False):
        st.dataframe(
            _rows_to_df(priority_status_rows(rows, include_pass=True)),
            use_container_width=True,
            hide_index=True,
        )


def _render_ai_operations_status(project_id: int) -> None:
    with SessionLocal() as db:
        rows = get_ai_operations_status_rows(db, project_id)

    st.markdown("#### 연결된 AI")
    cols = st.columns(len(rows))
    for col, row in zip(cols, rows):
        col.metric(row.area, row.status)
        col.caption(row.value)
        if row.status == FAIL:
            col.error(row.action)
        elif row.status == WARN:
            col.warning(row.action)
        else:
            col.success("정상")


def _render_readiness(context: ProjectContext) -> None:
    _render_action_shortcuts(context)
    st.divider()
    with SessionLocal() as db:
        rows = get_ai_readiness_rows(db, context.project_id)
    _render_status_focus("운영 준비 요약", rows)


def _render_scorecard(project_id: int) -> None:
    with SessionLocal() as db:
        rows = get_ai_evaluation_scorecard(db, project_id)
    _render_status_focus("품질 점검 요약", rows)


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
    st.title("AI 운영 현황")
    st.caption("연결된 LLM/embedding 설정과 AI 분석 결과의 준비 상태, 근거, 품질, 호출 기록을 확인합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return

    _render_ai_operations_status(context.project_id)
    st.divider()

    readiness_tab, trace_tab, scorecard_tab, report_tab, telemetry_tab = st.tabs(
        ["운영 준비", "근거 추적", "품질 점검", "주간 보고서", "호출 기록"]
    )
    with readiness_tab:
        _render_readiness(context)
    with trace_tab:
        _render_trace(context.project_id)
    with scorecard_tab:
        _render_scorecard(context.project_id)
    with report_tab:
        _render_report(context.project_id)
    with telemetry_tab:
        _render_telemetry(context.project_id)

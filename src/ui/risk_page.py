import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.services.risk_service import get_unresolved_findings, resolve_findings, run_risk_analysis, summarize_findings
from src.ui.project_context import require_project_context


LEVEL_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _findings_dataframe(findings) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": finding.id,
                "risk_level": finding.risk_level,
                "risk_type": finding.risk_type,
                "program_id": (finding.evidence or {}).get("program_id"),
                "program_name": (finding.evidence or {}).get("program_name"),
                "developer": (finding.evidence or {}).get("developer"),
                "title": finding.title,
                "description": finding.description,
                "plan_progress_rate": (finding.evidence or {}).get("plan_progress_rate"),
                "ai_progress_rate": (finding.evidence or {}).get("ai_progress_rate"),
                "progress_gap": (finding.evidence or {}).get("progress_gap"),
                "related_commit_count": (finding.evidence or {}).get("related_commit_count"),
                "detected_at": finding.detected_at,
            }
            for finding in findings
        ]
    )


def _render_dashboard(findings) -> None:
    summary = summarize_findings(findings)
    cols = st.columns(4)
    cols[0].metric("전체 리스크", summary["total"])
    cols[1].metric("HIGH", summary["high"])
    cols[2].metric("MEDIUM", summary["medium"])
    cols[3].metric("LOW", summary["low"])

    if not findings:
        st.success("현재 unresolved 리스크가 없습니다.")
        return

    chart_left, chart_right = st.columns(2)
    type_df = pd.DataFrame(
        [{"risk_type": risk_type, "count": count} for risk_type, count in summary["by_type"].items()]
    )
    developer_df = pd.DataFrame(
        [{"developer": developer, "count": count} for developer, count in summary["by_developer"].items()]
    )
    with chart_left:
        st.plotly_chart(px.bar(type_df, x="risk_type", y="count", text="count", title="리스크 유형별"), use_container_width=True)
    with chart_right:
        st.plotly_chart(
            px.bar(developer_df, x="developer", y="count", text="count", title="개발자별 리스크 프로그램 수"),
            use_container_width=True,
        )


def _render_findings(project_id: int, findings) -> None:
    st.subheader("리스크 프로그램 목록")
    if not findings:
        return

    df = _findings_dataframe(findings)
    df["level_rank"] = df["risk_level"].map(LEVEL_ORDER).fillna(0)
    df = df.sort_values(["level_rank", "detected_at"], ascending=[False, False])

    col1, col2, col3 = st.columns(3)
    levels = sorted(df["risk_level"].dropna().unique().tolist(), key=lambda value: -LEVEL_ORDER.get(value, 0))
    selected_levels = col1.multiselect("Risk Level", levels, default=levels)
    risk_types = sorted(df["risk_type"].dropna().unique().tolist())
    selected_types = col2.multiselect("Risk Type", risk_types, default=risk_types)
    developers = sorted(df["developer"].fillna("미지정").unique().tolist())
    selected_developers = col3.multiselect("담당자", developers, default=developers)

    filtered = df[
        df["risk_level"].isin(selected_levels)
        & df["risk_type"].isin(selected_types)
        & df["developer"].fillna("미지정").isin(selected_developers)
    ]
    st.dataframe(
        filtered[
            [
                "id",
                "risk_level",
                "risk_type",
                "program_id",
                "program_name",
                "developer",
                "title",
                "description",
                "plan_progress_rate",
                "ai_progress_rate",
                "progress_gap",
                "related_commit_count",
                "detected_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Resolved 처리")
    resolve_options = {
        f"{row.id} | {row.risk_level} | {row.program_id or '-'} | {row.title}": int(row.id)
        for row in filtered.itertuples()
    }
    selected = st.multiselect("resolved 처리할 리스크", list(resolve_options.keys()))
    if st.button("선택 항목 resolved 처리", disabled=not selected):
        ids = [resolve_options[label] for label in selected]
        with SessionLocal() as db:
            count = resolve_findings(db, ids)
        st.success(f"{count}건을 resolved 처리했습니다.")
        st.rerun()


def render_risk_page() -> None:
    st.title("Risk Analysis")
    st.caption("프로그램 목록, 개발계획, Git 커밋, LLM 매핑 결과를 기반으로 누락/위험 프로그램을 규칙 기반으로 탐지합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return
    project_id = context.project_id

    if st.button("리스크 분석 실행", type="primary"):
        with SessionLocal() as db:
            with st.spinner("규칙 기반 리스크를 탐지하고 저장하는 중입니다."):
                result = run_risk_analysis(db, project_id)
        st.success(
            f"탐지 {result.detected_count}건, 신규 {result.created_count}건, 업데이트 {result.updated_count}건, "
            f"자동 resolved {result.auto_resolved_count}건"
        )

    st.divider()
    with SessionLocal() as db:
        findings = get_unresolved_findings(db, project_id)

    _render_dashboard(findings)
    st.divider()
    _render_findings(project_id, findings)

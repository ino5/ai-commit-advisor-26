import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.models import AnalysisRun, GitCommit, Project
from src.services.developer_service import get_developer_stats
from src.services.progress_service import get_ai_progress_summary
from src.ui.project_context import require_project_context


def _program_df(summary) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "program_id": row.program_id,
                "program_name": row.program_name,
                "developer": row.developer,
                "status": row.status,
                "plan_progress_rate": row.plan_progress_rate,
                "ai_progress_rate": row.ai_progress_rate,
                "progress_gap": row.progress_gap,
                "is_risk": row.is_risk,
                "risk_reasons": ", ".join(row.risk_reasons),
            }
            for row in summary.rows
        ]
    )


def _render_project_summary(project_id: int) -> None:
    with SessionLocal() as db:
        project = db.query(Project).filter(Project.id == project_id).one()
        summary = get_ai_progress_summary(db, project_id)
        commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()
        recent_runs = (
            db.query(AnalysisRun)
            .filter(AnalysisRun.project_id == project_id)
            .order_by(AnalysisRun.started_at.desc().nullslast(), AnalysisRun.id.desc())
            .limit(10)
            .all()
        )
        developer_stats = get_developer_stats(db, project_id)

    st.subheader("프로젝트 현황")
    cols = st.columns(5)
    cols[0].metric("프로그램", len(summary.rows))
    cols[1].metric("커밋", commit_count)
    cols[2].metric("계획 진척도", f"{summary.plan_average}%")
    cols[3].metric("AI 진척도", f"{summary.ai_average}%")
    cols[4].metric("리스크", summary.risk_count)
    st.caption(f"마지막 Git 동기화: {project.last_synced_at.strftime('%Y-%m-%d %H:%M') if project.last_synced_at else '-'}")
    st.progress(min(max(summary.plan_average / 100, 0), 1), text=f"전체 계획 진척도 {summary.plan_average}%")

    if summary.rows:
        df = _program_df(summary)
        chart1, chart2 = st.columns(2)
        with chart1:
            st.subheader("상태별 프로그램 수")
            status_df = df.groupby("status", dropna=False).size().reset_index(name="count")
            st.plotly_chart(px.bar(status_df, x="status", y="count", text="count"), use_container_width=True)

        with chart2:
            st.subheader("개발자별 진행률")
            developer_df = (
                df.groupby("developer", dropna=False)[["plan_progress_rate", "ai_progress_rate"]]
                .mean()
                .round(1)
                .reset_index()
            )
            melted = developer_df.melt(
                id_vars=["developer"],
                value_vars=["plan_progress_rate", "ai_progress_rate"],
                var_name="progress_type",
                value_name="progress_rate",
            )
            st.plotly_chart(
                px.bar(melted, x="developer", y="progress_rate", color="progress_type", barmode="group"),
                use_container_width=True,
            )

        st.subheader("리스크 TOP 10")
        risk_df = df[df["is_risk"]].sort_values("progress_gap", ascending=False).head(10)
        if risk_df.empty:
            st.success("리스크 조건에 해당하는 프로그램이 없습니다.")
        else:
            st.dataframe(
                risk_df[
                    [
                        "program_id",
                        "program_name",
                        "developer",
                        "status",
                        "plan_progress_rate",
                        "ai_progress_rate",
                        "progress_gap",
                        "risk_reasons",
                    ]
                ],
                use_container_width=True,
            )

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("최근 분석 결과")
        if recent_runs:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "type": run.analysis_type or run.run_type,
                            "status": run.status,
                            "processed": run.processed_count,
                            "failed": run.failed_count,
                            "started_at": run.started_at,
                            "finished_at": run.finished_at,
                            "summary": run.summary,
                        }
                        for run in recent_runs
                    ]
                ),
                use_container_width=True,
            )
        else:
            st.info("분석 실행 이력이 없습니다.")

    with right:
        st.subheader("개발자 Git 활동")
        if developer_stats:
            stats_df = pd.DataFrame(developer_stats)
            st.plotly_chart(
                px.bar(stats_df, x="developer_name", y="commit_count", color="role", text="commit_count"),
                use_container_width=True,
            )
        else:
            st.info("개발자 Git 통계가 없습니다.")


def render_dashboard_page() -> None:
    st.title("Dashboard")
    st.caption("프로젝트 계획, AI 분석, Git 활동을 한 화면에서 확인합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return

    _render_project_summary(context.project_id)

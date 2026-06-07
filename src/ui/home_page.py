import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Developer, GitCommit, Program, Project
from src.services.progress_service import get_ai_progress_summary


def _format_datetime(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def _collect_overview() -> dict:
    init_db()
    with SessionLocal() as db:
        projects = db.query(Project).order_by(Project.name).all()
        project_count = len(projects)
        developer_count = db.query(Developer).count()
        program_count = db.query(Program).count()
        commit_count = db.query(GitCommit).count()
        last_synced_at = max((project.last_synced_at for project in projects if project.last_synced_at), default=None)

        summaries = [get_ai_progress_summary(db, project.id) for project in projects]
        rows = [row for summary in summaries for row in summary.rows]
        ai_average = round(sum(row.ai_progress_rate for row in rows) / len(rows), 1) if rows else 0.0
        risk_count = sum(1 for row in rows if row.is_risk)
        done_count = sum(1 for row in rows if row.plan_progress_rate >= 100)
        in_progress_count = sum(1 for row in rows if 0 < row.plan_progress_rate < 100)

    return {
        "project_count": project_count,
        "developer_count": developer_count,
        "program_count": program_count,
        "commit_count": commit_count,
        "last_synced_at": last_synced_at,
        "ai_average": ai_average,
        "risk_count": risk_count,
        "done_count": done_count,
        "in_progress_count": in_progress_count,
        "program_rows": rows,
        "projects": projects,
    }


def _render_kpis(overview: dict) -> None:
    cols = st.columns(5)
    cols[0].metric("총 프로그램", overview["program_count"])
    cols[1].metric("완료 프로그램", overview["done_count"])
    cols[2].metric("진행중 프로그램", overview["in_progress_count"])
    cols[3].metric("리스크 프로그램", overview["risk_count"])
    cols[4].metric("총 커밋 수", overview["commit_count"])

    cols = st.columns(4)
    cols[0].metric("프로젝트 수", overview["project_count"])
    cols[1].metric("개발자 수", overview["developer_count"])
    cols[2].metric("전체 AI 진척도", f"{overview['ai_average']}%")
    cols[3].metric("마지막 Git 동기화", _format_datetime(overview["last_synced_at"]))


def _render_charts(overview: dict) -> None:
    rows = overview["program_rows"]
    if not rows:
        st.info("프로그램 데이터가 아직 없습니다. 프로젝트와 프로그램 목록을 먼저 등록해 주세요.")
        return

    df = pd.DataFrame(
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
            for row in rows
        ]
    )

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("상태별 프로그램 수")
        status_df = df.groupby("status", dropna=False).size().reset_index(name="count")
        st.plotly_chart(px.bar(status_df, x="status", y="count", text="count"), use_container_width=True)

    with chart2:
        st.subheader("계획 vs AI 진척도")
        avg_df = pd.DataFrame(
            [
                {"type": "계획 진척도", "value": round(float(df["plan_progress_rate"].mean()), 1)},
                {"type": "AI 진척도", "value": round(float(df["ai_progress_rate"].mean()), 1)},
            ]
        )
        st.plotly_chart(px.bar(avg_df, x="type", y="value", text="value", range_y=[0, 100]), use_container_width=True)

    st.subheader("상위 리스크 프로그램")
    risk_df = df[df["is_risk"]].sort_values("progress_gap", ascending=False).head(10)
    if risk_df.empty:
        st.success("현재 리스크 프로그램이 없습니다.")
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


def render_home_page() -> None:
    st.title("AI Commit Advisor")
    st.caption("프로젝트 계획, Git 변경 이력, AI 매핑 결과를 한 곳에서 보는 프로젝트 분석 콘솔입니다.")

    overview = _collect_overview()
    _render_kpis(overview)

    st.divider()
    _render_charts(overview)

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.orm import joinedload

from src.db.database import SessionLocal
from src.db.models import Developer, Program
from src.ui.project_context import require_project_context


DONE_STATUSES = {"완료", "done", "completed", "complete", "finished"}


def _is_done(status: str | None) -> bool:
    return (status or "").strip().lower() in DONE_STATUSES


def _program_rows(programs: list[Program]) -> list[dict]:
    rows = []
    for program in programs:
        developer_name = program.developer
        if program.assigned_developer and program.assigned_developer.developer_name:
            developer_name = program.assigned_developer.developer_name

        rows.append(
            {
                "program_id": program.program_id,
                "program_name": program.program_name,
                "module": program.module,
                "screen_name": program.screen_name,
                "developer_id": program.developer_id,
                "developer_name": developer_name or "미지정",
                "planned_start_date": program.planned_start_date,
                "planned_end_date": program.planned_end_date,
                "actual_start_date": program.actual_start_date,
                "actual_end_date": program.actual_end_date,
                "status": program.status or "미지정",
                "progress_rate": float(program.progress_rate or 0),
            }
        )
    return rows


def _render_empty_state() -> None:
    st.info("표시할 프로그램 데이터가 없습니다. 프로그램 목록 업로드 후 다시 확인해 주세요.")


def render_planning_dashboard_page() -> None:
    st.title("개발계획 대시보드")
    st.caption("programs 테이블에 저장된 프로그램 목록과 개발계획 현황을 조회합니다.")

    context = require_project_context("먼저 프로젝트를 등록하거나 프로그램 목록을 업로드해 주세요.")
    if context is None:
        return
    project_id = context.project_id

    with SessionLocal() as db:
        programs = (
            db.query(Program)
            .options(joinedload(Program.assigned_developer))
            .outerjoin(Developer, Program.developer_id == Developer.developer_id)
            .filter(Program.project_id == project_id)
            .order_by(Program.planned_start_date, Program.planned_end_date, Program.program_id)
            .all()
        )

    rows = _program_rows(programs)
    if not rows:
        _render_empty_state()
        return

    df = pd.DataFrame(rows)
    total_count = len(df)
    done_count = int(df["status"].apply(_is_done).sum())
    average_progress = round(float(df["progress_rate"].mean()), 1) if total_count else 0
    plan_completion_rate = round((done_count / total_count) * 100, 1) if total_count else 0

    overdue_df = df[
        df["planned_end_date"].notna()
        & (df["planned_end_date"] < date.today())
        & (~df["status"].apply(_is_done))
    ].copy()

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("전체 프로그램", total_count)
    metric2.metric("완료 프로그램", done_count)
    metric3.metric("전체 계획 대비 완료율", f"{plan_completion_rate}%")
    metric4.metric("평균 진행률", f"{average_progress}%")

    st.progress(min(max(average_progress / 100, 0), 1), text=f"전체 평균 진행률 {average_progress}%")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.subheader("상태별 프로그램 수")
        status_df = df.groupby("status", dropna=False).size().reset_index(name="count")
        st.plotly_chart(px.bar(status_df, x="status", y="count", text="count"), use_container_width=True)
        st.dataframe(status_df, use_container_width=True)

    with chart_right:
        st.subheader("개발자별 배정 프로그램 수")
        developer_df = df.groupby(["developer_id", "developer_name"], dropna=False).size().reset_index(name="count")
        st.plotly_chart(px.bar(developer_df, x="developer_name", y="count", text="count"), use_container_width=True)
        st.dataframe(developer_df, use_container_width=True)

    st.subheader("프로그램 목록")
    st.dataframe(
        df[
            [
                "program_id",
                "program_name",
                "module",
                "screen_name",
                "developer_name",
                "planned_start_date",
                "planned_end_date",
                "status",
                "progress_rate",
            ]
        ],
        use_container_width=True,
    )

    st.subheader("계획 종료일 경과 미완료 프로그램")
    if overdue_df.empty:
        st.success("계획 종료일이 지났지만 완료되지 않은 프로그램이 없습니다.")
    else:
        st.dataframe(
            overdue_df[
                [
                    "program_id",
                    "program_name",
                    "developer_name",
                    "planned_end_date",
                    "status",
                    "progress_rate",
                ]
            ],
            use_container_width=True,
        )

import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.progress_service import get_ai_progress_summary, get_program_commit_details


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _rows_to_dataframe(rows) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "program_db_id": row.program_db_id,
                "program_id": row.program_id,
                "program_name": row.program_name,
                "developer": row.developer,
                "planned_start_date": row.planned_start_date,
                "planned_end_date": row.planned_end_date,
                "status": row.status,
                "plan_progress_rate": row.plan_progress_rate,
                "ai_progress_rate": row.ai_progress_rate,
                "progress_gap": row.progress_gap,
                "implementation_status": row.best_implementation_status,
                "mapping_count": row.mapping_count,
                "related_commit_count": row.related_commit_count,
                "is_risk": row.is_risk,
                "risk_reasons": ", ".join(row.risk_reasons),
            }
            for row in rows
        ]
    )


def _render_summary(summary) -> None:
    cols = st.columns(4)
    cols[0].metric("계획 진척도 평균", f"{summary.plan_average}%")
    cols[1].metric("AI 진척도 평균", f"{summary.ai_average}%")
    cols[2].metric("진척도 차이", f"{summary.progress_gap_average}%")
    cols[3].metric("리스크 프로그램", summary.risk_count)

    gap_ratio = min(max(summary.progress_gap_average / 100, 0), 1)
    st.progress(gap_ratio, text=f"계획 대비 AI 진척도 차이 {summary.progress_gap_average}%")


def _render_risk_top10(df: pd.DataFrame) -> None:
    st.subheader("상위 위험 프로그램 TOP 10")
    risk_df = df[df["is_risk"]].copy()
    if risk_df.empty:
        st.success("리스크 조건에 해당하는 프로그램이 없습니다.")
        return

    risk_df = risk_df.sort_values(["progress_gap", "planned_end_date"], ascending=[False, True]).head(10)
    st.dataframe(
        risk_df[
            [
                "program_id",
                "program_name",
                "developer",
                "planned_end_date",
                "status",
                "plan_progress_rate",
                "ai_progress_rate",
                "progress_gap",
                "implementation_status",
                "related_commit_count",
                "risk_reasons",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def _render_charts(df: pd.DataFrame) -> None:
    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.subheader("상태별 프로그램 수")
        status_df = df.groupby("status", dropna=False).size().reset_index(name="count")
        st.plotly_chart(px.bar(status_df, x="status", y="count", text="count"), use_container_width=True)

    with chart_right:
        st.subheader("개발자별 AI 진척도")
        developer_df = (
            df.groupby("developer", dropna=False)["ai_progress_rate"]
            .mean()
            .round(1)
            .reset_index(name="avg_ai_progress_rate")
            .sort_values("avg_ai_progress_rate", ascending=False)
        )
        st.plotly_chart(
            px.bar(developer_df, x="developer", y="avg_ai_progress_rate", text="avg_ai_progress_rate", range_y=[0, 100]),
            use_container_width=True,
        )

    st.subheader("계획 진척도 vs AI 진척도")
    compare_df = df[["program_id", "program_name", "plan_progress_rate", "ai_progress_rate", "is_risk"]].copy()
    compare_df["label"] = compare_df["program_id"].fillna(compare_df["program_name"])
    melted = compare_df.melt(
        id_vars=["label", "program_name", "is_risk"],
        value_vars=["plan_progress_rate", "ai_progress_rate"],
        var_name="progress_type",
        value_name="progress_rate",
    )
    st.plotly_chart(
        px.bar(
            melted,
            x="label",
            y="progress_rate",
            color="progress_type",
            barmode="group",
            hover_data=["program_name", "is_risk"],
        ),
        use_container_width=True,
    )


def _render_program_table(df: pd.DataFrame) -> None:
    st.subheader("프로그램별 비교")
    col1, col2, col3 = st.columns(3)
    risk_only = col1.checkbox("리스크만 보기", value=False)
    developers = sorted(df["developer"].dropna().unique().tolist())
    selected_developers = col2.multiselect("개발자 필터", developers, default=developers)
    min_gap = col3.slider("최소 진척도 차이", min_value=-100, max_value=100, value=-100)

    filtered = df[df["developer"].isin(selected_developers) & (df["progress_gap"] >= min_gap)].copy()
    if risk_only:
        filtered = filtered[filtered["is_risk"]]

    st.dataframe(
        filtered[
            [
                "program_id",
                "program_name",
                "developer",
                "planned_start_date",
                "planned_end_date",
                "status",
                "plan_progress_rate",
                "ai_progress_rate",
                "progress_gap",
                "implementation_status",
                "mapping_count",
                "related_commit_count",
                "risk_reasons",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def _render_program_detail(df: pd.DataFrame) -> None:
    st.subheader("관련 커밋 상세")
    labels = {
        f"{row.program_id or '-'} | {row.program_name} | gap {row.progress_gap}% | {row.risk_reasons or '정상'}": row.program_db_id
        for row in df.itertuples()
    }
    selected_label = st.selectbox("프로그램 선택", list(labels.keys()))
    selected_program_id = labels[selected_label]
    selected = df[df["program_db_id"] == selected_program_id].iloc[0]

    cols = st.columns(4)
    cols[0].metric("계획 진척도", f"{selected.plan_progress_rate}%")
    cols[1].metric("AI 진척도", f"{selected.ai_progress_rate}%")
    cols[2].metric("차이", f"{selected.progress_gap}%")
    cols[3].metric("관련 커밋", int(selected.related_commit_count))

    st.write(
        {
            "program_id": selected.program_id,
            "program_name": selected.program_name,
            "developer": selected.developer,
            "planned_start_date": selected.planned_start_date,
            "planned_end_date": selected.planned_end_date,
            "status": selected.status,
            "implementation_status": selected.implementation_status,
            "risk_reasons": selected.risk_reasons,
        }
    )

    with SessionLocal() as db:
        details = get_program_commit_details(db, selected_program_id)

    if not details:
        st.info("이 프로그램에 저장된 매핑 결과가 없습니다.")
        return

    detail_df = pd.DataFrame([detail.__dict__ for detail in details])
    st.dataframe(
        detail_df[
            [
                "commit_hash",
                "message",
                "committed_at",
                "author",
                "is_related",
                "relevance_score",
                "implementation_status",
                "reason",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_ai_progress_page() -> None:
    st.title("AI Progress")
    st.caption("계획 진척도와 LLM 매핑 결과 기반 AI 진척도를 비교하고 리스크를 추적합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]

    with SessionLocal() as db:
        summary = get_ai_progress_summary(db, project_id)

    if not summary.rows:
        st.info("표시할 프로그램 데이터가 없습니다. 프로그램 목록을 먼저 업로드해 주세요.")
        return

    df = _rows_to_dataframe(summary.rows)
    _render_summary(summary)
    st.divider()
    _render_risk_top10(df)
    st.divider()
    _render_charts(df)
    st.divider()
    _render_program_table(df)
    st.divider()
    _render_program_detail(df)

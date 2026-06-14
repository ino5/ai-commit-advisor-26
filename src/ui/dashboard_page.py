import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.models import AnalysisRun, GitCommit, Project
from src.services.developer_service import get_developer_stats
from src.services.progress_service import get_ai_progress_summary
from src.services.resource_metrics_service import (
    get_resource_metric_snapshots,
    get_resource_metrics_summary,
    save_resource_metric_snapshot,
)
from src.ui.project_context import require_project_context


RESOURCE_VALUE_HELP = {
    "unresolved_risk": "아직 해결 처리되지 않은 리스크 건수입니다. PL이 우선 검토해야 할 리스크 backlog로 봅니다.",
    "high_risk": "미해결 리스크 중 영향도가 HIGH인 건수입니다. 일정과 품질에 직접 영향을 줄 수 있는 항목입니다.",
    "forecast_delay": "AI 진척도와 계획 종료일 기준으로 7일 이상 지연이 예상되는 프로그램 수입니다.",
    "review_time": (
        "완료된 AI 코드리뷰 1건당 약 0.5시간의 사전 리뷰 부담을 줄일 수 있다고 보는 참고 추정값입니다. "
        "실제 확정 절감 시간이 아니라 조기 검토 효과를 가늠하기 위한 지표입니다."
    ),
    "extra_mm": (
        "HIGH 리스크와 예상 지연 프로그램을 조기에 대응했을 때 줄일 수 있다고 보는 추가 투입 규모입니다. "
        "현재 계산 기준은 HIGH 리스크 1건=0.25MM, 예상 지연 프로그램 1건=0.15MM입니다."
    ),
    "trend_metrics": "저장된 snapshot을 기준으로 시간에 따른 변화만 비교합니다. 값의 단위가 다른 지표를 함께 고르면 추세 방향 위주로 해석하세요.",
}


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
        resource_summary = get_resource_metrics_summary(db, project_id)

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

    st.divider()
    _render_resource_metrics(project_id, resource_summary)


def _snapshot_df(project_id: int) -> pd.DataFrame:
    with SessionLocal() as db:
        snapshots = get_resource_metric_snapshots(db, project_id, limit=30)
    return pd.DataFrame([row.__dict__ for row in snapshots])


def _render_resource_metric_trends(project_id: int) -> None:
    trend_df = _snapshot_df(project_id)
    if trend_df.empty:
        st.info("저장된 자원관리 snapshot이 없습니다. 현재 지표를 저장하면 이후 추세를 비교할 수 있습니다.")
        return

    trend_df["captured_label"] = pd.to_datetime(trend_df["captured_at"]).dt.strftime("%m-%d %H:%M")
    metric_options = {
        "예상 지연 프로그램": "forecasted_delay_program_count",
        "HIGH 리스크": "high_risk_count",
        "미해결 리스크": "unresolved_risk_count",
        "평균 업무량 점수": "average_workload_score",
        "평균 난이도": "average_difficulty_score",
        "리뷰 시간 절감 가능성": "estimated_review_hours_saved",
        "추가 투입 예방 가능성": "estimated_extra_mm_avoidance",
    }
    selected_metrics = st.multiselect(
        "추세 지표",
        list(metric_options.keys()),
        default=["예상 지연 프로그램", "HIGH 리스크", "평균 업무량 점수"],
        help=RESOURCE_VALUE_HELP["trend_metrics"],
    )
    if selected_metrics:
        chart_df = trend_df[["captured_label", *[metric_options[label] for label in selected_metrics]]].melt(
            id_vars=["captured_label"],
            var_name="metric",
            value_name="value",
        )
        label_by_column = {column: label for label, column in metric_options.items()}
        chart_df["metric"] = chart_df["metric"].map(label_by_column)
        st.plotly_chart(
            px.line(chart_df, x="captured_label", y="value", color="metric", markers=True, title="자원관리 참고 지표 추세"),
            use_container_width=True,
        )

    st.dataframe(
        trend_df[
            [
                "captured_at",
                "snapshot_label",
                "program_count",
                "developer_count",
                "unresolved_risk_count",
                "high_risk_count",
                "forecasted_delay_program_count",
                "average_workload_score",
                "average_difficulty_score",
                "estimated_review_hours_saved",
                "estimated_extra_mm_avoidance",
            ]
        ].rename(
            columns={
                "captured_at": "저장 시각",
                "snapshot_label": "라벨",
                "program_count": "프로그램",
                "developer_count": "개발자",
                "unresolved_risk_count": "미해결 리스크",
                "high_risk_count": "HIGH 리스크",
                "forecasted_delay_program_count": "예상 지연 프로그램",
                "average_workload_score": "평균 업무량",
                "average_difficulty_score": "평균 난이도",
                "estimated_review_hours_saved": "리뷰 시간 절감 가능성(h)",
                "estimated_extra_mm_avoidance": "추가 투입 예방 가능성(MM)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_resource_metrics(project_id: int, resource_summary) -> None:
    st.subheader("자원관리 지표")
    st.caption(resource_summary.interpretation_note)

    value = resource_summary.business_value
    st.caption(value.assumption)
    value_cols = st.columns(5)
    value_cols[0].metric("미해결 리스크", value.unresolved_risk_count, help=RESOURCE_VALUE_HELP["unresolved_risk"])
    value_cols[1].metric("HIGH 리스크", value.high_risk_count, help=RESOURCE_VALUE_HELP["high_risk"])
    value_cols[2].metric(
        "예상 지연 프로그램",
        value.forecasted_delay_program_count,
        help=RESOURCE_VALUE_HELP["forecast_delay"],
    )
    value_cols[3].metric(
        "리뷰 시간 절감 가능성",
        f"{value.estimated_review_hours_saved}h",
        help=RESOURCE_VALUE_HELP["review_time"],
    )
    value_cols[4].metric(
        "추가 투입 예방 가능성",
        f"{value.estimated_extra_mm_avoidance}MM",
        help=RESOURCE_VALUE_HELP["extra_mm"],
    )

    with st.expander("현재 자원관리 지표 snapshot 저장", expanded=False):
        st.caption("저장된 snapshot은 추세 분석에서 시간순 비교에 사용됩니다. 자동 저장이 아니라 PL이 기준 시점을 남기는 수동 저장입니다.")
        snapshot_label = st.text_input("Snapshot 라벨", value="", placeholder="예: 주간 점검 1차", key="resource_snapshot_label")
        if st.button("현재 지표 저장", key="save_resource_snapshot"):
            with SessionLocal() as db:
                snapshot = save_resource_metric_snapshot(db, project_id, snapshot_label=snapshot_label)
            st.success(f"자원관리 snapshot을 저장했습니다. 저장 시각: {snapshot.captured_at.strftime('%Y-%m-%d %H:%M')}")

    developer_tab, program_tab, trend_tab = st.tabs(["개발자별 부하", "예상 지연/난이도", "추세 분석"])

    with developer_tab:
        if not resource_summary.developer_metrics:
            st.info("개발자별 자원관리 지표를 계산할 프로그램 데이터가 없습니다.")
        else:
            developer_df = pd.DataFrame([row.__dict__ for row in resource_summary.developer_metrics])
            chart_left, chart_right = st.columns(2)
            with chart_left:
                st.plotly_chart(
                    px.bar(
                        developer_df,
                        x="developer",
                        y="workload_score",
                        color="workload_label",
                        text="workload_score",
                        title="개발자별 업무량 점수",
                        range_y=[0, 100],
                    ),
                    use_container_width=True,
                )
            with chart_right:
                st.plotly_chart(
                    px.bar(
                        developer_df,
                        x="developer",
                        y="average_difficulty_score",
                        color="difficulty_label",
                        text="average_difficulty_score",
                        title="개발자별 평균 난이도",
                        range_y=[0, 100],
                    ),
                    use_container_width=True,
                )
            st.dataframe(
                developer_df[
                    [
                        "developer",
                        "assigned_program_count",
                        "unfinished_program_count",
                        "risk_program_count",
                        "average_ai_progress_rate",
                        "average_progress_gap",
                        "workload_score",
                        "workload_label",
                        "average_difficulty_score",
                        "difficulty_label",
                    ]
                ].rename(
                    columns={
                        "developer": "개발자",
                        "assigned_program_count": "담당 프로그램",
                        "unfinished_program_count": "미완료 프로그램",
                        "risk_program_count": "리스크 프로그램",
                        "average_ai_progress_rate": "평균 AI 진척도",
                        "average_progress_gap": "평균 진척도 차이",
                        "workload_score": "업무량 점수",
                        "workload_label": "업무량 등급",
                        "average_difficulty_score": "평균 난이도",
                        "difficulty_label": "난이도 등급",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    with program_tab:
        if not resource_summary.program_metrics:
            st.info("프로그램별 자원관리 지표가 없습니다.")
        else:
            program_df = pd.DataFrame([row.__dict__ for row in resource_summary.program_metrics])
            delay_df = program_df[program_df["forecast_level"].isin(["DELAY_EXPECTED", "AT_RISK"])].copy()
            if delay_df.empty:
                st.success("예상 종료일 기준 지연 주의 프로그램이 없습니다.")
            else:
                st.dataframe(
                    delay_df[
                        [
                            "program_id",
                            "program_name",
                            "developer",
                            "ai_progress_rate",
                            "progress_gap",
                            "forecast_end_date",
                            "forecast_delay_days",
                            "forecast_label",
                            "forecast_confidence_label",
                            "difficulty_score",
                            "difficulty_label",
                            "unresolved_risk_count",
                        ]
                    ].rename(
                        columns={
                            "program_id": "프로그램 ID",
                            "program_name": "프로그램명",
                            "developer": "담당자",
                            "ai_progress_rate": "AI 진척도",
                            "progress_gap": "진척도 차이",
                            "forecast_end_date": "예상 종료일",
                            "forecast_delay_days": "예상 지연일",
                            "forecast_label": "예상 상태",
                            "forecast_confidence_label": "신뢰도",
                            "difficulty_score": "난이도 점수",
                            "difficulty_label": "난이도",
                            "unresolved_risk_count": "미해결 리스크",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

    with trend_tab:
        _render_resource_metric_trends(project_id)


def render_dashboard_page() -> None:
    st.title("Dashboard")
    st.caption("프로젝트 계획, AI 분석, Git 활동을 한 화면에서 확인합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return

    _render_project_summary(context.project_id)

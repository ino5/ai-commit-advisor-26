import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Developer, GitCommit, Program, ProgramImplementationStatus, Project, RiskFinding
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
        mapping_analyzed_commit_count = db.query(GitCommit).filter(GitCommit.mapping_analyzed_at.isnot(None)).count()
        implementation_status_count = db.query(ProgramImplementationStatus).count()
        risk_finding_count = db.query(RiskFinding).count()
        unresolved_risk_count = db.query(RiskFinding).filter(RiskFinding.resolved_yn == "N").count()
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
        "mapping_analyzed_commit_count": mapping_analyzed_commit_count,
        "implementation_status_count": implementation_status_count,
        "risk_finding_count": risk_finding_count,
        "unresolved_risk_count": unresolved_risk_count,
        "last_synced_at": last_synced_at,
        "ai_average": ai_average,
        "risk_count": risk_count,
        "done_count": done_count,
        "in_progress_count": in_progress_count,
        "program_rows": rows,
        "projects": projects,
    }


def _status_label(ok: bool) -> str:
    return "확인됨" if ok else "작업 필요"


def _pipeline_status_rows(overview: dict) -> list[dict]:
    return [
        {
            "항목": "프로젝트",
            "상태": _status_label(overview["project_count"] > 0),
            "현재 값": f"{overview['project_count']}건",
            "메모": "기준 프로젝트",
        },
        {
            "항목": "프로그램",
            "상태": _status_label(overview["program_count"] > 0),
            "현재 값": f"{overview['program_count']}건",
            "메모": "계획 비교 대상",
        },
        {
            "항목": "개발자",
            "상태": _status_label(overview["developer_count"] > 0),
            "현재 값": f"{overview['developer_count']}명",
            "메모": "담당자 기준",
        },
        {
            "항목": "Git 커밋",
            "상태": _status_label(overview["commit_count"] > 0),
            "현재 값": f"{overview['commit_count']}건",
            "메모": "변경 이력",
        },
        {
            "항목": "매핑 완료",
            "상태": _status_label(
                overview["commit_count"] > 0
                and overview["mapping_analyzed_commit_count"] >= overview["commit_count"]
            ),
            "현재 값": f"{overview['mapping_analyzed_commit_count']} / {overview['commit_count']}건",
            "메모": "진척도 근거",
        },
        {
            "항목": "구현상태",
            "상태": _status_label(overview["implementation_status_count"] > 0),
            "현재 값": f"{overview['implementation_status_count']}건",
            "메모": "저장 결과",
        },
        {
            "항목": "미해결 리스크",
            "상태": "검토 필요" if overview["unresolved_risk_count"] > 0 else "확인됨",
            "현재 값": f"{overview['unresolved_risk_count']}건",
            "메모": "열린 항목",
        },
    ]


def _next_actions(overview: dict) -> list[str]:
    if overview["project_count"] == 0:
        return ["Project에서 프로젝트와 Git 경로 등록"]
    if overview["program_count"] == 0:
        return ["Program에서 프로그램 목록 등록"]
    if overview["commit_count"] == 0:
        return ["Git에서 커밋 동기화"]
    if overview["mapping_analyzed_commit_count"] < overview["commit_count"]:
        return ["Mapping에서 미분석 커밋 처리"]
    if overview["implementation_status_count"] == 0:
        return ["Program Detail에서 구현상태 갱신"]
    if overview["risk_finding_count"] == 0:
        return ["Risk Analysis 실행"]
    actions = ["AI Progress에서 계획 대비 차이 확인"]
    if overview["unresolved_risk_count"] > 0:
        actions.append("Risk Analysis에서 미해결 항목 정리")
    else:
        actions.append("다음 점검까지 계획 변경만 모니터링")
    return actions


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
    cols[2].metric("추정 진척도", f"{overview['ai_average']}%")
    cols[3].metric("마지막 Git 동기화", _format_datetime(overview["last_synced_at"]))


def _render_charts(overview: dict) -> None:
    rows = overview["program_rows"]
    if not rows:
        st.info("프로그램 데이터 없음")
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
        st.subheader("계획 vs 추정 진척도")
        avg_df = pd.DataFrame(
            [
                {"type": "계획 진척도", "value": round(float(df["plan_progress_rate"].mean()), 1)},
                {"type": "추정 진척도", "value": round(float(df["ai_progress_rate"].mean()), 1)},
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


def _render_pipeline_status(overview: dict) -> None:
    st.subheader("분석 상태")
    st.dataframe(pd.DataFrame(_pipeline_status_rows(overview)), use_container_width=True, hide_index=True)


def _render_next_actions(overview: dict) -> None:
    st.subheader("다음 작업")
    for action in _next_actions(overview):
        st.info(action)


def render_home_page() -> None:
    st.title("AI Commit Advisor")
    st.caption("계획, 커밋, 진척도, 리스크 현황")

    overview = _collect_overview()
    _render_pipeline_status(overview)
    _render_next_actions(overview)

    st.divider()
    _render_kpis(overview)

    st.divider()
    _render_charts(overview)

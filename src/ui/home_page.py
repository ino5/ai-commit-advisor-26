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
            "항목": "프로젝트 등록",
            "상태": _status_label(overview["project_count"] > 0),
            "현재 값": f"{overview['project_count']}건",
            "업무 의미": "분석 기준 프로젝트가 등록되어 있는지 확인합니다.",
        },
        {
            "항목": "프로그램 목록",
            "상태": _status_label(overview["program_count"] > 0),
            "현재 값": f"{overview['program_count']}건",
            "업무 의미": "개발계획과 진척도 비교 대상이 되는 프로그램 수입니다.",
        },
        {
            "항목": "개발자 정보",
            "상태": _status_label(overview["developer_count"] > 0),
            "현재 값": f"{overview['developer_count']}명",
            "업무 의미": "담당자별 영향도와 리스크 확인에 사용하는 기준 정보입니다.",
        },
        {
            "항목": "Git 커밋 수집",
            "상태": _status_label(overview["commit_count"] > 0),
            "현재 값": f"{overview['commit_count']}건",
            "업무 의미": "소스 변경 이력이 수집되어 분석 근거로 사용할 수 있는지 확인합니다.",
        },
        {
            "항목": "매핑 분석 완료 커밋",
            "상태": _status_label(
                overview["commit_count"] > 0
                and overview["mapping_analyzed_commit_count"] >= overview["commit_count"]
            ),
            "현재 값": f"{overview['mapping_analyzed_commit_count']} / {overview['commit_count']}건",
            "업무 의미": "커밋이 프로그램과 연결되어 AI 진척도 계산 근거로 쓰일 수 있는지 확인합니다.",
        },
        {
            "항목": "구현상태 분석 결과",
            "상태": _status_label(overview["implementation_status_count"] > 0),
            "현재 값": f"{overview['implementation_status_count']}건",
            "업무 의미": "프로그램 단위 구현상태 추정 결과가 저장되어 있는지 확인합니다.",
        },
        {
            "항목": "미해결 리스크",
            "상태": "검토 필요" if overview["unresolved_risk_count"] > 0 else "확인됨",
            "현재 값": f"{overview['unresolved_risk_count']}건",
            "업무 의미": "Risk Analysis에서 아직 resolved 처리되지 않은 리스크입니다.",
        },
    ]


def _next_actions(overview: dict) -> list[str]:
    if overview["project_count"] == 0:
        return ["Project 화면에서 분석 대상 프로젝트와 Git 저장소 경로를 등록하세요."]
    if overview["program_count"] == 0:
        return ["Program 또는 프로그램 업로드 화면에서 프로그램 목록을 등록하세요."]
    if overview["commit_count"] == 0:
        return ["Git 화면에서 저장소 커밋을 동기화해 변경 이력을 수집하세요."]
    if overview["mapping_analyzed_commit_count"] < overview["commit_count"]:
        return ["Mapping 화면에서 미분석 커밋의 프로그램 매핑 분석을 실행하세요."]
    if overview["implementation_status_count"] == 0:
        return ["Program Detail에서 구현상태 재분석을 실행하거나 Mapping 결과를 먼저 검증하세요."]
    if overview["risk_finding_count"] == 0:
        return ["Risk Analysis 화면에서 최신 매핑 결과 기준 리스크 분석을 실행하고 결과를 확인하세요."]
    actions = ["AI Progress에서 계획 진척도와 AI 진척도 차이를 확인하세요."]
    if overview["unresolved_risk_count"] > 0:
        actions.append("Risk Analysis에서 미해결 리스크를 검토하고 조치 상태를 갱신하세요.")
    else:
        actions.append("현재 미해결 리스크가 없으면 다음 분석 주기까지 계획 대비 변동 사항을 모니터링하세요.")
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


def _render_pipeline_status(overview: dict) -> None:
    st.subheader("분석 파이프라인 상태")
    st.caption("업무 흐름별 데이터 준비 상태와 AI 분석 근거가 쌓인 정도를 확인합니다.")
    st.dataframe(pd.DataFrame(_pipeline_status_rows(overview)), use_container_width=True, hide_index=True)


def _render_next_actions(overview: dict) -> None:
    st.subheader("다음 권장 작업")
    st.caption("현재 분석 상태를 기준으로 우선 확인할 작업입니다.")
    for action in _next_actions(overview):
        st.info(action)


def render_home_page() -> None:
    st.title("AI Commit Advisor")
    st.caption(
        "개발계획, Git 변경 이력, AI 매핑 결과, 리스크를 통합해 보는 분석 콘솔입니다. "
        "AI 분석 결과는 근거 데이터와 함께 검증하는 보조 지표로 활용하세요."
    )

    overview = _collect_overview()
    _render_pipeline_status(overview)
    _render_next_actions(overview)

    st.divider()
    _render_kpis(overview)

    st.divider()
    _render_charts(overview)

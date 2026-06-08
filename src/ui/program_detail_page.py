import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.program_analysis_service import (
    get_commit_file_details,
    get_program_detail_analysis,
    list_program_options,
)
from src.services.program_implementation_analyzer import (
    ProgramImplementationAnalyzer,
    get_program_implementation_status,
)
from src.services.risk_service import get_unresolved_findings


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _format_date(value) -> str:
    return value.strftime("%Y-%m-%d") if value else "-"


def _format_datetime(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def _option_dataframe(options) -> pd.DataFrame:
    return pd.DataFrame([option.__dict__ for option in options])


def _render_program_selector(project_id: int) -> int | None:
    with SessionLocal() as db:
        options = list_program_options(db, project_id)

    if not options:
        st.info("프로그램 데이터가 없습니다. 프로그램 목록을 먼저 업로드해 주세요.")
        return None

    df = _option_dataframe(options)
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    keyword = filter_col1.text_input("program_name 검색", placeholder="프로그램명 일부를 입력하세요.")
    statuses = sorted(df["status"].dropna().unique().tolist())
    developers = sorted(df["developer"].dropna().unique().tolist())
    selected_statuses = filter_col2.multiselect("상태 필터", statuses, default=statuses)
    selected_developers = filter_col3.multiselect("담당자 필터", developers, default=developers)

    filtered = df[df["status"].isin(selected_statuses) & df["developer"].isin(selected_developers)].copy()
    if keyword:
        filtered = filtered[filtered["program_name"].str.contains(keyword, case=False, na=False)]

    if filtered.empty:
        st.warning("필터 조건에 맞는 프로그램이 없습니다.")
        return None

    labels = {
        f"{row.program_id or '-'} | {row.program_name} | {row.developer} | {row.status}": int(row.program_db_id)
        for row in filtered.itertuples()
    }
    selected_label = st.selectbox("프로그램 선택", list(labels.keys()))

    st.dataframe(
        filtered[["program_id", "program_name", "module", "screen_name", "developer", "status"]],
        use_container_width=True,
        hide_index=True,
    )
    return labels[selected_label]


def _render_basic_info(analysis) -> None:
    program = analysis.program
    st.subheader("프로그램 기본 정보")
    info_col, desc_col = st.columns([2, 1])
    with info_col:
        st.table(
            {
                "항목": [
                    "program_id",
                    "program_name",
                    "module",
                    "screen_name",
                    "담당 개발자",
                    "planned_start_date",
                    "planned_end_date",
                    "status",
                    "progress_rate",
                ],
                "값": [
                    program.program_id or "-",
                    program.program_name,
                    program.module or "-",
                    program.screen_name or "-",
                    analysis.developer,
                    _format_date(program.planned_start_date),
                    _format_date(program.planned_end_date),
                    program.status or "미지정",
                    f"{float(program.progress_rate or 0):.1f}%",
                ],
            }
        )
    with desc_col:
        st.markdown("**description**")
        st.write(program.description or "-")


def _render_kpis(analysis) -> None:
    st.subheader("KPI")
    cols = st.columns(5)
    cols[0].metric("AI 진척도", f"{analysis.ai_progress_rate:.1f}%")
    cols[1].metric("관련 커밋 수", analysis.related_commit_count)
    cols[2].metric("구현됨", analysis.implemented_count)
    cols[3].metric("일부구현", analysis.partial_count)
    cols[4].metric("판단불가", analysis.unknown_count)

    activity_cols = st.columns(4)
    activity_cols[0].metric("첫 커밋", _format_date(analysis.activity.first_commit_at))
    activity_cols[1].metric("마지막 커밋", _format_date(analysis.activity.last_commit_at))
    activity_cols[2].metric("최근 30일 커밋", analysis.activity.recent_30d_commit_count)
    activity_cols[3].metric("최근 90일 커밋", analysis.activity.recent_90d_commit_count)

    risk_message = ", ".join(analysis.risk.risk_reasons) if analysis.risk.risk_reasons else "리스크 조건 없음"
    if analysis.risk.risk_level == "HIGH":
        st.error(f"Risk Level: HIGH - {risk_message}")
    elif analysis.risk.risk_level == "MEDIUM":
        st.warning(f"Risk Level: MEDIUM - {risk_message}")
    else:
        st.success(f"Risk Level: LOW - {risk_message}")


def _render_saved_risks(project_id: int, program_db_id: int) -> None:
    st.subheader("저장된 리스크")
    with SessionLocal() as db:
        findings = get_unresolved_findings(db, project_id, program_id=program_db_id)

    if not findings:
        st.success("저장된 unresolved 리스크가 없습니다.")
        return

    rows = [
        {
            "risk_level": finding.risk_level,
            "risk_type": finding.risk_type,
            "title": finding.title,
            "description": finding.description,
            "detected_at": finding.detected_at,
        }
        for finding in findings
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _format_json_list(value) -> str:
    if not value:
        return "-"
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    return str(value)


def _render_implementation_status(program_db_id: int) -> None:
    st.subheader("구현상태 분석")

    button_col, hint_col = st.columns([1, 2])
    with button_col:
        run_analysis = st.button("구현상태 재분석", type="secondary")
    with hint_col:
        st.caption("프로그램-커밋 매핑 해시 목록이 이전 분석과 같으면 재분석을 건너뜁니다.")

    if run_analysis:
        with SessionLocal() as db:
            analyzer = ProgramImplementationAnalyzer()
            with st.spinner("선택한 프로그램의 구현상태를 분석 중입니다."):
                status_result, analyzed = analyzer.analyze_program(db, program_db_id, skip_unchanged=True)
                db.commit()
        if analyzed:
            st.success("구현상태 분석을 저장했습니다.")
        else:
            st.info("매핑된 커밋 목록이 변경되지 않아 기존 분석 결과를 사용합니다.")

    with SessionLocal() as db:
        status_result = get_program_implementation_status(db, program_db_id)

    if status_result is None:
        st.info("저장된 구현상태 분석 결과가 없습니다. 매핑 분석을 실행하거나 재분석 버튼을 눌러 생성하세요.")
        return

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("구현상태", status_result.status)
    metric_col2.metric("분석 일시", _format_datetime(status_result.analyzed_at))

    st.markdown("**상태 요약**")
    st.write(status_result.summary or "-")

    feature_col1, feature_col2 = st.columns(2)
    with feature_col1:
        st.markdown("**완료된 것으로 보이는 기능**")
        st.markdown(_format_json_list(status_result.completed_features))
    with feature_col2:
        st.markdown("**미완료 또는 불확실한 기능**")
        st.markdown(_format_json_list(status_result.incomplete_features))

    evidence = status_result.evidence_commits or []
    st.markdown("**주요 근거 커밋**")
    if not evidence:
        st.write("-")
        return
    st.dataframe(pd.DataFrame(evidence), use_container_width=True, hide_index=True)


def _commit_dataframe(analysis) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "commit_hash": row.commit_hash,
                "commit_message": row.commit_message,
                "author_name": row.author_name,
                "committed_at": row.committed_at,
                "relevance_score": row.relevance_score,
                "implementation_status": row.implementation_status,
                "reason": row.reason,
            }
            for row in analysis.commit_rows
        ]
    )


def _render_ai_and_developer_analysis(analysis) -> None:
    st.subheader("AI 분석 결과 / 개발자 분석")
    left, right = st.columns(2)

    status_df = pd.DataFrame(
        [
            {"implementation_status": "구현됨", "count": analysis.implemented_count},
            {"implementation_status": "일부구현", "count": analysis.partial_count},
            {"implementation_status": "판단불가", "count": analysis.unknown_count},
        ]
    )
    with left:
        st.plotly_chart(
            px.bar(status_df, x="implementation_status", y="count", text="count", title="구현 상태 분포"),
            use_container_width=True,
        )

    contribution_df = pd.DataFrame([item.__dict__ for item in analysis.developer_contributions])
    with right:
        if contribution_df.empty:
            st.info("관련 개발자 기여 데이터가 없습니다.")
        else:
            st.metric("관련 개발자 수", len(contribution_df))
            st.plotly_chart(
                px.bar(
                    contribution_df,
                    x="developer",
                    y="commit_count",
                    text="contribution_ratio",
                    title="개발자별 커밋 수 / 기여 비율",
                    hover_data=["contribution_ratio"],
                ),
                use_container_width=True,
            )


def _render_commits(project_id: int, program_db_id: int, analysis) -> None:
    st.subheader("관련 커밋 목록")
    commit_df = _commit_dataframe(analysis)
    if commit_df.empty:
        st.info("관련 커밋 매핑 결과가 없습니다.")
        return

    filter_col1, filter_col2 = st.columns(2)
    statuses = sorted(commit_df["implementation_status"].dropna().unique().tolist())
    authors = sorted(commit_df["author_name"].dropna().unique().tolist())
    selected_statuses = filter_col1.multiselect("구현상태 필터", statuses, default=statuses)
    selected_authors = filter_col2.multiselect("개발자 필터", authors, default=authors)
    filtered = commit_df[
        commit_df["implementation_status"].isin(selected_statuses) & commit_df["author_name"].isin(selected_authors)
    ].sort_values("relevance_score", ascending=False)

    st.dataframe(
        filtered[
            [
                "commit_hash",
                "commit_message",
                "author_name",
                "committed_at",
                "relevance_score",
                "implementation_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    if filtered.empty:
        st.warning("필터 조건에 맞는 커밋이 없습니다.")
        return

    st.subheader("커밋 상세 보기")
    labels = {
        f"{row.commit_hash} | {row.implementation_status} | {row.relevance_score:.1f} | {row.commit_message[:80]}": row.commit_hash
        for row in filtered.itertuples()
    }
    selected_label = st.selectbox("커밋 선택", list(labels.keys()))
    selected_hash = labels[selected_label]

    with SessionLocal() as db:
        message, files, reason = get_commit_file_details(db, program_db_id, selected_hash)

    st.markdown("**commit message**")
    st.write(message or "-")
    st.markdown("**LLM 판단 근거**")
    st.write(reason or "-")

    st.markdown("**changed files / diff snippet**")
    if not files:
        st.info("변경 파일 정보가 없습니다.")
        return

    for file in files:
        with st.expander(f"{file.change_type or '-'} | {file.file_path}", expanded=False):
            st.code(file.diff_snippet or "diff 없음", language="diff")


def render_program_detail_page() -> None:
    st.title("Program Detail")
    st.caption("특정 프로그램의 계획, AI 매핑 결과, 관련 커밋, 개발자 기여와 리스크를 한 화면에서 확인합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_project = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_project]

    st.divider()
    program_db_id = _render_program_selector(project_id)
    if program_db_id is None:
        return

    with SessionLocal() as db:
        analysis = get_program_detail_analysis(db, program_db_id)

    st.divider()
    top_left, top_right = st.columns([1, 1])
    with top_left:
        _render_basic_info(analysis)
    with top_right:
        _render_kpis(analysis)

    _render_saved_risks(project_id, program_db_id)
    st.divider()
    _render_implementation_status(program_db_id)
    st.divider()
    _render_ai_and_developer_analysis(analysis)
    st.divider()
    _render_commits(project_id, program_db_id, analysis)

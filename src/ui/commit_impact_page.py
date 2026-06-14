import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import date, timedelta

from src.db.database import SessionLocal
from src.services.commit_impact_service import get_commit_impact_analysis, list_commit_options
from src.ui.display_utils import format_datetime, key_value_dataframe
from src.ui.project_context import require_project_context


def _select_commit(project_id: int) -> int | None:
    st.subheader("커밋 선택")
    col1, col2, col3 = st.columns([2, 1.5, 1])
    message_keyword = col1.text_input("commit message 검색")
    author_keyword = col2.text_input("author 검색")
    use_date_filter = col3.checkbox("날짜 필터 사용", value=False)
    start_date = None
    end_date = None
    if use_date_filter:
        date_col1, date_col2 = st.columns(2)
        start_date = date_col1.date_input("시작일", value=date.today() - timedelta(days=90))
        end_date = date_col2.date_input("종료일", value=date.today())

    with SessionLocal() as db:
        commits = list_commit_options(
            db,
            project_id=project_id,
            message_keyword=message_keyword or None,
            author_keyword=author_keyword or None,
            start_date=start_date,
            end_date=end_date,
        )

    if not commits:
        st.info("조건에 맞는 커밋이 없습니다.")
        return None

    rows = pd.DataFrame(
        [
            {
                "commit_db_id": commit.commit_db_id,
                "commit_hash": commit.commit_hash[:12],
                "message": commit.message,
                "author_name": commit.author_name,
                "committed_at": commit.committed_at,
            }
            for commit in commits
        ]
    )
    labels = {
        f"{row.commit_hash} | {row.author_name} | {format_datetime(row.committed_at)} | {row.message[:90]}": int(row.commit_db_id)
        for row in rows.itertuples()
    }
    selected_label = st.selectbox("분석할 커밋", list(labels.keys()))
    st.dataframe(rows[["commit_hash", "message", "author_name", "committed_at"]], use_container_width=True, hide_index=True)
    return labels[selected_label]


def _render_kpis(analysis) -> None:
    st.subheader("영향도 대시보드")
    cols = st.columns(4)
    cols[0].metric("영향 프로그램 수", len(analysis.programs))
    cols[1].metric("영향 개발자 수", len(analysis.developers))
    cols[2].metric("영향 파일 수", len(analysis.files))
    cols[3].metric("영향도 점수", analysis.impact_score)

    message = ", ".join(analysis.impact_reasons)
    if analysis.impact_score == "HIGH":
        st.error(f"HIGH Impact - {message}")
    elif analysis.impact_score == "MEDIUM":
        st.warning(f"MEDIUM Impact - {message}")
    else:
        st.success(f"LOW Impact - {message}")


def _render_commit_summary(analysis) -> None:
    commit = analysis.commit
    st.subheader("커밋 요약")
    st.table(
        key_value_dataframe(
            [
                ("커밋", commit.commit_hash),
                ("메시지", commit.message),
                ("작성자", commit.author_name or commit.author),
                ("작성자 이메일", commit.author_email),
                ("커밋 시각", format_datetime(commit.committed_at)),
                ("Merge commit", "예" if commit.is_merge_commit else "아니오"),
            ]
        )
    )


def _render_programs(analysis) -> None:
    st.subheader("영향 프로그램 분석")
    if not analysis.programs:
        st.info("이 커밋과 연결된 program_commit_mappings 결과가 없습니다.")
        return

    df = pd.DataFrame([program.__dict__ for program in analysis.programs])
    st.dataframe(
        df[
            [
                "program_id",
                "program_name",
                "module",
                "screen_name",
                "developer",
                "relevance_score",
                "implementation_status",
                "reason",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def _render_files(analysis) -> None:
    st.subheader("영향 파일 분석")
    if not analysis.files:
        st.info("변경 파일 정보가 없습니다.")
        return

    file_df = pd.DataFrame(
        [{"file_path": file.file_path, "change_type": file.change_type, "diff_snippet": file.diff_snippet} for file in analysis.files]
    )
    st.dataframe(file_df[["file_path", "change_type"]], use_container_width=True, hide_index=True)

    selected_file = st.selectbox("diff snippet 보기", file_df["file_path"].tolist())
    selected = file_df[file_df["file_path"] == selected_file].iloc[0]
    st.code(selected.diff_snippet or "diff 없음", language="diff")


def _render_developers(analysis) -> None:
    st.subheader("영향 개발자 분석")
    if not analysis.developers:
        st.info("관련 개발자 정보가 없습니다.")
        return

    df = pd.DataFrame([developer.__dict__ for developer in analysis.developers])
    left, right = st.columns([1, 1])
    with left:
        st.dataframe(df, use_container_width=True, hide_index=True)
    with right:
        st.plotly_chart(
            px.bar(
                df,
                x="developer",
                y="commit_count",
                text="contribution_ratio",
                hover_data=["role", "contribution_ratio"],
                title="개발자별 영향 기여도",
            ),
            use_container_width=True,
        )


def render_commit_impact_page() -> None:
    st.title("Commit Impact")
    st.caption("특정 Git 커밋이 어떤 프로그램, 개발자, 모듈, 파일에 영향을 주는지 기존 매핑 결과로 분석합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return
    project_id = context.project_id

    commit_db_id = _select_commit(project_id)
    if commit_db_id is None:
        return

    with SessionLocal() as db:
        analysis = get_commit_impact_analysis(db, commit_db_id)

    st.divider()
    _render_kpis(analysis)
    _render_commit_summary(analysis)
    st.divider()
    top_left, top_right = st.columns([1.2, 1])
    with top_left:
        _render_programs(analysis)
    with top_right:
        _render_developers(analysis)
    st.divider()
    _render_files(analysis)

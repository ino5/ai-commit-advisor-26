from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.services.git_history_service import (
    get_commit_full_diff,
    get_git_history_detail,
    list_git_history_commits,
)
from src.ui.display_utils import format_datetime, key_value_dataframe
from src.ui.project_context import require_project_context


def _render_history_charts(rows: pd.DataFrame) -> None:
    if rows.empty or "committed_at" not in rows:
        return

    chart_rows = rows.copy()
    chart_rows["commit_date"] = pd.to_datetime(chart_rows["committed_at"], errors="coerce").dt.date
    chart_rows = chart_rows.dropna(subset=["commit_date"])
    if chart_rows.empty:
        return

    left, right = st.columns([1, 1])
    with left:
        daily = chart_rows.groupby("commit_date", as_index=False).size()
        st.plotly_chart(
            px.bar(daily, x="commit_date", y="size", title="일자별 커밋 수", labels={"size": "commit"}),
            use_container_width=True,
        )
    with right:
        author = chart_rows.groupby("author_name", as_index=False).size().sort_values("size", ascending=False)
        st.plotly_chart(
            px.bar(author, x="author_name", y="size", title="작성자별 커밋 수", labels={"size": "commit"}),
            use_container_width=True,
        )


def _select_commit(project_id: int) -> int | None:
    st.subheader("커밋 목록")
    col1, col2, col3 = st.columns([1.5, 1.2, 1.2])
    message_keyword = col1.text_input("메시지 검색", key="git_history_message")
    author_keyword = col2.text_input("작성자 검색", key="git_history_author")
    file_keyword = col3.text_input("파일 경로 검색", key="git_history_file")

    option_col1, option_col2, option_col3 = st.columns([1, 1, 1])
    use_date_filter = option_col1.checkbox("날짜 필터", value=False, key="git_history_use_date")
    limit = option_col2.number_input("최대 표시", min_value=20, max_value=1000, value=300, step=20)
    include_full_hash = option_col3.checkbox("전체 hash 표시", value=False)

    start_date = None
    end_date = None
    if use_date_filter:
        date_col1, date_col2 = st.columns(2)
        start_date = date_col1.date_input("시작일", value=date.today() - timedelta(days=90))
        end_date = date_col2.date_input("종료일", value=date.today())

    with SessionLocal() as db:
        commits = list_git_history_commits(
            db,
            project_id=project_id,
            message_keyword=message_keyword or None,
            author_keyword=author_keyword or None,
            file_keyword=file_keyword or None,
            start_date=start_date,
            end_date=end_date,
            limit=int(limit),
        )

    if not commits:
        st.info("조건에 맞는 커밋이 없습니다.")
        return None

    rows = pd.DataFrame(
        [
            {
                "commit_db_id": commit.commit_db_id,
                "commit_hash": commit.commit_hash if include_full_hash else commit.commit_hash[:12],
                "message": commit.message,
                "author_name": commit.author_name,
                "author_email": commit.author_email,
                "committed_at": commit.committed_at,
                "file_count": commit.file_count,
                "merge": commit.is_merge_commit,
            }
            for commit in commits
        ]
    )

    metric_cols = st.columns(3)
    metric_cols[0].metric("조회 커밋", len(rows))
    metric_cols[1].metric("변경 파일 합계", int(rows["file_count"].sum()))
    metric_cols[2].metric("작성자 수", rows["author_name"].nunique())

    _render_history_charts(rows)

    display_cols = ["commit_hash", "message", "author_name", "committed_at", "file_count", "merge"]
    st.dataframe(rows[display_cols], use_container_width=True, hide_index=True)

    labels = {
        f"{row.commit_hash} | {row.author_name} | {format_datetime(row.committed_at)} | {str(row.message)[:90]}": int(
            row.commit_db_id
        )
        for row in rows.itertuples()
    }
    selected_label = st.selectbox("상세 조회할 커밋", list(labels.keys()))
    return labels[selected_label]


def _render_commit_detail(project_id: int, commit_db_id: int) -> None:
    with SessionLocal() as db:
        detail = get_git_history_detail(db, project_id=project_id, commit_db_id=commit_db_id)

    if detail is None:
        st.error("선택한 커밋을 찾을 수 없습니다.")
        return

    commit = detail.commit
    st.subheader("커밋 상세")
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

    if not detail.files:
        st.info("이 커밋에는 저장된 변경 파일 정보가 없습니다. merge commit이거나 수집 당시 diff가 저장되지 않았을 수 있습니다.")
    else:
        file_rows = pd.DataFrame(
            [
                {
                    "file_path": file.file_path,
                    "change_type": file.change_type,
                    "diff_text": file.diff_text or "",
                }
                for file in detail.files
            ]
        )
        st.subheader("변경 파일")
        st.dataframe(file_rows[["file_path", "change_type"]], use_container_width=True, hide_index=True)

        selected_file = st.selectbox("저장된 diff preview", file_rows["file_path"].tolist())
        selected = file_rows[file_rows["file_path"] == selected_file].iloc[0]
        st.code(selected.diff_text or "저장된 diff가 없습니다.", language="diff")

    st.subheader("전체 diff")
    if st.checkbox("앱 서버 Git 저장소에서 전체 git show diff 조회", value=False):
        with SessionLocal() as db:
            full_diff = get_commit_full_diff(db, project_id=project_id, commit_db_id=commit_db_id)
        if full_diff.errors:
            for error in full_diff.errors:
                st.error(error)
        else:
            if full_diff.truncated:
                st.warning("diff가 커서 앞부분만 표시합니다.")
            st.code(full_diff.diff_text or "diff 없음", language="diff")


def render_git_history_page() -> None:
    st.title("Git History")
    st.caption("현재 프로젝트의 Git 커밋 이력, 변경 파일, 저장된 diff, 앱 서버 저장소의 전체 diff를 확인합니다.")

    context = require_project_context("먼저 프로젝트/Git 설정에서 프로젝트와 앱 서버 Git 저장소 경로를 등록해 주세요.")
    if context is None:
        return

    commit_db_id = _select_commit(context.project_id)
    if commit_db_id is None:
        return

    st.divider()
    _render_commit_detail(context.project_id, commit_db_id)

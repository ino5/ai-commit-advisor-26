from __future__ import annotations

import streamlit as st

from src.db.models import Project
from src.services.git_repository_status_service import GitRepositoryStatus, get_repository_status


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def _sync_label(status: GitRepositoryStatus) -> str:
    if status.db_matches_head is True:
        return "DB sync 최신"
    if status.db_matches_head is False:
        return "DB sync 필요"
    return "DB sync 확인 불가"


def render_repository_status(project: Project, *, compact: bool = False) -> GitRepositoryStatus:
    status = get_repository_status(project)

    st.subheader("앱 서버 저장소 상태")
    if status.errors:
        for error in status.errors:
            st.warning(error)

    if compact:
        col1, col2, col3 = st.columns(3)
        col1.metric("Repo HEAD", _short_hash(status.head_hash))
        col2.metric("Branch", status.branch or "-")
        col3.metric("DB sync", _sync_label(status))
        return status

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Repo HEAD", _short_hash(status.head_hash))
    col2.metric("DB sync commit", _short_hash(status.db_last_synced_commit_hash))
    col3.metric("Branch", status.branch or "-")
    col4.metric("DB sync", _sync_label(status))

    detail_col1, detail_col2, detail_col3 = st.columns(3)
    detail_col1.metric("Working tree", "변경 있음" if status.has_local_changes else "깨끗함")
    detail_col2.metric("변경 파일", status.dirty_file_count)
    if status.upstream:
        detail_col3.metric("Upstream", status.upstream)
    else:
        detail_col3.metric("Upstream", "-")

    if status.upstream and status.ahead_count is not None and status.behind_count is not None:
        ahead_col, behind_col = st.columns(2)
        ahead_col.metric("Ahead", status.ahead_count)
        behind_col.metric("Behind", status.behind_count)

    if status.resolved_path and status.resolved_path != status.configured_path:
        st.caption(f"실제 접근 경로: {status.resolved_path}")
    if status.storage_root:
        st.caption(f"허용된 저장소 루트: {status.storage_root}")

    if status.db_matches_head is False and status.head_hash:
        st.info("서버 저장소 HEAD와 DB 마지막 동기화 커밋이 다릅니다. 저장소 갱신 후 Git 동기화를 실행해 DB를 최신화하세요.")
    if status.has_local_changes:
        st.warning("서버 저장소 working tree에 local 변경이 있습니다. 분석용 서버 clone에는 local 변경을 남기지 않는 운영을 권장합니다.")

    return status

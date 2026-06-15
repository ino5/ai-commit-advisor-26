import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.models import Project
from src.services.git_followup_service import (
    GROUP_LATER,
    GROUP_RECOMMENDED,
    GitFollowUpStep,
    build_git_sync_follow_up,
)
from src.services.git_service import is_git_repository, sync_git_repository
from src.ui.git_status_panel import render_repository_status
from src.ui.project_context import project_scoped_key, require_project_context


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def _render_sync_result(result) -> None:
    if result.errors:
        for error in result.errors:
            st.error(error)
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("신규 저장 커밋", result.saved_commit_count)
    col2.metric("신규 저장 변경 파일", result.saved_file_count)
    col3.metric("건너뛴 중복 커밋", result.skipped_duplicate_count)

    st.write("최근 동기화 대상 커밋:", result.latest_commit_hash or "-")
    if result.recent_commits:
        st.subheader("최근 수집 커밋")
        st.dataframe(pd.DataFrame(result.recent_commits), use_container_width=True)
    else:
        st.info("이번 실행에서 새로 저장된 커밋이 없습니다.")


def _follow_up_rows(steps: list[GitFollowUpStep]) -> list[dict]:
    return [
        {
            "순서": step.order,
            "작업": step.title,
            "상태": step.status,
            "현재 값": step.current_value,
            "예상 소요": step.estimated_runtime,
            "부하/비용 주의": step.load_note,
            "다음 조치": step.next_action,
        }
        for step in steps
    ]


def _render_follow_up_actions(project_id: int, steps: list[GitFollowUpStep], key_suffix: str) -> None:
    action_steps = [step for step in steps if step.restartable]
    if not action_steps:
        return

    cols = st.columns(min(3, len(action_steps)))
    for index, step in enumerate(action_steps):
        col = cols[index % len(cols)]
        if col.button(
            f"{step.target_page}로 이동",
            key=project_scoped_key(project_id, f"git_followup_{key_suffix}_{step.step_id}"),
            use_container_width=True,
        ):
            st.session_state["sidebar_navigation"] = {"group": step.target_group, "page": step.target_page}
            st.rerun()


def _render_follow_up_group(
    project_id: int,
    title: str,
    steps: list[GitFollowUpStep],
    key_suffix: str,
    *,
    detail_expander: bool = True,
) -> None:
    st.markdown(f"#### {title}")
    if not steps:
        st.success("현재 기준으로 필요한 항목이 없습니다.")
        return

    for step in steps:
        st.markdown(f"**{step.order}. {step.title}** · `{step.status}`")
        st.caption(f"{step.current_value} · 예상 소요: {step.estimated_runtime} · {step.load_note}")
        st.caption(step.next_action)

    if detail_expander:
        with st.expander("상세 표", expanded=False):
            st.dataframe(pd.DataFrame(_follow_up_rows(steps)), hide_index=True, use_container_width=True)
    else:
        st.caption("상세 표")
        st.dataframe(pd.DataFrame(_follow_up_rows(steps)), hide_index=True, use_container_width=True)
    _render_follow_up_actions(project_id, steps, key_suffix)


def _render_follow_up_panel(db, project_id: int, sync_result=None) -> None:
    summary = build_git_sync_follow_up(db, project_id, sync_result)
    st.divider()
    st.subheader("동기화 후 다음 작업")
    st.caption(
        "Git Sync는 commit/diff를 수집하는 단계입니다. 아래 순서로 현재 소스 근거, 검색 준비, Mapping, Risk, Knowledge Graph를 맞추면 AI 화면이 최신 근거를 사용합니다."
    )

    cols = st.columns(4)
    cols[0].metric("이번 새 커밋", summary.synced_commit_count)
    cols[1].metric("이번 변경 파일", summary.synced_file_count)
    cols[2].metric("DB sync", "최신" if summary.db_matches_head else "확인 필요")
    cols[3].metric("DB 커밋", summary.total_commit_count)
    st.caption(
        f"Repo HEAD={_short_hash(summary.repo_head_hash)}, "
        f"DB Sync HEAD={_short_hash(summary.db_sync_head_hash)}, "
        f"최근 sync 대상={_short_hash(summary.latest_sync_commit_hash)}"
    )

    _render_follow_up_group(project_id, GROUP_RECOMMENDED, summary.recommended_steps, "recommended")
    with st.expander(GROUP_LATER, expanded=False):
        _render_follow_up_group(project_id, GROUP_LATER, summary.later_steps, "later", detail_expander=False)


def render_git_page() -> None:
    st.title("Git 동기화")
    st.caption("프로젝트에 등록된 앱 서버 Git 저장소의 전체 커밋을 수집하고 이후 새 커밋만 증분 동기화합니다.")

    context = require_project_context("먼저 프로젝트/Git 설정에서 프로젝트와 앱 서버 Git 저장소 경로를 등록해 주세요.")
    if context is None:
        return

    with SessionLocal() as db:
        project = db.get(Project, context.project_id)
        if project is None:
            st.error("선택한 프로젝트를 찾을 수 없습니다.")
            return

        st.text_input("앱 서버 Git 저장소 경로", value=project.git_repo_path or "", disabled=True)
        st.write("마지막 동기화 커밋:", project.last_synced_commit_hash or "-")
        st.write("마지막 동기화 시각:", project.last_synced_at or "-")
        status = render_repository_status(project)

        if not project.git_repo_path:
            st.warning("이 프로젝트에는 앱 서버 Git 저장소 경로가 등록되어 있지 않습니다.")
            return
        if not is_git_repository(project.git_repo_path):
            st.error("앱 서버에서 등록된 경로를 실제 Git 저장소로 확인할 수 없습니다. 프로젝트/Git 설정에서 경로를 수정해 주세요.")
            return

        full_col, incremental_col = st.columns(2)
        run_incremental = incremental_col.button("증분 동기화", type="primary", use_container_width=True)
        run_full = full_col.button("전체 수집", type="secondary", use_container_width=True)
        if status.db_matches_head is True:
            st.success("DB가 현재 서버 저장소 HEAD 기준으로 최신입니다. 새 commit을 가져온 뒤에는 증분 동기화를 실행하세요.")

        sync_result = None
        if run_full:
            with st.spinner("전체 Git 커밋을 수집하는 중입니다."):
                sync_result = sync_git_repository(db, project, full=True)
            _render_sync_result(sync_result)
        elif run_incremental:
            with st.spinner("새로 추가된 Git 커밋만 동기화하는 중입니다."):
                sync_result = sync_git_repository(db, project, full=False)
            _render_sync_result(sync_result)

        _render_follow_up_panel(db, project.id, sync_result)

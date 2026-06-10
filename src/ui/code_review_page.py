import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.models import Project
from src.services.code_review_service import CodeReviewService, get_recent_code_reviews
from src.ui.project_context import require_project_context


TARGET_OPTIONS = {
    "작업트리 변경": "working_tree",
    "Staged 변경": "staged",
    "최신 커밋": "latest_commit",
    "특정 커밋": "commit",
}
def _render_review_result(review) -> None:
    st.subheader("리뷰 결과")
    status_col, target_col, ref_col = st.columns(3)
    status_col.metric("상태", review.status)
    target_col.metric("대상", review.target_type)
    ref_col.metric("참조", review.target_ref[:12] if review.target_ref else "-")

    st.markdown("**요약**")
    st.write(review.summary or "-")

    st.markdown("**커밋 분석**")
    st.json(review.commit_analysis or {})

    st.markdown("**버그 탐지**")
    bug_findings = review.bug_findings or []
    if bug_findings:
        st.dataframe(pd.DataFrame(bug_findings), use_container_width=True, hide_index=True)
    else:
        st.success("탐지된 버그 후보가 없습니다.")

    st.markdown("**리팩토링 제안**")
    suggestions = review.refactoring_suggestions or []
    if suggestions:
        st.dataframe(pd.DataFrame(suggestions), use_container_width=True, hide_index=True)
    else:
        st.info("리팩토링 제안이 없습니다.")


def _render_review_history(project_id: int) -> None:
    st.subheader("리뷰 기록")
    with SessionLocal() as db:
        reviews = get_recent_code_reviews(db, project_id, limit=50)

    if not reviews:
        st.info("아직 저장된 코드리뷰 기록이 없습니다.")
        return

    rows = [
        {
            "id": review.id,
            "created_at": review.created_at,
            "status": review.status,
            "target_type": review.target_type,
            "target_ref": review.target_ref[:12] if review.target_ref else "-",
            "bug_count": len(review.bug_findings or []),
            "refactoring_count": len(review.refactoring_suggestions or []),
            "summary": review.summary,
        }
        for review in reviews
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_code_review_page() -> None:
    st.title("AI Code Review")
    st.caption("앱 서버 Git 저장소의 변경 또는 커밋을 LLM으로 분석해 커밋 요약, 버그 후보, 리팩토링 제안을 기록합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return
    project_id = context.project_id

    with SessionLocal() as db:
        project = db.query(Project).filter(Project.id == project_id).one()

    if not project.git_repo_path:
        st.warning("선택한 프로젝트에 앱 서버 Git 저장소 경로가 없습니다. 프로젝트/Git 설정에서 경로를 먼저 설정하세요.")
        return

    st.write({"app_server_git_repo_path": project.git_repo_path})
    st.divider()

    target_label = st.radio("리뷰 대상", list(TARGET_OPTIONS.keys()), horizontal=True)
    target_type = TARGET_OPTIONS[target_label]
    target_ref = None
    if target_type == "commit":
        target_ref = st.text_input("커밋 해시 또는 rev", value="HEAD")

    if st.button("AI 코드리뷰 실행", type="primary"):
        with SessionLocal() as db:
            project = db.query(Project).filter(Project.id == project_id).one()
            service = CodeReviewService()
            with st.spinner("AI 코드리뷰를 실행하고 기록하는 중입니다."):
                result = service.review_project(db, project, target_type=target_type, target_ref=target_ref)

        if result.errors:
            for error in result.errors:
                st.error(error)
        elif result.review:
            _render_review_result(result.review)

    st.divider()
    _render_review_history(project_id)

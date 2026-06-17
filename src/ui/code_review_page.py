import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.models import Project
from src.services.code_review_service import CodeReviewService, get_recent_code_reviews
from src.ui.display_utils import key_value_dataframe
from src.ui.project_context import require_project_context


TARGET_OPTIONS = {
    "최신 커밋 (권장)": "latest_commit",
    "특정 커밋": "commit",
    "서버 작업트리 변경": "working_tree",
    "서버 Staged 변경": "staged",
}

TARGET_TYPE_LABELS = {value: label for label, value in TARGET_OPTIONS.items()}
STATUS_LABELS = {
    "completed": "완료",
    "failed": "실패",
    "running": "실행 중",
    "pending": "대기",
}
SEVERITY_LABELS = {
    "high": "높음",
    "medium": "보통",
    "low": "낮음",
}
COMMIT_ANALYSIS_LABELS = {
    "change_intent": "변경 의도",
    "impact_scope": "영향 범위",
    "risk_level": "위험도",
}
COMMIT_ANALYSIS_VALUE_LABELS = {
    "local": "국소",
    "module": "모듈",
    "cross-cutting": "전반",
    "unknown": "판단 불가",
    "high": "높음",
    "medium": "보통",
    "low": "낮음",
}


def _status_label(status: str | None) -> str:
    if not status:
        return "-"
    return STATUS_LABELS.get(status, status)


def _severity_label(severity: str | None) -> str:
    if not severity:
        return "-"
    return SEVERITY_LABELS.get(severity, severity)


def _commit_analysis_display_rows(commit_analysis: dict) -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    for key, value in commit_analysis.items():
        label = COMMIT_ANALYSIS_LABELS.get(str(key), str(key))
        display_value = COMMIT_ANALYSIS_VALUE_LABELS.get(value, value) if isinstance(value, str) else value
        rows.append((label, display_value))
    return rows


def _review_provider_label(review) -> str:
    raw_response = review.raw_response or {}
    if isinstance(raw_response.get("llm"), dict):
        provider = raw_response["llm"].get("provider") or "-"
        model = raw_response["llm"].get("model") or "-"
        return f"{provider} / {model}"
    return str(raw_response.get("provider") or "-")


def _render_finding_cards(findings: list[dict]) -> None:
    for index, finding in enumerate(findings, start=1):
        with st.container(border=True):
            st.markdown(f"**Finding {index} · {_severity_label(finding.get('severity'))}**")
            st.write(f"파일: {finding.get('file') or '-'}")
            if finding.get("line") is not None:
                st.write(f"라인: {finding.get('line')}")
            st.write(f"문제: {finding.get('issue') or '-'}")
            st.write(f"권장 수정: {finding.get('recommendation') or '-'}")


def _render_suggestion_cards(suggestions: list[dict]) -> None:
    for index, suggestion in enumerate(suggestions, start=1):
        with st.container(border=True):
            st.markdown(f"**Suggestion {index}**")
            st.write(f"파일: {suggestion.get('file') or '-'}")
            if suggestion.get("line") is not None:
                st.write(f"라인: {suggestion.get('line')}")
            st.write(f"제안: {suggestion.get('suggestion') or '-'}")
            st.write(f"효과: {suggestion.get('benefit') or '-'}")


def _render_review_result(review) -> None:
    st.subheader("리뷰 결과")
    status_col, provider_col, target_col, ref_col = st.columns(4)
    status_col.metric("상태", _status_label(review.status))
    provider_col.metric("Provider", _review_provider_label(review))
    target_col.metric("대상", TARGET_TYPE_LABELS.get(review.target_type, review.target_type))
    ref_col.metric("참조", review.target_ref[:12] if review.target_ref else "-")

    st.markdown("**요약**")
    st.write(review.summary or "-")

    st.markdown("**커밋 분석**")
    commit_analysis = review.commit_analysis or {}
    if isinstance(commit_analysis, dict) and commit_analysis:
        st.table(key_value_dataframe(_commit_analysis_display_rows(commit_analysis)))
    else:
        st.info("커밋 분석 요약이 없습니다.")

    st.markdown("**버그 탐지**")
    bug_findings = review.bug_findings or []
    if bug_findings:
        _render_finding_cards(bug_findings)
    else:
        st.success("탐지된 버그 후보가 없습니다.")

    st.markdown("**리팩토링 제안**")
    suggestions = review.refactoring_suggestions or []
    if suggestions:
        _render_suggestion_cards(suggestions)
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
            "status": _status_label(review.status),
            "target_type": TARGET_TYPE_LABELS.get(review.target_type, review.target_type),
            "target_ref": review.target_ref[:12] if review.target_ref else "-",
            "bug_count": len(review.bug_findings or []),
            "refactoring_count": len(review.refactoring_suggestions or []),
            "summary": review.summary,
        }
        for review in reviews
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_latest_saved_review(project_id: int) -> None:
    with SessionLocal() as db:
        reviews = get_recent_code_reviews(db, project_id, limit=1)

    if not reviews:
        return

    st.caption("가장 최근에 저장된 AI Code Review 결과입니다. 새 리뷰를 실행하면 이 영역과 아래 기록이 함께 갱신됩니다.")
    _render_review_result(reviews[0])


def render_code_review_page() -> None:
    st.title("AI Code Review")
    st.caption("앱 서버 Git 저장소의 커밋 이력을 LLM으로 분석해 커밋 요약, 버그 후보, 리팩토링 제안을 기록합니다.")

    context = require_project_context("먼저 프로젝트를 등록해 주세요.")
    if context is None:
        return
    project_id = context.project_id

    with SessionLocal() as db:
        project = db.query(Project).filter(Project.id == project_id).one()

    if not project.git_repo_path:
        st.warning("선택한 프로젝트에 앱 서버 Git 저장소 경로가 없습니다. 프로젝트/Git 설정에서 경로를 먼저 설정하세요.")
        return

    st.caption(f"앱 서버 Git 저장소: {project.git_repo_path}")
    st.divider()

    target_label = st.radio("리뷰 대상", list(TARGET_OPTIONS.keys()), horizontal=True)
    target_type = TARGET_OPTIONS[target_label]
    st.caption(
        "중앙 앱 서버 모델에서는 최신/특정 커밋 리뷰가 기본 흐름입니다. "
        "서버 작업트리와 서버 Staged 변경은 분석용 서버 clone에 임시 변경이 남아 있을 때만 사용하세요."
    )
    target_ref = None
    if target_type == "commit":
        target_ref = st.text_input("커밋 해시 또는 rev", value="HEAD")
    elif target_type in {"working_tree", "staged"}:
        st.info("이 옵션은 앱 서버 Git 저장소의 local 변경을 리뷰합니다. 개발자 개인 PC의 작업트리나 staged 변경은 서버 앱에서 직접 볼 수 없습니다.")

    rendered_current_review = False
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
            rendered_current_review = True

    st.divider()
    if not rendered_current_review:
        _render_latest_saved_review(project_id)
    _render_review_history(project_id)

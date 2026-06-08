import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import GitCommit, Program, Project
from src.services.mapping_service import (
    DEFAULT_CANDIDATES_PER_COMMIT,
    DEFAULT_CANDIDATES_PER_PROGRAM,
    CommitMappingProgress,
    MappingService,
)
from src.services.mapping_feedback_service import (
    IMPLEMENTATION_STATUS_OPTIONS,
    apply_mapping_feedback,
    list_mapping_feedback_rows,
    list_mapping_review_queue_rows,
    summarize_mapping_feedback_quality,
)


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _commit_status(commit: GitCommit) -> str:
    return commit.mapping_analysis_status or "not_analyzed"


def _commit_label(commit: GitCommit) -> str:
    short_hash = commit.commit_hash[:12]
    message = (commit.message or "").splitlines()[0]
    committed_at = commit.committed_at.strftime("%Y-%m-%d %H:%M") if commit.committed_at else "-"
    return f"{short_hash} | {_commit_status(commit)} | {committed_at} | {message[:90]}"


def _load_commits(project_id: int) -> list[GitCommit]:
    with SessionLocal() as db:
        return (
            db.query(GitCommit)
            .filter(GitCommit.project_id == project_id)
            .order_by(GitCommit.committed_at.desc())
            .all()
        )


def _render_result(result) -> None:
    if result.errors:
        with st.expander("오류 상세", expanded=True):
            for error in result.errors[:20]:
                st.error(error)
            if len(result.errors) > 20:
                st.info(f"추가 오류 {len(result.errors) - 20}건은 analysis_runs 요약과 커밋 상태를 확인하세요.")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("분석 매핑", result.analyzed_count)
    col2.metric("신규 저장", result.created_count)
    col3.metric("업데이트", result.updated_count)
    col4.metric("건너뜀", result.skipped_count)
    col5.metric("실패 커밋", result.failed_count)

    if result.recent_results:
        st.subheader("최근 매핑 결과")
        st.dataframe(pd.DataFrame(result.recent_results), use_container_width=True)
    else:
        st.info("저장된 관련 매핑 결과가 없습니다.")


def _run_commit_analysis(
    project_id: int,
    commit_ids: list[int] | None,
    candidates_per_commit: int,
    skip_completed: bool,
) -> None:
    progress_bar = st.progress(0)
    progress_text = st.empty()

    def update_progress(progress: CommitMappingProgress) -> None:
        ratio = progress.processed_count / progress.total_count if progress.total_count else 1
        progress_bar.progress(min(ratio, 1.0))
        current = progress.current_commit_hash[:12] if progress.current_commit_hash else "-"
        progress_text.write(
            f"진행률: {progress.processed_count}/{progress.total_count}, "
            f"실패: {progress.failed_count}, 현재 커밋: {current}"
        )

    with SessionLocal() as db:
        service = MappingService()
        with st.spinner("커밋 기준 매핑 분석을 실행 중입니다. 완료된 커밋은 재시작 시 건너뜁니다."):
            result = service.analyze_commits(
                db,
                project_id=project_id,
                commit_ids=commit_ids,
                candidates_per_commit=candidates_per_commit,
                skip_completed=skip_completed,
                progress_callback=update_progress,
            )

    progress_bar.progress(1.0)
    progress_text.write("분석이 끝났습니다.")
    _render_result(result)


def _render_commit_based_mode(project_id: int) -> None:
    st.subheader("커밋 기준 분석")

    commits = _load_commits(project_id)
    if not commits:
        st.warning("분석할 Git 커밋이 없습니다.")
        return

    completed_count = sum(1 for commit in commits if _commit_status(commit) == "completed")
    failed_count = sum(1 for commit in commits if _commit_status(commit) == "failed")
    pending_commits = [commit for commit in commits if _commit_status(commit) != "completed"]
    pending_count = len(pending_commits)

    col1, col2, col3 = st.columns(3)
    col1.metric("미완료 커밋", pending_count)
    col2.metric("완료 커밋", completed_count)
    col3.metric("실패 커밋", failed_count)

    candidates_per_commit = st.slider(
        "커밋당 후보 프로그램 TOP N",
        min_value=3,
        max_value=30,
        value=DEFAULT_CANDIDATES_PER_COMMIT,
        help="커밋 1개마다 규칙/토큰 유사도로 후보 프로그램만 추린 뒤, 이 후보만 LLM에 전달합니다.",
    )

    st.markdown("**일괄 분석**")
    batch_col1, batch_col2 = st.columns([1, 2])
    run_pending = batch_col1.button("미완료 커밋 전체 분석", type="primary", disabled=pending_count == 0)
    retry_failed = batch_col2.checkbox("실패 커밋도 다시 시도", value=True)

    if run_pending:
        retryable_statuses = {"not_analyzed", "failed"} if retry_failed else {"not_analyzed"}
        target_ids = [commit.id for commit in commits if _commit_status(commit) in retryable_statuses]
        _run_commit_analysis(
            project_id=project_id,
            commit_ids=target_ids,
            candidates_per_commit=candidates_per_commit,
            skip_completed=True,
        )
        return

    st.markdown("**선택 분석**")
    status_filter = st.multiselect(
        "목록에 표시할 상태",
        ["not_analyzed", "failed", "completed"],
        default=["not_analyzed", "failed"],
    )
    filtered_commits = [commit for commit in commits if _commit_status(commit) in set(status_filter)]

    default_selection_limit = min(20, len(filtered_commits))
    default_labels = [_commit_label(commit) for commit in filtered_commits[:default_selection_limit]]
    commit_options = {_commit_label(commit): commit.id for commit in filtered_commits}
    selected_commit_labels = st.multiselect(
        "분석할 커밋 여러 개 선택",
        list(commit_options.keys()),
        default=default_labels,
        help="필요한 커밋을 여러 개 고른 뒤 한 번에 분석할 수 있습니다.",
    )

    selected_commit_ids = [commit_options[label] for label in selected_commit_labels]
    selected_col1, selected_col2, selected_col3 = st.columns([1, 1, 2])
    run_selected = selected_col1.button("선택한 커밋 분석", disabled=not selected_commit_ids)
    force_reanalyze = selected_col2.checkbox("완료 커밋도 재분석", value=False)
    selected_col3.caption(f"선택: {len(selected_commit_ids)}건 / 표시: {len(filtered_commits)}건")

    if run_selected:
        _run_commit_analysis(
            project_id=project_id,
            commit_ids=selected_commit_ids,
            candidates_per_commit=candidates_per_commit,
            skip_completed=not force_reanalyze,
        )


def _render_program_based_mode(project_id: int) -> None:
    st.subheader("프로그램 기준 분석")
    candidates_per_program = st.slider(
        "프로그램당 분석할 커밋 후보 수",
        min_value=1,
        max_value=30,
        value=min(DEFAULT_CANDIDATES_PER_PROGRAM, 5),
        help="기존 방식입니다. 프로그램별로 후보 커밋을 추리고 각 조합을 LLM으로 분석합니다.",
    )
    related_only = st.checkbox("관련 커밋으로 판단된 결과만 저장", value=False)

    if not st.button("프로그램 기준 매핑 분석 실행", type="primary"):
        return

    with SessionLocal() as db:
        service = MappingService()
        with st.spinner("프로그램별 후보 커밋을 분석하고 저장하는 중입니다."):
            result = service.analyze_project(
                db,
                project_id=project_id,
                candidates_per_program=candidates_per_program,
                related_only=related_only,
            )

    _render_result(result)


def _format_feedback_datetime(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def _feedback_rows_dataframe(rows) -> pd.DataFrame:
    df = pd.DataFrame([row.__dict__ for row in rows])
    if df.empty:
        return df
    df["commit_hash_short"] = df["commit_hash"].str.slice(0, 12)
    df["feedback_updated_at"] = df["feedback_updated_at"].apply(_format_feedback_datetime)
    df["review_reasons"] = df["review_reasons"].apply(lambda reasons: ", ".join(reasons or []))
    return df


def _row_labels(rows) -> dict[str, object]:
    return {
        (
            f"{row.mapping_id} | {row.program_id or '-'} | {row.program_name} | "
            f"{row.commit_hash[:12]} | {row.commit_message[:80]}"
        ): row
        for row in rows
    }


def _render_mapping_feedback(project_id: int) -> None:
    st.subheader("매핑 피드백")
    st.caption("AI 매핑 결과를 사람이 보정하면 영향도, 진척도, 리스크 분석에서 보정된 값이 사용됩니다.")

    with SessionLocal() as db:
        summary = summarize_mapping_feedback_quality(db, project_id)

    metric_cols = st.columns(6)
    metric_cols[0].metric("전체 매핑", summary.total_count)
    metric_cols[1].metric("피드백 완료", summary.feedback_completed_count)
    metric_cols[2].metric("피드백 미완료", summary.feedback_pending_count)
    metric_cols[3].metric("리뷰 필요", summary.review_needed_count)
    metric_cols[4].metric("판단불가", summary.unknown_status_count)
    metric_cols[5].metric("낮은 관련도", summary.low_relevance_count)

    st.markdown("#### 리뷰 큐")
    queue_col1, queue_col2 = st.columns([1, 2])
    queue_filter = queue_col1.selectbox(
        "리뷰 큐 필터",
        ["전체", "리뷰 필요만", "피드백 미완료", "판단불가", "낮은 관련도", "비관련 판정"],
        index=1,
    )
    queue_keyword = queue_col2.text_input(
        "리뷰 큐 검색어",
        placeholder="프로그램명, program_id, commit message, commit hash",
        key="mapping_review_queue_keyword",
    )

    with SessionLocal() as db:
        queue_rows = list_mapping_review_queue_rows(
            db,
            project_id,
            queue_filter=queue_filter,
            keyword=queue_keyword or None,
        )

    selected_queue_row = None
    if queue_rows:
        queue_df = _feedback_rows_dataframe(queue_rows)
        st.dataframe(
            queue_df[
                [
                    "mapping_id",
                    "program_id",
                    "program_name",
                    "commit_hash_short",
                    "commit_message",
                    "relevance_score",
                    "is_related",
                    "implementation_status",
                    "has_feedback",
                    "review_needed",
                    "review_reasons",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        queue_labels = _row_labels(queue_rows)
        selected_queue_label = st.selectbox(
            "리뷰 큐에서 보정할 매핑 선택",
            ["선택 안 함", *list(queue_labels.keys())],
            key="mapping_review_queue_select",
        )
        if selected_queue_label != "선택 안 함":
            selected_queue_row = queue_labels[selected_queue_label]
    else:
        st.info("리뷰 큐 조건에 맞는 매핑 결과가 없습니다.")

    st.divider()
    st.markdown("#### 매핑 목록 / 보정")
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    keyword = filter_col1.text_input("프로그램/커밋 검색", key="mapping_feedback_keyword")
    only_feedback = filter_col2.checkbox("피드백 완료만", value=False)
    relation_filter_label = filter_col3.selectbox("관련 여부", ["전체", "관련", "비관련"])
    related_filter = {"관련": True, "비관련": False}.get(relation_filter_label)

    with SessionLocal() as db:
        rows = list_mapping_feedback_rows(
            db,
            project_id,
            only_feedback=only_feedback,
            related_filter=related_filter,
            keyword=keyword or None,
        )

    if not rows:
        st.info("조건에 맞는 매핑 결과가 없습니다. 먼저 매핑 분석을 실행하세요.")
        return

    df = _feedback_rows_dataframe(rows)
    st.dataframe(
        df[
            [
                "mapping_id",
                "program_id",
                "program_name",
                "commit_hash_short",
                "commit_message",
                "relevance_score",
                "is_related",
                "implementation_status",
                "has_feedback",
                "feedback_updated_at",
                "review_needed",
                "review_reasons",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    labels = _row_labels(rows)
    default_index = 0
    label_keys = list(labels.keys())
    if selected_queue_row is not None:
        for index, label in enumerate(label_keys):
            if labels[label].mapping_id == selected_queue_row.mapping_id:
                default_index = index
                break
    selected_label = st.selectbox("보정할 매핑 선택", label_keys, index=default_index, key="mapping_feedback_select")
    selected = labels[selected_label]

    status_index = IMPLEMENTATION_STATUS_OPTIONS.index(selected.implementation_status)
    relation_index = 0 if selected.is_related is not False else 1
    with st.form("mapping_feedback_form"):
        form_col1, form_col2, form_col3 = st.columns([1, 1, 1])
        relation_label = form_col1.radio("관련 여부", ["관련", "비관련"], index=relation_index, horizontal=True)
        relevance_score = form_col2.slider(
            "관련도 점수",
            min_value=0.0,
            max_value=100.0,
            value=float(selected.relevance_score),
            step=1.0,
        )
        implementation_status = form_col3.selectbox(
            "구현상태",
            IMPLEMENTATION_STATUS_OPTIONS,
            index=status_index,
        )
        reason = st.text_area("보정 근거", value=selected.reason, height=120)
        submitted = st.form_submit_button("피드백 저장", type="primary")

    if submitted:
        with SessionLocal() as db:
            apply_mapping_feedback(
                db,
                selected.mapping_id,
                is_related=relation_label == "관련",
                relevance_score=relevance_score,
                implementation_status=implementation_status,
                reason=reason,
            )
        st.success("매핑 피드백을 저장했습니다.")
        st.rerun()


def render_mapping_page() -> None:
    st.title("프로그램-커밋 매핑 분석")
    st.caption("커밋 기준 분석을 기본 추천 방식으로 사용합니다. 기존 프로그램 기준 분석도 유지됩니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]

    with SessionLocal() as db:
        program_count = db.query(Program).filter(Program.project_id == project_id).count()
        commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()

    metric1, metric2 = st.columns(2)
    metric1.metric("프로그램 수", program_count)
    metric2.metric("Git 커밋 수", commit_count)

    if program_count == 0 or commit_count == 0:
        st.warning("분석하려면 프로그램 목록과 Git 커밋 데이터가 모두 필요합니다.")
        return

    mode = st.radio(
        "분석 모드",
        ["커밋 기준 분석", "프로그램 기준 분석", "매핑 피드백"],
        index=0,
        horizontal=True,
    )

    if mode == "커밋 기준 분석":
        _render_commit_based_mode(project_id)
    elif mode == "프로그램 기준 분석":
        _render_program_based_mode(project_id)
    else:
        _render_mapping_feedback(project_id)

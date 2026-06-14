import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.git_service import is_git_repository
from src.services.git_remote_service import clone_or_update_project_repository, validate_git_remote_url_for_storage
from src.services.project_management_service import (
    delete_project,
    get_project_delete_impact,
    get_project_reset_impact,
    reset_project_analysis_data,
)
from src.ui.git_status_panel import render_repository_status
from src.ui.project_context import CURRENT_PROJECT_ID_KEY, load_projects, set_current_project_id
from src.utils.repo_path import is_repo_path_allowed, repo_storage_root_label


def _render_project_delete_section(project: Project) -> None:
    st.divider()
    st.subheader("프로젝트 삭제")
    st.warning(
        "프로젝트를 삭제하면 해당 프로젝트의 프로그램, Git 이력, 매핑, 리스크, RAG 인덱스, "
        "Project Chat, AI Code Review 결과가 함께 삭제됩니다. 전역 개발자 마스터는 삭제하지 않습니다."
    )

    with SessionLocal() as db:
        impact = get_project_delete_impact(db, int(project.id))

    if impact is None:
        st.info("삭제할 프로젝트를 찾을 수 없습니다.")
        return

    impact_rows = [
        {"데이터": "프로그램/개발계획", "건수": impact.program_count},
        {"데이터": "Git commit", "건수": impact.git_commit_count},
        {"데이터": "변경 파일/diff", "건수": impact.commit_file_count},
        {"데이터": "프로그램-커밋 매핑", "건수": impact.mapping_count},
        {"데이터": "분석 실행 이력", "건수": impact.analysis_run_count},
        {"데이터": "구현상태 분석", "건수": impact.implementation_status_count},
        {"데이터": "리스크", "건수": impact.risk_finding_count},
        {"데이터": "AI Code Review", "건수": impact.code_review_count},
        {"데이터": "자원관리 Snapshot", "건수": impact.resource_metric_snapshot_count},
        {"데이터": "Project Chat 세션", "건수": impact.chat_session_count},
        {"데이터": "Project Chat 메시지", "건수": impact.chat_message_count},
        {"데이터": "RAG chunk", "건수": impact.document_chunk_count},
        {"데이터": "RAG vector", "건수": impact.vector_item_count},
        {"데이터": "표준용어/표준단어", "건수": impact.standard_term_count},
        {"데이터": "프로젝트 개발자 연결", "건수": impact.project_developer_count},
        {"데이터": "전역 개발자 마스터(삭제 안 함)", "건수": impact.developer_count},
    ]
    st.dataframe(impact_rows, hide_index=True, use_container_width=True)

    with st.form(f"project_delete_form_{project.id}"):
        confirmation = st.text_input(
            "삭제하려면 프로젝트명을 그대로 입력하세요.",
            placeholder=project.name,
        )
        submitted = st.form_submit_button("프로젝트 삭제", type="primary")

    if not submitted:
        return
    if confirmation.strip() != project.name:
        st.error("프로젝트명이 일치하지 않아 삭제하지 않았습니다.")
        return

    deleted_project_id = int(project.id)
    with SessionLocal() as db:
        deleted_impact = delete_project(db, deleted_project_id)

    if deleted_impact is None:
        st.info("이미 삭제된 프로젝트입니다.")
        set_current_project_id(None)
        st.rerun()

    remaining = load_projects()
    next_project_id = int(remaining[0].id) if remaining else None
    set_current_project_id(next_project_id)
    st.success(f"{project.name} 프로젝트를 삭제했습니다.")
    st.rerun()


def _render_project_reset_section(project: Project) -> None:
    st.divider()
    st.subheader("분석 데이터 초기화")
    st.info(
        "프로젝트명, Git 저장소 경로, 프로그램/개발계획, 프로젝트 개발자 연결, 표준용어/표준단어는 유지하고 "
        "Git 수집 결과와 분석 결과만 지웁니다. 같은 프로젝트로 검증이나 검증을 다시 시작할 때 사용하세요."
    )

    with SessionLocal() as db:
        impact = get_project_reset_impact(db, int(project.id))

    if impact is None:
        st.info("초기화할 프로젝트를 찾을 수 없습니다.")
        return

    impact_rows = [
        {"구분": "유지", "데이터": "프로그램/개발계획", "건수": impact.preserved_program_count},
        {"구분": "유지", "데이터": "표준용어/표준단어", "건수": impact.preserved_standard_term_count},
        {"구분": "유지", "데이터": "프로젝트 개발자 연결", "건수": impact.preserved_project_developer_count},
        {"구분": "초기화", "데이터": "Git commit", "건수": impact.git_commit_count},
        {"구분": "초기화", "데이터": "변경 파일/diff", "건수": impact.commit_file_count},
        {"구분": "초기화", "데이터": "프로그램-커밋 매핑", "건수": impact.mapping_count},
        {"구분": "초기화", "데이터": "분석 실행 이력", "건수": impact.analysis_run_count},
        {"구분": "초기화", "데이터": "구현상태 분석", "건수": impact.implementation_status_count},
        {"구분": "초기화", "데이터": "리스크", "건수": impact.risk_finding_count},
        {"구분": "초기화", "데이터": "AI Code Review", "건수": impact.code_review_count},
        {"구분": "초기화", "데이터": "자원관리 Snapshot", "건수": impact.resource_metric_snapshot_count},
        {"구분": "초기화", "데이터": "Project Chat 세션", "건수": impact.chat_session_count},
        {"구분": "초기화", "데이터": "Project Chat 메시지", "건수": impact.chat_message_count},
        {"구분": "초기화", "데이터": "RAG chunk", "건수": impact.document_chunk_count},
        {"구분": "초기화", "데이터": "RAG vector", "건수": impact.vector_item_count},
    ]
    st.dataframe(impact_rows, hide_index=True, use_container_width=True)

    with st.form(f"project_reset_form_{project.id}"):
        confirmation = st.text_input(
            "초기화하려면 프로젝트명을 그대로 입력하세요.",
            placeholder=project.name,
        )
        submitted = st.form_submit_button("분석 데이터 초기화", type="primary")

    if not submitted:
        return
    if confirmation.strip() != project.name:
        st.error("프로젝트명이 일치하지 않아 초기화하지 않았습니다.")
        return

    with SessionLocal() as db:
        reset_impact = reset_project_analysis_data(db, int(project.id))

    if reset_impact is None:
        st.info("이미 삭제된 프로젝트입니다.")
        set_current_project_id(None)
        st.rerun()

    set_current_project_id(int(project.id))
    st.success(f"{project.name} 프로젝트의 분석 데이터를 초기화했습니다.")
    st.rerun()


def _render_remote_repository_section(project: Project) -> None:
    st.divider()
    st.subheader("서버 저장소 clone/fetch")
    st.caption(
        "Git remote URL과 branch가 저장된 프로젝트는 앱 서버가 저장소 경로에 clone하거나 origin을 fetch/reset할 수 있습니다. "
        "access token, SSH key, password는 앱에 저장하지 않으며 서버 OS의 Git 인증 설정을 사용합니다."
    )
    if not project.git_remote_url:
        st.info("Git remote URL을 저장하면 서버 저장소 clone/fetch를 사용할 수 있습니다.")
        return
    if not project.git_repo_path:
        st.info("앱 서버 Git 저장소 경로를 저장하면 서버 저장소 clone/fetch를 사용할 수 있습니다.")
        return

    force_reset = st.checkbox(
        "working tree local 변경이 있어도 reset",
        value=False,
        help="분석용 clone의 local 변경을 버려도 되는 운영 정책이 확실할 때만 선택하세요.",
        key=f"project_remote_force_reset_{project.id}",
    )
    if not st.button("서버 저장소 clone/fetch", type="secondary", key=f"project_remote_sync_{project.id}"):
        return

    with st.spinner("앱 서버 Git 저장소를 clone/fetch/reset하는 중입니다."):
        result = clone_or_update_project_repository(project, force_reset=force_reset)

    for message in result.messages:
        st.info(message)
    if result.status in {"cloned", "updated"}:
        st.success(
            f"서버 저장소 준비 완료: {result.status}, "
            f"HEAD {result.head_before[:12] if result.head_before else '-'} -> "
            f"{result.head_after[:12] if result.head_after else '-'}"
        )
        st.rerun()
    elif result.status == "skipped":
        for error in result.errors:
            st.warning(error)
    else:
        for error in result.errors:
            st.error(error)


def render_project_page() -> None:
    st.title("프로젝트/Git 설정")
    st.caption("프로젝트와 앱 서버에서 접근 가능한 Git 저장소 경로를 등록합니다.")
    st.info(
        "Git 저장소 경로는 브라우저 사용자 PC가 아니라 현재 AI Commit Advisor 앱 서버 기준입니다. "
        "사내 서버 운영에서는 서버에 clone된 저장소 경로를 입력하세요."
    )
    storage_root = repo_storage_root_label()
    if storage_root:
        st.caption(f"허용된 저장소 루트: {storage_root}")

    projects = load_projects()
    project_options = ["새 프로젝트"] + [f"{project.id} - {project.name}" for project in projects]
    current_project_id = st.session_state.get(CURRENT_PROJECT_ID_KEY)
    default_index = 0
    for index, option in enumerate(project_options):
        if option.startswith(f"{current_project_id} - "):
            default_index = index
            break
    selected = st.selectbox("프로젝트 선택", project_options, index=default_index)
    selected_project = None
    if selected != "새 프로젝트":
        selected_id = int(selected.split(" - ", 1)[0])
        selected_project = next((project for project in projects if project.id == selected_id), None)

    with st.form("project_form"):
        name = st.text_input("프로젝트명", value=selected_project.name if selected_project else "")
        repo_path = st.text_input(
            "앱 서버 Git 저장소 경로",
            value=selected_project.git_repo_path if selected_project else "",
            help="사용자 PC 경로가 아니라 Streamlit 앱이 실행 중인 서버에서 접근 가능한 Git 저장소 경로입니다.",
        )
        remote_url = st.text_input(
            "Git remote URL",
            value=selected_project.git_remote_url if selected_project else "",
            help="선택 사항입니다. 저장하면 앱 서버가 이 URL을 사용해 저장소를 clone/fetch할 수 있습니다. 인증 정보는 저장하지 마세요.",
        )
        branch = st.text_input(
            "Git branch",
            value=selected_project.git_branch if selected_project and selected_project.git_branch else "main",
            help="서버 저장소 clone/fetch/reset에 사용할 branch입니다.",
        )
        description = st.text_area("설명", value=selected_project.description if selected_project else "")
        submitted = st.form_submit_button("프로젝트 저장", type="primary")

    if not submitted:
        if selected_project:
            st.write("마지막 동기화 커밋:", selected_project.last_synced_commit_hash or "-")
            st.write("마지막 동기화 시각:", selected_project.last_synced_at or "-")
            if selected_project.git_repo_path:
                render_repository_status(selected_project, compact=True)
            _render_remote_repository_section(selected_project)
            _render_project_reset_section(selected_project)
            _render_project_delete_section(selected_project)
        return

    if not name.strip():
        st.error("프로젝트명을 입력해 주세요.")
        return
    if repo_path.strip() and not is_repo_path_allowed(repo_path.strip()):
        st.error("입력한 Git 저장소 경로가 허용된 저장소 루트 밖에 있습니다.")
        return
    remote_url_value = remote_url.strip()
    remote_validation_error = validate_git_remote_url_for_storage(remote_url_value)
    if remote_validation_error:
        st.error(remote_validation_error)
        return
    if repo_path.strip() and not remote_url_value and not is_git_repository(repo_path.strip()):
        st.error("앱 서버에서 입력한 경로를 실제 Git 저장소로 확인할 수 없습니다.")
        return

    init_db()
    with SessionLocal() as db:
        if selected_project:
            project = db.get(Project, selected_project.id)
        else:
            project = Project(name=name.strip())
            db.add(project)

        project.name = name.strip()
        project.git_repo_path = repo_path.strip() or None
        project.git_remote_url = remote_url_value or None
        project.git_branch = branch.strip() or None
        project.description = description.strip() or None
        db.commit()
        db.refresh(project)
        saved_project_id = int(project.id)

    set_current_project_id(saved_project_id)
    st.success("프로젝트를 저장했습니다.")

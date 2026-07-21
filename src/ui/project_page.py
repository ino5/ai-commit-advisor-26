import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.git_service import is_git_repository
from src.services.git_remote_service import (
    clone_or_update_project_repository,
    validate_git_remote_url_for_storage,
    validate_managed_git_remote_url_for_storage,
)
from src.services.project_management_service import (
    delete_project,
    get_project_delete_impact,
    get_project_reset_impact,
    reset_project_analysis_data,
)
from src.ui.git_status_panel import render_repository_status
from src.ui.project_context import CURRENT_PROJECT_ID_KEY, load_projects, set_current_project_id
from src.utils.repo_path import (
    build_managed_repo_path,
    is_managed_repo_path,
    is_repo_path_allowed,
    managed_repo_storage_root_label,
    repo_storage_root_label,
)


MANAGED_REPOSITORY_MODE = "Git URL에서 가져오기"
EXISTING_REPOSITORY_MODE = "서버에 이미 있는 저장소 사용"


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
    if is_managed_repo_path(project.git_repo_path):
        st.caption(
            "관리형 저장소는 앱 전용 쓰기 가능 폴더에서 clone/fetch/reset합니다. "
            "인증정보가 없는 허용된 공개 HTTPS Git URL만 사용할 수 있습니다."
        )
    else:
        st.caption(
            "기존 서버 경로는 분석에 그대로 사용할 수 있습니다. clone/fetch 가능 여부는 해당 경로의 서버 쓰기 권한에 따르며, "
            "access token, SSH key, password는 앱에 저장하지 않습니다."
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
    st.caption("프로젝트와 Git 저장소 준비 방식을 등록합니다.")
    st.info(
        "브라우저 사용자 PC의 로컬 경로는 서버가 직접 읽을 수 없습니다. 공개 저장소는 `Git URL에서 가져오기`를 사용하고, "
        "운영자가 서버에 준비한 저장소는 `서버에 이미 있는 저장소 사용`을 선택하세요."
    )
    storage_root = repo_storage_root_label()
    if storage_root:
        st.caption(f"기존 서버 저장소 루트: {storage_root} (Docker 기본 구성에서는 읽기 전용)")
    managed_storage_root = managed_repo_storage_root_label()
    if managed_storage_root:
        st.caption(f"Git URL 관리형 저장소 루트: {managed_storage_root}")

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

    repository_modes = [EXISTING_REPOSITORY_MODE]
    if managed_storage_root:
        repository_modes.insert(0, MANAGED_REPOSITORY_MODE)
    selected_mode = (
        MANAGED_REPOSITORY_MODE
        if managed_storage_root and (selected_project is None or is_managed_repo_path(selected_project.git_repo_path))
        else EXISTING_REPOSITORY_MODE
    )

    repository_mode = st.radio(
        "저장소 등록 방식",
        repository_modes,
        index=repository_modes.index(selected_mode),
        horizontal=True,
        key=f"project_repository_mode_{selected_project.id if selected_project else 'new'}",
    )
    managed_mode = repository_mode == MANAGED_REPOSITORY_MODE

    with st.form("project_form"):
        name = st.text_input("프로젝트명", value=selected_project.name if selected_project else "")
        if managed_mode:
            repo_path = selected_project.git_repo_path if selected_project and is_managed_repo_path(selected_project.git_repo_path) else ""
            st.caption("서버 저장소 경로는 프로젝트를 저장할 때 자동으로 배정됩니다.")
        else:
            repo_path = st.text_input(
                "앱 서버 Git 저장소 경로",
                value=selected_project.git_repo_path if selected_project else "",
                help="사용자 PC 경로가 아니라 Streamlit 앱이 실행 중인 서버에서 접근 가능한 Git 저장소 경로입니다.",
            )
        remote_url = st.text_input(
            "공개 HTTPS Git URL" if managed_mode else "Git remote URL",
            value=selected_project.git_remote_url if selected_project else "",
            help=(
                "GitHub, GitLab, Bitbucket의 인증정보 없는 공개 HTTPS clone URL을 입력합니다."
                if managed_mode
                else "선택 사항입니다. 서버 경로에 쓰기 권한이 있으면 이 URL로 clone/fetch할 수 있습니다. 인증 정보는 저장하지 마세요."
            ),
        )
        branch = st.text_input(
            "Git branch",
            value=selected_project.git_branch if selected_project and selected_project.git_branch else "main",
            help="서버 저장소 clone/fetch/reset에 사용할 branch입니다.",
        )
        description = st.text_area("설명", value=selected_project.description if selected_project else "")
        submitted = st.form_submit_button(
            "저장소 준비 및 프로젝트 저장" if managed_mode else "프로젝트 저장",
            type="primary",
        )

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
    if managed_mode and not managed_storage_root:
        st.error("관리형 Git 저장소 루트가 설정되지 않았습니다. 서버 운영 설정을 확인해 주세요.")
        return
    if not managed_mode and repo_path.strip() and not is_repo_path_allowed(repo_path.strip()):
        st.error("입력한 Git 저장소 경로가 허용된 저장소 루트 밖에 있습니다.")
        return
    remote_url_value = remote_url.strip()
    remote_validation_error = (
        validate_managed_git_remote_url_for_storage(remote_url_value)
        if managed_mode
        else validate_git_remote_url_for_storage(remote_url_value)
    )
    if remote_validation_error:
        st.error(remote_validation_error)
        return
    if not managed_mode and repo_path.strip() and not remote_url_value and not is_git_repository(repo_path.strip()):
        st.error("앱 서버에서 입력한 경로를 실제 Git 저장소로 확인할 수 없습니다.")
        return

    saved_project_values: dict[str, object]
    init_db()
    with SessionLocal() as db:
        if selected_project:
            project = db.get(Project, selected_project.id)
        else:
            project = Project(name=name.strip())
            db.add(project)
            db.flush()

        project.name = name.strip()
        if managed_mode:
            project.git_repo_path = (
                repo_path.strip()
                if repo_path.strip() and is_managed_repo_path(repo_path.strip())
                else build_managed_repo_path(int(project.id))
            )
        else:
            project.git_repo_path = repo_path.strip() or None
        project.git_remote_url = remote_url_value or None
        project.git_branch = branch.strip() or None
        project.description = description.strip() or None
        db.commit()
        db.refresh(project)
        saved_project_id = int(project.id)
        saved_project_values = {
            "id": saved_project_id,
            "name": project.name,
            "git_repo_path": project.git_repo_path,
            "git_remote_url": project.git_remote_url,
            "git_branch": project.git_branch,
        }

    set_current_project_id(saved_project_id)
    if not managed_mode:
        st.success("프로젝트를 저장했습니다.")
        return

    managed_project = Project(**saved_project_values)
    with st.spinner("관리형 저장소를 clone/fetch하는 중입니다."):
        result = clone_or_update_project_repository(managed_project)
    for message in result.messages:
        st.info(message)
    if result.status in {"cloned", "updated"}:
        st.success(f"프로젝트와 관리형 저장소를 준비했습니다. HEAD {result.head_after[:12] if result.head_after else '-'}")
        return
    st.warning("프로젝트 정보는 저장했지만 관리형 저장소를 준비하지 못했습니다. 아래 오류를 확인한 뒤 다시 실행해 주세요.")
    for error in result.errors:
        st.error(error)

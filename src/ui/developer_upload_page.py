import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Developer
from src.services.developer_management_service import (
    build_developer_template_excel,
    delete_developer,
    developer_column_guide,
    existing_developer_ids,
    get_developer_delete_impact,
    save_developers_with_result,
    save_manual_developer,
    update_developer,
    validate_developer_import,
)
from src.services.excel_service import read_developer_excel
from src.services.project_developer_service import list_global_developers, list_project_developers
from src.ui.project_context import get_current_project_context
from src.ui.sample_artifact_download import render_sample_artifact_download


def _empty_payload() -> dict:
    return {
        "developer_id": "",
        "developer_name": "",
        "email": "",
        "role": "",
        "skills": "",
    }


def _developer_payload(developer: Developer | None = None) -> dict:
    if developer is None:
        return _empty_payload()
    return {
        "developer_id": developer.developer_id or "",
        "developer_name": developer.developer_name or "",
        "email": developer.email or "",
        "role": developer.role or "",
        "skills": developer.skills or "",
    }


def _render_form(prefix: str, initial: dict) -> dict:
    col1, col2 = st.columns(2)
    payload = {
        "developer_id": col1.text_input("developer_id *", value=initial["developer_id"], key=f"{prefix}_developer_id"),
        "developer_name": col2.text_input(
            "developer_name *",
            value=initial["developer_name"],
            key=f"{prefix}_developer_name",
        ),
    }
    col3, col4 = st.columns(2)
    payload["email"] = col3.text_input("email", value=initial["email"], key=f"{prefix}_email")
    payload["role"] = col4.text_input("role", value=initial["role"], key=f"{prefix}_role")
    payload["skills"] = st.text_area("skills", value=initial["skills"], key=f"{prefix}_skills")
    return payload


def _load_developers(keyword: str | None = None) -> list[Developer]:
    with SessionLocal() as db:
        return list_global_developers(db, keyword)


def _project_developers(project_id: int, keyword: str | None = None) -> list[Developer]:
    with SessionLocal() as db:
        return list_project_developers(db, project_id, keyword)


def _existing_developer_ids() -> set[str]:
    with SessionLocal() as db:
        return existing_developer_ids(db)


def _render_developer_table(developers: list[Developer]) -> None:
    rows = [
        {
            "developer_id": developer.developer_id,
            "developer_name": developer.developer_name,
            "email": developer.email,
            "role": developer.role,
            "skills": developer.skills,
        }
        for developer in developers
    ]
    if not rows:
        st.info("표시할 개발자가 없습니다.")
        return
    st.caption(f"최대 500건까지 표시합니다. 현재 표시: {len(rows)}건")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_manage_section(developers: list[Developer], prefix: str) -> None:
    if not developers:
        return
    st.subheader("수정 / 삭제")
    labels = {
        f"{developer.developer_id} | {developer.developer_name} | {developer.email or '-'}": developer.id
        for developer in developers
    }
    selected_label = st.selectbox("개발자 선택", list(labels.keys()), key=f"{prefix}_developer_manage_select")
    selected_pk = labels[selected_label]
    with SessionLocal() as db:
        selected = db.query(Developer).filter(Developer.id == selected_pk).one()
        initial = _developer_payload(selected)
        impact = get_developer_delete_impact(db, selected.developer_id)

    edit_tab, delete_tab = st.tabs(["수정", "삭제"])
    with edit_tab:
        with st.form(f"{prefix}_developer_edit_form"):
            payload = _render_form(f"{prefix}_edit_developer", initial)
            submitted = st.form_submit_button("수정 저장", type="primary")
        if submitted:
            with SessionLocal() as db:
                validation = update_developer(db, selected_pk, payload)
            if validation.is_valid:
                st.success("개발자 정보를 수정했습니다.")
                st.rerun()
            for error in validation.errors:
                st.error(error)

    with delete_tab:
        st.warning(
            "이 삭제는 전역 개발자 마스터를 삭제합니다. 현재 프로젝트 연결만 제거하는 기능은 아직 제공하지 않습니다."
        )
        st.metric("담당 프로그램", impact.assigned_program_count)
        st.metric("프로젝트 연결", impact.project_membership_count)
        confirm = st.checkbox(
            f"{selected.developer_id} 전역 삭제를 확인합니다.",
            key=f"{prefix}_developer_delete_confirm_{selected_pk}",
        )
        if st.button("개발자 삭제", type="primary", disabled=not confirm, key=f"{prefix}_developer_delete_button"):
            with SessionLocal() as db:
                delete_developer(db, selected_pk)
            st.success("개발자를 삭제했습니다.")
            st.rerun()


def _render_project_tab(project_id: int) -> None:
    st.subheader("현재 프로젝트 개발자")
    keyword = st.text_input("검색", placeholder="developer_id, developer_name, email, role")
    developers = _project_developers(project_id, keyword or None)
    _render_developer_table(developers)
    _render_manage_section(developers, "project")


def _render_global_tab() -> None:
    st.subheader("전역 개발자 마스터")
    st.caption("전역 마스터는 여러 프로젝트에서 재사용될 수 있습니다. 현재 프로젝트 연결 여부와 별개로 전체 개발자를 보여줍니다.")
    keyword = st.text_input("전역 검색", placeholder="developer_id, developer_name, email, role")
    developers = _load_developers(keyword or None)
    _render_developer_table(developers)
    _render_manage_section(developers, "global")


def _render_create_tab(project_id: int | None) -> None:
    st.subheader("직접 추가")
    with st.form("developer_create_form"):
        payload = _render_form("create_developer", _empty_payload())
        submitted = st.form_submit_button("개발자 추가", type="primary")
    if not submitted:
        return
    with SessionLocal() as db:
        validation = save_manual_developer(db, payload, project_id=project_id)
    if validation.is_valid:
        st.success("개발자를 추가했습니다.")
        st.rerun()
    for error in validation.errors:
        st.error(error)


def _render_upload_tab(project_id: int | None) -> None:
    st.subheader("Excel 업로드")
    st.caption("저장 전 미리보기와 검증 결과를 확인한 뒤 반영합니다.")
    render_sample_artifact_download("developers")
    uploaded_file = st.file_uploader("개발자 목록 엑셀 파일", type=["xlsx", "xls"])
    if not uploaded_file:
        return

    df = read_developer_excel(uploaded_file.getvalue())
    st.subheader("엑셀 미리보기")
    st.dataframe(df.head(20), use_container_width=True)
    if df.empty:
        st.warning("엑셀 파일에 데이터가 없습니다.")
        return

    validation = validate_developer_import(df, _existing_developer_ids())
    preview_df = pd.DataFrame(validation.preview_rows)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("신규", validation.new_count)
    col2.metric("수정", validation.update_count)
    col3.metric("오류", validation.error_count)
    col4.metric("저장 가능", len(validation.valid_rows))
    st.dataframe(preview_df.head(100), use_container_width=True, hide_index=True)
    if validation.error_count:
        st.warning("오류가 있는 행은 저장에서 제외됩니다. errors 컬럼을 확인하세요.")
    else:
        st.success("저장 전 검증을 통과했습니다.")

    if st.button("검증 통과 행 저장", type="primary", disabled=not validation.valid_rows):
        with SessionLocal() as db:
            result = save_developers_with_result(db, validation.valid_rows, project_id=project_id, source="excel")
        col1, col2, col3 = st.columns(3)
        col1.metric("신규 생성", result.created_count)
        col2.metric("업데이트", result.updated_count)
        col3.metric("건너뜀", result.skipped_count)
        st.success(f"저장 완료: 총 {result.saved_count}명 개발자를 생성/수정했습니다.")


def _render_template_tab() -> None:
    st.subheader("양식 안내")
    st.dataframe(developer_column_guide(), use_container_width=True, hide_index=True)
    st.download_button(
        "개발자 Excel 양식 다운로드",
        data=build_developer_template_excel(),
        file_name="developer_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def render_developer_upload_page() -> None:
    init_db()
    st.title("개발자 관리")
    st.caption("현재 프로젝트 개발자 연결을 기본으로 조회하고, 전역 개발자 마스터를 함께 관리합니다.")
    context = get_current_project_context()
    if context is None:
        st.info("등록된 프로젝트가 없어 전역 개발자 마스터만 관리합니다.")
        tab1, tab2, tab3, tab4 = st.tabs(["전역 마스터", "직접 추가", "Excel 업로드", "양식"])
        with tab1:
            _render_global_tab()
        with tab2:
            _render_create_tab(None)
        with tab3:
            _render_upload_tab(None)
        with tab4:
            _render_template_tab()
        return

    st.caption(f"현재 프로젝트: {context.project_name} ({context.project_id})")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["현재 프로젝트", "전역 마스터", "직접 추가", "Excel 업로드", "양식"])
    with tab1:
        _render_project_tab(context.project_id)
    with tab2:
        _render_global_tab()
    with tab3:
        _render_create_tab(context.project_id)
    with tab4:
        _render_upload_tab(context.project_id)
    with tab5:
        _render_template_tab()

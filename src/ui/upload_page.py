import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Program
from src.services.excel_service import read_program_excel, save_programs_for_project_id
from src.services.program_management_service import (
    delete_program,
    get_program_delete_impact,
    save_manual_program_for_project,
    update_program,
)
from src.services.program_import_service import (
    PROGRAM_TEMPLATE_COLUMNS,
    REQUIRED_PROGRAM_COLUMNS,
    build_program_template_excel,
    program_column_guide,
    validate_program_import,
)
from src.ui.project_context import get_current_project_context
from src.ui.sample_artifact_download import render_sample_artifact_download


TARGET_COLUMNS = PROGRAM_TEMPLATE_COLUMNS


def _guess_source_column(target_column: str, source_columns: list[str]) -> str | None:
    normalized_sources = {column.strip().lower(): column for column in source_columns}
    aliases = {
        "program_id": ["program_id", "프로그램id", "프로그램_id", "프로그램ID", "program id"],
        "program_name": ["program_name", "프로그램명", "program name", "name"],
        "screen_name": ["screen_name", "화면명", "화면", "screen name"],
        "module": ["module", "모듈", "업무", "주요기능"],
        "description": ["description", "설명", "기능설명", "desc"],
        "developer_name": ["developer_name", "개발자명", "담당자", "개발자", "developer name"],
        "developer_email": ["developer_email", "email", "이메일", "개발자이메일", "developer email"],
        "planned_start_date": ["planned_start_date", "계획시작일", "계획 시작일", "planned start date"],
        "planned_end_date": ["planned_end_date", "계획종료일", "계획 종료일", "planned end date"],
        "status": ["status", "상태", "진행상태"],
        "progress_rate": ["progress_rate", "진행률", "progress", "progress rate"],
    }
    for alias in aliases.get(target_column, [target_column]):
        match = normalized_sources.get(alias.strip().lower())
        if match:
            return match
    return None


def _existing_program_ids(project_id: int | None) -> set[str]:
    if project_id is None:
        return set()
    with SessionLocal() as db:
        rows = db.query(Program.program_id).filter(Program.project_id == project_id).all()
    return {str(row[0]) for row in rows if row[0]}


def _empty_program_payload() -> dict:
    return {
        "program_id": "",
        "program_name": "",
        "screen_name": "",
        "module": "",
        "description": "",
        "developer_name": "",
        "developer_email": "",
        "planned_start_date": None,
        "planned_end_date": None,
        "status": "",
        "progress_rate": 0.0,
    }


def _program_payload(program: Program | None = None) -> dict:
    if program is None:
        return _empty_program_payload()
    return {
        "program_id": program.program_id or "",
        "program_name": program.program_name or "",
        "screen_name": program.screen_name or "",
        "module": program.module or "",
        "description": program.description or "",
        "developer_name": program.developer or "",
        "developer_email": "",
        "planned_start_date": program.planned_start_date,
        "planned_end_date": program.planned_end_date,
        "status": program.status or "",
        "progress_rate": float(program.progress_rate or 0),
    }


def _render_program_form(prefix: str, initial: dict) -> dict:
    col1, col2 = st.columns(2)
    payload = {
        "program_id": col1.text_input("program_id *", value=initial["program_id"], key=f"{prefix}_program_id"),
        "program_name": col2.text_input("program_name *", value=initial["program_name"], key=f"{prefix}_program_name"),
    }
    col3, col4 = st.columns(2)
    payload["module"] = col3.text_input("module", value=initial["module"], key=f"{prefix}_module")
    payload["screen_name"] = col4.text_input("screen_name", value=initial["screen_name"], key=f"{prefix}_screen_name")
    payload["description"] = st.text_area("description", value=initial["description"], key=f"{prefix}_description")

    dev_col1, dev_col2 = st.columns(2)
    payload["developer_name"] = dev_col1.text_input(
        "developer_name",
        value=initial["developer_name"],
        key=f"{prefix}_developer_name",
    )
    payload["developer_email"] = dev_col2.text_input(
        "developer_email",
        value=initial["developer_email"],
        key=f"{prefix}_developer_email",
    )

    date_col1, date_col2, status_col, progress_col = st.columns(4)
    payload["planned_start_date"] = date_col1.date_input(
        "planned_start_date",
        value=initial["planned_start_date"],
        key=f"{prefix}_planned_start_date",
    )
    payload["planned_end_date"] = date_col2.date_input(
        "planned_end_date",
        value=initial["planned_end_date"],
        key=f"{prefix}_planned_end_date",
    )
    payload["status"] = status_col.text_input("status", value=initial["status"], key=f"{prefix}_status")
    payload["progress_rate"] = progress_col.number_input(
        "progress_rate",
        min_value=0.0,
        max_value=100.0,
        value=float(initial["progress_rate"]),
        step=1.0,
        key=f"{prefix}_progress_rate",
    )
    return payload


def _load_programs(db: Session, project_id: int, keyword: str | None = None) -> list[Program]:
    query = db.query(Program).filter(Program.project_id == project_id)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (Program.program_id.ilike(pattern))
            | (Program.program_name.ilike(pattern))
            | (Program.module.ilike(pattern))
            | (Program.developer.ilike(pattern))
        )
    return query.order_by(Program.program_id, Program.program_name).limit(500).all()


def _render_column_guide() -> None:
    st.subheader("양식 안내")
    st.dataframe(program_column_guide(), use_container_width=True, hide_index=True)
    st.download_button(
        "프로그램 Excel 양식 다운로드",
        data=build_program_template_excel(),
        file_name="program_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def _render_current_programs(project_id: int | None) -> None:
    st.subheader("현재 프로그램 데이터")
    if project_id is None:
        st.info("기존 프로젝트를 선택하면 등록된 프로그램을 확인할 수 있습니다.")
        return

    keyword = st.text_input("검색", placeholder="program_id, program_name, module, developer")
    with SessionLocal() as db:
        programs = _load_programs(db, project_id, keyword or None)

    rows = [
        {
            "program_id": program.program_id,
            "program_name": program.program_name,
            "module": program.module,
            "screen_name": program.screen_name,
            "developer": program.developer,
            "planned_start_date": program.planned_start_date,
            "planned_end_date": program.planned_end_date,
            "status": program.status,
            "progress_rate": program.progress_rate,
        }
        for program in programs
    ]
    if not rows:
        st.info("등록된 프로그램이 없습니다.")
        return
    st.caption(f"최대 500건까지 표시합니다. 현재 표시: {len(rows)}건")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("수정 / 삭제")
    labels = {
        f"{program.program_id or '-'} | {program.program_name} | {program.module or '-'}": program.id
        for program in programs
    }
    selected_label = st.selectbox("프로그램 선택", list(labels.keys()), key="program_manage_select")
    selected_id = labels[selected_label]

    with SessionLocal() as db:
        selected_program = db.query(Program).filter(Program.id == selected_id).one()
        initial = _program_payload(selected_program)
        impact = get_program_delete_impact(db, selected_id)

    edit_tab, delete_tab = st.tabs(["수정", "삭제"])
    with edit_tab:
        with st.form("program_edit_form"):
            payload = _render_program_form("edit", initial)
            submitted = st.form_submit_button("수정 저장", type="primary")
        if submitted:
            with SessionLocal() as db:
                validation = update_program(db, selected_id, payload)
            if validation.is_valid:
                st.success("프로그램을 수정했습니다.")
                st.rerun()
            for error in validation.errors:
                st.error(error)

    with delete_tab:
        st.warning("프로그램을 삭제하면 연결된 매핑, 리스크, 구현상태 분석도 함께 삭제됩니다.")
        col1, col2, col3 = st.columns(3)
        col1.metric("매핑", impact.mapping_count)
        col2.metric("리스크", impact.risk_count)
        col3.metric("구현상태 분석", impact.implementation_status_count)
        confirm = st.checkbox(
            f"{selected_program.program_id or selected_program.program_name} 삭제를 확인합니다.",
            key=f"delete_confirm_{selected_id}",
        )
        if st.button("프로그램 삭제", type="primary", disabled=not confirm):
            with SessionLocal() as db:
                delete_program(db, selected_id)
            st.success("프로그램을 삭제했습니다.")
            st.rerun()


def _render_manual_create_tab(project_id: int) -> None:
    st.subheader("직접 추가")
    st.caption("Excel 없이 현재 프로젝트에 프로그램을 한 건씩 등록합니다.")
    with st.form("program_create_form"):
        payload = _render_program_form("create", _empty_program_payload())
        submitted = st.form_submit_button("프로그램 추가", type="primary")
    if not submitted:
        return

    init_db()
    with SessionLocal() as db:
        validation = save_manual_program_for_project(db, project_id, payload)
    if validation.is_valid:
        st.success("프로그램을 추가했습니다.")
        st.rerun()
    for error in validation.errors:
        st.error(error)


def _render_column_mapping(source_columns: list[str]) -> dict[str, str | None]:
    st.subheader("컬럼 매핑")
    st.caption("엑셀 컬럼명이 다르면 각 항목에 맞는 원본 컬럼을 선택해 주세요.")

    options = ["선택 안 함"] + source_columns
    mapping: dict[str, str | None] = {}

    for index, target_column in enumerate(TARGET_COLUMNS):
        default_source = _guess_source_column(target_column, source_columns)
        default_index = options.index(default_source) if default_source in options else 0
        required_mark = " *" if target_column in REQUIRED_PROGRAM_COLUMNS else ""
        selected = st.selectbox(
            f"{target_column}{required_mark}",
            options,
            index=default_index,
            key=f"program_column_mapping_{index}_{target_column}",
        )
        mapping[target_column] = None if selected == "선택 안 함" else selected
    return mapping


def _render_upload_tab(project_id: int) -> None:
    st.subheader("Excel 업로드")
    st.caption("저장 전 미리보기와 검증 결과를 확인한 뒤 현재 프로젝트에 반영합니다.")
    render_sample_artifact_download("programs")
    uploaded_file = st.file_uploader("프로그램 목록 엑셀 파일", type=["xlsx", "xls"])

    if not uploaded_file:
        return

    df = read_program_excel(uploaded_file.getvalue())
    st.subheader("엑셀 미리보기")
    st.dataframe(df.head(20), use_container_width=True)

    if df.empty:
        st.warning("엑셀 파일에 데이터가 없습니다.")
        return

    source_columns = [str(column) for column in df.columns]
    mapping = _render_column_mapping(source_columns)
    missing_required = [column for column in REQUIRED_PROGRAM_COLUMNS if not mapping.get(column)]

    if missing_required:
        st.warning(f"필수 컬럼을 매핑해 주세요: {', '.join(missing_required)}")
        return

    validation = validate_program_import(df, mapping, _existing_program_ids(project_id))
    preview_df = pd.DataFrame(validation.preview_rows)
    st.subheader("검증 결과")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("신규", validation.new_count)
    col2.metric("수정", validation.update_count)
    col3.metric("오류", validation.error_count)
    col4.metric("저장 가능", len(validation.valid_rows))

    if not preview_df.empty:
        st.dataframe(preview_df.head(100), use_container_width=True, hide_index=True)
    if validation.error_count:
        st.warning("오류가 있는 행은 저장에서 제외됩니다. errors 컬럼을 확인하세요.")
    else:
        st.success("저장 전 검증을 통과했습니다.")

    if st.button("검증 통과 행 저장", type="primary", disabled=not validation.valid_rows):
        init_db()
        with SessionLocal() as db:
            result = save_programs_for_project_id(db, project_id, validation.valid_rows)

        col1, col2, col3 = st.columns(3)
        col1.metric("신규 생성", result.created_count)
        col2.metric("업데이트", result.updated_count)
        col3.metric("건너뜀", result.skipped_count)
        st.success(f"저장 완료: 총 {result.saved_count}개 프로그램을 생성/수정했습니다.")


def render_upload_page() -> None:
    st.title("프로그램 관리")
    st.caption("프로그램 데이터를 조회하고, 양식을 내려받고, Excel 업로드 전 검증 후 저장합니다.")

    context = get_current_project_context()
    if context is None:
        st.info("먼저 프로젝트/Git 설정에서 프로젝트를 등록한 뒤 프로그램을 관리해 주세요.")
        return
    project_id = context.project_id
    st.caption(f"현재 프로젝트: {context.project_name} ({project_id})")

    tab1, tab2, tab3, tab4 = st.tabs(["현재 데이터", "직접 추가", "Excel 업로드", "양식"])
    with tab1:
        _render_current_programs(project_id)
    with tab2:
        _render_manual_create_tab(project_id)
    with tab3:
        _render_upload_tab(project_id)
    with tab4:
        _render_column_guide()

import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Program, Project
from src.services.excel_service import read_program_excel, save_programs_with_result
from src.services.program_import_service import (
    PROGRAM_TEMPLATE_COLUMNS,
    REQUIRED_PROGRAM_COLUMNS,
    build_program_template_excel,
    program_column_guide,
    validate_program_import,
)


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


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _project_selector() -> tuple[int | None, str]:
    projects = _load_projects()
    options = ["새 프로젝트: Default Project"] + [f"{project.id} - {project.name}" for project in projects]
    selected = st.selectbox("프로젝트 선택", options)
    if selected.startswith("새 프로젝트"):
        return None, "Default Project"
    selected_id = int(selected.split(" - ", 1)[0])
    project = next(project for project in projects if project.id == selected_id)
    return selected_id, project.name


def _existing_program_ids(project_id: int | None) -> set[str]:
    if project_id is None:
        return set()
    with SessionLocal() as db:
        rows = db.query(Program.program_id).filter(Program.project_id == project_id).all()
    return {str(row[0]) for row in rows if row[0]}


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
        query = db.query(Program).filter(Program.project_id == project_id)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                (Program.program_id.ilike(pattern))
                | (Program.program_name.ilike(pattern))
                | (Program.module.ilike(pattern))
                | (Program.developer.ilike(pattern))
            )
        programs = query.order_by(Program.program_id, Program.program_name).limit(500).all()

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


def _render_upload_tab(project_id: int | None, project_name: str) -> None:
    st.subheader("Excel 업로드")
    st.caption("저장 전 미리보기와 검증 결과를 확인한 뒤 반영합니다.")
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
            result = save_programs_with_result(db, project_name.strip() or "Default Project", validation.valid_rows)

        col1, col2, col3 = st.columns(3)
        col1.metric("신규 생성", result.created_count)
        col2.metric("업데이트", result.updated_count)
        col3.metric("건너뜀", result.skipped_count)
        st.success(f"저장 완료: 총 {result.saved_count}개 프로그램을 생성/수정했습니다.")


def render_upload_page() -> None:
    st.title("프로그램 관리")
    st.caption("프로그램 데이터를 조회하고, 양식을 내려받고, Excel 업로드 전 검증 후 저장합니다.")

    project_id, project_name = _project_selector()
    if project_id is None:
        project_name = st.text_input("새 프로젝트명", value=project_name)

    tab1, tab2, tab3 = st.tabs(["현재 데이터", "Excel 업로드", "양식"])
    with tab1:
        _render_current_programs(project_id)
    with tab2:
        _render_upload_tab(project_id, project_name)
    with tab3:
        _render_column_guide()

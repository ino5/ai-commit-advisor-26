from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy.orm import joinedload

from src.db.database import SessionLocal
from src.db.models import Developer, Program
from src.services.development_plan_management_service import (
    bulk_update_plan,
    build_plan_template_excel,
    plan_column_guide,
    save_plan_rows,
    update_program_plan,
    validate_plan_import,
)
from src.services.excel_service import read_program_excel
from src.ui.project_context import require_project_context
from src.ui.sample_artifact_download import render_sample_artifact_download


def _load_programs(project_id: int, keyword: str | None = None) -> list[Program]:
    with SessionLocal() as db:
        query = (
            db.query(Program)
            .options(joinedload(Program.assigned_developer))
            .filter(Program.project_id == project_id)
        )
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                (Program.program_id.ilike(pattern))
                | (Program.program_name.ilike(pattern))
                | (Program.developer.ilike(pattern))
                | (Program.status.ilike(pattern))
            )
        return query.order_by(Program.planned_start_date, Program.program_id).limit(500).all()


def _program_rows(programs: list[Program]) -> list[dict]:
    rows = []
    for program in programs:
        rows.append(
            {
                "program_db_id": program.id,
                "program_id": program.program_id,
                "program_name": program.program_name,
                "developer_id": program.developer_id,
                "developer_name": (
                    program.assigned_developer.developer_name
                    if program.assigned_developer and program.assigned_developer.developer_name
                    else program.developer
                ),
                "planned_start_date": program.planned_start_date,
                "planned_end_date": program.planned_end_date,
                "actual_start_date": program.actual_start_date,
                "actual_end_date": program.actual_end_date,
                "status": program.status,
                "progress_rate": float(program.progress_rate or 0),
            }
        )
    return rows


def _developer_options() -> dict[str, str | None]:
    with SessionLocal() as db:
        developers = db.query(Developer).order_by(Developer.developer_name).all()
    options = {"담당자 없음": None}
    options.update({f"{dev.developer_id} | {dev.developer_name}": dev.developer_id for dev in developers})
    return options


def _render_current_tab(project_id: int) -> None:
    st.subheader("현재 개발계획")
    keyword = st.text_input("검색", placeholder="program_id, program_name, developer, status")
    programs = _load_programs(project_id, keyword or None)
    rows = _program_rows(programs)
    if not rows:
        st.info("표시할 프로그램이 없습니다.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_edit_tab(project_id: int) -> None:
    st.subheader("직접 수정")
    programs = _load_programs(project_id)
    if not programs:
        st.info("수정할 프로그램이 없습니다.")
        return
    labels = {f"{program.program_id or '-'} | {program.program_name}": program for program in programs}
    selected_label = st.selectbox("프로그램 선택", list(labels.keys()), key="plan_edit_select")
    selected = labels[selected_label]
    developer_options = _developer_options()
    current_developer_label = next(
        (label for label, value in developer_options.items() if value == selected.developer_id),
        "담당자 없음",
    )

    with st.form("plan_edit_form"):
        developer_label = st.selectbox(
            "developer_id",
            list(developer_options.keys()),
            index=list(developer_options.keys()).index(current_developer_label),
        )
        col1, col2, col3, col4 = st.columns(4)
        planned_start = col1.date_input("planned_start_date", value=selected.planned_start_date)
        planned_end = col2.date_input("planned_end_date", value=selected.planned_end_date)
        actual_start = col3.date_input("actual_start_date", value=selected.actual_start_date)
        actual_end = col4.date_input("actual_end_date", value=selected.actual_end_date)
        status = st.text_input("status", value=selected.status or "")
        progress_rate = st.number_input(
            "progress_rate",
            min_value=0.0,
            max_value=100.0,
            value=float(selected.progress_rate or 0),
            step=1.0,
        )
        submitted = st.form_submit_button("개발계획 저장", type="primary")
    if not submitted:
        return
    payload = {
        "developer_id": developer_options[developer_label],
        "planned_start_date": planned_start,
        "planned_end_date": planned_end,
        "actual_start_date": actual_start,
        "actual_end_date": actual_end,
        "status": status.strip() or None,
        "progress_rate": progress_rate,
    }
    with SessionLocal() as db:
        validation = update_program_plan(db, selected.id, payload)
    if validation.is_valid:
        st.success("개발계획을 수정했습니다.")
        st.rerun()
    for error in validation.errors:
        st.error(error)


def _existing_ids(project_id: int) -> tuple[set[str], set[str]]:
    with SessionLocal() as db:
        program_ids = {
            str(row[0])
            for row in db.query(Program.program_id).filter(Program.project_id == project_id).all()
            if row[0]
        }
        developer_ids = {str(row[0]) for row in db.query(Developer.developer_id).all() if row[0]}
    return program_ids, developer_ids


def _render_upload_tab(project_id: int) -> None:
    st.subheader("Excel 업로드")
    render_sample_artifact_download(
        "development_plan",
        prerequisite="샘플 개발계획은 같은 Sample Shop의 개발자 목록과 프로그램 목록을 먼저 저장해야 검증을 통과합니다.",
    )
    uploaded_file = st.file_uploader("개발계획 엑셀 파일", type=["xlsx", "xls"])
    if not uploaded_file:
        return
    df = read_program_excel(uploaded_file.getvalue())
    st.subheader("엑셀 미리보기")
    st.dataframe(df.head(20), use_container_width=True)
    if df.empty:
        st.warning("엑셀 파일에 데이터가 없습니다.")
        return
    program_ids, developer_ids = _existing_ids(project_id)
    validation = validate_plan_import(df, program_ids, developer_ids)
    preview_df = pd.DataFrame(validation.preview_rows)
    col1, col2, col3 = st.columns(3)
    col1.metric("수정", validation.update_count)
    col2.metric("오류", validation.error_count)
    col3.metric("저장 가능", len(validation.valid_rows))
    st.dataframe(preview_df.head(100), use_container_width=True, hide_index=True)
    if validation.error_count:
        st.warning("오류가 있는 행은 저장에서 제외됩니다. errors 컬럼을 확인하세요.")
    else:
        st.success("저장 전 검증을 통과했습니다.")
    if st.button("검증 통과 행 저장", type="primary", disabled=not validation.valid_rows):
        with SessionLocal() as db:
            result = save_plan_rows(db, project_id, validation.valid_rows)
        st.success(f"개발계획 저장 완료: 수정 {result.updated_count}건, 건너뜀 {result.skipped_count}건")


def _render_bulk_tab(project_id: int) -> None:
    st.subheader("일괄 업데이트")
    programs = _load_programs(project_id)
    if not programs:
        st.info("업데이트할 프로그램이 없습니다.")
        return
    labels = {f"{program.program_id or '-'} | {program.program_name}": program.id for program in programs}
    selected_labels = st.multiselect("대상 프로그램", list(labels.keys()))
    col1, col2 = st.columns(2)
    status = col1.text_input("status 일괄 변경", placeholder="비워두면 변경하지 않음")
    use_progress = col2.checkbox("progress_rate 변경", value=False)
    progress_rate = col2.number_input("progress_rate", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
    selected_ids = [labels[label] for label in selected_labels]
    if st.button("일괄 업데이트", type="primary", disabled=not selected_ids):
        with SessionLocal() as db:
            result = bulk_update_plan(
                db,
                selected_ids,
                status=status.strip() if status.strip() else None,
                progress_rate=progress_rate if use_progress else None,
            )
        st.success(f"{result.updated_count}건을 업데이트했습니다.")


def _render_template_tab() -> None:
    st.subheader("양식 안내")
    st.dataframe(plan_column_guide(), use_container_width=True, hide_index=True)
    st.download_button(
        "개발계획 Excel 양식 다운로드",
        data=build_plan_template_excel(),
        file_name="development_plan_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def render_development_plan_upload_page() -> None:
    st.title("개발계획 관리")
    st.caption("개발계획을 조회하고, 직접 수정/일괄 수정하거나, Excel 업로드 전 검증 후 저장합니다.")
    context = require_project_context("먼저 프로젝트와 프로그램을 등록해 주세요.")
    if context is None:
        return
    project_id = context.project_id

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["현재 계획", "직접 수정", "Excel 업로드", "일괄 업데이트", "양식"])
    with tab1:
        _render_current_tab(project_id)
    with tab2:
        _render_edit_tab(project_id)
    with tab3:
        _render_upload_tab(project_id)
    with tab4:
        _render_bulk_tab(project_id)
    with tab5:
        _render_template_tab()

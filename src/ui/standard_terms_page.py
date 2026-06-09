import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.standard_term_service import (
    build_standard_term_template_excel,
    existing_standard_term_keys,
    read_standard_term_excel,
    save_standard_terms,
    search_standard_terms,
    standard_term_column_guide,
    validate_standard_term_import,
)


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def _project_selector() -> int | None:
    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return None
    options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected = st.selectbox("프로젝트 선택", list(options.keys()))
    return options[selected]


def _render_column_guide() -> None:
    st.subheader("양식 안내")
    st.caption("필수 입력은 한글 용어와 영문 용어입니다. 약어는 권장 값이며, 검색용 camelCase/snake_case 등은 앱이 자동 파생합니다.")
    st.dataframe(standard_term_column_guide(), use_container_width=True, hide_index=True)
    st.download_button(
        "표준용어 Excel 양식 다운로드",
        data=build_standard_term_template_excel(),
        file_name="standard_terms_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def _render_current_terms(project_id: int) -> None:
    st.subheader("현재 표준용어/표준단어")
    keyword = st.text_input("검색", placeholder="한글 용어, 영문 용어, 약어, 설명")
    with SessionLocal() as db:
        terms = search_standard_terms(db, project_id, keyword or None)

    if not terms:
        st.info("등록된 표준용어/표준단어가 없습니다.")
        return

    rows = [
        {
            "term_type": term.term_type,
            "korean_term": term.korean_term,
            "english_term": term.english_term,
            "abbreviation": term.abbreviation,
            "derived_keywords": ", ".join(term.derived_keywords or []),
            "description": term.description,
        }
        for term in terms
    ]
    st.caption(f"최대 500건까지 표시합니다. 현재 표시: {len(rows)}건")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_upload_tab(project_id: int) -> None:
    st.subheader("Excel 업로드")
    st.caption("저장 전 미리보기와 검증 결과를 확인한 뒤 반영합니다.")
    uploaded_file = st.file_uploader("표준용어/표준단어 엑셀 파일", type=["xlsx", "xls"])
    if not uploaded_file:
        return

    df = read_standard_term_excel(uploaded_file.getvalue())
    st.subheader("엑셀 미리보기")
    st.dataframe(df.head(20), use_container_width=True)

    if df.empty:
        st.warning("엑셀 파일에 데이터가 없습니다.")
        return

    with SessionLocal() as db:
        existing_terms = existing_standard_term_keys(db, project_id)
    validation = validate_standard_term_import(df, existing_terms)

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
        with SessionLocal() as db:
            project = db.get(Project, project_id)
            if project is None:
                st.error("프로젝트를 찾을 수 없습니다.")
                return
            result = save_standard_terms(db, project, validation.valid_rows)

        col1, col2, col3 = st.columns(3)
        col1.metric("신규 생성", result.created_count)
        col2.metric("업데이트", result.updated_count)
        col3.metric("건너뜀", result.skipped_count)
        st.success(f"저장 완료: 총 {result.saved_count}개 표준용어/표준단어를 생성/수정했습니다.")
        st.rerun()


def render_standard_terms_page() -> None:
    st.title("표준용어/표준단어")
    st.caption("SI 산출물의 표준용어와 표준단어를 업로드해 한글 업무 질문을 코드/DB 식별자로 연결합니다.")

    project_id = _project_selector()
    if project_id is None:
        return

    tab1, tab2, tab3 = st.tabs(["현재 데이터", "Excel 업로드", "양식"])
    with tab1:
        _render_current_terms(project_id)
    with tab2:
        _render_upload_tab(project_id)
    with tab3:
        _render_column_guide()

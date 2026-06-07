import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.services.excel_service import normalize_program_rows, read_program_excel, save_programs_with_result


REQUIRED_COLUMNS = ["program_id", "program_name"]
OPTIONAL_COLUMNS = [
    "screen_name",
    "module",
    "description",
    "developer_name",
    "developer_email",
    "planned_start_date",
    "planned_end_date",
    "status",
    "progress_rate",
]
TARGET_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


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


def _render_column_mapping(source_columns: list[str]) -> dict[str, str | None]:
    st.subheader("컬럼 매핑")
    st.caption("엑셀 컬럼명이 다르면 각 항목에 맞는 원본 컬럼을 선택해 주세요.")

    options = ["선택 안 함"] + source_columns
    mapping: dict[str, str | None] = {}

    for index, target_column in enumerate(TARGET_COLUMNS):
        default_source = _guess_source_column(target_column, source_columns)
        default_index = options.index(default_source) if default_source in options else 0
        required_mark = " *" if target_column in REQUIRED_COLUMNS else ""
        selected = st.selectbox(
            f"{target_column}{required_mark}",
            options,
            index=default_index,
            key=f"program_column_mapping_{index}_{target_column}",
        )
        mapping[target_column] = None if selected == "선택 안 함" else selected
    return mapping


def render_upload_page() -> None:
    st.title("프로그램 목록 업로드")
    st.caption("엑셀 파일을 업로드해 Git 커밋 매핑 분석의 기준이 되는 programs 데이터를 저장합니다.")

    project_name = st.text_input("프로젝트명", value="Default Project")
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
    missing_required = [column for column in REQUIRED_COLUMNS if not mapping.get(column)]

    if missing_required:
        st.warning(f"필수 컬럼을 매핑해 주세요: {', '.join(missing_required)}")
        return

    rows = normalize_program_rows(df, mapping)
    preview_df = pd.DataFrame(rows)
    st.subheader("매핑 결과 미리보기")
    st.dataframe(preview_df.drop(columns=["raw_metadata"], errors="ignore").head(20), use_container_width=True)
    st.info(f"저장 대상 {len(rows)}개 행을 읽었습니다.")

    if st.button("프로그램 목록 저장", type="primary"):
        init_db()
        with SessionLocal() as db:
            result = save_programs_with_result(db, project_name.strip() or "Default Project", rows)

        col1, col2, col3 = st.columns(3)
        col1.metric("신규 생성", result.created_count)
        col2.metric("업데이트", result.updated_count)
        col3.metric("건너뜀", result.skipped_count)
        st.success(f"저장 완료: 총 {result.saved_count}개 프로그램을 생성/수정했습니다.")

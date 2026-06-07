import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.services.excel_service import normalize_program_rows, read_program_excel, save_programs


def render_development_plan_upload_page() -> None:
    st.title("개발계획 업로드")
    st.caption(
        "program_id 기준으로 developer_id, planned_start_date, planned_end_date, "
        "actual_start_date, actual_end_date, status, progress_rate 컬럼을 업데이트합니다."
    )

    project_name = st.text_input("프로젝트명", value="Default Project")
    uploaded_file = st.file_uploader("개발계획 엑셀 파일", type=["xlsx", "xls"])

    if not uploaded_file:
        return

    df = read_program_excel(uploaded_file.getvalue())
    st.dataframe(df.head(20), use_container_width=True)
    rows = normalize_program_rows(df)
    st.info(f"미리보기 기준 {len(rows)}개 행을 읽었습니다.")

    if st.button("개발계획 저장", type="primary"):
        init_db()
        with SessionLocal() as db:
            saved_count = save_programs(db, project_name.strip() or "Default Project", rows)
        st.success(f"{saved_count}개 프로그램의 개발계획을 저장했습니다.")

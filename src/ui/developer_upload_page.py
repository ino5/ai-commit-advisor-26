import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.services.excel_service import normalize_developer_rows, read_developer_excel, save_developers


def render_developer_upload_page() -> None:
    st.title("개발자 목록 업로드")
    st.caption("developer_id, developer_name, email, role, skills 컬럼을 저장합니다.")

    uploaded_file = st.file_uploader("개발자 목록 엑셀 파일", type=["xlsx", "xls"])

    if not uploaded_file:
        return

    df = read_developer_excel(uploaded_file.getvalue())
    st.dataframe(df.head(20), use_container_width=True)
    rows = normalize_developer_rows(df)
    st.info(f"미리보기 기준 {len(rows)}개 행을 읽었습니다.")

    if st.button("개발자 목록 저장", type="primary"):
        init_db()
        with SessionLocal() as db:
            saved_count = save_developers(db, rows)
        st.success(f"{saved_count}명 개발자를 저장했습니다.")

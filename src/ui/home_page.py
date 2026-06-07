import streamlit as st

from src.db.database import test_connection


def render_home_page() -> None:
    st.title("AI Commit Advisor")
    st.write(
        "엑셀 프로그램 목록과 로컬 Git 커밋/diff 정보를 기반으로 "
        "LLM/RAG 프로그램-커밋 추천을 확장해가는 PoC입니다."
    )

    st.subheader("환경 상태")
    if st.button("DB 연결 테스트"):
        try:
            test_connection()
            st.success("DB 연결 성공")
        except Exception as exc:
            st.error(f"DB 연결 실패: {exc}")

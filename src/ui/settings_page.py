import streamlit as st

from src.db.database import test_connection
from src.utils.config import settings


def _masked(value: str | None) -> str:
    if not value:
        return "미설정"
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}***{value[-3:]}"


def render_settings_page() -> None:
    st.title("설정")
    st.caption("AI Commit Advisor의 연결 상태와 모델 설정을 확인합니다.")

    st.subheader("시스템 상태")
    col1, col2 = st.columns(2)
    if col1.button("DB 연결 확인", type="primary"):
        try:
            test_connection()
            st.success("DB 연결이 정상입니다.")
        except Exception as exc:
            st.error(f"DB 연결 실패: {exc}")
    col2.metric("pgvector dimension", settings.pgvector_dimension)

    st.divider()
    st.subheader("LLM 설정")
    st.table(
        {
            "항목": ["provider", "base_url", "model", "api_key"],
            "값": [
                settings.llm_provider,
                settings.llm_base_url or "미설정",
                settings.llm_model or "미설정",
                _masked(settings.llm_api_key),
            ],
        }
    )

    st.subheader("Embedding 설정")
    st.table(
        {
            "항목": ["provider", "base_url", "model", "api_key"],
            "값": [
                settings.embedding_provider,
                settings.embedding_base_url or settings.llm_base_url or "미설정",
                settings.embedding_model or "미설정",
                _masked(settings.embedding_api_key),
            ],
        }
    )

    st.info("`.env`를 변경한 뒤에는 Streamlit 앱을 재시작해야 설정이 반영됩니다.")

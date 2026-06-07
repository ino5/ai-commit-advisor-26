import streamlit as st

from src.rag.chunker import chunk_text


def render_rag_page() -> None:
    st.title("RAG")
    st.write("chunk 생성, vector 저장, 검색 기능이 들어갈 예정입니다.")

    sample_text = st.text_area("Chunk 테스트 텍스트", value="프로그램 설명 또는 커밋 diff 텍스트를 입력하세요.")
    if st.button("Chunk 생성 stub"):
        chunks = chunk_text(sample_text, chunk_size=300, overlap=50)
        st.write(f"{len(chunks)}개 chunk 생성")
        st.json(chunks)

    if st.button("Vector 저장 stub"):
        st.info("임베딩 모델과 저장 전략 확정 후 구현합니다.")

    if st.button("검색 stub"):
        st.info("pgvector 유사도 검색은 다음 단계에서 구현합니다.")

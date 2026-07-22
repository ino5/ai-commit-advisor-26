import streamlit as st

from src.services.sample_artifact_service import (
    SAMPLE_ARTIFACT_METADATA,
    SAMPLE_EXCEL_MIME,
    SampleArtifactKind,
    build_sample_artifact_excel,
)


def render_sample_artifact_download(kind: SampleArtifactKind, *, prerequisite: str | None = None) -> None:
    metadata = SAMPLE_ARTIFACT_METADATA[kind]
    st.markdown("#### 샘플 데이터")
    st.caption(
        f"Sample Shop 시연에 사용한 {metadata.display_name} Excel입니다. "
        "내려받은 뒤 아래 업로더에서 미리보기와 검증 결과를 확인해 주세요."
    )
    if prerequisite:
        st.info(prerequisite)
    st.download_button(
        f"샘플 {metadata.display_name} Excel 다운로드",
        data=build_sample_artifact_excel(kind),
        file_name=metadata.file_name,
        mime=SAMPLE_EXCEL_MIME,
        key=f"sample_artifact_download_{kind}",
    )
    st.divider()

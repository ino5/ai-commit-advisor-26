import streamlit as st

from src.ui.ai_progress_page import render_ai_progress_page
from src.ui.code_review_page import render_code_review_page
from src.ui.commit_impact_page import render_commit_impact_page
from src.ui.dashboard_page import render_dashboard_page
from src.ui.development_plan_upload_page import render_development_plan_upload_page
from src.ui.developer_page import render_developer_page
from src.ui.developer_upload_page import render_developer_upload_page
from src.ui.git_page import render_git_page
from src.ui.home_page import render_home_page
from src.ui.mapping_page import render_mapping_page
from src.ui.planning_dashboard_page import render_planning_dashboard_page
from src.ui.program_detail_page import render_program_detail_page
from src.ui.project_page import render_project_page
from src.ui.rag_page import render_rag_page
from src.ui.sample_data_page import render_sample_data_page
from src.ui.settings_page import render_settings_page
from src.ui.upload_page import render_upload_page


st.set_page_config(
    page_title="AI Commit Advisor",
    page_icon="",
    layout="wide",
)


PAGE_GROUPS = {
    "개요": {
        "Home": render_home_page,
    },
    "프로젝트 관리": {
        "프로젝트": render_project_page,
        "개발자": render_developer_page,
        "Program Detail": render_program_detail_page,
        "개발자 목록 업로드": render_developer_upload_page,
        "프로그램 목록 업로드": render_upload_page,
        "개발계획 업로드": render_development_plan_upload_page,
    },
    "데이터 수집": {
        "Git 동기화": render_git_page,
        "샘플 데이터 생성": render_sample_data_page,
    },
    "AI 분석": {
        "Mapping": render_mapping_page,
        "Commit Impact": render_commit_impact_page,
        "RAG 검색": render_rag_page,
        "AI Code Review": render_code_review_page,
    },
    "분석 결과": {
        "Dashboard": render_dashboard_page,
        "개발계획 대시보드": render_planning_dashboard_page,
        "AI Progress": render_ai_progress_page,
    },
    "관리": {
        "설정": render_settings_page,
    },
}


def main() -> None:
    st.sidebar.title("AI Commit Advisor")
    st.sidebar.caption("AI 프로젝트 분석 콘솔")

    group = st.sidebar.radio("업무 영역", list(PAGE_GROUPS.keys()))
    pages = PAGE_GROUPS[group]
    page_name = st.sidebar.radio("화면", list(pages.keys()))

    st.sidebar.divider()
    st.sidebar.caption(f"{group} / {page_name}")
    pages[page_name]()


if __name__ == "__main__":
    main()

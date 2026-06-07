import streamlit as st

from src.ui.dashboard_page import render_dashboard_page
from src.ui.development_plan_upload_page import render_development_plan_upload_page
from src.ui.developer_page import render_developer_page
from src.ui.developer_upload_page import render_developer_upload_page
from src.ui.git_page import render_git_page
from src.ui.home_page import render_home_page
from src.ui.mapping_page import render_mapping_page
from src.ui.planning_dashboard_page import render_planning_dashboard_page
from src.ui.project_page import render_project_page
from src.ui.rag_page import render_rag_page
from src.ui.sample_data_page import render_sample_data_page
from src.ui.upload_page import render_upload_page


st.set_page_config(
    page_title="AI Commit Advisor",
    page_icon="",
    layout="wide",
)


PAGES = {
    "Home": render_home_page,
    "Project": render_project_page,
    "Developer": render_developer_page,
    "개발자 목록 업로드": render_developer_upload_page,
    "프로그램 목록 업로드": render_upload_page,
    "개발계획 업로드": render_development_plan_upload_page,
    "개발계획 대시보드": render_planning_dashboard_page,
    "Mapping": render_mapping_page,
    "샘플 데이터 생성": render_sample_data_page,
    "Git": render_git_page,
    "RAG": render_rag_page,
    "Dashboard": render_dashboard_page,
}


def main() -> None:
    st.sidebar.title("AI Commit Advisor")
    selected_page = st.sidebar.radio("Menu", list(PAGES.keys()))
    PAGES[selected_page]()


if __name__ == "__main__":
    main()

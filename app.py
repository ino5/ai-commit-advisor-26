from collections.abc import Callable

import streamlit as st

from src.ui.ai_progress_page import render_ai_progress_page
from src.ui.code_review_page import render_code_review_page
from src.ui.commit_impact_page import render_commit_impact_page
from src.ui.dashboard_page import render_dashboard_page
from src.ui.development_plan_upload_page import render_development_plan_upload_page
from src.ui.developer_page import render_developer_page
from src.ui.developer_upload_page import render_developer_upload_page
from src.ui.git_history_page import render_git_history_page
from src.ui.git_page import render_git_page
from src.ui.home_page import render_home_page
from src.ui.mapping_page import render_mapping_page
from src.ui.planning_dashboard_page import render_planning_dashboard_page
from src.ui.program_detail_page import render_program_detail_page
from src.ui.project_chat_page import render_project_chat_page
from src.ui.project_context import render_global_project_selector
from src.ui.project_page import render_project_page
from src.ui.rag_page import render_rag_page
from src.ui.risk_page import render_risk_page
from src.ui.sample_data_page import render_sample_data_page
from src.ui.settings_page import render_settings_page
from src.ui.standard_terms_page import render_standard_terms_page
from src.ui.upload_page import render_upload_page


st.set_page_config(
    page_title="AI Commit Advisor",
    page_icon="",
    layout="wide",
)


PAGE_GROUPS = {
    "개요": {
        "Home": render_home_page,
        "Dashboard": render_dashboard_page,
        "AI Progress": render_ai_progress_page,
    },
    "프로젝트 설정": {
        "프로젝트/Git 설정": render_project_page,
        "Git 동기화": render_git_page,
        "샘플 데이터 생성": render_sample_data_page,
    },
    "산출물 관리": {
        "개발자 현황": render_developer_page,
        "개발자 목록": render_developer_upload_page,
        "프로그램 목록": render_upload_page,
        "개발계획": render_development_plan_upload_page,
        "표준용어/표준단어": render_standard_terms_page,
    },
    "분석 실행": {
        "Mapping": render_mapping_page,
        "Risk Analysis": render_risk_page,
        "RAG 검색": render_rag_page,
        "Project Chat": render_project_chat_page,
        "AI Code Review": render_code_review_page,
    },
    "분석 결과": {
        "Program Detail": render_program_detail_page,
        "Git History": render_git_history_page,
        "Commit Impact": render_commit_impact_page,
        "개발계획 대시보드": render_planning_dashboard_page,
    },
    "관리": {
        "설정": render_settings_page,
    },
}

DEFAULT_GROUP = "개요"
DEFAULT_PAGE = "Home"
NAV_STATE_KEY = "sidebar_navigation"


def _inject_sidebar_styles() -> None:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] .stButton {
            margin: 0.1rem 0 0.35rem 0;
        }
        section[data-testid="stSidebar"] .stButton > button {
            align-items: center;
            border: 0;
            border-left: 3px solid transparent;
            border-radius: 6px;
            box-sizing: border-box;
            display: flex;
            font-size: 0.86rem;
            justify-content: flex-start;
            line-height: 1.35;
            min-height: 2.35rem;
            padding: 0.42rem 0.62rem;
            text-align: left;
            width: 100%;
            background: transparent;
            color: inherit;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(49, 51, 63, 0.08);
        }
        section[data-testid="stSidebar"] .stButton > button p {
            font-size: 0.86rem;
            line-height: 1.35;
        }
        section[data-testid="stSidebar"] .nav-current {
            border-top: 1px solid rgba(49, 51, 63, 0.14);
            color: #475569;
            font-size: 0.82rem;
            margin-top: 0.85rem;
            padding-top: 0.7rem;
        }
        section[data-testid="stSidebar"] details {
            margin: 0.35rem 0;
        }
        section[data-testid="stSidebar"] details summary p {
            color: #475569;
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _ensure_navigation_state() -> dict:
    state = st.session_state.get(NAV_STATE_KEY)
    if not isinstance(state, dict):
        state = {"group": DEFAULT_GROUP, "page": DEFAULT_PAGE}
    group = state.get("group") if state.get("group") in PAGE_GROUPS else DEFAULT_GROUP
    page = state.get("page") if state.get("page") in PAGE_GROUPS[group] else next(iter(PAGE_GROUPS[group]))
    state = {"group": group, "page": page}
    st.session_state[NAV_STATE_KEY] = state
    return state


def _select_page(group: str, page: str) -> None:
    st.session_state[NAV_STATE_KEY] = {"group": group, "page": page}


def _render_sidebar_navigation() -> tuple[str, str, Callable[[], None]]:
    _inject_sidebar_styles()
    state = _ensure_navigation_state()

    st.sidebar.title("AI Commit Advisor")
    st.sidebar.caption("업무 흐름 기반 프로젝트 분석 콘솔")
    render_global_project_selector()
    st.sidebar.markdown('<div class="nav-current">현재 위치</div>', unsafe_allow_html=True)
    st.sidebar.caption(f"{state['group']} / {state['page']}")

    for group, pages in PAGE_GROUPS.items():
        with st.sidebar.expander(group, expanded=group == state["group"]):
            for page_name in pages:
                is_active = group == state["group"] and page_name == state["page"]
                if st.button(page_name, key=f"nav_{group}_{page_name}", use_container_width=True):
                    if is_active:
                        continue
                    _select_page(group, page_name)
                    st.rerun()

    selected_group = st.session_state[NAV_STATE_KEY]["group"]
    selected_page = st.session_state[NAV_STATE_KEY]["page"]
    return selected_group, selected_page, PAGE_GROUPS[selected_group][selected_page]


def main() -> None:
    _, _, render_page = _render_sidebar_navigation()
    render_page()


if __name__ == "__main__":
    main()

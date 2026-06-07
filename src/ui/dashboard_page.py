import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.developer_service import get_developer_stats


def render_dashboard_page() -> None:
    st.title("Dashboard")
    init_db()

    with SessionLocal() as db:
        projects = db.query(Project).order_by(Project.name).all()

    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(options.keys()))
    project_id = options[selected_label]

    with SessionLocal() as db:
        stats = get_developer_stats(db, project_id)

    if not stats:
        st.info("표시할 Git 개발자 통계가 없습니다. Git 수집 후 Developer 메뉴에서 자동 추출을 실행해 주세요.")
        return

    df = pd.DataFrame(stats)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("개발자별 커밋 수")
        st.plotly_chart(px.bar(df, x="developer_name", y="commit_count", color="role"), use_container_width=True)
    with col2:
        st.subheader("개발자별 변경 파일 수")
        st.plotly_chart(px.bar(df, x="developer_name", y="file_count", color="role"), use_container_width=True)

    st.dataframe(df, use_container_width=True)

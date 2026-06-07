import pandas as pd
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import GitCommit, Program, Project
from src.services.mapping_service import DEFAULT_CANDIDATES_PER_PROGRAM, MappingService


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def render_mapping_page() -> None:
    st.title("프로그램-커밋 매핑 분석")
    st.caption("프로그램 목록과 Git 커밋 정보를 LLM으로 분석해 관련 커밋 추천 결과를 저장합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트를 등록해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]

    with SessionLocal() as db:
        program_count = db.query(Program).filter(Program.project_id == project_id).count()
        commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()

    metric1, metric2 = st.columns(2)
    metric1.metric("프로그램 수", program_count)
    metric2.metric("Git 커밋 수", commit_count)

    if program_count == 0 or commit_count == 0:
        st.warning("분석하려면 프로그램 목록과 Git 커밋 수집 데이터가 모두 필요합니다.")
        return

    candidates_per_program = st.slider(
        "프로그램별 분석할 커밋 후보 수",
        min_value=1,
        max_value=30,
        value=min(DEFAULT_CANDIDATES_PER_PROGRAM, 5),
        help="로컬 소형 모델은 3~5를 권장합니다. 값이 클수록 분석 시간과 LLM 호출 횟수가 늘어납니다.",
    )
    related_only = st.checkbox("관련 커밋으로 판단된 결과만 저장", value=False)

    if st.button("매핑 분석 실행", type="primary"):
        with SessionLocal() as db:
            service = MappingService()
            with st.spinner("프로그램별 관련 커밋을 분석하고 저장하는 중입니다."):
                result = service.analyze_project(
                    db,
                    project_id=project_id,
                    candidates_per_program=candidates_per_program,
                    related_only=related_only,
                )

        if result.errors:
            for error in result.errors:
                st.error(error)
            return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("분석 건수", result.analyzed_count)
        col2.metric("신규 저장", result.created_count)
        col3.metric("업데이트", result.updated_count)
        col4.metric("건너뜀", result.skipped_count)

        if result.recent_results:
            st.subheader("최근 매핑 결과")
            st.dataframe(pd.DataFrame(result.recent_results), use_container_width=True)
        else:
            st.info("저장된 매핑 결과가 없습니다.")

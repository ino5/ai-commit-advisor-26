import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Project
from src.services.developer_service import (
    ROLE_OPTIONS,
    extract_developers_from_git_commits,
    get_developer_stats,
    update_developer_profile,
)


def _load_projects() -> list[Project]:
    init_db()
    with SessionLocal() as db:
        return db.query(Project).order_by(Project.name).all()


def render_developer_page() -> None:
    st.title("Developer")
    st.caption("Git 커밋 author 정보를 기준으로 개발자를 자동 추출하고 role, skills를 관리합니다.")

    projects = _load_projects()
    if not projects:
        st.info("먼저 프로젝트/Git 설정에서 프로젝트를 등록하고 Git 동기화에서 커밋을 수집해 주세요.")
        return

    project_options = {f"{project.name} ({project.id})": project.id for project in projects}
    selected_label = st.selectbox("프로젝트 선택", list(project_options.keys()))
    project_id = project_options[selected_label]

    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is None:
            st.error("선택한 프로젝트를 찾을 수 없습니다.")
            return

        st.write("Git 저장소:", project.git_repo_path or "-")

        if st.button("개발자 자동 추출", type="primary"):
            result = extract_developers_from_git_commits(db, project.id)
            st.success(
                f"자동 추출 완료: 신규 {result.created_count}명, 갱신 {result.updated_count}명, "
                f"중복/변경없음 {result.skipped_count}명"
            )

        stats = get_developer_stats(db, project.id)

    if not stats:
        st.info("표시할 Git author 데이터가 없습니다. Git 동기화에서 전체 수집 또는 증분 동기화를 먼저 실행해 주세요.")
        return

    df = pd.DataFrame(stats)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("개발자별 커밋 수")
        st.plotly_chart(
            px.bar(df, x="developer_name", y="commit_count", color="role", text="commit_count"),
            use_container_width=True,
        )
    with chart_col2:
        st.subheader("개발자별 변경 파일 수")
        st.plotly_chart(
            px.bar(df, x="developer_name", y="file_count", color="role", text="file_count"),
            use_container_width=True,
        )

    st.subheader("개발자 목록")
    editable_columns = [
        "developer_id",
        "developer_key",
        "developer_name",
        "email",
        "role",
        "skills",
        "commit_count",
        "file_count",
    ]
    edited_df = st.data_editor(
        df[editable_columns],
        use_container_width=True,
        hide_index=True,
        disabled=["developer_id", "developer_key", "developer_name", "email", "commit_count", "file_count"],
        column_config={
            "role": st.column_config.SelectboxColumn("role", options=ROLE_OPTIONS),
            "skills": st.column_config.TextColumn("skills"),
        },
    )

    if st.button("개발자 정보 저장"):
        saved_count = 0
        with SessionLocal() as db:
            for _, row in edited_df.iterrows():
                if pd.isna(row["developer_id"]):
                    continue
                original = df[df["developer_id"] == row["developer_id"]].iloc[0]
                role_changed = (row.get("role") or "") != (original.get("role") or "")
                skills_changed = (row.get("skills") or "") != (original.get("skills") or "")
                if not role_changed and not skills_changed:
                    continue
                update_developer_profile(
                    db,
                    int(row["developer_id"]),
                    str(row.get("role") or "").strip(),
                    str(row.get("skills") or "").strip(),
                )
                saved_count += 1
        st.success(f"{saved_count}명 개발자 정보를 저장했습니다.")

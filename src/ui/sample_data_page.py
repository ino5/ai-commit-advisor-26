from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.generate_sample_development_data import find_program_csv_candidates, generate_sample_data


def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    return output.getvalue()


def _prepare_downloads(developers: pd.DataFrame, programs: pd.DataFrame, plan: pd.DataFrame) -> dict[str, bytes]:
    return {
        "sample_developers.xlsx": _to_excel_bytes(developers),
        "sample_programs.xlsx": _to_excel_bytes(programs.drop(columns=["_keywords"], errors="ignore")),
        "sample_development_plan.xlsx": _to_excel_bytes(plan),
    }


def render_sample_data_page() -> None:
    st.title("샘플 데이터 생성")
    st.caption(
        "앱 서버에서 접근 가능한 Git 저장소의 commit author, commit date, 변경 파일 경로를 분석해 업로드 테스트용 가상 Excel 데이터를 생성합니다. "
        "실제 업무 데이터가 아닌 업로드 테스트용 샘플입니다."
    )

    repo_path = st.text_input("앱 서버 Git 저장소 경로", value=r"C:\dev\ai-advisor-sample-shop")
    repo_path_obj = Path(repo_path).expanduser()
    use_existing_program_csv = st.checkbox(
        "저장소의 기존 프로그램목록 CSV를 우선 사용",
        value=False,
        help="기본 자동 검색 기준은 입력한 Git 저장소 루트의 *프로그램목록*.csv 파일입니다.",
    )
    program_csv_path = None
    if use_existing_program_csv:
        st.info(f"자동 검색 기준 경로: {repo_path_obj.resolve() if repo_path_obj.exists() else repo_path_obj}")
        candidates = find_program_csv_candidates(repo_path_obj.resolve()) if repo_path_obj.exists() else []
        candidate_labels = ["자동 검색 결과 사용"]
        candidate_labels.extend(str(candidate) for candidate in candidates)
        candidate_labels.append("직접 입력")
        selected_csv = st.selectbox("프로그램목록 CSV 선택", candidate_labels)

        if candidates:
            st.caption("발견된 CSV: " + ", ".join(str(candidate) for candidate in candidates))
        else:
            st.warning("입력한 Git 저장소 루트에서 *프로그램목록*.csv 파일을 찾지 못했습니다.")

        if selected_csv == "직접 입력":
            direct_path = st.text_input("프로그램목록 CSV 직접 경로")
            program_csv_path = Path(direct_path).expanduser().resolve() if direct_path.strip() else None
        elif selected_csv != "자동 검색 결과 사용":
            program_csv_path = Path(selected_csv)
    else:
        st.caption("프로그램 목록은 파일 경로, Controller, Service, Mapper/Repository 이름 기준으로 가상 생성됩니다.")

    if st.button("샘플 데이터 생성", type="primary"):
        path = Path(repo_path).expanduser().resolve()
        if not path.exists():
            st.error("앱 서버에서 입력한 경로를 찾을 수 없습니다.")
            return
        if not (path / ".git").exists():
            st.error("앱 서버에서 입력한 경로를 Git 저장소로 확인할 수 없습니다.")
            return
        if use_existing_program_csv and program_csv_path is not None and not program_csv_path.exists():
            st.error("입력한 프로그램목록 CSV 경로가 존재하지 않습니다.")
            return

        try:
            with st.spinner("Git 로그를 분석하고 샘플 Excel 데이터를 생성하는 중입니다."):
                developers, programs, plan = generate_sample_data(
                    path,
                    use_existing_program_csv=use_existing_program_csv,
                    program_csv_path=program_csv_path,
                )
                st.session_state["sample_data_frames"] = {
                    "developers": developers,
                    "programs": programs.drop(columns=["_keywords"], errors="ignore"),
                    "plan": plan,
                }
                st.session_state["sample_data_downloads"] = _prepare_downloads(developers, programs, plan)
        except Exception as exc:
            st.error(f"샘플 데이터 생성 중 오류가 발생했습니다: {exc}")
            return

    frames = st.session_state.get("sample_data_frames")
    downloads = st.session_state.get("sample_data_downloads")
    if not frames or not downloads:
        return

    developers = frames["developers"]
    programs = frames["programs"]
    plan = frames["plan"]

    col1, col2, col3 = st.columns(3)
    col1.metric("개발자", len(developers))
    col2.metric("프로그램", len(programs))
    col3.metric("개발계획", len(plan))

    st.subheader("다운로드")
    dl1, dl2, dl3 = st.columns(3)
    dl1.download_button(
        "개발자 목록",
        downloads["sample_developers.xlsx"],
        file_name="sample_developers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    dl2.download_button(
        "프로그램 목록",
        downloads["sample_programs.xlsx"],
        file_name="sample_programs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    dl3.download_button(
        "개발계획",
        downloads["sample_development_plan.xlsx"],
        file_name="sample_development_plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    dev_tab, program_tab, plan_tab = st.tabs(["개발자", "프로그램", "개발계획"])
    with dev_tab:
        st.dataframe(developers, use_container_width=True)
    with program_tab:
        st.dataframe(programs, use_container_width=True)
    with plan_tab:
        st.dataframe(plan, use_container_width=True)
        if "status" in plan.columns:
            st.bar_chart(plan["status"].value_counts())

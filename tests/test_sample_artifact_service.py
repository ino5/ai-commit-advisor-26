from io import BytesIO

import pandas as pd
import pytest

from src.services.developer_management_service import validate_developer_import
from src.services.development_plan_management_service import validate_plan_import
from src.services.program_import_service import PROGRAM_TEMPLATE_COLUMNS, validate_program_import
from src.services.sample_artifact_service import (
    SAMPLE_ARTIFACT_METADATA,
    build_sample_artifact_excel,
)
from src.services.standard_term_service import validate_standard_term_import
from src.ui import sample_artifact_download


EXPECTED_SHAPES = {
    "developers": (
        6,
        ["developer_id", "developer_name", "email", "role", "skills"],
    ),
    "programs": (
        8,
        ["program_id", "program_name", "module", "screen_name", "description"],
    ),
    "development_plan": (
        8,
        [
            "program_id",
            "developer_id",
            "planned_start_date",
            "planned_end_date",
            "actual_start_date",
            "actual_end_date",
            "status",
            "progress_rate",
        ],
    ),
    "standard_terms": (
        14,
        ["term_type", "korean_term", "english_term", "abbreviation", "description"],
    ),
}


def _read_sample(kind: str) -> pd.DataFrame:
    return pd.read_excel(BytesIO(build_sample_artifact_excel(kind)), engine="openpyxl")


@pytest.mark.parametrize("kind", EXPECTED_SHAPES)
def test_sample_artifact_excel_has_expected_shape(kind: str) -> None:
    expected_rows, expected_columns = EXPECTED_SHAPES[kind]

    df = _read_sample(kind)

    assert len(df) == expected_rows
    assert list(df.columns) == expected_columns
    assert SAMPLE_ARTIFACT_METADATA[kind].file_name.startswith("sample_")


def test_sample_artifact_excels_pass_current_upload_validators() -> None:
    developers = _read_sample("developers")
    programs = _read_sample("programs")
    plan = _read_sample("development_plan")
    standard_terms = _read_sample("standard_terms")

    developer_validation = validate_developer_import(developers, set())
    program_validation = validate_program_import(
        programs,
        {column: column if column in programs.columns else None for column in PROGRAM_TEMPLATE_COLUMNS},
        set(),
    )
    plan_validation = validate_plan_import(
        plan,
        set(programs["program_id"]),
        set(developers["developer_id"]),
    )
    term_validation = validate_standard_term_import(standard_terms, set())

    assert developer_validation.error_count == 0
    assert len(developer_validation.valid_rows) == 6
    assert program_validation.error_count == 0
    assert len(program_validation.valid_rows) == 8
    assert plan_validation.error_count == 0
    assert len(plan_validation.valid_rows) == 8
    assert term_validation.error_count == 0
    assert len(term_validation.valid_rows) == 14


def test_sample_development_plan_keeps_demo_risk_rows() -> None:
    plan = _read_sample("development_plan").set_index("program_id")

    assert plan.loc["SMP-CPN-001", "status"] == "지연"
    assert plan.loc["SMP-CPN-001", "progress_rate"] == 80
    assert plan.loc["SMP-SET-001", "status"] == "지연"
    assert plan.loc["SMP-SET-001", "progress_rate"] == 45
    assert pd.isna(plan.loc["SMP-SET-001", "developer_id"])


class FakeStreamlit:
    def __init__(self) -> None:
        self.download: dict | None = None
        self.info_text: str | None = None

    def markdown(self, _text: str) -> None:
        pass

    def caption(self, _text: str) -> None:
        pass

    def info(self, text: str) -> None:
        self.info_text = text

    def download_button(self, label: str, **kwargs) -> None:
        self.download = {"label": label, **kwargs}

    def divider(self) -> None:
        pass


def test_development_plan_download_renders_prerequisite_and_workbook(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(sample_artifact_download, "st", fake_st)

    sample_artifact_download.render_sample_artifact_download(
        "development_plan",
        prerequisite="개발자와 프로그램을 먼저 저장하세요.",
    )

    assert fake_st.info_text == "개발자와 프로그램을 먼저 저장하세요."
    assert fake_st.download is not None
    assert fake_st.download["label"] == "샘플 개발계획 Excel 다운로드"
    assert fake_st.download["file_name"] == "sample_development_plan.xlsx"
    assert len(pd.read_excel(BytesIO(fake_st.download["data"]))) == 8

from io import BytesIO

import pandas as pd

from src.services.program_import_service import (
    PROGRAM_TEMPLATE_COLUMNS,
    build_program_template_excel,
    validate_program_import,
)


def _mapping(df: pd.DataFrame):
    return {column: column if column in df.columns else None for column in PROGRAM_TEMPLATE_COLUMNS}


def test_validate_program_import_counts_new_update_and_errors():
    df = pd.DataFrame(
        [
            {
                "program_id": "P001",
                "program_name": "Existing",
                "planned_start_date": "2026-06-01",
                "planned_end_date": "2026-06-02",
                "progress_rate": 20,
            },
            {
                "program_id": "P002",
                "program_name": "New",
                "planned_start_date": "2026-06-03",
                "planned_end_date": "2026-06-01",
                "progress_rate": 30,
            },
            {
                "program_id": "P003",
                "program_name": "Bad progress",
                "planned_start_date": "2026-06-01",
                "planned_end_date": "2026-06-02",
                "progress_rate": 120,
            },
            {
                "program_id": "P004",
                "program_name": "Valid new",
                "planned_start_date": "2026-06-01",
                "planned_end_date": "2026-06-02",
                "progress_rate": 100,
            },
        ]
    )

    result = validate_program_import(df, _mapping(df), existing_program_ids={"P001"})

    assert result.update_count == 1
    assert result.new_count == 1
    assert result.error_count == 2
    assert result.skipped_count == 2
    assert len(result.valid_rows) == 2
    assert result.preview_rows[0]["action"] == "update"
    assert result.preview_rows[3]["action"] == "new"


def test_validate_program_import_detects_duplicate_program_id():
    df = pd.DataFrame(
        [
            {"program_id": "P001", "program_name": "A"},
            {"program_id": "P001", "program_name": "B"},
        ]
    )

    result = validate_program_import(df, _mapping(df), existing_program_ids=set())

    assert result.new_count == 1
    assert result.error_count == 1
    assert "중복" in result.preview_rows[1]["errors"]


def test_validate_program_import_reports_missing_required_mapping():
    df = pd.DataFrame([{"program_id": "P001", "program_name": "A"}])
    mapping = _mapping(df)
    mapping["program_name"] = None

    result = validate_program_import(df, mapping, existing_program_ids=set())

    assert result.error_count == 1
    assert result.valid_rows == []
    assert "필수 컬럼 매핑 누락" in result.preview_rows[0]["errors"]


def test_build_program_template_excel_contains_required_columns():
    excel_bytes = build_program_template_excel()
    df = pd.read_excel(BytesIO(excel_bytes))

    assert {"program_id", "program_name"}.issubset(set(df.columns))

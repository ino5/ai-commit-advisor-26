from datetime import date
from io import BytesIO

import pandas as pd

from src.services.development_plan_management_service import (
    build_plan_template_excel,
    validate_plan_import,
    validate_plan_payload,
)


def test_validate_plan_payload_rejects_bad_date_order_and_progress():
    validation = validate_plan_payload(
        {
            "planned_start_date": date(2026, 6, 10),
            "planned_end_date": date(2026, 6, 1),
            "actual_start_date": date(2026, 6, 12),
            "actual_end_date": date(2026, 6, 11),
            "progress_rate": 101,
        }
    )

    assert validation.is_valid is False
    assert len(validation.errors) == 3


def test_validate_plan_import_counts_valid_and_errors():
    df = pd.DataFrame(
        [
            {
                "program_id": "P001",
                "developer_id": "dev001",
                "planned_start_date": "2026-06-01",
                "planned_end_date": "2026-06-10",
                "progress_rate": 10,
            },
            {
                "program_id": "P999",
                "developer_id": "dev001",
                "progress_rate": 20,
            },
            {
                "program_id": "P002",
                "developer_id": "missing",
                "progress_rate": 30,
            },
            {
                "program_id": "P002",
                "developer_id": "dev001",
                "progress_rate": 120,
            },
        ]
    )

    result = validate_plan_import(df, existing_program_ids={"P001", "P002"}, existing_developer_ids={"dev001"})

    assert result.update_count == 1
    assert result.error_count == 3
    assert len(result.valid_rows) == 1
    assert result.preview_rows[0]["action"] == "update"
    assert "등록된 프로그램" in result.preview_rows[1]["errors"]
    assert "developer_id" in result.preview_rows[2]["errors"]
    assert "progress_rate" in result.preview_rows[3]["errors"]


def test_build_plan_template_excel_contains_required_program_id():
    excel_bytes = build_plan_template_excel()
    df = pd.read_excel(BytesIO(excel_bytes))

    assert "program_id" in df.columns
    assert "progress_rate" in df.columns

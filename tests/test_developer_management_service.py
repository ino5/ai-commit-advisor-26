from io import BytesIO

import pandas as pd

from src.services.developer_management_service import (
    build_developer_template_excel,
    normalize_developer_payload,
    validate_developer_import,
    validate_developer_payload,
)


def test_validate_developer_payload_requires_id_and_name():
    validation = validate_developer_payload({"developer_id": "", "developer_name": ""})

    assert validation.is_valid is False
    assert "developer_id" in validation.errors[0]
    assert "developer_name" in validation.errors[1]


def test_normalize_developer_payload_strips_text():
    normalized = normalize_developer_payload(
        {
            "developer_id": " dev001 ",
            "developer_name": " Hong ",
            "email": " hong@example.com ",
            "role": " Backend ",
            "skills": " Python ",
        }
    )

    assert normalized["developer_id"] == "dev001"
    assert normalized["developer_name"] == "Hong"
    assert normalized["email"] == "hong@example.com"
    assert normalized["role"] == "Backend"
    assert normalized["skills"] == "Python"


def test_validate_developer_import_counts_new_update_and_duplicate():
    df = pd.DataFrame(
        [
            {"developer_id": "dev001", "developer_name": "Existing"},
            {"developer_id": "dev002", "developer_name": "New"},
            {"developer_id": "dev002", "developer_name": "Duplicate"},
            {"developer_id": "", "developer_name": "Missing ID"},
        ]
    )

    result = validate_developer_import(df, existing_developer_ids={"dev001"})

    assert result.update_count == 1
    assert result.new_count == 1
    assert result.error_count == 2
    assert len(result.valid_rows) == 2
    assert "중복" in result.preview_rows[2]["errors"]


def test_build_developer_template_excel_contains_required_columns():
    excel_bytes = build_developer_template_excel()
    df = pd.read_excel(BytesIO(excel_bytes))

    assert {"developer_id", "developer_name"}.issubset(set(df.columns))

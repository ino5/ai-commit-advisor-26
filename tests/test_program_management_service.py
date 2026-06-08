from datetime import date

from src.services.program_management_service import (
    ProgramDeleteImpact,
    normalize_program_payload,
    validate_program_payload,
)


def test_validate_program_payload_requires_id_and_name():
    validation = validate_program_payload({"program_id": "", "program_name": ""})

    assert validation.is_valid is False
    assert "program_id" in validation.errors[0]
    assert "program_name" in validation.errors[1]


def test_validate_program_payload_rejects_bad_dates_and_progress():
    validation = validate_program_payload(
        {
            "program_id": "P001",
            "program_name": "Program",
            "planned_start_date": date(2026, 6, 10),
            "planned_end_date": date(2026, 6, 1),
            "progress_rate": 101,
        }
    )

    assert validation.is_valid is False
    assert any("planned_start_date" in error for error in validation.errors)
    assert any("progress_rate" in error for error in validation.errors)


def test_normalize_program_payload_strips_text_and_builds_metadata():
    normalized = normalize_program_payload(
        {
            "program_id": " P001 ",
            "program_name": " Name ",
            "module": " auth ",
            "progress_rate": 50,
            "planned_start_date": date(2026, 6, 1),
        }
    )

    assert normalized["program_id"] == "P001"
    assert normalized["program_name"] == "Name"
    assert normalized["module"] == "auth"
    assert normalized["progress_rate"] == 50.0
    assert normalized["raw_metadata"]["planned_start_date"] == "2026-06-01"


def test_program_delete_impact_total_related_count():
    impact = ProgramDeleteImpact(mapping_count=2, risk_count=3, implementation_status_count=1)

    assert impact.total_related_count == 6

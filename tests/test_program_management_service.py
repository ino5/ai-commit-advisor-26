from datetime import date
import uuid

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import Program, Project
from src.services.program_management_service import (
    ProgramDeleteImpact,
    normalize_program_payload,
    save_manual_program_for_project,
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


def test_save_manual_program_for_project_uses_existing_project_id():
    init_db()
    project_name = f"program-project-{uuid.uuid4()}"
    with SessionLocal() as db:
        project = Project(name=project_name)
        db.add(project)
        db.commit()
        project_id = int(project.id)
        project_count = db.query(Project).count()

        validation = save_manual_program_for_project(
            db,
            project_id,
            {
                "program_id": "P001",
                "program_name": "현재 프로젝트 프로그램",
                "planned_start_date": date(2026, 6, 1),
                "planned_end_date": date(2026, 6, 10),
                "progress_rate": 10,
            },
        )

        assert validation.is_valid is True
        saved = db.query(Program).filter(Program.project_id == project_id, Program.program_id == "P001").one()
        assert saved.program_name == "현재 프로젝트 프로그램"
        assert db.query(Project).count() == project_count

        db.delete(saved)
        db.delete(project)
        db.commit()

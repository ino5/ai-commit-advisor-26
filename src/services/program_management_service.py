from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from src.db.models import Program, ProgramCommitMapping, ProgramImplementationStatus, Project, RiskFinding
from src.services.excel_service import save_programs_for_project_id, save_programs_with_result


@dataclass
class ProgramFormValidation:
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class ProgramDeleteImpact:
    mapping_count: int = 0
    risk_count: int = 0
    implementation_status_count: int = 0

    @property
    def total_related_count(self) -> int:
        return self.mapping_count + self.risk_count + self.implementation_status_count


def validate_program_payload(payload: dict) -> ProgramFormValidation:
    errors: list[str] = []
    if not str(payload.get("program_id") or "").strip():
        errors.append("program_id를 입력하세요.")
    if not str(payload.get("program_name") or "").strip():
        errors.append("program_name을 입력하세요.")

    start = payload.get("planned_start_date")
    end = payload.get("planned_end_date")
    if start and end and start > end:
        errors.append("planned_start_date는 planned_end_date보다 늦을 수 없습니다.")

    progress = payload.get("progress_rate")
    if progress is not None and not 0 <= float(progress) <= 100:
        errors.append("progress_rate는 0부터 100 사이여야 합니다.")
    return ProgramFormValidation(errors)


def normalize_program_payload(payload: dict) -> dict:
    progress = payload.get("progress_rate")
    normalized = {
        "program_id": str(payload.get("program_id") or "").strip(),
        "program_name": str(payload.get("program_name") or "").strip(),
        "screen_name": str(payload.get("screen_name") or "").strip() or None,
        "module": str(payload.get("module") or "").strip() or None,
        "description": str(payload.get("description") or "").strip() or None,
        "developer_name": str(payload.get("developer_name") or "").strip() or None,
        "developer_email": str(payload.get("developer_email") or "").strip() or None,
        "planned_start_date": payload.get("planned_start_date"),
        "planned_end_date": payload.get("planned_end_date"),
        "status": str(payload.get("status") or "").strip() or None,
        "progress_rate": float(progress) if progress is not None else None,
    }
    normalized["raw_metadata"] = {
        key: (value.isoformat() if isinstance(value, date) else value)
        for key, value in normalized.items()
        if key != "raw_metadata"
    }
    return normalized


def save_manual_program(db: Session, project_name: str, payload: dict) -> ProgramFormValidation:
    validation = validate_program_payload(payload)
    if not validation.is_valid:
        return validation
    save_programs_with_result(db, project_name, [normalize_program_payload(payload)])
    return validation


def save_manual_program_for_project(db: Session, project_id: int, payload: dict) -> ProgramFormValidation:
    validation = validate_program_payload(payload)
    if not validation.is_valid:
        return validation
    save_programs_for_project_id(db, project_id, [normalize_program_payload(payload)])
    return validation


def update_program(db: Session, program_id: int, payload: dict) -> ProgramFormValidation:
    validation = validate_program_payload(payload)
    if not validation.is_valid:
        return validation

    program = db.query(Program).filter(Program.id == program_id).one()
    normalized = normalize_program_payload(payload)
    duplicate = (
        db.query(Program.id)
        .filter(
            Program.project_id == program.project_id,
            Program.program_id == normalized["program_id"],
            Program.id != program.id,
        )
        .first()
    )
    if duplicate:
        return ProgramFormValidation(errors=["같은 프로젝트에 동일한 program_id가 이미 있습니다."])

    program.program_id = normalized["program_id"]
    program.program_name = normalized["program_name"]
    program.screen_name = normalized["screen_name"]
    program.module = normalized["module"]
    program.description = normalized["description"]
    program.developer = normalized["developer_name"]
    program.planned_start_date = normalized["planned_start_date"]
    program.planned_end_date = normalized["planned_end_date"]
    program.status = normalized["status"]
    program.progress_rate = normalized["progress_rate"]
    program.raw_metadata = normalized["raw_metadata"]
    db.commit()
    return validation


def get_program_delete_impact(db: Session, program_id: int) -> ProgramDeleteImpact:
    return ProgramDeleteImpact(
        mapping_count=db.query(ProgramCommitMapping).filter(ProgramCommitMapping.program_id == program_id).count(),
        risk_count=db.query(RiskFinding).filter(RiskFinding.program_id == program_id).count(),
        implementation_status_count=(
            db.query(ProgramImplementationStatus)
            .filter(ProgramImplementationStatus.program_id == program_id)
            .count()
        ),
    )


def delete_program(db: Session, program_id: int) -> None:
    program = db.query(Program).filter(Program.id == program_id).one()
    db.delete(program)
    db.commit()


def get_project_name(db: Session, project_id: int) -> str:
    project = db.query(Project).filter(Project.id == project_id).one()
    return project.name

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.db.models import Developer, Program
from src.services.excel_service import normalize_program_rows


PLAN_TEMPLATE_COLUMNS = [
    "program_id",
    "developer_id",
    "planned_start_date",
    "planned_end_date",
    "actual_start_date",
    "actual_end_date",
    "status",
    "progress_rate",
]


@dataclass
class PlanImportValidation:
    valid_rows: list[dict] = field(default_factory=list)
    preview_rows: list[dict] = field(default_factory=list)
    error_count: int = 0
    update_count: int = 0
    skipped_count: int = 0


@dataclass
class PlanFormValidation:
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class PlanUpdateResult:
    updated_count: int = 0
    skipped_count: int = 0


def build_plan_template_excel() -> bytes:
    df = pd.DataFrame(
        [
            {
                "program_id": "P001",
                "developer_id": "dev001",
                "planned_start_date": "2026-06-01",
                "planned_end_date": "2026-06-15",
                "actual_start_date": "",
                "actual_end_date": "",
                "status": "진행중",
                "progress_rate": 50,
            }
        ]
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="development_plan")
    return output.getvalue()


def plan_column_guide() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"column": "program_id", "required": "Y", "description": "업데이트할 프로그램 ID"},
            {"column": "developer_id", "required": "N", "description": "담당 개발자 ID"},
            {"column": "planned_start_date", "required": "N", "description": "계획 시작일. 예: 2026-06-01"},
            {"column": "planned_end_date", "required": "N", "description": "계획 종료일. 예: 2026-06-15"},
            {"column": "actual_start_date", "required": "N", "description": "실제 시작일"},
            {"column": "actual_end_date", "required": "N", "description": "실제 종료일"},
            {"column": "status", "required": "N", "description": "진행 상태. 예: 예정, 진행중, 완료"},
            {"column": "progress_rate", "required": "N", "description": "진행률. 0부터 100 사이 숫자"},
        ]
    )


def _is_blank(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _parse_date(value: Any) -> tuple[bool, date | None]:
    if _is_blank(value):
        return True, None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return False, None
    return True, parsed.date()


def _parse_progress(value: Any) -> tuple[bool, float | None]:
    if _is_blank(value):
        return True, None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False, None
    return 0 <= parsed <= 100, parsed


def validate_plan_payload(payload: dict) -> PlanFormValidation:
    errors = []
    planned_start = payload.get("planned_start_date")
    planned_end = payload.get("planned_end_date")
    actual_start = payload.get("actual_start_date")
    actual_end = payload.get("actual_end_date")
    progress = payload.get("progress_rate")
    if planned_start and planned_end and planned_start > planned_end:
        errors.append("planned_start_date는 planned_end_date보다 늦을 수 없습니다.")
    if actual_start and actual_end and actual_start > actual_end:
        errors.append("actual_start_date는 actual_end_date보다 늦을 수 없습니다.")
    if progress is not None and not 0 <= float(progress) <= 100:
        errors.append("progress_rate는 0부터 100 사이여야 합니다.")
    return PlanFormValidation(errors)


def validate_plan_import(
    df: pd.DataFrame,
    existing_program_ids: set[str],
    existing_developer_ids: set[str],
) -> PlanImportValidation:
    rows = normalize_program_rows(df)
    result = PlanImportValidation()
    seen_program_ids: set[str] = set()

    for index, row in enumerate(rows):
        row_number = index + 2
        program_id = str(row.get("program_id") or "").strip()
        developer_id = str(row.get("developer_id") or "").strip()
        errors = []
        if not program_id:
            errors.append("program_id 값이 비어 있습니다.")
        elif program_id not in existing_program_ids:
            errors.append("등록된 프로그램이 아닙니다.")
        if program_id and program_id in seen_program_ids:
            errors.append("파일 안에 중복된 program_id가 있습니다.")
        if program_id:
            seen_program_ids.add(program_id)
        if developer_id and developer_id not in existing_developer_ids:
            errors.append("등록된 developer_id가 아닙니다.")

        progress_ok, progress = _parse_progress(row.get("progress_rate"))
        if not progress_ok:
            errors.append("progress_rate는 0부터 100 사이 숫자여야 합니다.")
        validation = validate_plan_payload({**row, "progress_rate": progress})
        errors.extend(validation.errors)

        result.preview_rows.append(
            {
                "row_number": row_number,
                "program_id": program_id,
                "developer_id": developer_id,
                "planned_start_date": row.get("planned_start_date"),
                "planned_end_date": row.get("planned_end_date"),
                "actual_start_date": row.get("actual_start_date"),
                "actual_end_date": row.get("actual_end_date"),
                "status": row.get("status"),
                "progress_rate": progress,
                "action": "error" if errors else "update",
                "errors": "; ".join(errors),
            }
        )
        if errors:
            result.error_count += 1
            result.skipped_count += 1
            continue
        result.update_count += 1
        result.valid_rows.append(row)
    return result


def apply_plan_to_program(program: Program, payload: dict, developer: Developer | None = None) -> None:
    if developer is not None:
        program.developer_id = developer.developer_id
        program.developer = developer.developer_name
    if payload.get("planned_start_date") is not None:
        program.planned_start_date = payload.get("planned_start_date")
    if payload.get("planned_end_date") is not None:
        program.planned_end_date = payload.get("planned_end_date")
    if payload.get("actual_start_date") is not None:
        program.actual_start_date = payload.get("actual_start_date")
    if payload.get("actual_end_date") is not None:
        program.actual_end_date = payload.get("actual_end_date")
    if payload.get("status") is not None:
        program.status = payload.get("status") or None
    if payload.get("progress_rate") is not None:
        program.progress_rate = float(payload.get("progress_rate"))


def update_program_plan(db: Session, program_db_id: int, payload: dict) -> PlanFormValidation:
    validation = validate_plan_payload(payload)
    if not validation.is_valid:
        return validation
    program = db.query(Program).filter(Program.id == program_db_id).one()
    developer = None
    developer_id = payload.get("developer_id")
    if developer_id:
        developer = db.query(Developer).filter(Developer.developer_id == developer_id).one_or_none()
        if developer is None:
            return PlanFormValidation(errors=["등록된 developer_id가 아닙니다."])
    apply_plan_to_program(program, payload, developer)
    db.commit()
    return validation


def save_plan_rows(db: Session, project_id: int, rows: list[dict]) -> PlanUpdateResult:
    result = PlanUpdateResult()
    for row in rows:
        program = (
            db.query(Program)
            .filter(Program.project_id == project_id, Program.program_id == row.get("program_id"))
            .one_or_none()
        )
        if program is None:
            result.skipped_count += 1
            continue
        developer = None
        if row.get("developer_id"):
            developer = db.query(Developer).filter(Developer.developer_id == row.get("developer_id")).one_or_none()
        apply_plan_to_program(program, row, developer)
        result.updated_count += 1
    db.commit()
    return result


def bulk_update_plan(
    db: Session,
    program_ids: list[int],
    *,
    status: str | None = None,
    progress_rate: float | None = None,
) -> PlanUpdateResult:
    result = PlanUpdateResult()
    for program in db.query(Program).filter(Program.id.in_(program_ids)).all():
        if status is not None:
            program.status = status or None
        if progress_rate is not None:
            program.progress_rate = float(progress_rate)
        result.updated_count += 1
    db.commit()
    return result

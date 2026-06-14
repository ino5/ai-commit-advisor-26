from io import BytesIO
from dataclasses import dataclass
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.db.models import Developer, Program, Project
from src.services.developer_service import make_developer_key


@dataclass
class ProgramSaveResult:
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0

    @property
    def saved_count(self) -> int:
        return self.created_count + self.updated_count


def read_program_excel(file_bytes: bytes) -> pd.DataFrame:
    """Read an uploaded Excel file and return the raw program list DataFrame."""
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    df.columns = [str(column).strip() for column in df.columns]
    return df


def read_developer_excel(file_bytes: bytes) -> pd.DataFrame:
    """Read an uploaded Excel file and return the raw developer list DataFrame."""
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    df.columns = [str(column).strip() for column in df.columns]
    return df


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def _clean_row(row: dict) -> dict:
    return {str(key).strip(): _clean_value(value) for key, value in row.items()}


def _json_safe_value(value: Any) -> Any:
    value = _clean_value(value)
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _json_safe_row(row: dict) -> dict:
    return {key: _json_safe_value(value) for key, value in row.items()}


def _parse_date(value: Any):
    value = _clean_value(value)
    if value is None:
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _parse_float(value: Any) -> float | None:
    value = _clean_value(value)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def apply_column_mapping(df: pd.DataFrame, column_mapping: dict[str, str | None]) -> pd.DataFrame:
    mapped = pd.DataFrame()
    for target_column, source_column in column_mapping.items():
        if source_column:
            mapped[target_column] = df[source_column]
    return mapped


def normalize_program_rows(df: pd.DataFrame, column_mapping: dict[str, str | None] | None = None) -> list[dict]:
    """Convert program Excel rows into normalized dictionaries."""
    if column_mapping:
        df = apply_column_mapping(df, column_mapping)

    rows = []
    for row in df.to_dict(orient="records"):
        clean = _clean_row(row)
        rows.append(
            {
                "program_id": clean.get("program_id"),
                "program_name": clean.get("program_name"),
                "screen_name": clean.get("screen_name"),
                "module": clean.get("module"),
                "description": clean.get("description"),
                "developer_id": clean.get("developer_id"),
                "developer_name": clean.get("developer_name"),
                "developer_email": clean.get("developer_email") or clean.get("email"),
                "planned_start_date": _parse_date(clean.get("planned_start_date")),
                "planned_end_date": _parse_date(clean.get("planned_end_date")),
                "actual_start_date": _parse_date(clean.get("actual_start_date")),
                "actual_end_date": _parse_date(clean.get("actual_end_date")),
                "progress_rate": _parse_float(clean.get("progress_rate")),
                "status": clean.get("status"),
                "raw_metadata": _json_safe_row(clean),
            }
        )
    return rows


def normalize_developer_rows(df: pd.DataFrame) -> list[dict]:
    """Convert developer Excel rows into normalized dictionaries."""
    rows = []
    for row in df.to_dict(orient="records"):
        clean = _clean_row(row)
        rows.append(
            {
                "developer_key": clean.get("developer_key") or clean.get("developer_id"),
                "developer_id": clean.get("developer_id"),
                "developer_name": clean.get("developer_name"),
                "email": clean.get("email"),
                "role": clean.get("role"),
                "skills": clean.get("skills"),
            }
        )
    return rows


def get_or_create_project(db: Session, project_name: str) -> Project:
    project = db.query(Project).filter(Project.name == project_name).one_or_none()
    if project:
        return project

    project = Project(name=project_name)
    db.add(project)
    db.flush()
    return project


def save_developers(db: Session, rows: list[dict]) -> int:
    saved_count = 0
    for row in rows:
        if not row.get("developer_id") or not row.get("developer_name"):
            continue

        developer = db.query(Developer).filter(Developer.developer_id == row["developer_id"]).one_or_none()
        if developer is None:
            developer = Developer(
                developer_key=row.get("developer_key") or row["developer_id"],
                developer_id=row["developer_id"],
                developer_name=row["developer_name"],
            )
            db.add(developer)

        developer.developer_key = row.get("developer_key") or row["developer_id"]
        developer.developer_name = row["developer_name"]
        developer.email = row.get("email")
        developer.role = row.get("role")
        developer.skills = row.get("skills")
        saved_count += 1

    db.commit()
    return saved_count


def _get_or_create_developer(db: Session, developer_name: str | None, developer_email: str | None, developer_id: str | None) -> Developer | None:
    if not developer_name and not developer_email and not developer_id:
        return None

    developer = None
    if developer_email:
        developer = db.query(Developer).filter(Developer.email == developer_email).one_or_none()
    if developer is None and developer_id:
        developer = db.query(Developer).filter(Developer.developer_id == developer_id).one_or_none()

    safe_name = developer_name or developer_email or developer_id or "unknown"
    safe_key = developer_id or make_developer_key(safe_name, developer_email)

    if developer is None:
        developer = Developer(
            developer_key=safe_key,
            developer_id=safe_key,
            developer_name=safe_name,
            email=developer_email,
        )
        db.add(developer)
        db.flush()
    else:
        if developer_name:
            developer.developer_name = developer_name
        if developer_email and not developer.email:
            developer.email = developer_email
        if not developer.developer_key:
            developer.developer_key = developer.developer_id or safe_key

    return developer


def _save_programs_for_project(db: Session, project: Project, rows: list[dict]) -> ProgramSaveResult:
    result = ProgramSaveResult()

    for row in rows:
        if not row.get("program_id") and not row.get("program_name"):
            result.skipped_count += 1
            continue

        developer_id = row.get("developer_id")
        developer_name = row.get("developer_name")
        developer_email = row.get("developer_email")
        developer = _get_or_create_developer(db, developer_name, developer_email, developer_id)
        if developer is not None:
            developer_id = developer.developer_id
            developer_name = developer.developer_name

        program = None
        if row.get("program_id"):
            program = (
                db.query(Program)
                .filter(Program.project_id == project.id, Program.program_id == row["program_id"])
                .one_or_none()
            )
        if program is None:
            if not row.get("program_name"):
                result.skipped_count += 1
                continue
            program = Program(project_id=project.id, program_name=row["program_name"])
            db.add(program)
            result.created_count += 1
        else:
            result.updated_count += 1

        if row.get("program_id"):
            program.program_id = row.get("program_id")
        if row.get("program_name"):
            program.program_name = row["program_name"]
        if row.get("screen_name") is not None:
            program.screen_name = row.get("screen_name")
        if row.get("module") is not None:
            program.module = row.get("module")
        if row.get("description") is not None:
            program.description = row.get("description")
        if developer_id is not None:
            program.developer_id = developer_id
        if developer_name is not None:
            program.developer = developer_name
        if row.get("planned_start_date") is not None:
            program.planned_start_date = row.get("planned_start_date")
        if row.get("planned_end_date") is not None:
            program.planned_end_date = row.get("planned_end_date")
        if row.get("actual_start_date") is not None:
            program.actual_start_date = row.get("actual_start_date")
        if row.get("actual_end_date") is not None:
            program.actual_end_date = row.get("actual_end_date")
        if row.get("progress_rate") is not None:
            program.progress_rate = row.get("progress_rate")
        if row.get("status") is not None:
            program.status = row.get("status")
        program.raw_metadata = row.get("raw_metadata")

    db.commit()
    return result


def save_programs_with_result(db: Session, project_name: str, rows: list[dict]) -> ProgramSaveResult:
    project = get_or_create_project(db, project_name)
    return _save_programs_for_project(db, project, rows)


def save_programs_for_project_id(db: Session, project_id: int, rows: list[dict]) -> ProgramSaveResult:
    project = db.query(Project).filter(Project.id == project_id).one()
    return _save_programs_for_project(db, project, rows)


def save_programs(db: Session, project_name: str, rows: list[dict]) -> int:
    return save_programs_with_result(db, project_name, rows).saved_count

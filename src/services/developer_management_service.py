from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd
from sqlalchemy.orm import Session

from src.db.models import Developer, Program
from src.services.developer_service import make_developer_key
from src.services.excel_service import normalize_developer_rows


DEVELOPER_TEMPLATE_COLUMNS = ["developer_id", "developer_name", "email", "role", "skills"]


@dataclass
class DeveloperImportValidation:
    valid_rows: list[dict] = field(default_factory=list)
    preview_rows: list[dict] = field(default_factory=list)
    error_count: int = 0
    new_count: int = 0
    update_count: int = 0
    skipped_count: int = 0


@dataclass
class DeveloperSaveResult:
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0

    @property
    def saved_count(self) -> int:
        return self.created_count + self.updated_count


@dataclass
class DeveloperFormValidation:
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class DeveloperDeleteImpact:
    assigned_program_count: int = 0


def build_developer_template_excel() -> bytes:
    df = pd.DataFrame(
        [
            {
                "developer_id": "dev001",
                "developer_name": "홍길동",
                "email": "hong@example.com",
                "role": "Backend Developer",
                "skills": "Python, SQL",
            }
        ]
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="developers")
    return output.getvalue()


def developer_column_guide() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"column": "developer_id", "required": "Y", "description": "개발자 고유 ID. 기존 ID와 같으면 업데이트됩니다."},
            {"column": "developer_name", "required": "Y", "description": "개발자 이름"},
            {"column": "email", "required": "N", "description": "이메일. Git author email 매칭에 사용됩니다."},
            {"column": "role", "required": "N", "description": "역할. 예: Backend Developer"},
            {"column": "skills", "required": "N", "description": "보유 기술 또는 담당 영역"},
        ]
    )


def validate_developer_payload(payload: dict) -> DeveloperFormValidation:
    errors = []
    if not str(payload.get("developer_id") or "").strip():
        errors.append("developer_id를 입력하세요.")
    if not str(payload.get("developer_name") or "").strip():
        errors.append("developer_name을 입력하세요.")
    return DeveloperFormValidation(errors)


def normalize_developer_payload(payload: dict) -> dict:
    developer_id = str(payload.get("developer_id") or "").strip()
    developer_name = str(payload.get("developer_name") or "").strip()
    email = str(payload.get("email") or "").strip() or None
    return {
        "developer_key": make_developer_key(developer_id or developer_name, email),
        "developer_id": developer_id,
        "developer_name": developer_name,
        "email": email,
        "role": str(payload.get("role") or "").strip() or None,
        "skills": str(payload.get("skills") or "").strip() or None,
    }


def validate_developer_import(df: pd.DataFrame, existing_developer_ids: set[str]) -> DeveloperImportValidation:
    rows = normalize_developer_rows(df)
    seen_ids: set[str] = set()
    result = DeveloperImportValidation()

    for index, row in enumerate(rows):
        row_number = index + 2
        developer_id = str(row.get("developer_id") or "").strip()
        developer_name = str(row.get("developer_name") or "").strip()
        errors = []
        if not developer_id:
            errors.append("developer_id 값이 비어 있습니다.")
        if not developer_name:
            errors.append("developer_name 값이 비어 있습니다.")
        if developer_id and developer_id in seen_ids:
            errors.append("파일 안에 중복된 developer_id가 있습니다.")
        if developer_id:
            seen_ids.add(developer_id)

        action = "error" if errors else ("update" if developer_id in existing_developer_ids else "new")
        result.preview_rows.append(
            {
                "row_number": row_number,
                "developer_id": developer_id,
                "developer_name": developer_name,
                "email": row.get("email"),
                "role": row.get("role"),
                "skills": row.get("skills"),
                "action": action,
                "errors": "; ".join(errors),
            }
        )
        if errors:
            result.error_count += 1
            result.skipped_count += 1
            continue
        if action == "update":
            result.update_count += 1
        else:
            result.new_count += 1
        result.valid_rows.append(row)
    return result


def save_developers_with_result(db: Session, rows: list[dict]) -> DeveloperSaveResult:
    result = DeveloperSaveResult()
    for row in rows:
        validation = validate_developer_payload(row)
        if not validation.is_valid:
            result.skipped_count += 1
            continue

        normalized = normalize_developer_payload(row)
        developer = db.query(Developer).filter(Developer.developer_id == normalized["developer_id"]).one_or_none()
        if developer is None:
            developer = Developer(
                developer_key=normalized["developer_key"],
                developer_id=normalized["developer_id"],
                developer_name=normalized["developer_name"],
            )
            db.add(developer)
            result.created_count += 1
        else:
            result.updated_count += 1

        developer.developer_key = normalized["developer_key"]
        developer.developer_name = normalized["developer_name"]
        developer.email = normalized["email"]
        developer.role = normalized["role"]
        developer.skills = normalized["skills"]
    db.commit()
    return result


def save_manual_developer(db: Session, payload: dict) -> DeveloperFormValidation:
    validation = validate_developer_payload(payload)
    if not validation.is_valid:
        return validation
    save_developers_with_result(db, [payload])
    return validation


def update_developer(db: Session, developer_pk: int, payload: dict) -> DeveloperFormValidation:
    validation = validate_developer_payload(payload)
    if not validation.is_valid:
        return validation
    normalized = normalize_developer_payload(payload)
    duplicate = (
        db.query(Developer.id)
        .filter(Developer.developer_id == normalized["developer_id"], Developer.id != developer_pk)
        .first()
    )
    if duplicate:
        return DeveloperFormValidation(errors=["동일한 developer_id가 이미 있습니다."])

    developer = db.query(Developer).filter(Developer.id == developer_pk).one()
    old_developer_id = developer.developer_id
    developer.developer_key = normalized["developer_key"]
    developer.developer_id = normalized["developer_id"]
    developer.developer_name = normalized["developer_name"]
    developer.email = normalized["email"]
    developer.role = normalized["role"]
    developer.skills = normalized["skills"]
    db.query(Program).filter(Program.developer_id == old_developer_id).update(
        {
            Program.developer_id: normalized["developer_id"],
            Program.developer: normalized["developer_name"],
        },
        synchronize_session=False,
    )
    db.commit()
    return validation


def get_developer_delete_impact(db: Session, developer_id: str) -> DeveloperDeleteImpact:
    return DeveloperDeleteImpact(
        assigned_program_count=db.query(Program).filter(Program.developer_id == developer_id).count()
    )


def delete_developer(db: Session, developer_pk: int) -> None:
    developer = db.query(Developer).filter(Developer.id == developer_pk).one()
    db.query(Program).filter(Program.developer_id == developer.developer_id).update(
        {
            Program.developer_id: None,
            Program.developer: None,
        },
        synchronize_session=False,
    )
    db.delete(developer)
    db.commit()

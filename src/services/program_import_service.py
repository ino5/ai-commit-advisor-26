from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

import pandas as pd

from src.services.excel_service import apply_column_mapping, normalize_program_rows


REQUIRED_PROGRAM_COLUMNS = ["program_id", "program_name"]
OPTIONAL_PROGRAM_COLUMNS = [
    "screen_name",
    "module",
    "description",
    "developer_name",
    "developer_email",
    "planned_start_date",
    "planned_end_date",
    "status",
    "progress_rate",
]
PROGRAM_TEMPLATE_COLUMNS = REQUIRED_PROGRAM_COLUMNS + OPTIONAL_PROGRAM_COLUMNS


@dataclass
class ProgramImportValidation:
    valid_rows: list[dict] = field(default_factory=list)
    preview_rows: list[dict] = field(default_factory=list)
    error_count: int = 0
    new_count: int = 0
    update_count: int = 0
    skipped_count: int = 0


def build_program_template_excel() -> bytes:
    df = pd.DataFrame(
        [
            {
                "program_id": "P001",
                "program_name": "로그인 API",
                "screen_name": "로그인",
                "module": "auth",
                "description": "사용자 로그인 인증 처리",
                "developer_name": "홍길동",
                "developer_email": "hong@example.com",
                "planned_start_date": "2026-06-01",
                "planned_end_date": "2026-06-15",
                "status": "진행중",
                "progress_rate": 50,
            }
        ]
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="programs")
    return output.getvalue()


def program_column_guide() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"column": "program_id", "required": "Y", "description": "프로그램 고유 ID. 기존 ID와 같으면 업데이트됩니다."},
            {"column": "program_name", "required": "Y", "description": "프로그램명"},
            {"column": "screen_name", "required": "N", "description": "화면명 또는 메뉴명"},
            {"column": "module", "required": "N", "description": "업무/모듈 구분"},
            {"column": "description", "required": "N", "description": "기능 설명"},
            {"column": "developer_name", "required": "N", "description": "담당 개발자명"},
            {"column": "developer_email", "required": "N", "description": "담당 개발자 이메일"},
            {"column": "planned_start_date", "required": "N", "description": "계획 시작일. 예: 2026-06-01"},
            {"column": "planned_end_date", "required": "N", "description": "계획 종료일. 예: 2026-06-15"},
            {"column": "status", "required": "N", "description": "진행 상태. 예: 예정, 진행중, 완료"},
            {"column": "progress_rate", "required": "N", "description": "진행률. 0부터 100 사이 숫자"},
        ]
    )


def _is_blank(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _parse_date_for_validation(value: Any) -> tuple[bool, Any]:
    if _is_blank(value):
        return True, None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return False, None
    return True, parsed.date()


def _parse_progress_for_validation(value: Any) -> tuple[bool, float | None]:
    if _is_blank(value):
        return True, None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False, None
    return 0 <= parsed <= 100, parsed


def validate_program_import(
    df: pd.DataFrame,
    column_mapping: dict[str, str | None],
    existing_program_ids: set[str],
) -> ProgramImportValidation:
    missing_mappings = [column for column in REQUIRED_PROGRAM_COLUMNS if not column_mapping.get(column)]
    if missing_mappings:
        preview = [
            {
                "row_number": "-",
                "program_id": "",
                "program_name": "",
                "action": "error",
                "errors": f"필수 컬럼 매핑 누락: {', '.join(missing_mappings)}",
            }
        ]
        return ProgramImportValidation(preview_rows=preview, error_count=1, skipped_count=len(df))

    mapped_df = apply_column_mapping(df, column_mapping)
    normalized_rows = normalize_program_rows(df, column_mapping)
    seen_program_ids: set[str] = set()
    result = ProgramImportValidation()

    for index, row in mapped_df.iterrows():
        row_number = int(index) + 2
        normalized = normalized_rows[index]
        program_id = str(normalized.get("program_id") or "").strip()
        program_name = str(normalized.get("program_name") or "").strip()
        errors: list[str] = []

        if not program_id:
            errors.append("program_id 값이 비어 있습니다.")
        if not program_name:
            errors.append("program_name 값이 비어 있습니다.")
        if program_id and program_id in seen_program_ids:
            errors.append("파일 안에 중복된 program_id가 있습니다.")
        if program_id:
            seen_program_ids.add(program_id)

        planned_start_ok, planned_start = _parse_date_for_validation(row.get("planned_start_date"))
        planned_end_ok, planned_end = _parse_date_for_validation(row.get("planned_end_date"))
        if not planned_start_ok:
            errors.append("planned_start_date 날짜 형식이 올바르지 않습니다.")
        if not planned_end_ok:
            errors.append("planned_end_date 날짜 형식이 올바르지 않습니다.")
        if planned_start and planned_end and planned_start > planned_end:
            errors.append("planned_start_date가 planned_end_date보다 늦습니다.")

        progress_ok, progress = _parse_progress_for_validation(row.get("progress_rate"))
        if not progress_ok:
            errors.append("progress_rate는 0부터 100 사이 숫자여야 합니다.")

        action = "error" if errors else ("update" if program_id in existing_program_ids else "new")
        preview = {
            "row_number": row_number,
            "program_id": program_id,
            "program_name": program_name,
            "module": normalized.get("module"),
            "developer_name": normalized.get("developer_name"),
            "planned_start_date": normalized.get("planned_start_date"),
            "planned_end_date": normalized.get("planned_end_date"),
            "progress_rate": progress,
            "action": action,
            "errors": "; ".join(errors),
        }
        result.preview_rows.append(preview)

        if errors:
            result.error_count += 1
            result.skipped_count += 1
            continue
        if action == "update":
            result.update_count += 1
        else:
            result.new_count += 1
        result.valid_rows.append(normalized)

    return result

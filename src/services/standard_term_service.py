from __future__ import annotations

import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.db.models import Project, StandardTerm


REQUIRED_STANDARD_TERM_COLUMNS = ["korean_term", "english_term"]
OPTIONAL_STANDARD_TERM_COLUMNS = ["abbreviation", "term_type", "description"]
STANDARD_TERM_TEMPLATE_COLUMNS = ["term_type", "korean_term", "english_term", "abbreviation", "description"]


@dataclass
class StandardTermImportValidation:
    valid_rows: list[dict] = field(default_factory=list)
    preview_rows: list[dict] = field(default_factory=list)
    error_count: int = 0
    new_count: int = 0
    update_count: int = 0
    skipped_count: int = 0


@dataclass
class StandardTermSaveResult:
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0

    @property
    def saved_count(self) -> int:
        return self.created_count + self.updated_count


def _clean_value(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    stripped = str(value).strip()
    return stripped or None


def _split_words(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = re.sub(r"[_\-/]+", " ", value)
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", normalized)
    return [word.lower() for word in re.findall(r"[A-Za-z0-9]+", normalized)]


def _camel_case(words: list[str]) -> str | None:
    if not words:
        return None
    return words[0] + "".join(word.capitalize() for word in words[1:])


def _pascal_case(words: list[str]) -> str | None:
    if not words:
        return None
    return "".join(word.capitalize() for word in words)


def _snake_case(words: list[str]) -> str | None:
    if not words:
        return None
    return "_".join(words)


def derive_keywords(english_term: str, abbreviation: str | None = None) -> list[str]:
    values: list[str] = []

    def add(value: str | None) -> None:
        if value and value not in values:
            values.append(value)

    for source in [english_term, abbreviation]:
        words = _split_words(source)
        if not words:
            continue
        add(" ".join(words))
        add(_camel_case(words))
        add(_pascal_case(words))
        snake = _snake_case(words)
        add(snake)
        add(snake.upper() if snake else None)
        add("".join(words))
        for word in words:
            add(word)

    return values


def read_standard_term_excel(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    df.columns = [str(column).strip() for column in df.columns]
    return df


def build_standard_term_template_excel() -> bytes:
    df = pd.DataFrame(
        [
            {
                "term_type": "표준용어",
                "korean_term": "결제금액",
                "english_term": "payment amount",
                "abbreviation": "pay amt",
                "description": "결제 요청 금액",
            },
            {
                "term_type": "표준단어",
                "korean_term": "승인",
                "english_term": "authorization",
                "abbreviation": "auth",
                "description": "승인 처리",
            },
        ],
        columns=STANDARD_TERM_TEMPLATE_COLUMNS,
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="standard_terms")
    return output.getvalue()


def standard_term_column_guide() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"column": "korean_term", "required": "Y", "description": "한글 표준용어/표준단어"},
            {"column": "english_term", "required": "Y", "description": "영문 표준명. 예: payment amount"},
            {"column": "abbreviation", "required": "N", "description": "약어. 예: pay amt"},
            {"column": "term_type", "required": "N", "description": "표준용어 또는 표준단어"},
            {"column": "description", "required": "N", "description": "업무 의미 또는 사용 맥락"},
        ]
    )


def normalize_standard_term_rows(df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for row in df.to_dict(orient="records"):
        clean = {str(key).strip(): _clean_value(value) for key, value in row.items()}
        english_term = clean.get("english_term") or ""
        abbreviation = clean.get("abbreviation")
        rows.append(
            {
                "term_type": clean.get("term_type") or "표준용어",
                "korean_term": clean.get("korean_term"),
                "english_term": clean.get("english_term"),
                "abbreviation": abbreviation,
                "description": clean.get("description"),
                "derived_keywords": derive_keywords(english_term, abbreviation),
                "raw_metadata": clean,
            }
        )
    return rows


def validate_standard_term_import(
    df: pd.DataFrame,
    existing_terms: set[tuple[str, str]],
) -> StandardTermImportValidation:
    missing_columns = [column for column in REQUIRED_STANDARD_TERM_COLUMNS if column not in df.columns]
    if missing_columns:
        return StandardTermImportValidation(
            preview_rows=[
                {
                    "row_number": "-",
                    "korean_term": "",
                    "english_term": "",
                    "action": "error",
                    "errors": f"필수 컬럼 누락: {', '.join(missing_columns)}",
                }
            ],
            error_count=1,
            skipped_count=len(df),
        )

    normalized_rows = normalize_standard_term_rows(df)
    seen: set[tuple[str, str]] = set()
    result = StandardTermImportValidation()

    for index, row in enumerate(normalized_rows):
        row_number = index + 2
        korean_term = row.get("korean_term") or ""
        english_term = row.get("english_term") or ""
        term_key = (korean_term.casefold(), english_term.casefold())
        errors: list[str] = []

        if not korean_term:
            errors.append("korean_term 값이 비어 있습니다.")
        if not english_term:
            errors.append("english_term 값이 비어 있습니다.")
        if term_key in seen:
            errors.append("파일 안에 중복된 korean_term + english_term 조합이 있습니다.")
        if korean_term and english_term:
            seen.add(term_key)

        action = "error" if errors else ("update" if term_key in existing_terms else "new")
        result.preview_rows.append(
            {
                "row_number": row_number,
                "term_type": row.get("term_type"),
                "korean_term": korean_term,
                "english_term": english_term,
                "abbreviation": row.get("abbreviation"),
                "derived_keywords": ", ".join(row.get("derived_keywords") or []),
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


def existing_standard_term_keys(db: Session, project_id: int) -> set[tuple[str, str]]:
    rows = db.query(StandardTerm.korean_term, StandardTerm.english_term).filter(StandardTerm.project_id == project_id).all()
    return {(korean.casefold(), english.casefold()) for korean, english in rows}


def save_standard_terms(db: Session, project: Project, rows: list[dict]) -> StandardTermSaveResult:
    result = StandardTermSaveResult()
    for row in rows:
        korean_term = row.get("korean_term")
        english_term = row.get("english_term")
        if not korean_term or not english_term:
            result.skipped_count += 1
            continue

        term = (
            db.query(StandardTerm)
            .filter(
                StandardTerm.project_id == project.id,
                StandardTerm.korean_term == korean_term,
                StandardTerm.english_term == english_term,
            )
            .one_or_none()
        )
        if term is None:
            term = StandardTerm(project_id=project.id, korean_term=korean_term, english_term=english_term)
            db.add(term)
            result.created_count += 1
        else:
            result.updated_count += 1

        term.term_type = row.get("term_type")
        term.abbreviation = row.get("abbreviation")
        term.description = row.get("description")
        term.derived_keywords = row.get("derived_keywords") or derive_keywords(english_term, row.get("abbreviation"))
        term.raw_metadata = row.get("raw_metadata")

    db.commit()
    return result


def search_standard_terms(db: Session, project_id: int, keyword: str | None = None, limit: int = 500) -> list[StandardTerm]:
    query = db.query(StandardTerm).filter(StandardTerm.project_id == project_id)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (StandardTerm.korean_term.ilike(pattern))
            | (StandardTerm.english_term.ilike(pattern))
            | (StandardTerm.abbreviation.ilike(pattern))
            | (StandardTerm.description.ilike(pattern))
        )
    return query.order_by(StandardTerm.korean_term, StandardTerm.english_term).limit(limit).all()

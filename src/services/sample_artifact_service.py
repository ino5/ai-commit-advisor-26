from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import Literal

import pandas as pd

from scripts.create_sample_target_repo import DEVELOPERS, PROGRAM_ROWS, STANDARD_TERM_ROWS
from scripts.generate_sample_development_data import developer_id_for


SampleArtifactKind = Literal["developers", "programs", "development_plan", "standard_terms"]
SAMPLE_EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass(frozen=True)
class SampleArtifactMetadata:
    display_name: str
    file_name: str


SAMPLE_ARTIFACT_METADATA: dict[SampleArtifactKind, SampleArtifactMetadata] = {
    "developers": SampleArtifactMetadata("개발자", "sample_developers.xlsx"),
    "programs": SampleArtifactMetadata("프로그램", "sample_programs.xlsx"),
    "development_plan": SampleArtifactMetadata("개발계획", "sample_development_plan.xlsx"),
    "standard_terms": SampleArtifactMetadata("표준용어/표준단어", "sample_standard_terms.xlsx"),
}


SAMPLE_DEVELOPMENT_PLAN_ROWS = [
    {
        "program_id": "SMP-ORD-001",
        "developer_id": "DEV_MINSU_KIM",
        "planned_start_date": date(2026, 4, 26),
        "planned_end_date": date(2026, 5, 25),
        "actual_start_date": date(2026, 4, 27),
        "actual_end_date": date(2026, 5, 20),
        "status": "완료",
        "progress_rate": 100,
    },
    {
        "program_id": "SMP-ORD-002",
        "developer_id": "DEV_MINSU_KIM",
        "planned_start_date": date(2026, 4, 27),
        "planned_end_date": date(2026, 5, 20),
        "actual_start_date": date(2026, 5, 1),
        "actual_end_date": date(2026, 5, 16),
        "status": "완료",
        "progress_rate": 100,
    },
    {
        "program_id": "SMP-INV-001",
        "developer_id": "DEV_JIHOON_PARK",
        "planned_start_date": date(2026, 4, 25),
        "planned_end_date": date(2026, 6, 1),
        "actual_start_date": date(2026, 4, 28),
        "actual_end_date": date(2026, 5, 30),
        "status": "완료",
        "progress_rate": 100,
    },
    {
        "program_id": "SMP-PAY-001",
        "developer_id": "DEV_JIEUN_LEE",
        "planned_start_date": date(2026, 4, 26),
        "planned_end_date": date(2026, 6, 2),
        "actual_start_date": date(2026, 4, 30),
        "actual_end_date": date(2026, 5, 28),
        "status": "완료",
        "progress_rate": 100,
    },
    {
        "program_id": "SMP-RPT-001",
        "developer_id": "DEV_JIHOON_PARK",
        "planned_start_date": date(2026, 4, 30),
        "planned_end_date": date(2026, 6, 6),
        "actual_start_date": date(2026, 5, 3),
        "actual_end_date": date(2026, 6, 5),
        "status": "완료",
        "progress_rate": 100,
    },
    {
        "program_id": "SMP-UI-001",
        "developer_id": "DEV_JIEUN_LEE",
        "planned_start_date": date(2026, 4, 30),
        "planned_end_date": date(2026, 6, 9),
        "actual_start_date": date(2026, 5, 5),
        "actual_end_date": date(2026, 6, 8),
        "status": "완료",
        "progress_rate": 100,
    },
    {
        "program_id": "SMP-CPN-001",
        "developer_id": "DEV_JIEUN_LEE",
        "planned_start_date": date(2026, 5, 18),
        "planned_end_date": date(2026, 5, 28),
        "actual_start_date": date(2026, 5, 23),
        "actual_end_date": None,
        "status": "지연",
        "progress_rate": 80,
    },
    {
        "program_id": "SMP-SET-001",
        "developer_id": "",
        "planned_start_date": date(2026, 5, 12),
        "planned_end_date": date(2026, 5, 24),
        "actual_start_date": None,
        "actual_end_date": None,
        "status": "지연",
        "progress_rate": 45,
    },
]


def _developer_rows() -> list[dict]:
    return [
        {
            "developer_id": developer_id_for(profile.name, profile.email),
            "developer_name": profile.name,
            "email": profile.email,
            "role": profile.role,
            "skills": profile.skills,
        }
        for profile in sorted(DEVELOPERS.values(), key=lambda item: item.name)
    ]


def _program_rows() -> list[dict]:
    return [
        {
            "program_id": row["프로그램ID"],
            "program_name": row["프로그램명"],
            "module": row["주요기능"],
            "screen_name": row["주요URL/화면"],
            "description": row["기능설명"],
        }
        for row in PROGRAM_ROWS
    ]


def sample_artifact_dataframe(kind: SampleArtifactKind) -> pd.DataFrame:
    if kind == "developers":
        return pd.DataFrame(_developer_rows())
    if kind == "programs":
        return pd.DataFrame(_program_rows())
    if kind == "development_plan":
        return pd.DataFrame(SAMPLE_DEVELOPMENT_PLAN_ROWS)
    if kind == "standard_terms":
        return pd.DataFrame([dict(row) for row in STANDARD_TERM_ROWS])
    raise ValueError(f"지원하지 않는 샘플 산출물 종류입니다: {kind}")


def build_sample_artifact_excel(kind: SampleArtifactKind) -> bytes:
    output = BytesIO()
    sample_artifact_dataframe(kind).to_excel(output, index=False, engine="openpyxl")
    return output.getvalue()

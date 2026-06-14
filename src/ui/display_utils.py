from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def format_date(value) -> str:
    return value.strftime("%Y-%m-%d") if value else "-"


def format_datetime(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def key_value_dataframe(rows: Iterable[tuple[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "항목": label,
                "값": "-" if value is None or value == "" else value,
            }
            for label, value in rows
        ]
    )

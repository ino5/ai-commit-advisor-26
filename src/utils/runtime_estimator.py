from __future__ import annotations

from dataclasses import dataclass


ESTIMATED_SECONDS_PER_ITEM = {
    "embedding": (1, 5),
    "mapping": (10, 30),
    "implementation_analysis": (15, 45),
    "code_review": (20, 60),
}


@dataclass(frozen=True)
class RuntimeEstimate:
    item_count: int
    min_seconds: int
    max_seconds: int

    @property
    def label(self) -> str:
        return format_runtime_range(self.min_seconds, self.max_seconds)


def estimate_runtime(item_count: int, work_type: str) -> RuntimeEstimate:
    min_per_item, max_per_item = ESTIMATED_SECONDS_PER_ITEM.get(work_type, (5, 15))
    safe_count = max(0, int(item_count or 0))
    return RuntimeEstimate(
        item_count=safe_count,
        min_seconds=safe_count * min_per_item,
        max_seconds=safe_count * max_per_item,
    )


def format_runtime_range(min_seconds: int, max_seconds: int) -> str:
    if max_seconds <= 0:
        return "약 0분"
    if max_seconds < 60:
        return f"약 {max(1, min_seconds)}-{max_seconds}초"
    return f"약 {_ceil_minutes(min_seconds)}-{_ceil_minutes(max_seconds)}분"


def _ceil_minutes(seconds: int) -> int:
    return max(1, (max(0, seconds) + 59) // 60)

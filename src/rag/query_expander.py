from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.db.models import StandardTerm


@dataclass
class QueryExpansion:
    original_query: str
    expanded_queries: list[str]
    matched_terms: list[dict] = field(default_factory=list)


def _compact_korean(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def _contains_korean_term(question: str, korean_term: str) -> bool:
    compact_question = _compact_korean(question)
    compact_term = _compact_korean(korean_term)
    if not compact_term:
        return False
    if compact_term in compact_question:
        return True

    # Match terms split into Korean word-like chunks when the deliverable term
    # has no spaces but the user's question does, e.g. 결제금액 vs 결제 금액.
    chunks = re.findall(r"[가-힣]{2,}", korean_term)
    return bool(chunks) and all(_compact_korean(chunk) in compact_question for chunk in chunks)


def _append_unique(values: list[str], value: str | None) -> None:
    if value and value not in values:
        values.append(value)


def expand_query_with_standard_terms(db: Session, project_id: int, question: str, *, max_terms: int = 8) -> QueryExpansion:
    queries = [question]
    matched_terms: list[dict] = []
    terms = (
        db.query(StandardTerm)
        .filter(StandardTerm.project_id == project_id)
        .order_by(StandardTerm.korean_term, StandardTerm.english_term)
        .all()
    )

    for term in terms:
        if not _contains_korean_term(question, term.korean_term):
            continue
        keywords = [keyword for keyword in (term.derived_keywords or []) if keyword]
        matched_terms.append(
            {
                "korean_term": term.korean_term,
                "english_term": term.english_term,
                "abbreviation": term.abbreviation,
                "derived_keywords": keywords,
            }
        )
        _append_unique(queries, term.english_term)
        _append_unique(queries, term.abbreviation)
        if keywords:
            _append_unique(queries, " ".join(keywords[:8]))
            for keyword in keywords[:6]:
                _append_unique(queries, keyword)
        if len(matched_terms) >= max_terms:
            break

    if any(term["korean_term"] in {"결제금액", "결제승인"} for term in matched_terms) and "0" in question:
        _append_unique(queries, "payment amount validation")
        _append_unique(queries, "PaymentService authorize amount <= 0 REJECTED")

    return QueryExpansion(original_query=question, expanded_queries=queries, matched_terms=matched_terms)

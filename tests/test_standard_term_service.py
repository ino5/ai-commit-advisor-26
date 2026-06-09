import pandas as pd

from src.services.standard_term_service import (
    derive_keywords,
    normalize_standard_term_rows,
    validate_standard_term_import,
)


def test_derive_keywords_generates_common_identifier_forms() -> None:
    keywords = derive_keywords("payment amount", "pay amt")

    assert "payment amount" in keywords
    assert "paymentAmount" in keywords
    assert "PaymentAmount" in keywords
    assert "payment_amount" in keywords
    assert "PAYMENT_AMOUNT" in keywords
    assert "paymentamount" in keywords
    assert "payAmt" in keywords
    assert "pay_amt" in keywords
    assert "PAY_AMT" in keywords
    assert "amount" in keywords


def test_validate_standard_term_import_requires_core_columns() -> None:
    df = pd.DataFrame([{"korean_term": "결제금액"}])

    validation = validate_standard_term_import(df, existing_terms=set())

    assert validation.error_count == 1
    assert "필수 컬럼 누락" in validation.preview_rows[0]["errors"]


def test_validate_standard_term_import_detects_duplicate_terms() -> None:
    df = pd.DataFrame(
        [
            {"korean_term": "결제금액", "english_term": "payment amount", "abbreviation": "pay amt"},
            {"korean_term": "결제금액", "english_term": "payment amount", "abbreviation": "pay amt"},
        ]
    )

    validation = validate_standard_term_import(df, existing_terms=set())

    assert validation.error_count == 1
    assert validation.new_count == 1
    assert "중복" in validation.preview_rows[1]["errors"]


def test_normalize_standard_term_rows_derives_keywords() -> None:
    df = pd.DataFrame(
        [
            {
                "term_type": "표준용어",
                "korean_term": "결제금액",
                "english_term": "payment amount",
                "abbreviation": "pay amt",
                "description": "결제 요청 금액",
            }
        ]
    )

    rows = normalize_standard_term_rows(df)

    assert rows[0]["korean_term"] == "결제금액"
    assert "paymentAmount" in rows[0]["derived_keywords"]
    assert "pay_amt" in rows[0]["derived_keywords"]

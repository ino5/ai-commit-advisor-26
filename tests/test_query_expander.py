from src.rag.query_expander import expand_query_with_standard_terms


class FakeQuery:
    def __init__(self, terms):
        self.terms = terms

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.terms


class FakeSession:
    def __init__(self, terms):
        self.terms = terms

    def query(self, *_args, **_kwargs):
        return FakeQuery(self.terms)


class FakeTerm:
    korean_term = "결제금액"
    english_term = "payment amount"
    abbreviation = "pay amt"
    derived_keywords = ["paymentAmount", "payment_amount", "amount", "pay_amt"]


def test_expand_query_uses_standard_terms_for_korean_question() -> None:
    db_session = FakeSession([FakeTerm()])

    expansion = expand_query_with_standard_terms(
        db_session,
        1,
        "결제 금액이 0원 이하일 때 어떤 검증 로직이 동작하나요?",
    )

    assert expansion.original_query.startswith("결제 금액")
    assert "payment amount" in expansion.expanded_queries
    assert "paymentAmount payment_amount amount pay_amt" in expansion.expanded_queries
    assert "PaymentService authorize amount <= 0 REJECTED" in expansion.expanded_queries
    assert expansion.matched_terms[0]["korean_term"] == "결제금액"

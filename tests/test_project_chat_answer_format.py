from src.rag.chat_service import clean_llm_answer


def test_clean_llm_answer_unwraps_json_response_block() -> None:
    raw = '```json\n{"response": "PaymentService.java:1-24 근거에서 amount <= 0이면 REJECTED를 반환합니다."}\n```'

    assert clean_llm_answer(raw) == "PaymentService.java:1-24 근거에서 amount <= 0이면 REJECTED를 반환합니다."


def test_clean_llm_answer_keeps_plain_markdown() -> None:
    raw = "- `src/app.py:1-2`에서 처리합니다."

    assert clean_llm_answer(raw) == raw

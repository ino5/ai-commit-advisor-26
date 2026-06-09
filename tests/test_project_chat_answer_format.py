from src.rag.chat_service import clean_llm_answer, ensure_answer_citations


def test_clean_llm_answer_unwraps_json_response_block() -> None:
    raw = '```json\n{"response": "PaymentService.java:1-24 근거에서 amount <= 0이면 REJECTED를 반환합니다."}\n```'

    assert clean_llm_answer(raw) == "PaymentService.java:1-24 근거에서 amount <= 0이면 REJECTED를 반환합니다."


def test_clean_llm_answer_keeps_plain_markdown() -> None:
    raw = "- `src/app.py:1-2`에서 처리합니다."

    assert clean_llm_answer(raw) == raw


def test_ensure_answer_citations_appends_metadata_line_ranges() -> None:
    answer = "PaymentService authorize 메서드에서 검증합니다."
    sources = [
        {
            "source_id": "src/main/java/PaymentService.java",
            "metadata": {
                "file_path": "src/main/java/PaymentService.java",
                "line_start": 1,
                "line_end": 24,
            },
        }
    ]

    cited = ensure_answer_citations(answer, sources)

    assert "근거:" in cited
    assert "`src/main/java/PaymentService.java:1-24`" in cited

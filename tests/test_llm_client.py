import json

from src.services.llm_client import LLMClient


class _ChatResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(
            {"choices": [{"message": {"content": '{"status":"ok"}'}}]}
        ).encode("utf-8")


def test_local_llm_sends_json_schema_for_structured_request(monkeypatch):
    requests = []

    def fake_urlopen(req, timeout):
        requests.append(json.loads(req.data.decode("utf-8")))
        return _ChatResponse()

    monkeypatch.setattr("src.services.llm_client.request.urlopen", fake_urlopen)
    client = LLMClient(
        provider="local_openai",
        model="qwen2.5-coder-7b-instruct",
        base_url="http://127.0.0.1:12345/v1",
    )
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"],
        "additionalProperties": False,
    }

    response = client.generate(
        "Return JSON",
        response_schema=schema,
        response_schema_name="mapping result",
    )

    assert response.text == '{"status":"ok"}'
    assert requests[0]["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "mapping_result",
            "strict": True,
            "schema": schema,
        },
    }
    assert "reasoning_effort" not in requests[0]


def test_qwen3_request_disables_reasoning(monkeypatch):
    requests = []

    def fake_urlopen(req, timeout):
        requests.append(json.loads(req.data.decode("utf-8")))
        return _ChatResponse()

    monkeypatch.setattr("src.services.llm_client.request.urlopen", fake_urlopen)
    client = LLMClient(
        provider="local_openai",
        model="qwen3.5-4b",
        base_url="http://127.0.0.1:12345/v1",
    )

    client.generate("Analyze this change")

    assert requests[0]["reasoning_effort"] == "none"

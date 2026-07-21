import json

from src.rag.embedding_client import EmbeddingClient


class _EmbeddingResponse:
    def __init__(self, dimension: int = 768, count: int = 1) -> None:
        self.dimension = dimension
        self.count = count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(
            {
                "data": [
                    {"index": index, "embedding": [float(index)] * self.dimension}
                    for index in range(self.count)
                ]
            }
        ).encode("utf-8")


def test_nomic_embedding_adds_distinct_query_and_document_prefixes(monkeypatch):
    payloads = []

    def fake_urlopen(req, timeout):
        payloads.append(json.loads(req.data.decode("utf-8")))
        return _EmbeddingResponse()

    monkeypatch.setattr("src.rag.embedding_client.request.urlopen", fake_urlopen)
    client = EmbeddingClient(
        provider="local_openai",
        model="text-embedding-nomic-embed-text-v2-moe",
        base_url="http://127.0.0.1:12345/v1",
    )

    client.embed_query("결제 승인 한도는 어디에서 확인하나요?")
    client.embed_document("public class PaymentService {}")

    assert payloads[0]["input"] == "search_query: 결제 승인 한도는 어디에서 확인하나요?"
    assert payloads[1]["input"] == "search_document: public class PaymentService {}"
    assert client.embedding_model_name == (
        "local_openai:text-embedding-nomic-embed-text-v2-moe:retrieval-v1"
    )


def test_nomic_embedding_does_not_duplicate_existing_task_prefix(monkeypatch):
    payloads = []

    def fake_urlopen(req, timeout):
        payloads.append(json.loads(req.data.decode("utf-8")))
        return _EmbeddingResponse()

    monkeypatch.setattr("src.rag.embedding_client.request.urlopen", fake_urlopen)
    client = EmbeddingClient(
        provider="local_openai",
        model="nomic-embed-text-v2-moe",
        base_url="http://127.0.0.1:12345/v1",
    )

    client.embed_query("search_query: payment limit")

    assert payloads[0]["input"] == "search_query: payment limit"


def test_non_nomic_embedding_keeps_input_and_storage_key_unchanged(monkeypatch):
    payloads = []

    def fake_urlopen(req, timeout):
        payloads.append(json.loads(req.data.decode("utf-8")))
        return _EmbeddingResponse()

    monkeypatch.setattr("src.rag.embedding_client.request.urlopen", fake_urlopen)
    client = EmbeddingClient(
        provider="local_openai",
        model="qwen3-embedding-0.6b",
        base_url="http://127.0.0.1:12345/v1",
    )

    client.embed_query("한국어 코드 검색")

    assert payloads[0]["input"] == "한국어 코드 검색"
    assert client.embedding_model_name == "local_openai:qwen3-embedding-0.6b"


def test_nomic_embedding_batches_documents_and_preserves_response_order(monkeypatch):
    payloads = []

    def fake_urlopen(req, timeout):
        payload = json.loads(req.data.decode("utf-8"))
        payloads.append(payload)
        return _EmbeddingResponse(count=len(payload["input"]))

    monkeypatch.setattr("src.rag.embedding_client.request.urlopen", fake_urlopen)
    client = EmbeddingClient(
        provider="local_openai",
        model="text-embedding-nomic-embed-text-v2-moe",
        base_url="http://127.0.0.1:12345/v1",
    )

    embeddings = client.embed_documents(["결제 서비스", "배송 서비스"])

    assert payloads[0]["input"] == [
        "search_document: 결제 서비스",
        "search_document: 배송 서비스",
    ]
    assert len(embeddings) == 2
    assert embeddings[0][0] == 0.0
    assert embeddings[1][0] == 1.0

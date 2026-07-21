from __future__ import annotations

import hashlib
import json
from urllib import request
from urllib.error import HTTPError, URLError

from src.utils.config import settings


OPENAI_COMPATIBLE_PROVIDERS = {"openai", "local", "local_openai", "openai-compatible"}
NOMIC_RETRIEVAL_PROFILE = "retrieval-v1"
NOMIC_TASK_PREFIXES = {
    "document": "search_document: ",
    "query": "search_query: ",
}


class EmbeddingClient:
    """Provider-neutral embedding client for mock and OpenAI-compatible embeddings."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider = (provider or settings.embedding_provider or "mock").strip().lower()
        self.model = model or settings.embedding_model or "text-embedding-model"
        self.base_url = (
            base_url or settings.embedding_base_url or settings.llm_base_url or "http://127.0.0.1:1234/v1"
        ).rstrip("/")
        self.api_key = settings.embedding_api_key or settings.llm_api_key

    def embed_text(self, text: str) -> list[float]:
        """Embed a query-like text.

        Retrieval code should prefer ``embed_query`` or ``embed_document`` so
        models with task-specific input conventions receive the right prefix.
        """
        return self.embed_query(text)

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, task="query")

    def embed_document(self, text: str) -> list[float]:
        return self._embed(text, task="document")

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return self._embed_many(texts, task="query")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_many(texts, task="document")

    def _embed(self, text: str, task: str) -> list[float]:
        prepared_text = self._prepare_retrieval_text(text, task)
        if self.provider == "mock":
            return self._embed_mock(prepared_text)
        if self.provider in OPENAI_COMPATIBLE_PROVIDERS:
            return self._embed_openai_compatible(prepared_text)
        raise NotImplementedError(f"Embedding provider is not implemented yet: {self.provider}")

    def _embed_many(self, texts: list[str], task: str) -> list[list[float]]:
        if not texts:
            return []
        prepared_texts = [self._prepare_retrieval_text(text, task) for text in texts]
        if self.provider == "mock":
            return [self._embed_mock(text) for text in prepared_texts]
        if self.provider in OPENAI_COMPATIBLE_PROVIDERS:
            return self._embed_openai_compatible_many(prepared_texts)
        raise NotImplementedError(f"Embedding provider is not implemented yet: {self.provider}")

    @property
    def embedding_model_name(self) -> str:
        name = f"{self.provider}:{self.model}"
        if self._uses_nomic_retrieval_profile:
            return f"{name}:{NOMIC_RETRIEVAL_PROFILE}"
        return name

    @property
    def _uses_nomic_retrieval_profile(self) -> bool:
        return "nomic-embed-text" in self.model.lower()

    def _prepare_retrieval_text(self, text: str, task: str) -> str:
        if not self._uses_nomic_retrieval_profile:
            return text
        try:
            prefix = NOMIC_TASK_PREFIXES[task]
        except KeyError as exc:
            raise ValueError(f"Unsupported embedding task: {task}") from exc
        if text.startswith(prefix):
            return text
        return f"{prefix}{text}"

    def _embed_mock(self, text: str) -> list[float]:
        # Deterministic hashing vector. It is crude, but useful for local smoke tests
        # and keeps pgvector cosine search non-zero without external services.
        dimension = settings.pgvector_dimension
        vector = [0.0] * dimension
        tokens = text.lower().split()
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        if not tokens:
            vector[0] = 1.0
        return vector

    def _embed_openai_compatible(self, text: str) -> list[float]:
        return self._request_openai_compatible_embeddings(text)[0]

    def _embed_openai_compatible_many(self, texts: list[str]) -> list[list[float]]:
        return self._request_openai_compatible_embeddings(texts)

    def _request_openai_compatible_embeddings(self, inputs: str | list[str]) -> list[list[float]]:
        if not self.base_url:
            raise RuntimeError("EMBEDDING_BASE_URL or LLM_BASE_URL must be set for OpenAI-compatible embeddings")
        if not self.model or self.model == "text-embedding-model":
            raise RuntimeError("EMBEDDING_MODEL must be set for OpenAI-compatible embeddings")

        payload = {"model": self.model, "input": inputs}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(f"{self.base_url}/embeddings", data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Embedding HTTP error {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"Embedding connection failed: {exc.reason}") from exc

        data_items = raw.get("data")
        expected_count = 1 if isinstance(inputs, str) else len(inputs)
        if not isinstance(data_items, list) or len(data_items) != expected_count:
            actual_count = len(data_items) if isinstance(data_items, list) else 0
            raise RuntimeError(
                f"Embedding response item count mismatch: got {actual_count}, expected {expected_count}"
            )

        indexed_items = []
        for position, item in enumerate(data_items):
            if not isinstance(item, dict):
                raise RuntimeError(f"Embedding response data[{position}] was not an object")
            index = item.get("index", position)
            if not isinstance(index, int) or index < 0 or index >= expected_count:
                raise RuntimeError(f"Embedding response contained an invalid index: {index}")
            indexed_items.append((index, item))

        indexed_items.sort(key=lambda pair: pair[0])
        if [index for index, _ in indexed_items] != list(range(expected_count)):
            raise RuntimeError("Embedding response indexes were missing or duplicated")

        embeddings: list[list[float]] = []
        for index, item in indexed_items:
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise RuntimeError(f"Embedding response did not contain data[{index}].embedding")
            if len(embedding) != settings.pgvector_dimension:
                raise RuntimeError(
                    f"Embedding dimension mismatch: got {len(embedding)}, expected {settings.pgvector_dimension}"
                )
            embeddings.append([float(value) for value in embedding])
        return embeddings

    def test_connection(self) -> tuple[bool, str]:
        try:
            vector = self.embed_query("embedding connection test")
        except Exception as exc:
            return False, str(exc)
        return True, f"Embedding OK: model={self.embedding_model_name}, dimension={len(vector)}"

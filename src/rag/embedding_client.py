from __future__ import annotations

import hashlib
import json
from urllib import request
from urllib.error import HTTPError, URLError

from src.utils.config import settings


OPENAI_COMPATIBLE_PROVIDERS = {"openai", "local", "local_openai", "openai-compatible"}


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
        if self.provider == "mock":
            return self._embed_mock(text)
        if self.provider in OPENAI_COMPATIBLE_PROVIDERS:
            return self._embed_openai_compatible(text)
        raise NotImplementedError(f"Embedding provider is not implemented yet: {self.provider}")

    @property
    def embedding_model_name(self) -> str:
        return f"{self.provider}:{self.model}"

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
        if not self.base_url:
            raise RuntimeError("EMBEDDING_BASE_URL or LLM_BASE_URL must be set for OpenAI-compatible embeddings")
        if not self.model or self.model == "text-embedding-model":
            raise RuntimeError("EMBEDDING_MODEL must be set for OpenAI-compatible embeddings")

        payload = {"model": self.model, "input": text}
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

        embedding = raw.get("data", [{}])[0].get("embedding")
        if not isinstance(embedding, list):
            raise RuntimeError("Embedding response did not contain data[0].embedding")
        if len(embedding) != settings.pgvector_dimension:
            raise RuntimeError(
                f"Embedding dimension mismatch: got {len(embedding)}, expected {settings.pgvector_dimension}"
            )
        return [float(value) for value in embedding]

    def test_connection(self) -> tuple[bool, str]:
        try:
            vector = self.embed_text("embedding connection test")
        except Exception as exc:
            return False, str(exc)
        return True, f"Embedding OK: model={self.embedding_model_name}, dimension={len(vector)}"

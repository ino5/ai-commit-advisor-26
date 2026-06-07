from src.utils.config import settings


class EmbeddingClient:
    """Provider-neutral embedding client shell."""

    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self.provider = provider or settings.embedding_provider
        self.model = model or settings.embedding_model
        self.api_key = settings.embedding_api_key

    def embed_text(self, text: str) -> list[float]:
        if self.provider == "mock":
            # Deterministic placeholder vector; replace with real embedding provider later.
            return [0.0] * settings.pgvector_dimension
        raise NotImplementedError(f"Embedding provider is not implemented yet: {self.provider}")

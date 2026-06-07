from sqlalchemy.orm import Session

from src.rag.embedding_client import EmbeddingClient
from src.rag.vector_store import VectorStore


class Retriever:
    """Query-time RAG retrieval placeholder."""

    def __init__(self, db: Session, embedding_client: EmbeddingClient | None = None) -> None:
        self.embedding_client = embedding_client or EmbeddingClient()
        self.vector_store = VectorStore(db)

    def retrieve(self, query: str, limit: int = 5) -> list[dict]:
        query_embedding = self.embedding_client.embed_text(query)
        chunks = self.vector_store.search_similar(query_embedding, limit=limit)
        return [{"id": chunk.id, "text": chunk.chunk_text, "source_type": chunk.source_type} for chunk in chunks]

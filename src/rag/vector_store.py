from sqlalchemy.orm import Session

from src.db.models import DocumentChunk, VectorItem


class VectorStore:
    """Storage shell for chunks and vectors."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_chunk(self, source_type: str, chunk_text: str, source_id: str | None = None) -> DocumentChunk:
        chunk = DocumentChunk(source_type=source_type, source_id=source_id, chunk_text=chunk_text)
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def save_vector(self, chunk_id: int, embedding: list[float], embedding_model: str | None = None) -> VectorItem:
        item = VectorItem(chunk_id=chunk_id, embedding=embedding, embedding_model=embedding_model)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def search_similar(self, query_embedding: list[float], limit: int = 5) -> list[DocumentChunk]:
        # pgvector similarity query will be implemented after embedding strategy is finalized.
        _ = query_embedding
        _ = limit
        return []

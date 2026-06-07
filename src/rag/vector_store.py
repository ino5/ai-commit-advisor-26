from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import DocumentChunk, VectorItem


@dataclass
class EmbeddingBuildResult:
    created_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    errors: list[str] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


class VectorStore:
    """Storage shell for chunks and vectors."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_chunk(
        self,
        source_type: str,
        chunk_text: str,
        source_id: str | None = None,
        project_id: int | None = None,
        chunk_index: int = 0,
        raw_metadata: dict | None = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            project_id=project_id,
            source_type=source_type,
            source_id=source_id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            raw_metadata=raw_metadata,
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def save_vector(self, chunk_id: int, embedding: list[float], embedding_model: str | None = None) -> VectorItem:
        existing = (
            self.db.query(VectorItem)
            .filter(VectorItem.chunk_id == chunk_id, VectorItem.embedding_model == embedding_model)
            .one_or_none()
        )
        if existing is not None:
            return existing

        item = VectorItem(chunk_id=chunk_id, embedding=embedding, embedding_model=embedding_model)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def has_vector(self, chunk_id: int, embedding_model: str | None) -> bool:
        return (
            self.db.query(VectorItem.id)
            .filter(VectorItem.chunk_id == chunk_id, VectorItem.embedding_model == embedding_model)
            .first()
            is not None
        )

    def embed_missing_chunks(
        self,
        embedding_client,
        project_id: int | None = None,
        source_types: list[str] | None = None,
        limit: int | None = None,
    ) -> EmbeddingBuildResult:
        result = EmbeddingBuildResult()
        query = self.db.query(DocumentChunk).order_by(DocumentChunk.id)
        if project_id is not None:
            query = query.filter(DocumentChunk.project_id == project_id)
        if source_types:
            query = query.filter(DocumentChunk.source_type.in_(source_types))
        if limit is not None:
            query = query.limit(limit)

        for chunk in query.all():
            if self.has_vector(chunk.id, embedding_client.embedding_model_name):
                result.skipped_count += 1
                continue

            try:
                embedding = embedding_client.embed_text(chunk.chunk_text)
                self.save_vector(chunk.id, embedding, embedding_client.embedding_model_name)
                metadata = dict(chunk.raw_metadata or {})
                metadata["embedding_status"] = "completed"
                metadata["embedding_model"] = embedding_client.embedding_model_name
                chunk.raw_metadata = metadata
                result.created_count += 1
            except Exception as exc:
                metadata = dict(chunk.raw_metadata or {})
                metadata["embedding_status"] = "failed"
                metadata["embedding_error"] = str(exc)
                chunk.raw_metadata = metadata
                result.failed_count += 1
                result.errors.append(f"chunk_id={chunk.id}: {exc}")
            self.db.commit()
        return result

    def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 5,
        project_id: int | None = None,
        source_types: list[str] | None = None,
        embedding_model: str | None = None,
    ) -> list[dict]:
        distance = VectorItem.embedding.cosine_distance(query_embedding)
        statement = (
            select(DocumentChunk, VectorItem, distance.label("distance"))
            .join(VectorItem, VectorItem.chunk_id == DocumentChunk.id)
            .order_by(distance)
            .limit(limit)
        )
        if project_id is not None:
            statement = statement.where(DocumentChunk.project_id == project_id)
        if source_types:
            statement = statement.where(DocumentChunk.source_type.in_(source_types))
        if embedding_model is not None:
            statement = statement.where(VectorItem.embedding_model == embedding_model)

        rows = []
        for chunk, vector, item_distance in self.db.execute(statement).all():
            similarity = 1 - float(item_distance or 0)
            rows.append(
                {
                    "chunk": chunk,
                    "vector": vector,
                    "distance": float(item_distance or 0),
                    "similarity": similarity,
                }
            )
        return rows

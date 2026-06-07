from sqlalchemy.orm import Session

from src.rag.embedding_client import EmbeddingClient
from src.rag.vector_store import VectorStore


class Retriever:
    """Query-time RAG retrieval."""

    def __init__(self, db: Session, embedding_client: EmbeddingClient | None = None) -> None:
        self.embedding_client = embedding_client or EmbeddingClient()
        self.vector_store = VectorStore(db)

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        project_id: int | None = None,
        source_types: list[str] | None = None,
    ) -> list[dict]:
        query_embedding = self.embedding_client.embed_text(query)
        results = self.vector_store.search_similar(
            query_embedding,
            limit=limit,
            project_id=project_id,
            source_types=source_types,
            embedding_model=self.embedding_client.embedding_model_name,
        )
        return [
            {
                "id": result["chunk"].id,
                "source_type": result["chunk"].source_type,
                "source_id": result["chunk"].source_id,
                "chunk_index": result["chunk"].chunk_index,
                "text": result["chunk"].chunk_text,
                "metadata": result["chunk"].raw_metadata or {},
                "similarity": result["similarity"],
                "distance": result["distance"],
            }
            for result in results
        ]

    def retrieve_program_ids(self, query: str, project_id: int, limit: int = 10) -> list[int]:
        results = self.retrieve(query, limit=limit, project_id=project_id, source_types=["program"])
        program_ids: list[int] = []
        seen = set()
        for result in results:
            program_db_id = (result.get("metadata") or {}).get("program_db_id")
            if program_db_id is None or program_db_id in seen:
                continue
            seen.add(program_db_id)
            program_ids.append(int(program_db_id))
        return program_ids

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
        query_embedding = self.embedding_client.embed_query(query)
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

    def retrieve_multi_query(
        self,
        queries: list[str],
        limit: int = 5,
        project_id: int | None = None,
        source_types: list[str] | None = None,
    ) -> list[dict]:
        merged: dict[int, dict] = {}
        for query in queries:
            for result in self.retrieve(query, limit=limit, project_id=project_id, source_types=source_types):
                chunk_id = int(result["id"])
                current = merged.get(chunk_id)
                if current is None or float(result.get("similarity") or 0) > float(current.get("similarity") or 0):
                    result = dict(result)
                    result["matched_query"] = query
                    merged[chunk_id] = result

        def sort_key(item: dict) -> tuple[int, int, float]:
            metadata = item.get("metadata") or {}
            file_path = str(metadata.get("file_path") or item.get("source_id") or "")
            source_priority = 0 if item.get("source_type") == "source_file" else 1
            path_priority = 0 if file_path.startswith(("src/main/", "src/test/")) else 1
            return (source_priority, path_priority, -float(item.get("similarity") or 0))

        return sorted(merged.values(), key=sort_key)[:limit]

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

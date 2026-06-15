from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg2://ai_user:ai_password@localhost:5432/ai_commit_advisor",
        alias="DATABASE_URL",
    )
    pgvector_dimension: int = Field(default=1536, alias="PGVECTOR_DIMENSION")
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL")
    embedding_provider: str = Field(default="mock", alias="EMBEDDING_PROVIDER")
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_model: str | None = Field(default=None, alias="EMBEDDING_MODEL")
    embedding_base_url: str | None = Field(default=None, alias="EMBEDDING_BASE_URL")
    repo_storage_root: str | None = Field(default=None, alias="REPO_STORAGE_ROOT")
    repo_path_host_prefix: str | None = Field(default=None, alias="REPO_PATH_HOST_PREFIX")
    repo_path_container_prefix: str | None = Field(default=None, alias="REPO_PATH_CONTAINER_PREFIX")
    neo4j_enabled: bool = Field(default=False, alias="NEO4J_ENABLED")
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="ai_commit_advisor", alias="NEO4J_PASSWORD")
    neo4j_database: str | None = Field(default=None, alias="NEO4J_DATABASE")
    neo4j_write_batch_size: int = Field(default=500, alias="NEO4J_WRITE_BATCH_SIZE")
    neo4j_retry_attempts: int = Field(default=2, alias="NEO4J_RETRY_ATTEMPTS")
    neo4j_retry_backoff_seconds: float = Field(default=0.5, alias="NEO4J_RETRY_BACKOFF_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

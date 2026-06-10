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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

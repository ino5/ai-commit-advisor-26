from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from src.db.database import engine


BASELINE_REVISION = "20260608_0001"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _ensure_pgvector_extension() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def _stamp_existing_schema_if_needed() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        has_application_schema = inspector.has_table("projects")
        has_alembic_version = inspector.has_table("alembic_version")
        if not has_application_schema or has_alembic_version:
            return

        config = _alembic_config()
        config.attributes["connection"] = connection
        command.stamp(config, BASELINE_REVISION)


def run_migrations() -> None:
    _ensure_pgvector_extension()
    _stamp_existing_schema_if_needed()
    command.upgrade(_alembic_config(), "head")


def init_db() -> None:
    run_migrations()


if __name__ == "__main__":
    init_db()
    print("Database migrations applied.")

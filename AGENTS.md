# Agent Instructions

## AI Change Log

When making code, schema, test, documentation, or behavior changes, update `AI_CHANGELOG.md` before finishing.

Each entry should include:

- date
- summary of what changed
- important files or modules
- verification commands and results

Do not record trivial read-only investigation unless it changes project direction.

## Database Migrations

Schema changes must be handled through Alembic migrations in `migrations/versions/`.

Do not add schema-upgrade `ALTER TABLE` lists to `src/db/init_db.py`.

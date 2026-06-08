# Agent Instructions

## AI Change Log

When making code, schema, test, documentation, or behavior changes, update `AI_CHANGELOG.md` before finishing.

Each entry should include:

- date
- summary of what changed
- important files or modules
- verification commands and results

Do not record trivial read-only investigation unless it changes project direction.

## Roadmap

Before starting meaningful feature, UX, schema, test, or documentation work, check `ROADMAP.md`.

When working on a roadmap task:

- set the task status to `In Progress` when implementation starts
- update checklist items as they are completed
- set the task status to `Done` only after implementation, verification, docs, and `AI_CHANGELOG.md` updates are complete
- add the related `AI_CHANGELOG.md` heading and commit hash after committing, when available

For work that is not already in `ROADMAP.md`, add or update a task entry before implementing when the work affects product direction.

## Database Migrations

Schema changes must be handled through Alembic migrations in `migrations/versions/`.

Do not add schema-upgrade `ALTER TABLE` lists to `src/db/init_db.py`.

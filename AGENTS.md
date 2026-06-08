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

## AI Documentation

When changing AI-facing behavior such as Mapping, RAG, Project Chat, Code Review, AI Progress, Risk Analysis, embedding, or LLM behavior, update `docs/ai-technical-overview.md` if the public explanation or safety model changes.

## Sample Target Repository

When changing the synthetic sample target repository, sample commit history, sample data generation, or demo scenario, check `docs/sample-target-repo-demo-design.md` before implementing.

Keep the sample target repository aligned with the demo design:

- target repo location and generation flow
- intended commit scenarios
- product features each sample scenario should demonstrate
- expected risk, mapping, RAG, Project Chat, Code Review, and AI Progress demo points

## Pre-Commit Documentation Check

Before committing or pushing changes, check whether the change requires updates to project documentation.

Use this checklist:

- `AI_CHANGELOG.md`: required for code, schema, test, documentation, or behavior changes.
- `ROADMAP.md`: required when starting or completing roadmap-tracked work, or when the work affects product direction.
- `README.md`: required when setup, usage, workflows, screens, sample data, commands, or user-facing behavior changes.
- `README_ARCHITECTURE.md`: required when architecture, module boundaries, service responsibilities, or data flow changes.
- `docs/ai-technical-overview.md`: required when Mapping, RAG, Project Chat, Code Review, AI Progress, Risk Analysis, embedding, or LLM behavior changes.
- `docs/db-migrations.md`: required when database migration process or schema management guidance changes.
- `docs/sample-target-repo-demo-design.md`: required when sample target repo goals, commit scenarios, demo coverage, or sample generation direction changes.

If no documentation update is needed, mention that in the final response or commit notes.

## Database Migrations

Schema changes must be handled through Alembic migrations in `migrations/versions/`.

Do not add schema-upgrade `ALTER TABLE` lists to `src/db/init_db.py`.

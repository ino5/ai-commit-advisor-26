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

## Documentation Context And Rationale

When documenting features, architecture, workflows, or AI behavior, include the reason the change exists instead of recording only implementation details.

Prefer documentation that explains:

- the user problem, operational gap, or system limitation that made the feature necessary
- the concrete scenario or failure mode that the design is meant to address
- the chosen approach and why it fits the project better than obvious alternatives
- important tradeoffs, boundaries, or remaining limitations that future maintainers should preserve or revisit

## User-Facing Documentation Language

User-facing documentation should use Korean for explanatory prose by default, especially when describing setup, workflows, feature behavior, operational guidance, and product decisions.

This applies to README sections, feature guides, setup and operations guides, architecture explanations, screenshot captions, sample/demo guides, migration guidance, and other documents a teammate or product user would read to use or understand the app.

Do not force every heading, label, or familiar product/documentation term into Korean when the English form is clearer or more natural. Keep technical identifiers and conventional labels in their original form when that is clearer or required, including:

- file paths
- commands
- environment variables
- API names
- model/provider names
- common documentation labels such as `Quick Start` or `Screenshot Gallery` when they read more naturally
- table, column, class, function, and module names
- UI product names that are intentionally English in the app

Internal agent instructions, historical changelog entries, roadmap task names, commit messages, code comments tied to source conventions, and generated third-party content do not need forced translation unless the user explicitly asks for it.

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

## README Screenshot Guidance

When refreshing README screenshots, capture the feature value rather than only the initial or empty state.

Prefer screenshots that show a meaningful workflow state, such as:

- selected sample project or realistic data
- user input or target selection when it is needed to understand the flow
- validation, execution, analysis, or saved result
- evidence, detail, or output tables when they are central to the feature

If one screenshot cannot clearly show the workflow, split it into sequential screenshots with short labels.

Avoid README screenshots that mainly show a blank form, empty/default project, idle button, or pre-execution state unless that state is the feature being documented.

## Commit Boundaries

When committing changes, keep materially different concerns in separate commits when practical.

Separate commits are expected when a change mixes distinct work types, such as:

- source code behavior fixes
- tests for the behavior fix
- product documentation or screenshots
- roadmap or changelog bookkeeping
- generated sample data

If a verification or documentation task reveals a real code bug, commit the bug fix separately from the documentation, screenshot, or bookkeeping refresh when practical.

## Database Migrations

Schema changes must be handled through Alembic migrations in `migrations/versions/`.

Do not add schema-upgrade `ALTER TABLE` lists to `src/db/init_db.py`.

# Agent Instructions

## AI Change Log

When making code, schema, test, documentation, or behavior changes, update `AI_CHANGELOG.md` before finishing.

Write new `AI_CHANGELOG.md` entries in Korean by default, including headings, summaries, important files/modules, and verification results. Keep file paths, commands, environment variables, API names, model/provider names, table/class/function names, and conventional product labels in their original form when that is clearer.

Historical English entries do not need to be translated retroactively unless the user explicitly asks to rewrite those entries or the entry is already being edited for another reason.

Each entry should include:

- date
- summary of what changed
- important files or modules
- verification commands and results

Do not record trivial read-only investigation unless it changes project direction.

## Failure History

When a failure, incident, or significant mistake is caused by agent work or investigated during agent work, update `docs/failure-history.md` before finishing if the failure has reusable learning value.

This is not limited to CI. Record failures that reveal a product, UX, AI behavior, RAG/embedding, data, schema, migration, sample data, documentation, test, dependency, workflow, environment, deployment, or operational policy gap.

Each failure-history entry should include:

- date
- related feature, document, run/job URL, or commit when available
- symptom
- root cause
- background or structural cause
- why local, CI, review, or prior verification missed it
- fix
- prevention policy
- remaining limitations or follow-up checks
- verification commands and results

When adding or changing tests that require PostgreSQL, pgvector, Docker services, browser automation, local LLM/embedding servers, external APIs, or other infrastructure, check the CI workflow in the same change set. If CI should not call an external service, set explicit mock/default environment variables in the workflow.

Do not treat GitHub Actions warnings as root causes unless the log shows they stopped the job. Record warnings separately from the actual failed step.

## Roadmap

Before starting meaningful feature, UX, schema, test, or documentation work, check `ROADMAP.md`.

When working on a roadmap task:

- set the task status to `In Progress` when implementation starts
- update checklist items as they are completed
- set the task status to `Done` only after implementation, verification, docs, and `AI_CHANGELOG.md` updates are complete
- add the related `AI_CHANGELOG.md` heading when a roadmap-tracked task is completed
- do not maintain commit hashes in `ROADMAP.md`; use Git history for commit-level traceability and avoid follow-up commits whose only purpose is filling a Roadmap hash cell

For work that is not already in `ROADMAP.md`, add or update a task entry before implementing when the work affects product direction.

Use `ROADMAP.md` `Candidate Tasks` for known product, UX, state-management, architecture, or engineering concerns that should be preserved but are not yet approved for implementation.

When a user asks to record a concern, tradeoff, or possible future improvement without starting work, add or update a candidate task instead of creating a full active roadmap task.

When starting work from a candidate task:

- move or copy it into the priority overview before implementation
- add a dedicated roadmap task section with goal and checklist
- set the active task status to `In Progress`
- leave the candidate only if there is still unresolved scope that should remain tracked separately

## Documentation Impact Gate

Before proposing or starting meaningful code, UX, test, behavior, automation, operations, or documentation work, explicitly classify the documentation impact.

Check at minimum:

- `AI_CHANGELOG.md` for any code, schema, test, documentation, or behavior change.
- `ROADMAP.md` for roadmap-tracked work, product-direction changes, UX direction changes, or agent-policy work.
- `docs/engineering-decisions.md` when the work introduces or changes a repeatable engineering, UX implementation, verification, documentation, automation, deployment, operations, or agent-policy convention.
- `docs/failure-history.md` when the work investigates or fixes a recurring failure, missed verification, incident, or agent-caused mistake with reusable learning value.
- User-facing docs when setup, usage, workflows, screenshots, sample data, commands, or visible behavior changes.
- `docs/architecture.md` when architecture, module boundaries, service responsibilities, or data flow changes.
- `docs/ai-technical-overview.md` when Mapping, RAG, Project Chat, Code Review, AI Progress, Risk Analysis, embedding, LLM behavior, or AI safety explanation changes.
- `docs/db-migrations.md` when database migration process or schema management guidance changes.
- `docs/sample-target-repo-demo-design.md` when sample project goals, commit scenarios, demo coverage, or sample generation direction changes.

When the user frames a change in terms of maintainability, future reuse, verification policy, structural tradeoffs, operating policy, or agent behavior, treat `docs/engineering-decisions.md` as a required review candidate before implementation.

If a document is not updated after this review, state why in the plan, final response, or commit notes.

## AI Documentation

When changing AI-facing behavior such as Mapping, RAG, Project Chat, Code Review, AI Progress, Risk Analysis, embedding, or LLM behavior, update `docs/ai-technical-overview.md` if the public explanation or safety model changes.

## Documentation Context And Rationale

When documenting features, architecture, workflows, or AI behavior, include the reason the change exists instead of recording only implementation details.

Prefer documentation that explains:

- the user problem, operational gap, or system limitation that made the feature necessary
- the concrete scenario or failure mode that the design is meant to address
- the chosen approach and why it fits the project better than obvious alternatives
- important tradeoffs, boundaries, or remaining limitations that future maintainers should preserve or revisit

## Engineering Decisions

When a non-trivial decision changes how the project is built, verified, documented, automated, deployed, or operated, update `docs/engineering-decisions.md` before finishing if the decision has future reuse value.

Use the engineering decisions log for decisions that are not primarily failures or incidents but still need durable rationale, including:

- choosing one implementation, verification, automation, documentation, deployment, or operations approach over another
- adding a repeatable workflow or agent policy that affects future work
- accepting a meaningful tradeoff in cost, reliability, maintainability, speed, or scope
- defining a cross-feature convention that future features should follow

Each decision entry should include:

- date
- decision title
- background or problem context
- chosen approach
- reasons for the choice
- alternatives considered
- impact, tradeoffs, and remaining limitations
- related documents, changelog entries, failure-history entries, or commits when available

Do not duplicate `AI_CHANGELOG.md`: use the changelog for concrete file/behavior changes and verification results. Do not duplicate `docs/failure-history.md`: use failure history when a failure, incident, or significant mistake reveals a reusable root cause or prevention rule. Link between the documents when a failure leads to a broader decision.

## Feature Rationale Documentation

When adding a meaningful new feature, workflow, AI behavior, operational behavior, or major UX change, update an appropriate Markdown document with the feature rationale before finishing.

The documentation should explain:

- why the feature was introduced
- what user problem, operational gap, or system limitation it addresses
- expected effect or value
- when users should use it
- important tradeoffs, boundaries, and remaining limitations
- related verification or failure-history lessons, if any

Prefer updating an existing relevant document before creating a new one. Create a dedicated `docs/*.md` file only when the feature is large enough that `README.md`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/architecture.md`, or `docs/ai-technical-overview.md` would become too broad.

## User-Facing Documentation Language

User-facing documentation should use Korean for explanatory prose by default, especially when describing setup, workflows, feature behavior, operational guidance, and product decisions.

This applies to README sections, feature guides, setup and operations guides, architecture explanations, screenshot captions, sample/demo guides, migration guidance, and other documents a teammate or product user would read to use or understand the app.

Do not force every heading, label, or familiar product/documentation term into Korean when the English form is clearer or more natural. Keep technical identifiers and conventional labels in their original form when that is clearer or required, including:

- file paths
- commands
- environment variables
- API names
- model/provider names
- common documentation labels such as `Quick Start` or `Application Preview` when they read more naturally
- table, column, class, function, and module names
- UI product names that are intentionally English in the app

Internal agent instructions, historical changelog entries, roadmap task names, commit messages, code comments tied to source conventions, and generated third-party content do not need forced translation unless the user explicitly asks for it.

## Natural Korean Documentation Wording

User-facing Korean documentation should read like product documentation written by a person, not a literal translation of internal identifiers.

When describing demo/sample materials to users, use reader-facing product terms instead of literal internal repository or data-generation terminology. Describe what the reader is using and why it matters; mention Git repositories, generated data, or internal demo mechanics only when that distinction affects the user's action.

Avoid literal or AI-sounding wording in user-facing prose. In particular, do not translate internal repository roles, data-generation mechanics, or demo implementation details too directly when a simpler product-facing phrase would be clearer.

Use technical wording only when it is a file name, code identifier, historical task title, or the exact technical distinction is necessary.

When a technical file name still contains older internal wording, keep the file path unchanged if renaming would create churn, but make the surrounding link label and explanatory sentence natural.

## AI-Sounding Wording Review

Before finishing work that changes user-facing prose, UI copy, README sections, feature guides, setup/operations guides, Application Preview captions, sample/demo guides, reports, PPT/PPTX decks, or other presentation material, explicitly check whether the changed text still contains AI-sounding wording.

Treat this as a required finishing check, not a nice-to-have style pass. Review the changed diff and, when practical, use `rg` against the touched user-facing files for vague, generic, or translation-like expressions. Replace them with concrete product wording that names the actor, workflow, evidence, action, or limitation.

Examples of wording to challenge:

- generic claims such as "혁신적인", "강력한", "원활한", "향상된 사용자 경험", "AI 기반으로 자동화" when the sentence does not say what actually changes for the user
- literal translations of internal mechanics, repository roles, data-generation steps, or implementation details when a reader-facing product phrase would be clearer
- broad AI claims that imply certainty, autonomous judgment, or business value without traceable evidence, boundary, or user action
- repeated template-like phrasing such as "이를 통해 ... 할 수 있습니다" when a shorter direct sentence would read more naturally

Do not rewrite stable product labels, code identifiers, API/model names, file paths, commands, historical changelog entries, or user-quoted wording solely because they look technical. When a term such as `AI Use Case`, `AI Progress`, `Project Chat`, or `PL Briefing` is an intentional product label, keep it and make the surrounding sentence natural.

In the final response, changelog entry, or work notes, mention that this wording review was performed when the change includes meaningful user-facing prose or presentation copy.

## Korean Text And Encoding

This repository contains Korean Markdown and UTF-8 text. On Windows, PowerShell output can look corrupted when a command uses the console default encoding instead of UTF-8.

When reading Korean Markdown or other user-facing text files, prefer commands that explicitly set UTF-8, for example:

- `Get-Content -Path README.md -Encoding UTF8`
- `Get-Content -Path docs\setup-and-operations.md -Encoding UTF8`
- `rg -n "검색어" README.md docs`

If Korean text appears garbled in command output:

- do not assume the file content itself is corrupted
- re-read the file with an explicit UTF-8 command before editing
- avoid rewriting Korean prose just to "fix" text that was only garbled in terminal output
- mention encoding uncertainty in the work notes when it affects verification

When editing Markdown that already contains Korean text, preserve UTF-8 content and keep changes scoped to the requested wording or behavior.

## Sample Target Repository

When changing the demo sample project, sample commit history, sample data generation, or demo scenario, check `docs/sample-target-repo-demo-design.md` before implementing.

`docs/demo-user-guide.md` is a user-facing usage guide that uses the sample project as its default walkthrough example. It can be used as a demo walkthrough, but keep its visible title and prose framed as a general usage guide rather than a sample-project-only or validation-only document.

When verifying that guide end to end, do not crowd the user-facing guide with execution logs. Store dated verification results in a separate document such as `docs/sample-project-usage-verification.md`, and keep evidence screenshots under `docs/images/usage-verification/`. If the purpose is to prove the real workflow, use actual local LLM/embedding providers rather than mock providers, and record `LLM_PROVIDER`, `LLM_MODEL`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `PGVECTOR_DIMENSION`, runtime surface, sample project path, commit count, verification date, commands, results, and known limitations. Link from the user-facing guide or README only when it helps readers find the evidence without turning the guide into an internal verification log.

Keep the sample project aligned with the demo design:

- sample project location and generation flow
- intended commit scenarios
- product features each sample scenario should demonstrate
- expected risk, mapping, RAG, Project Chat, Code Review, and AI Progress demo points

## Pre-Commit Documentation Check

Before committing or pushing changes, check whether the change requires updates to project documentation.

Use this checklist:

- `AI_CHANGELOG.md`: required for code, schema, test, documentation, or behavior changes.
- `ROADMAP.md`: required when starting or completing roadmap-tracked work, or when the work affects product direction.
- `README.md`: required when setup, usage, workflows, screens, sample data, commands, or user-facing behavior changes.
- Feature rationale documentation: required when a meaningful new feature, workflow, AI behavior, operational behavior, or major UX change is introduced.
- `docs/architecture.md`: required when architecture, module boundaries, service responsibilities, or data flow changes.
- `docs/ai-technical-overview.md`: required when Mapping, RAG, Project Chat, Code Review, AI Progress, Risk Analysis, embedding, or LLM behavior changes.
- `docs/engineering-decisions.md`: required when a meaningful engineering, operations, verification, automation, deployment, or documentation-structure decision is introduced or changed.
- `docs/db-migrations.md`: required when database migration process or schema management guidance changes.
- `docs/sample-target-repo-demo-design.md`: required when sample project goals, commit scenarios, demo coverage, or sample generation direction changes.
- `docs/failure-history.md`: required when a failure, incident, or significant mistake has reusable root-cause or prevention value.

If no documentation update is needed, mention that in the final response or commit notes.

## Application Preview Screenshot Guidance

When refreshing README or Application Preview screenshots, capture the feature value rather than only the initial or empty state.

Prefer screenshots that show a meaningful workflow state, such as:

- selected sample project or realistic data
- user input or target selection when it is needed to understand the flow
- validation, execution, analysis, or saved result
- evidence, detail, or output tables when they are central to the feature

If one screenshot cannot clearly show the workflow, split it into sequential screenshots with short labels.

Avoid README screenshots that mainly show a blank form, empty/default project, idle button, or pre-execution state unless that state is the feature being documented.

## Demo Runtime Startup

When asked to start, restart, or check the prepared demo runtime, use the repository startup contract instead of reconstructing commands from chat history:

- Read `README.md` `검증된 시연 서버 재기동` and `docs/demo-runbook.md` `기동 절차` before changing runtime state.
- Use `scripts/demo_start.ps1` as the default startup entry point. Use `-CheckOnly` for a read-only status check.
- Do not rebuild the app image unless the user asks for current source changes to be included or `-Build` is otherwise justified.
- Do not create a new Quick Tunnel unless no Tunnel is running and the user needs an external URL. Check and reuse the current URL first.
- Do not stop or remove a running Quick Tunnel unless the user explicitly asks to end external access. Repository-created Tunnel containers use `restart=unless-stopped`; after a Docker daemon restart, run `status` and report the newly issued current URL because a Quick Tunnel URL can change.
- Do not use `docker compose down`, `docker compose down -v`, delete volumes, reset the database, or start a second local Streamlit port as part of normal demo startup.
- Treat Docker containers and host ports as shared across branches, worktrees, terminals, and Agent sessions.
- The prepared demo contract is Docker `8501`, project `1`, LM Studio `12345`, Chat context length `8192`, `text-embedding-nomic-embed-text-v2-moe`, and embedding dimension `768`. If the repository docs or runtime disagree, stop and report the mismatch instead of silently choosing a different setup.

## Verification Surface Selection

Choose the cheapest verification surface that still exercises the behavior being changed.

Use local `.venv` verification first for ordinary Python code, service logic, unit/integration tests, documentation-only changes, and Streamlit UI changes that do not depend on Docker runtime behavior. Typical commands:

- `.\.venv\Scripts\python.exe -m compileall src app.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m streamlit run app.py`

Use Docker verification when the change or bug depends on container runtime behavior, including:

- `Dockerfile` or `docker-compose.yml` changes
- container environment variables
- DB hostnames, service healthchecks, startup migration, or deployment smoke checks
- host-to-container volume mounts
- repository path mapping between Windows host paths and Linux container paths
- bugs that reproduce only in Docker or only after container startup

Do not rebuild the Docker image for every app source change by default. Rebuild with `docker compose up -d --build app` only when the Docker image or container runtime is part of what must be verified.

Docker build logs can be long. Prefer checking the concise command result, container health, relevant service logs, and targeted smoke checks. Inspect full build or container logs only when a failure requires them.

When a screenshot or UI verification is captured from Docker, confirm the Docker runtime can access any required host resources, such as local Git repositories, model servers, mounted files, or DB services. If the same feature can behave differently in local Python and Docker, state which surface was verified.

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

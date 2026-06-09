# Roadmap

## Management Rules

- Check this file before starting meaningful feature, UX, schema, test, or documentation work.
- Move a task to `In Progress` when implementation starts.
- Move a task to `Done` when implementation, verification, `AI_CHANGELOG.md`, and documentation updates are complete.
- Record the related `AI_CHANGELOG.md` heading and commit hash after completion.
- Keep tasks small enough to complete and verify in one focused change set when practical.

## Priority Overview

| Priority | Area | Task | Status | Related AI Change Log | Commit |
|---|---|---|---|---|---|
| P0 | Data UX | Program management UX improvement | Done | 프로그램 관리 UX 2차 개선 | b1cf9ef |
| P0 | Data UX | Developer management UX improvement | Done | 개발자 관리 UX 개선 | d00b868 |
| P0 | Data UX | Development plan management UX improvement | Done | 개발계획 관리 UX 개선 | 130c2f8 |
| P1 | RAG | Project Chat answer quality and history persistence | In Progress | Project Chat 답변 품질과 근거 부족 처리 개선 | edcb4e7 |
| P1 | RAG | Standard terminology glossary upload and Korean query expansion | Done | Standard terminology documentation and screenshots | 05a40ad |
| P1 | RAG | Incremental source indexing and embedding cost control | Planned | Source indexing and embedding plan | - |
| P1 | RAG | Project Chat answer formatting and citation accuracy | Done | Standard terminology documentation and screenshots | 05a40ad |
| P1 | RAG | Source file re-index warning and one-click refresh | Done | source_file 인덱스 상태 표시 세부 보완 | 7895831 |
| P1 | Program Detail | Implementation status result display improvement | Done | Program Detail 구현상태 분석 결과 표시 개선 | fa625d2 |
| P1 | AI Analysis | Conservative implementation status prompt and fallback | Done | 구현상태 분석 프롬프트와 fallback 보수화 | 704c7cf |
| P1 | AI Progress | Show implementation status analysis results | Done | AI Progress 구현상태 분석 결과 표시 | c42d847 |
| P1 | Mapping | Mapping feedback analytics and review queue | Done | Mapping 피드백 리뷰 큐와 품질 지표 추가 | fc87e29 |
| P1 | DB | Alembic migration stabilization | Done | Alembic DB 마이그레이션 도입 | a3892bd |
| P1 | Ops | LLM/Embedding batch safety and estimated runtime | Done | LLM/Embedding 배치 안전장치와 예상시간 표시 | a151133 |
| P2 | UX | Sidebar navigation UX improvement | Done | Sidebar 메뉴 UX 개선 | 0312a0a |
| P2 | UX | Artifact management menu grouping | Done | Artifact management sidebar grouping | 60dd64c |
| P2 | Ops | CI test workflow | Done | CI 테스트 워크플로우 추가 | 562da8a |
| P2 | UX | Home analysis command center | Done | Home 분석 관제 화면 개선 | c3a30a1 |
| P2 | UX | Home copy tone cleanup | Done | Home 문구 톤 정리 | c8c421e |
| P2 | Ops | Home UI visual verification script | Done | Home UI 검증 스크립트 추가 | c8c421e |
| P2 | UX | Sidebar menu layout stabilization | Done | Sidebar 메뉴 위치 흔들림 보정 | 5ee2065 |
| P2 | Sample Data | Synthetic target project repository | Done | 가상 샘플 대상 프로젝트 생성 스크립트 추가 | fa7fcbb |
| P2 | Sample Data | Rich demo target repository scenario design | Done | 샘플 대상 repo 데모 시나리오 설계 문서 추가 | 7038ac5 |
| P2 | Sample Data | Rich demo target repository implementation | Done | 풍부한 샘플 대상 repo 구현 | fd1940d |
| P2 | Docs | Rich sample demo walkthrough and screenshots | Done | 풍부한 샘플 데모 검증과 화면 캡처 갱신 | dd8fd5e |
| P2 | Docs | README documentation hub restructure | Done | README 문서 허브 개편 | 6b27b35 |
| P2 | Docs | Local LLM env onboarding guide | Done | local LLM env 예시와 Project Chat 재현 절차 | 02f2b14 |
| P2 | Docs | Korean-first user documentation cleanup | Done | Korean-first user documentation cleanup | - |
| P2 | Ops | Application Dockerfile and deployment guide | Planned | - | - |

## P0 - Program Management UX Improvement

Status: Done

Goal:
Make program data manageable without knowing the Excel schema in advance.

Checklist:

- [x] Add program Excel template download.
- [x] Show required and optional column guide in the UI.
- [x] Add upload preview before save.
- [x] Add upload validation for required columns, duplicate program IDs, dates, and progress values.
- [x] Show import summary: new rows, updated rows, skipped/error rows.
- [x] Add existing program search and filters.
- [x] Add manual program creation form.
- [x] Add program edit flow.
- [x] Add program delete flow with impact warning.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.
- [x] Update related README sections.

## P0 - Developer Management UX Improvement

Status: Done

Goal:
Make developer data easy to create, correct, and remove from the UI.

Checklist:

- [x] Add developer Excel template download.
- [x] Show required and optional column guide in the UI.
- [x] Add upload preview and validation.
- [x] Add existing developer search and filters.
- [x] Add manual developer creation form.
- [x] Add developer edit flow.
- [x] Add delete flow with assigned program warning.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.
- [x] Update related README sections.

## P0 - Development Plan Management UX Improvement

Status: Done

Goal:
Make plan progress, dates, status, and assignments editable without re-uploading Excel.

Checklist:

- [x] Add development plan Excel template download.
- [x] Show required and optional column guide in the UI.
- [x] Add upload preview and validation.
- [x] Add current plan grid with filters.
- [x] Add manual plan update form.
- [x] Add bulk status/progress update where safe.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.
- [x] Update related README sections.

## P1 - Project Chat Answer Quality And History Persistence

Status: In Progress

Goal:
Improve Project Chat from session-only Q&A into a more reliable project assistant.

Checklist:

- [ ] Persist chat sessions in the database.
- [ ] Add project-level chat history list.
- [ ] Add source citation export or copy-friendly format.
- [x] Add "insufficient evidence" answer classification.
- [x] Separate current source evidence from historical/reference evidence in the UI.
- [x] Add focused tests for insufficient, stale/invalid, and verified source evidence.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Standard Terminology Glossary Upload And Korean Query Expansion

Status: Done

Goal:
Improve Korean business-question retrieval by using project standard terminology and standard words to connect Korean terms with code, DB, and naming identifiers.

Scope:

- Add a project-level standard terminology/standard word management menu.
- Support Excel template download and Excel upload for SI-style terminology deliverables.
- Keep the Excel input lightweight: teams enter Korean term, English term, and abbreviation; the app derives search variants.
- Use uploaded terminology to expand Korean Project Chat and RAG queries into English/code/DB identifier candidates.
- Keep query expansion deterministic first, without adding an extra LLM call per chat question.

Suggested menu:

- `데이터 관리 > 표준용어/표준단어`

Excel columns:

- Required: `korean_term`, `english_term`
- Recommended: `abbreviation`
- Optional: `term_type`, `description`

Derived search variants:

- tokenized English words
- abbreviation tokens
- `camelCase`
- `PascalCase`
- `snake_case`
- `UPPER_SNAKE_CASE`
- compact lowercase form

Checklist:

- [x] Add schema for project-level glossary terms through Alembic migration.
- [x] Add glossary service for normalization, validation, and derived keyword generation.
- [x] Add Excel template generation for standard terminology upload.
- [x] Add Excel upload validation for required columns, duplicate Korean/English terms, and empty values.
- [x] Add current glossary list/search UI.
- [x] Add glossary query expansion for Project Chat and RAG retrieval.
- [x] Merge multi-query retrieval results by chunk id and prefer verified `source_file` evidence for Project Chat.
- [x] Add focused tests for Korean payment amount questions expanding to `payment`, `amount`, `PaymentService`, `payment_amount`, and abbreviation variants.
- [x] Update README, Feature Guide, and AI technical overview.
- [x] Update `AI_CHANGELOG.md`.

Out of scope for first pass:

- Manual row-level glossary edit/delete UI.
- LLM-based query rewrite.
- Full DB table/column lineage inference from source code.

## P1 - Incremental Source Indexing And Embedding Cost Control

Status: Planned

Goal:
Make Project Chat source indexing practical for large SI repositories and cloud deployment by avoiding full source scans and repeated embedding calls during normal work.

Context:

- Git commit sync is already incremental through `last_synced_commit_hash`.
- Source file re-indexing is currently manual and content-aware, but it still scans the repository tree.
- Embedding generation already creates vectors only for missing `chunk_id + embedding_model` pairs.
- A complete commit-triggered incremental source indexing pipeline does not exist yet.

Design document:

- `docs/source-indexing-and-embedding-plan.md`

Checklist:

- [ ] Document current behavior and limitations in user-facing operations guidance.
- [ ] Add a changed-file source indexing service that accepts added, modified, deleted, and renamed file paths.
- [ ] Rebuild chunks only for changed source files during incremental refresh.
- [ ] Remove chunks and vectors for deleted source files.
- [ ] Keep full source re-indexing as a separate recovery and large-change action.
- [ ] Add UI status for missing embeddings, stale chunks, and when full re-index is recommended.
- [ ] Keep embedding generation explicit or limited so cloud API usage is controlled.
- [ ] Add focused tests for modified, deleted, renamed, unchanged, and model-changed indexing cases.
- [ ] Update README, setup/operations guidance, AI technical overview, and `AI_CHANGELOG.md` when implemented.

## P1 - Project Chat Answer Formatting And Citation Accuracy

Status: Done

Goal:
Make Project Chat answers presentation-ready and defensible by preventing JSON-shaped responses, reducing line-number hallucination, and showing source evidence clearly.

Observed issues:

- local LLM responses can return JSON code blocks even when the UI expects readable chat text.
- The LLM can infer incorrect line numbers instead of using the provided source metadata.
- README screenshots look weak when answers show `Mock answer`, hidden evidence, or only file lists.

Checklist:

- [x] Strengthen the Project Chat prompt to forbid JSON/code-block response wrappers unless the user explicitly asks for JSON.
- [x] Require Markdown prose/bullets in Korean for normal answers.
- [x] Require file paths and line ranges to be copied only from retrieved source metadata.
- [x] Add response post-processing for common JSON wrapper shapes from local LLMs.
- [x] Show the matched/expanded query information in debug or evidence context when useful.
- [x] Adjust source evidence rendering so screenshots can show answer plus key evidence without looking empty.
- [x] Add focused tests for JSON wrapper cleanup and citation line-range preservation.
- [x] Refresh the Project Chat README screenshot only after real local LLM/RAG verification succeeds.
- [x] Update README, Screenshot Gallery, Feature Guide, and AI technical overview as needed.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Source File Re-Index Warning And One-Click Refresh

Status: Done

Goal:
Reduce stale RAG results when the repository HEAD changes after indexing.

Checklist:

- [x] Show indexed HEAD vs current HEAD in RAG and Project Chat.
- [x] Show indexed HEAD variants and current HEAD mismatch chunk count.
- [x] Add stale source_file chunk count.
- [x] Add one-click source_file re-index action.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Implementation Status Result Display Improvement

Status: Done

Goal:
Make saved program implementation status analysis easier for business owners to understand and verify.

Checklist:

- [x] Show AI status values as business-friendly Korean labels.
- [x] Add explanatory guidance that the result is an AI estimate requiring owner confirmation.
- [x] Improve saved result layout for status, analyzed time, evidence count, summary, features, and evidence commits.
- [x] Make evidence commit rendering defensive for malformed payloads.
- [x] Keep reanalysis failures from breaking the whole Program Detail page.
- [x] Run compileall and pytest.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Conservative Implementation Status Prompt And Fallback

Status: Done

Goal:
Make program implementation status analysis more conservative and easier to verify in business review.

Checklist:

- [x] Rewrite the LLM prompt in Korean with conservative status rules.
- [x] Clarify that commits alone do not prove testing, deployment, or production verification.
- [x] Make fallback summaries and incomplete guidance Korean.
- [x] Avoid easy COMPLETED fallback results.
- [x] Add focused tests for fallback and payload normalization.
- [x] Update AI technical overview.
- [x] Run compileall and pytest.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Show Implementation Status Analysis Results In AI Progress

Status: Done

Goal:
Show saved program-level implementation analysis beside existing AI progress metrics without changing progress calculations.

Checklist:

- [x] Add implementation analysis fields to progress summary rows.
- [x] Map saved implementation analysis statuses to business-friendly labels.
- [x] Add implementation analysis columns to the AI Progress program table.
- [x] Show selected program implementation analysis summary in the detail area.
- [x] Add guidance explaining AI progress rate versus implementation analysis.
- [x] Keep AI progress, progress gap, and risk calculations unchanged.
- [x] Add focused tests.
- [x] Update README and AI technical overview where needed.
- [x] Run compileall and pytest.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Mapping Feedback Analytics And Review Queue

Status: Done

Goal:
Turn manual mapping feedback into an analysis quality workflow.

Checklist:

- [x] Add feedback completed/pending/review-needed quality summary.
- [x] Add review queue candidates for no feedback, unknown status, low relevance, short reason, and unrelated mappings.
- [x] Add review queue filters and keyword search.
- [x] Reuse the existing mapping feedback correction form for selected queue rows.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.

## P1 - LLM/Embedding Batch Safety And Estimated Runtime

Status: Done

Goal:
Reduce local LLM and embedding overload by showing estimated runtime and keeping batch execution bounded.

Checklist:

- [x] Add a reusable estimated runtime helper.
- [x] Show estimated runtime before RAG embedding execution.
- [x] Show estimated runtime before source_file refresh with embedding.
- [x] Use safer default embedding batch sizes for local runs.
- [x] Add focused tests.
- [x] Update README and `AI_CHANGELOG.md`.

## P2 - Sidebar Navigation UX Improvement

Status: Done

Goal:
Make the sidebar feel like workflow navigation instead of radio-button settings.

Checklist:

- [x] Replace the two-level radio menu with grouped navigation controls.
- [x] Keep the existing page groups and page renderers.
- [x] Show the current menu path clearly.
- [x] Update README and `AI_CHANGELOG.md`.
- [x] Run compileall and pytest.

## P2 - Artifact Management Menu Grouping

Status: Done

Goal:
Group upload and direct-management screens for project artifacts so users can find SI deliverables in one sidebar section.

Checklist:

- [x] Add a sidebar group for artifact management screens.
- [x] Move developer list, program list, development plan, and standard terminology management pages into the artifact group.
- [x] Keep Git sync and sample data generation under data collection.
- [x] Update related workflow documentation.
- [x] Run compile and UI verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - CI Test Workflow

Status: Done

Goal:
Run tests consistently before merge or push.

Checklist:

- [x] Add GitHub Actions workflow.
- [x] Run py_compile or import smoke check.
- [x] Run pytest.
- [x] Document local verification commands.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Home Analysis Command Center

Status: Done

Goal:
Make Home a practical analysis command center that shows pipeline status and next work items.

Checklist:

- [x] Rewrite Home guidance in a business workflow tone.
- [x] Add analysis pipeline status for project, program, developer, Git, mapping, implementation status, and unresolved risk data.
- [x] Add data-driven next recommended actions.
- [x] Keep existing KPI and chart sections.
- [x] Update README and `AI_CHANGELOG.md`.

## P2 - Home Copy Tone Cleanup

Status: Done

Goal:
Make Home feel less like an explanatory AI demo and more like a compact work status screen.

Checklist:

- [x] Shorten Home header copy.
- [x] Replace long pipeline explanations with compact status notes.
- [x] Shorten next action messages.
- [x] Keep existing Home data collection and charts unchanged.
- [x] Run compileall.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Home UI Visual Verification Script

Status: Done

Goal:
Make Home copy and layout verification repeatable without relying on Node Playwright.

Checklist:

- [x] Add a Python Playwright verification script for Home.
- [x] Record Playwright as a local dependency.
- [x] Document the verification command.
- [x] Run the script against the local Streamlit server.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Sidebar Menu Layout Stabilization

Status: Done

Goal:
Keep sidebar menu item positions stable when switching pages.

Checklist:

- [x] Normalize active and inactive menu item box sizing.
- [x] Keep active and inactive menu item spacing consistent.
- [x] Run compileall and focused UI verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Synthetic Target Project Repository

Status: Done

Goal:
Create a separate fake Git project that can be used as a clean AI Commit Advisor analysis target.

Checklist:

- [x] Add a script that creates a sibling sample Git repository.
- [x] Include realistic developers, program list, source files, and commit history.
- [x] Generate sample Excel upload files from the fake repository.
- [x] Document how to create and use the sample target.
- [x] Run compileall and sample generation.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Rich Demo Target Repository Scenario Design

Status: Done

Goal:
Define how the synthetic sample target repository should demonstrate the full AI Commit Advisor feature set before expanding its source files and commit history.

Checklist:

- [x] Document the current sample target strengths and gaps.
- [x] Define target demo scale for programs, developers, and commits.
- [x] Map sample commit scenarios to Git Sync, Mapping, Program Detail, Commit Impact, Risk Analysis, RAG, Project Chat, AI Code Review, and AI Progress.
- [x] Define intentional risk and review scenarios.
- [x] Add agent guidance for checking the demo design before changing sample target repo behavior.
- [x] Add pre-commit documentation check guidance for related Markdown files.
- [x] Update README sample data guidance.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Rich Demo Target Repository Implementation

Status: Done

Goal:
Expand the synthetic sample target repository from a minimal verification dataset into a richer demo dataset that exercises the full AI Commit Advisor workflow.

Checklist:

- [x] Expand generated program rows for additional demo-risk scenarios.
- [x] Expand sample commit history to about 30 commits.
- [x] Add source and documentation scenarios for code review, RAG, Project Chat, commit impact, and AI Progress.
- [x] Add development-plan overrides for delayed, unassigned, and no-related-commit risk scenarios.
- [x] Update focused tests for the richer sample shape.
- [x] Regenerate the sibling sample target repository.
- [x] Update README and sample design documentation if needed.
- [x] Run compileall, pytest, and sample generation verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Rich Sample Demo Walkthrough And Screenshots

Status: Done

Goal:
Verify the expanded sample target repository through the actual app workflow and align the README walkthrough and feature screenshots with the richer 8-program, 30-commit demo data.

Checklist:

- [x] Document the safe execution flow to avoid excessive LLM and embedding work.
- [x] Register or refresh the sample project in the app with `C:\dev\ai-advisor-sample-shop`.
- [x] Upload the `advisor_uploads` developer, program, and development-plan Excel files.
- [x] Run Git sync, Mapping, Risk Analysis, AI Progress, Commit Impact, RAG, Project Chat, and AI Code Review checks.
- [x] Document the recommended demo walkthrough, including expected risk scenarios and recommended code review commits.
- [x] Refresh README feature screenshots that changed because of the richer sample data.
- [x] Update `docs/sample-target-repo-demo-design.md` if verified behavior differs from the design.
- [x] Update `AI_CHANGELOG.md`.

## P2 - README Documentation Hub Restructure

Status: Done

Goal:
Make README easier for teammates to scan by turning it into a concise entry document and moving detailed screenshots, feature explanations, setup, and operations guidance into dedicated docs.

Checklist:

- [x] Keep README focused on overview, quick start, sample project entry points, representative screenshots, and documentation links.
- [x] Move feature screenshots into `docs/screenshot-gallery.md`.
- [x] Move feature workflow explanations into `docs/feature-guide.md`.
- [x] Move setup, LLM/embedding, RAG operations, and verification commands into `docs/setup-and-operations.md`.
- [x] Use GitHub-friendly relative links from README to each supporting document.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Local LLM Env Onboarding Guide

Status: Done

Goal:
Make it clear which environment file teammates should use for lightweight mock runs versus real local LLM/RAG/Project Chat verification.

Checklist:

- [x] Add a local LLM environment example for LM Studio based chat and embedding.
- [x] Keep `.env.example` as the lightweight mock default.
- [x] Explain the two env choices in README Quick Start.
- [x] Document that provider/model changes require regenerating embeddings for RAG Search and Project Chat.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Korean-First User Documentation Cleanup

Status: Done

Goal:
Make user-facing Markdown documentation Korean-first unless a technical identifier, command, file path, API name, or product name is clearer in English.

Checklist:

- [x] Translate English-heavy docs under `docs/` to Korean while preserving code identifiers and commands.
- [x] Keep internal agent/task-management documents out of scope unless they directly face users.
- [x] Align architecture and feature wording where user-facing menu names changed.
- [x] Run markdown/link sanity checks.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Application Dockerfile And Deployment Guide

Status: Planned

Goal:
Make local and server deployment repeatable.

Checklist:

- [ ] Add application Dockerfile.
- [ ] Add compose service for Streamlit app.
- [ ] Document environment variables.
- [ ] Document migration startup behavior.
- [ ] Add deployment smoke check.
- [ ] Update `AI_CHANGELOG.md`.

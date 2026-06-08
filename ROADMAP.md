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
| P1 | RAG | Project Chat answer quality and history persistence | Planned | Project Chat 전용 메뉴 추가 | 330434b |
| P1 | RAG | Source file re-index warning and one-click refresh | Done | source_file 인덱스 상태 확인과 원클릭 재인덱싱 | de4a16e |
| P1 | Mapping | Mapping feedback analytics and review queue | Planned | 매핑 피드백 기능 추가 | 466d131 |
| P1 | DB | Alembic migration stabilization | Done | Alembic DB 마이그레이션 도입 | a3892bd |
| P2 | Ops | CI test workflow | Planned | - | - |
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

Status: Planned

Goal:
Improve Project Chat from session-only Q&A into a more reliable project assistant.

Checklist:

- [ ] Persist chat sessions in the database.
- [ ] Add project-level chat history list.
- [ ] Add source citation export or copy-friendly format.
- [ ] Add "insufficient evidence" answer classification.
- [ ] Add focused tests.
- [ ] Update `AI_CHANGELOG.md`.

## P1 - Source File Re-Index Warning And One-Click Refresh

Status: Done

Goal:
Reduce stale RAG results when the repository HEAD changes after indexing.

Checklist:

- [x] Show indexed HEAD vs current HEAD in RAG and Project Chat.
- [x] Add stale source_file chunk count.
- [x] Add one-click source_file re-index action.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Mapping Feedback Analytics And Review Queue

Status: Planned

Goal:
Turn manual mapping feedback into an analysis quality workflow.

Checklist:

- [ ] Add feedback completed/pending summary.
- [ ] Add low-confidence mapping review queue.
- [ ] Add filters for stale, corrected, and disputed mappings.
- [ ] Add feedback export.
- [ ] Add focused tests.
- [ ] Update `AI_CHANGELOG.md`.

## P2 - CI Test Workflow

Status: Planned

Goal:
Run tests consistently before merge or push.

Checklist:

- [ ] Add GitHub Actions workflow.
- [ ] Run py_compile or import smoke check.
- [ ] Run pytest.
- [ ] Document local verification commands.
- [ ] Update `AI_CHANGELOG.md`.

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

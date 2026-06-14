# AI Change Log

## 2026-06-14

### Demo user guide

- Added a user-facing 시연 사용 가이드 that walks through the sample-project demonstration flow from project registration and Git sync through Mapping, Risk Analysis, AI Progress, Program Detail, Git History, Commit Impact, RAG, Project Chat, and AI Code Review.
- Linked the guide from README so presenters can find it directly from the documentation hub.
- Corrected the stale sample walkthrough wording that still described the expected sample commit count as 30 instead of 48.
- Important files: `docs/demo-user-guide.md`, `README.md`, `docs/rich-sample-demo-walkthrough.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `rg -n "demo-user-guide|시연 사용 가이드|예상 샘플 commit 수|30입니다|48입니다" README.md docs\demo-user-guide.md docs\rich-sample-demo-walkthrough.md` found the README link, new guide title, and 48-commit wording with no stale 30-commit wording; `git diff --check` reported only Windows line-ending warnings and no whitespace errors.

## 2026-06-10

### CI Git default branch test fix

- Made Git repository status tests deterministic on Linux CI by explicitly creating or renaming temporary test repositories to the `main` branch before pushing to `origin/main`.
- Recorded the CI failure lesson that Git-dependent tests must not rely on each developer machine's global `init.defaultBranch`.
- Important files: `tests/test_git_repository_status_service.py`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: Linux container reproduction with Git installed failed before the fix on `test_repository_status_reports_upstream_ahead_behind` because `git push -u origin main` had no local `main` ref; `.\.venv\Scripts\python.exe -m compileall src app.py tests` passed; `.\.venv\Scripts\python.exe -m pytest tests\test_git_repository_status_service.py -q` passed with 4 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 95 tests; Linux container verification with Git installed and CI-like env passed with 95 tests.

### Commit-based mapping fallback and verified application screenshots

- Ran the 48-commit sample project through the core demo pipeline before refreshing screenshots: Git sync data, commit-based Mapping, Risk Analysis, AI Progress, RAG indexing/retrieval, and Project Chat.
- Added a commit-based Mapping fallback so malformed LLM JSON responses use conservative token-similarity evidence instead of leaving a single commit in failed state and blocking downstream verification.
- Added a process-local DB initialization lock so concurrent Streamlit sessions do not run Alembic migrations at the same time during screenshot automation.
- Extended screenshot automation with project selection, tab/action support, and realistic RAG search input.
- Refreshed Application Preview screenshots for Home, Mapping, Risk Analysis, AI Progress, RAG Search, Project Chat, Git History, and Git History detail against `AAA Sample Shop Rich Demo 48`.
- Refreshed the README top representative screenshot `docs/images/ai-commit-advisor-home.png` from the same verified Home state so README and Application Preview show the same sample project status.
- Added `docs/images/ai-commit-advisor-home-48.png` and updated README to use that versioned file name so GitHub/browser image cache cannot keep showing the previous representative screenshot.
- Updated AI behavior documentation, Application Preview context, roadmap tracking, and failure history for the verified demo flow and the two reusable failure lessons.
- Important files: `src/services/mapping_service.py`, `src/db/init_db.py`, `scripts/capture_feature_screenshot.py`, `tests/test_mapping_service.py`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/failure-history.md`, `docs/images/ai-commit-advisor-home.png`, `docs/images/ai-commit-advisor-home-48.png`, `docs/images/features/*.png`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py scripts` passed; `.\.venv\Scripts\python.exe -m pytest tests\test_mapping_service.py -q` passed with 4 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 95 tests; 48-commit Mapping verification completed 48 commits with 0 failed and 59 mappings; Risk Analysis produced 12 unresolved risks; AI Progress produced 8 implementation-status rows with plan average 90.6%, AI average 50.0%, and gap 40.6%; RAG indexing built and embedded 296 chunks with 0 failures; Project Chat answered `결제금액 검증은 어디에서 수행되나요?` with 8 sources including `PaymentService.java`; screenshot capture passed for `home`, `mapping`, `risk-analysis`, `ai-progress`, `rag-search`, `project-chat`, `git-history`, and `git-history-detail`; `git diff --check` passed with only Windows line-ending warnings.

### Sample project commit history expansion

- Expanded the generated 샘플 프로젝트 history from 30 to 48 commits while keeping the existing 8-program Spring MVC + MyBatis shape.
- Added meaningful follow-up scenarios for payment audit and amount limits, inventory release, dashboard stale-payment warning, settlement export partial evidence, return backlog documentation, sales-report tax correction, coupon partial completion, operator audit evidence, QA checklists, and Project Chat citation prompts.
- Updated sample design and walkthrough documentation to describe the new 35-50 commit target range and 48-commit generated dataset.
- Regenerated the sibling sample project repository at `C:\dev\ai-advisor-sample-shop` with 48 commits and refreshed upload Excel files.
- Important files: `scripts/create_sample_target_repo.py`, `tests/test_sample_data_generation.py`, `docs/sample-target-repo-demo-design.md`, `docs/rich-sample-demo-walkthrough.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m py_compile scripts\create_sample_target_repo.py` passed; `.\.venv\Scripts\python.exe -m pytest tests\test_sample_data_generation.py -q` passed with 12 tests; `.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force` passed and regenerated `C:\dev\ai-advisor-sample-shop`; `git -C C:\dev\ai-advisor-sample-shop rev-list --count HEAD` returned `48`; `git -C C:\dev\ai-advisor-sample-shop status --short` returned no changes; upload files `sample_developers.xlsx`, `sample_development_plan.xlsx`, `sample_programs.xlsx`, and `sample_standard_terms.xlsx` exist; local Streamlit web verification on `http://localhost:8537` created `AAA Sample Shop 48 Web Test (97)`, Git full sync stored 48 commits and 105 changed files, the same import/save services used by the Excel upload screens stored 8 programs, 8 development-plan rows, and 10 standard terms, Home displayed 8 programs and 48 commits, Git History displayed 48 commits and 105 changed files, Program management displayed 8 programs, and Standard Terms displayed 10 rows; `.\.venv\Scripts\python.exe -m compileall scripts src app.py` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 94 tests.

### Server repository status display

- Added `src/services/git_repository_status_service.py` to read app-server Git repository branch, HEAD, upstream, ahead/behind, working tree changes, storage-root allowance, and DB sync mismatch status without mutating the repo.
- Added a shared `src/ui/git_status_panel.py` status panel.
- Updated `Git 동기화` to show full repository status before sync actions, including Repo HEAD, DB sync commit, branch, upstream, ahead/behind, dirty file count, and guidance when DB sync is stale.
- Updated `프로젝트/Git 설정` to show a compact repository status summary for the selected project.
- Added focused tests for clean repo status, dirty working tree detection, missing path handling, and upstream ahead/behind detection.
- Updated feature, setup/operations, architecture, and roadmap documentation.
- Important files: `src/services/git_repository_status_service.py`, `src/ui/git_status_panel.py`, `src/ui/git_page.py`, `src/ui/project_page.py`, `tests/test_git_repository_status_service.py`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/architecture.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest tests/test_git_repository_status_service.py -q` passed with 4 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 94 tests.

### Git History Application Preview screenshot

- Added Git History scenarios to `scripts/capture_feature_screenshot.py` so the commit list/activity graph state and commit detail/diff preview state can be recaptured.
- Captured `docs/images/features/git-history.png` against the local Streamlit app using the `AAA Sample Shop Rich Demo` project with 30 commits and 77 changed files.
- Captured `docs/images/features/git-history-detail.png` to show selected commit metadata, changed files, saved diff preview, and full-diff control.
- Updated `docs/application-preview.md` to include both Git History screenshots.
- Important files: `scripts/capture_feature_screenshot.py`, `docs/application-preview.md`, `docs/images/features/git-history.png`, `docs/images/features/git-history-detail.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature git-history --url http://127.0.0.1:8531 --screenshot docs\images\features\git-history.png --surface local --height 1700 --expect-text "AAA Sample Shop Rich Demo" --expect-text "변경 파일" --expect-text "저장된 diff preview"` passed; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature git-history-detail --url http://127.0.0.1:8531 --screenshot docs\images\features\git-history-detail.png --surface local --height 1000 --expect-text "AAA Sample Shop Rich Demo" --expect-text "저장된 diff preview" --expect-text "전체 diff"` passed; visual inspection confirmed the screenshots show meaningful Git History states.

### Git History viewer

- Added `src/services/git_history_service.py` for project-scoped commit listing, commit detail lookup, changed-file diff preview data, and safe full `git show` retrieval for DB-registered commits.
- Added `src/ui/git_history_page.py` with message, author, file path, date, and limit filters; commit KPI summary; daily and author commit charts; selected commit details; changed file diff preview; and optional full diff lookup from the app-server Git repository.
- Added the `Git History` navigation entry under `분석 결과`.
- Added focused tests for message/author/file filtering, commit detail retrieval, full diff lookup, and missing-commit safety behavior.
- Updated README, feature guide, architecture docs, and roadmap tracking for the new Git History screen.
- Important files: `app.py`, `src/services/git_history_service.py`, `src/ui/git_history_page.py`, `tests/test_git_history_service.py`, `README.md`, `docs/feature-guide.md`, `docs/architecture.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py scripts\update_server_repos.py` passed; `.\.venv\Scripts\python.exe -m pytest tests/test_git_history_service.py -q` passed with 2 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 90 tests.

### Server repository update runbook and script

- Added `scripts/update_server_repos.py` for internal server operators to update pre-cloned repositories under `REPO_STORAGE_ROOT`.
- Kept the script credential-free: it does not clone repositories or store Git secrets, and defaults to `git fetch --prune` without hard reset.
- Added explicit `--reset`, `--branch`, `--force`, `--dry-run`, and `--repo` options so branch reset is deliberate and dirty working trees are not reset unless forced.
- Added `docs/server-repository-update-runbook.md` with manual commands, script usage, dry-run examples, and the recommended sequence before app Git Sync.
- Linked the runbook from README, setup/operations, Git repository operating model, and engineering decision docs.
- Promoted and completed the roadmap task for the server repository update runbook/script.
- Important files: `scripts/update_server_repos.py`, `docs/server-repository-update-runbook.md`, `README.md`, `docs/git-repository-operating-model.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m py_compile scripts\update_server_repos.py` passed; `.\.venv\Scripts\python.exe scripts\update_server_repos.py --help` passed; dry-run against a temporary Git repository under `.tmp\server-repo-update-check` passed; `git diff --check` passed with only line-ending warnings.

### App-server Git repository operating model

- Reframed Git repository access from browser-user local paths to app-server-accessible repository paths for internal-network server operation.
- Added optional `REPO_STORAGE_ROOT` configuration and project path validation so server deployments can restrict registered Git repositories to an approved storage root.
- Updated Git/project UI labels and messages to use app-server Git repository wording.
- Added `docs/git-repository-operating-model.md` and linked it from README to explain the server-path model, recommended repo storage layout, Docker path mapping, Git Sync boundaries, and security notes.
- Added the same app-server path clarification to README Quick Start and setup/operations local execution guidance so first-time local users understand that their PC is the app server.
- Documented sample project path handling for local Python, default Windows Docker Compose, and internal-server demo runs.
- Documented the recommended operating policy that repository clone/fetch/reset remains an operator or external script responsibility for now, while AI Commit Advisor analyzes pre-cloned app-server repository paths and performs DB Git Sync.
- Added a roadmap candidate for a server repository update runbook/script before any app-managed clone/fetch workflow.
- Updated setup/operations, feature guide, architecture, engineering decision, environment examples, Docker Compose, and roadmap documentation.
- Preserved `git_repo_path` as the internal DB/model name for compatibility while clarifying its meaning in user-facing docs.
- Important files: `src/utils/config.py`, `src/utils/repo_path.py`, `src/ui/project_page.py`, `src/ui/git_page.py`, `src/ui/code_review_page.py`, `src/ui/rag_page.py`, `src/ui/sample_data_page.py`, `tests/test_repo_path.py`, `README.md`, `docs/git-repository-operating-model.md`, `docs/setup-and-operations.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/sample-target-repo-demo-design.md`, `docs/architecture.md`, `docs/feature-guide.md`, `docs/engineering-decisions.md`, `docker-compose.yml`, `.env.example`, `.env.local-llm.example`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest tests/test_repo_path.py -q` passed with 5 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 88 tests.

### Roadmap candidate task tracking

- Added a `Candidate Tasks` section to `ROADMAP.md` for unresolved product, UX, state-management, and architecture concerns that should be preserved without marking them active.
- Recorded follow-up candidates for project-scoped UI state namespacing, program management project-flow cleanup, and developer management scope decision.
- Updated `AGENTS.md` so agents add candidate tasks when the user wants to preserve a concern without starting implementation, and promote candidates into active roadmap tasks before implementation.
- Recorded the documentation/roadmap management decision in `docs/engineering-decisions.md`.
- Important files: `ROADMAP.md`, `AGENTS.md`, `docs/engineering-decisions.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path ROADMAP.md -Encoding UTF8`, `Get-Content -Path AGENTS.md -Encoding UTF8`, and `Get-Content -Path docs\engineering-decisions.md -Encoding UTF8` rendered the new sections correctly; `rg -n "Candidate Tasks|Project-scoped UI state namespacing|Program management project flow cleanup|Developer management scope decision" ROADMAP.md AGENTS.md docs\engineering-decisions.md AI_CHANGELOG.md` confirmed expected references; `git diff --check` passed with only line-ending warnings.

### Home current project focus

- Changed Home from an all-project aggregate into a current-project command screen that uses the shared sidebar project context.
- Scoped Home pipeline status, next actions, KPIs, progress charts, and risk program table to the selected project.
- Kept app-level project count and developer count as secondary context while project-specific program, commit, mapping, implementation status, and risk counts use the current project.
- Updated feature and architecture documentation, refreshed the Home Application Preview screenshot, and tracked the UX task in `ROADMAP.md`.
- Important files: `src/ui/home_page.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/images/features/home.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 85 tests; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8524 --screenshot docs\images\features\home.png --surface local --expect-text "현재 프로젝트: AAA Sample Shop Rich Demo (4)" --expect-text "현재 프로젝트의 계획, 커밋, 진척도, 리스크 현황"` passed and confirmed Home shows current-project counts such as 8 programs and 30 commits for the sample project.

### Global project context

- Added `src/ui/project_context.py` as the shared UI helper for current project selection, validation, deleted-selection recovery, and sidebar rendering.
- Moved the current project selector into the sidebar and converted project-scoped pages to use the shared context instead of repeated page-level `프로젝트 선택` controls.
- Kept `프로젝트/Git 설정` as the project creation/editing exception and synchronized saved projects back to the global current project.
- Updated `프로그램 관리` so the global project is the default target while preserving an explicit `새 프로젝트명으로 저장` exception for legacy upload/create flows.
- Added focused tests for project context selection retention, invalid selection recovery, and no-project cleanup.
- Updated feature, architecture, engineering decision, roadmap, changelog, and Home preview screenshot documentation for the new project-selection flow.
- Important files: `app.py`, `src/ui/project_context.py`, `src/ui/*_page.py`, `tests/test_project_context.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `docs/images/features/home.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 85 tests; Browser verification on `http://localhost:8522` confirmed Home, Dashboard, and Mapping show the sidebar current project without duplicated page-level project selectors, while `프로젝트/Git 설정` keeps its expected project selector; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8522 --screenshot docs\images\features\home.png --surface local` passed.

### AI Agent onboarding guide

- Added `docs/agent-onboarding.md`, a beginner-friendly Korean guide for developers using AI Agent workflows with this project.
- Explained that `AGENTS.md` is durable project guidance loaded by Codex from the project folder, not text that needs to be repeated in every prompt.
- Clarified when users should mention `ROADMAP.md`, documentation checks, verification constraints, or exclusions directly in a prompt.
- Linked the onboarding guide from README and tracked the documentation task in `ROADMAP.md`.
- Generalized README and onboarding wording around `AI Agent` users instead of naming Codex beginners or teammates in the entry description.
- Shortened the guide title and README description so the onboarding link reads like a project document rather than a generic AI Agent introduction.
- Important files: `docs/agent-onboarding.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Test-Path docs\agent-onboarding.md` returned `True`; `rg -n "AI Agent 작업 안내|AGENTS.md를 매번" README.md docs\agent-onboarding.md AI_CHANGELOG.md ROADMAP.md` confirmed the expected references; `Get-Content -Path README.md -Encoding UTF8` rendered the README document link correctly; `git diff --check` passed with only Git line-ending warnings.

### Sidebar navigation structure stabilization

- Rendered active and inactive sidebar menu items through the same `st.button` path instead of mixing Streamlit buttons with custom `.nav-active` markup.
- Removed custom active menu `div` CSS and made repeated clicks on the current page a no-op without rerun.
- Expanded Home screenshot verification so sidebar checks fail when custom `.nav-active` markup returns or when menu item boxes, text offsets, or adjacent spacing change after navigation.
- Recorded the maintainability decision in `docs/engineering-decisions.md` and the previous CSS-only stabilization gap in `docs/failure-history.md`.
- Important files: `app.py`, `scripts/capture_feature_screenshot.py`, `docs/engineering-decisions.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall app.py src scripts` passed; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8518 --screenshot .tmp\sidebar-structure-home.png --surface local` passed; `git diff --check` passed with only Git line-ending warnings.

### Documentation impact gate policy

- Added a `Documentation Impact Gate` to `AGENTS.md` so meaningful code, UX, test, behavior, automation, operations, and documentation work must classify documentation impact before implementation.
- Made `docs/engineering-decisions.md` a required review candidate when a request is framed around maintainability, future reuse, verification policy, structural tradeoffs, operating policy, or agent behavior.
- Recorded the policy rationale in `docs/engineering-decisions.md` and the missed engineering-decision review in `docs/failure-history.md`.
- Added a roadmap task for the documentation impact gate policy work.
- Important files: `AGENTS.md`, `docs/engineering-decisions.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8`, `Get-Content -Path docs\engineering-decisions.md -Encoding UTF8`, and `Get-Content -Path docs\failure-history.md -Encoding UTF8` rendered the new policy, decision, and failure-history entries correctly; `rg -n "Documentation Impact Gate|Documentation impact gate|Engineering decision review|engineering-decisions.md" AGENTS.md docs AI_CHANGELOG.md ROADMAP.md` confirmed the expected references; `git diff --check` passed with only Git line-ending warnings.

### Sidebar 메뉴 계층 크기 조정

- Sidebar 중메뉴가 하위 메뉴보다 살짝 크게 보이도록 그룹 제목은 `0.9rem`, 하위 메뉴와 선택 메뉴는 `0.86rem`으로 조정했습니다.
- Streamlit button 내부 텍스트에도 같은 크기와 line-height를 적용해 메뉴 클릭 전후 글자 크기가 달라 보이지 않도록 했습니다.
- Home Application Preview screenshot을 새 사이드바 계층 스타일이 보이도록 다시 캡처했습니다.
- 기능 가이드와 Application Preview 문서에 사이드바 중메뉴/하위 메뉴 계층 의도를 반영했습니다.
- Important files: `app.py`, `docs/images/features/home.png`, `docs/feature-guide.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall app.py src` passed; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8511 --screenshot docs\images\features\home.png --surface local` passed; browser inspection on local port 8511 confirmed group labels render at 14.4px and child menu items render at 13.76px; clicking `Dashboard` confirmed active and inactive child menu text both render at 13.76px with 18.576px line-height before and after selection.

### Reader-facing wording policy simplification

- Simplified the `AGENTS.md` natural Korean documentation wording policy by removing preferred phrase examples.
- Kept the principle that user-facing Korean docs should use reader-facing product terms instead of literal internal repository or data-generation terminology.
- Kept the guidance to preserve stable technical file paths while making link labels and surrounding explanation natural.
- Important files: `AGENTS.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8` rendered the simplified policy correctly; targeted search confirmed the preferred phrase examples were removed from `AGENTS.md`; `git diff --check` passed with only Git line-ending warnings.

### Natural wording policy generalization

- Generalized the `AGENTS.md` natural Korean documentation wording policy so it no longer lists awkward phrases one by one.
- Kept the preferred `샘플 프로젝트`, `데모용 샘플 프로젝트`, `샘플 프로젝트 Git 저장소`, and `샘플 프로젝트 설계` guidance while describing the avoid rule as a general principle.
- Important files: `AGENTS.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: targeted `AGENTS.md` search confirmed the explicit awkward-phrase list was removed; `Get-Content -Path AGENTS.md -Encoding UTF8` rendered the generalized policy correctly; `git diff --check` passed with only Git line-ending warnings.

### Sample project wording cleanup

- Added `AGENTS.md` guidance to avoid literal sample/demo wording such as `샘플 대상 저장소`, `합성 샘플 저장소`, and `sample target repo` in user-facing Korean documentation.
- Updated README, sample project design, and sample verification guide prose to use `샘플 프로젝트`, `데모용 샘플 프로젝트`, and `샘플 프로젝트 Git 저장소` where appropriate.
- Recorded the wording decision in `docs/engineering-decisions.md`.
- Kept code identifiers and existing file names unchanged to avoid unnecessary path churn.
- Important files: `AGENTS.md`, `README.md`, `docs/sample-target-repo-demo-design.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/source-indexing-and-embedding-plan.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: targeted wording search across README and user-facing docs returned no matches for the awkward sample-target/synthetic-target wording; `Get-Content -Encoding UTF8` confirmed README, sample project design, and sample verification guide render Korean text correctly; `git diff --check` passed with only Git line-ending warnings.

### Application Preview rename

- Renamed the previous screenshot-focused document to `docs/application-preview.md`.
- Updated README, Feature Guide, setup/operations guidance, `AGENTS.md`, and engineering decision references to use `Application Preview`.
- Renamed the agent screenshot policy section to `Application Preview Screenshot Guidance`.
- Replaced stale Markdown path references so current documentation searches point to the new document path.
- Important files: `docs/application-preview.md`, `README.md`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `AGENTS.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: legacy gallery naming and path searches returned no matches; local `Test-Path` checks passed for `docs\application-preview.md` and updated Markdown files; `Get-Content -Path docs\application-preview.md -Encoding UTF8` rendered the renamed Korean document correctly; `git diff --check` passed with only Git line-ending warnings.

### Architecture document path cleanup

- Moved the root architecture guide to `docs/architecture.md` so detailed project documentation lives under `docs/`.
- Updated README and `AGENTS.md` references to use the new architecture document path.
- Replaced stale architecture document path references in Markdown history so current path searches do not point to the removed root file.
- Recorded the documentation structure rationale in `docs/engineering-decisions.md`.
- Important files: `docs/architecture.md`, `README.md`, `AGENTS.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `rg -n "README_ARCHITECTURE\\.md" .` returned no matches; `rg -n "docs/architecture\\.md|architecture\\.md|Architecture document path cleanup|아키텍처" README.md AGENTS.md AI_CHANGELOG.md ROADMAP.md docs` confirmed the new references; local `Test-Path` checks passed for `docs\architecture.md` and updated Markdown files; `Get-Content -Path docs\architecture.md -Encoding UTF8` rendered the moved Korean document correctly; `git diff --check` passed with only Git line-ending warnings.

### Feature screenshot capture automation

- Added `scripts/capture_feature_screenshot.py`, an extensible Playwright-based capture tool with starter scenarios for `home` and `project-chat`.
- Kept `scripts/verify_home_ui.py` as a compatibility wrapper around the new Home scenario.
- Documented capture commands, runtime surface labeling, and `--expect-text` / `--forbid-text` state checks in setup and operations guidance.
- Updated the engineering decisions log with the implemented script and initial scenario scope.
- Important files: `scripts/capture_feature_screenshot.py`, `scripts/verify_home_ui.py`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m py_compile scripts\\capture_feature_screenshot.py scripts\\verify_home_ui.py` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --help` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --feature home --url http://localhost:8501 --screenshot .tmp\\feature-home-check.png --surface local` passed; `.\\.venv\\Scripts\\python.exe scripts\\verify_home_ui.py --url http://localhost:8501 --screenshot .tmp\\home-wrapper-check.png` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --feature project-chat --url http://localhost:8501 --screenshot .tmp\\project-chat-scenario-check.png --surface local` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --feature all --url http://localhost:8501 --output-dir .tmp\\feature-captures --surface local` passed and wrote only under `.tmp`; `git diff --check` passed.

### Engineering decisions documentation log

- Added `docs/engineering-decisions.md` to record non-failure engineering, operations, verification, automation, deployment, and documentation-structure decisions with rationale and tradeoffs.
- Recorded the screenshot capture automation direction as the first decision, including why future capture work should use extensible feature scenarios instead of one-off manual flows.
- Updated `AGENTS.md`, README, and failure-history guidance so agents can distinguish changelog entries, failure history, and decision history.
- Added a roadmap task for the decision log documentation work.
- Important files: `docs/engineering-decisions.md`, `AGENTS.md`, `README.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path docs\engineering-decisions.md -Encoding UTF8` rendered the new Korean decision log correctly; `rg -n "engineering-decisions|Engineering Decisions|Engineering decisions documentation log|Engineering Decisions Log" README.md AGENTS.md docs\failure-history.md AI_CHANGELOG.md ROADMAP.md` confirmed the expected links and policy references; local `Test-Path` checks passed for the linked Markdown files; `git diff --check` passed with only Git line-ending warnings.

### Ignore Codex attachment staging folder

- Added `.codex-remote-attachments/` to `.gitignore` so uploaded chat attachment files do not appear as untracked project changes.
- Important files: `.gitignore`, `AI_CHANGELOG.md`.
- Verification: `git status --short --branch` no longer lists `.codex-remote-attachments/` as an untracked path; `git diff --check` passed.

### Verification surface selection agent policy

- Added `AGENTS.md` guidance for choosing local `.venv` verification versus Docker verification based on the behavior being changed.
- Clarified that ordinary app source changes should not trigger Docker image rebuilds by default, while Dockerfile, Compose, mount, env, startup migration, healthcheck, and container-only bugs require Docker verification.
- Added guidance to keep Docker build log inspection targeted because build logs are long, and to state which surface was verified when local Python and Docker can differ.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8` confirmed the new policy text; `git diff --check` passed.

### Project Chat verified answer screenshot recapture

- Re-captured the Project Chat screenshot after confirming Docker source verification was fixed.
- The refreshed screenshot shows matching Current HEAD and Indexed HEAD, a successful answer for `결제금액 검증은 어디에서 수행되나요?`, visible `PaymentService.java` evidence, and `근거 복사용 Markdown`.
- Important files: `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: Playwright verified `대화 이력`, the payment validation question, `PaymentService.java`, current source evidence count, and `근거 복사용 Markdown` were visible; visually inspected the screenshot; `git diff --check` passed.

### Docker repository path mapping for Project Chat verification

- Added repository path prefix mapping so Docker app containers can read host Git repositories stored in the DB as Windows paths such as `C:\dev\ai-advisor-sample-shop`.
- Mounted `C:/dev` into the app container as `/host-dev` and added `REPO_PATH_HOST_PREFIX` / `REPO_PATH_CONTAINER_PREFIX` environment variables in Compose.
- Installed `git` in the Docker image because Git Sync and current HEAD checks need the Git command inside the app container.
- Applied mapped repo paths to Git commands, source_file chunking, source index status, and Project Chat source verification.
- Added focused tests for repository path mapping.
- Documented the Docker host repo mount behavior in setup/operations, architecture, and failure history.
- Re-captured the Project Chat screenshot after Docker source verification was restored so the answer shows verified `PaymentService.java` evidence instead of an insufficient-evidence state.
- Important files: `Dockerfile`, `src/utils/config.py`, `src/utils/repo_path.py`, `src/services/git_service.py`, `src/rag/source_verifier.py`, `src/rag/source_index_service.py`, `src/rag/chunker.py`, `tests/test_repo_path.py`, `docker-compose.yml`, `docs/setup-and-operations.md`, `docs/architecture.md`, `docs/failure-history.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m py_compile src/utils/config.py src/utils/repo_path.py src/services/git_service.py src/rag/source_verifier.py src/rag/source_index_service.py src/rag/chunker.py` passed; `.\\.venv\\Scripts\\python.exe -m pytest tests/test_repo_path.py tests/test_source_file_rag.py tests/test_source_index_service.py tests/test_project_chat_service.py -q` passed; `docker compose config` passed; Docker app verified the sample Project Chat source index with matching Current HEAD and Indexed HEAD, invalid/stale/mismatch counts at 0, and visible `PaymentService.java` answer evidence; `git diff --check` passed.

### CI manual rerun trigger for hosted runner failures

- Added `workflow_dispatch` to the GitHub Actions CI workflow so CI can be manually rerun from the Actions UI without creating another push.
- Documented the GitHub-hosted runner acquisition failure for `docs: explain RAG chat rationale #42`, including how to distinguish platform runner failures from code/test failures.
- Important files: `.github/workflows/ci.yml`, `docs/failure-history.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m compileall src app.py` passed; `.\\.venv\\Scripts\\python.exe -m pytest -q` passed with 80 tests; `git diff --check` passed.

### Project Chat persisted history screenshot refresh

- Refreshed the Project Chat screenshot so the gallery shows the newly added persisted `대화 이력`, saved question/answer rendering, verified current source evidence, and `근거 복사용 Markdown` export area.
- Added a short Application Preview caption describing the captured Project Chat state.
- Important files: `docs/images/features/project-chat.png`, `docs/application-preview.md`, `AI_CHANGELOG.md`.
- Verification: Playwright captured `docs/images/features/project-chat.png` from `http://localhost:8501` after verifying `대화 이력`, `결제금액 검증은 어디에서 수행되나요?`, `근거 복사용 Markdown`, and answer evidence were visible; visually inspected the refreshed screenshot; `git diff --check` passed.

### Korean text encoding agent policy

- Added `AGENTS.md` guidance for reading Korean Markdown and UTF-8 text on Windows with explicit UTF-8 commands.
- Clarified that garbled PowerShell output should not be treated as file corruption until the file is re-read with explicit UTF-8.
- Added guardrails to avoid rewriting Korean prose just to fix terminal-output mojibake.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8` rendered Korean policy text correctly; `git diff --check` passed.

### Korean documentation wording cleanup

- Cleaned up awkward Korean wording in Markdown documentation where English terms had been translated too literally.
- Renamed the sample walkthrough wording to `샘플 프로젝트 검증 가이드`.
- Replaced reader-limiting wording with more general reader-focused phrasing where the document is not team-only.
- Replaced literal safety-sequence wording with `권장 실행 흐름` or direct explanations about avoiding excessive LLM/embedding work.
- Important files: `README.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/sample-target-repo-demo-design.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: searched Markdown for the awkward sample-guide and reader-limiting phrases; `git diff --check` passed.

### Application Dockerfile and deployment guide

- Added an application `Dockerfile` so the Streamlit app can be built and run with a repeatable Python 3.11 container image.
- Added `.dockerignore` to keep local virtualenvs, caches, secrets, generated screenshots, and database data out of the Docker build context.
- Expanded `docker-compose.yml` with a Streamlit `app` service, PostgreSQL healthcheck, mock LLM/embedding defaults, and container-to-host local LLM base URLs.
- Documented Docker deployment rationale, environment variables, migration startup behavior, and smoke-check commands in the setup/operations guide.
- Updated README Quick Start to distinguish local Python execution with `docker compose up -d postgres` from full Docker app execution with `docker compose up -d --build`.
- Updated the architecture document with the Docker deployment structure and startup migration flow.
- Important files: `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `README.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `docker compose config` passed; `docker build -t ai-commit-advisor:local .` passed; `docker compose up -d --build app` passed; `Invoke-WebRequest http://localhost:8501/_stcore/health -UseBasicParsing` returned HTTP 200; `docker compose ps` showed `ai_commit_advisor_app` and `ai_commit_advisor_postgres` healthy; `docker exec ai_commit_advisor_postgres pg_isready -U ai_user -d ai_commit_advisor` reported accepting connections.

### Project Chat database history and citation export

- Added database-backed Project Chat sessions and messages so project conversations survive Streamlit session resets and can be reopened by project.
- Added Alembic migration `20260610_0004_add_project_chat_sessions` for `project_chat_sessions` and `project_chat_messages`.
- Added a Project Chat history service for session creation, message persistence, UI conversion, and copy-friendly Markdown citation export.
- Updated the Project Chat UI with project-level `대화 이력`, `새 대화`, persisted message rendering, and `근거 복사용 Markdown` for assistant answers.
- Updated README, feature guide, architecture, setup/operations, and AI technical overview documentation to explain persisted chat history, citation export, and traceability.
- Important files: `src/db/models.py`, `migrations/versions/20260610_0004_add_project_chat_sessions.py`, `src/rag/chat_history_service.py`, `src/ui/project_chat_page.py`, `tests/test_project_chat_history_service.py`, `README.md`, `docs/architecture.md`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/ai-technical-overview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m py_compile src/db/models.py src/rag/chat_history_service.py src/ui/project_chat_page.py migrations/versions/20260610_0004_add_project_chat_sessions.py` passed; `.\\.venv\\Scripts\\python.exe -m compileall src tests` passed; `.\\.venv\\Scripts\\python.exe -m pytest -q` passed with 80 tests; `git diff --check` passed without whitespace errors; Browser verification against `http://localhost:8512` confirmed Project Chat history controls render.

### Feature rationale documentation policy

- Added `AGENTS.md` guidance that meaningful new features, workflows, AI behavior, operational behavior, and major UX changes require rationale documentation in an appropriate Markdown file.
- Clarified that rationale documentation should explain why the feature was introduced, the user or operational gap it addresses, expected effect, usage timing, tradeoffs, limitations, and related verification or failure-history lessons.
- Added feature rationale documentation to the pre-commit documentation checklist.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Project failure history documentation and agent policy

- Added `docs/failure-history.md` to record reusable project-wide failure root causes, fixes, prevention rules, remaining limits, and verification results.
- Documented the incremental source indexing CI failure as the first entry, where DB-backed tests were added without a pgvector PostgreSQL service in GitHub Actions.
- Added `AGENTS.md` policy requiring failure history updates when product, UX, AI behavior, RAG/embedding, data, schema, migration, sample data, documentation, test, dependency, workflow, environment, deployment, or operational mistakes reveal reusable learning.
- Linked the failure history document from the README documentation hub.
- Important files: `docs/failure-history.md`, `AGENTS.md`, `README.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed; README documentation links for the new file passed local path checks.

## 2026-06-09

### CI database service for incremental source indexing tests

- Added a pgvector PostgreSQL service to the GitHub Actions CI workflow so database-backed source indexing tests can run in CI.
- Set CI `DATABASE_URL`, `PGVECTOR_DIMENSION`, `LLM_PROVIDER=mock`, and `EMBEDDING_PROVIDER=mock` explicitly to match the test environment assumptions.
- Important files: `.github/workflows/ci.yml`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m compileall src tests` passed; `.\\.venv\\Scripts\\python.exe -m pytest -q` passed with 78 tests.

### RAG and Project Chat rationale documentation

- Added feature guide rationale for why Project Chat uses verified current `source_file` chunks and standard terminology expansion instead of answering from stale chunks or commit diffs.
- Important files: `docs/feature-guide.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Incremental source indexing and embedding cost control

- Added manual incremental source indexing for `source_file` chunks so RAG and Project Chat can refresh only Git Sync changed files instead of scanning the whole repository during normal work.
- Added changed-file handling for added, modified, copied, deleted, and renamed files. Deleted and replaced source chunks now remove related vectors so stale file evidence does not remain searchable.
- Kept embedding generation explicit: incremental indexing and Project Chat source refresh leave new chunks as `embedding_status=pending`; users generate missing vectors from `RAG 검색 > Embedding` with a bounded limit.
- Added current embedding-model missing vector count to source index status and surfaced it in RAG and Project Chat.
- Added RAG and Project Chat buttons for `최근 Git sync 변경 파일만 인덱싱`, while keeping full `현재 소스 다시 인덱싱` as the recovery/initial-build action.
- Expanded Korean operations and AI technical documentation so teammates can distinguish Git Sync, incremental indexing, full re-indexing, and embedding generation from documentation alone.
- Important files: `src/rag/source_index_service.py`, `src/rag/chunker.py`, `src/ui/rag_page.py`, `src/ui/project_chat_page.py`, `tests/test_incremental_source_index_service.py`, `docs/setup-and-operations.md`, `docs/ai-technical-overview.md`, `docs/source-indexing-and-embedding-plan.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src tests` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 78 tests; Browser verification against `http://localhost:8511` confirmed the new incremental indexing controls render on RAG and Project Chat.

### Agent documentation rationale guidance

- Added AGENTS guidance that feature, architecture, workflow, and AI behavior documentation should capture the user problem, operational gap, design rationale, tradeoffs, and remaining limitations, not only implementation details.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Korean-first user documentation cleanup

- Reworked user-facing Markdown documentation so explanatory prose is Korean-first, while preserving natural English headings, code identifiers, commands, environment variables, API names, and product/menu names where appropriate.
- Translated English-heavy documentation for source indexing, sample target repo design, rich sample demo walkthrough, DB migrations, and AI technical overview.
- Aligned README documentation links, screenshot gallery labels, and architecture/menu wording with the current Korean sidebar structure.
- Added an agent instruction that user-facing documentation should use Korean for explanatory prose by default without forcing familiar English documentation labels into Korean.
- Kept internal agent/task-management documents such as `AGENTS.md`, `ROADMAP.md`, and historical `AI_CHANGELOG.md` entries out of the translation scope except for the new roadmap/changelog bookkeeping.
- Important files: `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/db-migrations.md`, `docs/feature-guide.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/sample-target-repo-demo-design.md`, `docs/application-preview.md`, `docs/setup-and-operations.md`, `docs/source-indexing-and-embedding-plan.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed; project Markdown link sanity check passed.

### Artifact management sidebar grouping

- Added a `산출물 관리` sidebar group for developer list, program list, development plan, and standard terminology management screens.
- Renamed the Git-author developer page menu label to `개발자 현황` and shortened artifact page labels so upload/direct-management screens are easier to find.
- Updated the feature guide and screenshot gallery labels to match the new sidebar grouping.
- Refreshed the README and screenshot gallery Home images so the sidebar shows the new artifact management grouping.
- Important files: `app.py`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/images/ai-commit-advisor-home.png`, `docs/images/features/home.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.venv\Scripts\python.exe -m py_compile app.py`, `.venv\Scripts\python.exe scripts\verify_home_ui.py --url http://localhost:8510 --screenshot docs\images\features\home.png`, `git diff --check`, and in-app Browser verification against `http://localhost:8510` passed.

### Project Chat history roadmap status correction

- Corrected the `Project Chat Answer Quality And History Persistence` roadmap detail status from `Done` to `In Progress` because database chat persistence, project-level history, and citation export remain incomplete.
- Important files: `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Source indexing and embedding plan

- Added a handoff design document for incremental source indexing, embedding cost control, cloud embedding operation, and Project Chat evidence scope.
- Added a roadmap task for incremental source indexing and embedding cost control so future implementation has a tracked plan.
- Linked the new design document from the README documentation hub for teammate handoff.
- Important files: `docs/source-indexing-and-embedding-plan.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Project Chat reset button alignment

- Adjusted the Project Chat section header column ratio so the reset action sits farther to the right as a section-level action.
- Important files: `src/ui/project_chat_page.py`, `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: `py_compile src/ui/project_chat_page.py` and `git diff --check` passed.

### Project Chat reset button placement

- Moved the Project Chat reset action from the search setting controls to the chat section header.
- Kept the reset button available in the chat header so the first answered turn does not render with a disabled-looking action.
- Important files: `src/ui/project_chat_page.py`, `AI_CHANGELOG.md`.
- Verification: `py_compile src/ui/project_chat_page.py` and `git diff --check` passed.

### Project Chat screenshot top-state refresh

- Refreshed the Project Chat screenshot so it shows the selected sample project, source index status, chat controls, Korean question, answer, and source citations in one view.
- Important files: `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected the refreshed screenshot; `git diff --check` passed.

### Standard terminology documentation and screenshots

- Updated README, Feature Guide, and AI technical overview to explain standard terminology upload and deterministic Korean query expansion.
- Added the standard terminology page to the screenshot gallery.
- Important files: `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/images/features/standard-terms.png`, `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: refreshed screenshots through the local Streamlit app; `git diff --check` passed.

### Project Chat answer formatting and evidence context

- Strengthened the Project Chat prompt so normal answers should be Korean Markdown, not JSON/code-block wrappers, and line ranges must be copied from retrieved metadata.
- Added local LLM response cleanup for common JSON wrapper responses such as fenced `{"response": "..."}` payloads.
- Added citation post-processing so answers that omit file line ranges append verified source metadata citations.
- Added Project Chat evidence context for matched standard terms and expanded queries so Korean query expansion is explainable during verification.
- Important files: `src/rag/chat_service.py`, `src/ui/project_chat_page.py`, `tests/test_project_chat_answer_format.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `pytest tests/test_project_chat_answer_format.py tests/test_project_chat_service.py -q` and `git diff --check` passed.

### Glossary-based Korean query expansion

- Added deterministic Project Chat query expansion using uploaded project standard terms and standard words.
- Added multi-query retrieval that merges results by chunk id and prefers verified source files under `src/main` or `src/test` for Project Chat evidence.
- Added focused query expansion tests for Korean payment amount questions expanding toward payment/code identifiers and `amount <= 0` search hints.
- Important files: `src/rag/query_expander.py`, `src/rag/retriever.py`, `src/rag/chat_service.py`, `tests/test_query_expander.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `pytest tests/test_query_expander.py tests/test_project_chat_service.py -q` and `git diff --check` passed.

### Standard terminology upload UI

- Added a Streamlit `표준용어/표준단어` page under data collection for project-level glossary upload and lookup.
- Added Excel template download, column guide, upload preview, validation summary, save action, and current glossary search/table display.
- Important files: `app.py`, `src/ui/standard_terms_page.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `py_compile app.py src/ui/standard_terms_page.py` and `git diff --check` passed.

### Standard terminology schema and service

- Added the `standard_terms` database model and Alembic migration for project-level SI standard terminology and standard words.
- Added a standard term service for Excel template generation, upload parsing, validation, save/update behavior, search, and derived keyword generation from English terms and abbreviations.
- Added focused tests for derived camelCase/PascalCase/snake_case/upper-snake keywords, required columns, duplicate detection, and row normalization.
- Important files: `src/db/models.py`, `migrations/versions/20260609_0003_add_standard_terms.py`, `src/services/standard_term_service.py`, `tests/test_standard_term_service.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `pytest tests/test_standard_term_service.py -q` and `git diff --check` passed.

### Sample standard terminology artifact plan

- Added sample target repository terminology rows for SI-style standard terms and standard words, including Korean term, English term, abbreviation, and description.
- Updated the sample target generator to create `advisor_uploads/sample_standard_terms.xlsx` alongside the existing developer, program, and development-plan upload files.
- Documented the standard terminology demo dataset and expected Korean Project Chat expansion scenario in the sample target repository design.
- Important files: `scripts/create_sample_target_repo.py`, `tests/test_sample_data_generation.py`, `docs/sample-target-repo-demo-design.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Project Chat glossary and Korean query expansion roadmap

- Added roadmap tasks for project standard terminology/standard word Excel upload, deterministic Korean query expansion, and Project Chat answer formatting/citation accuracy.
- Captured the agreed first-pass scope: teams enter Korean term, English term, and abbreviation while the app derives camelCase, PascalCase, snake_case, upper snake, token, and compact search variants.
- Documented that the initial query expansion should use uploaded terminology deterministically before adding any optional LLM query rewrite.
- Important files: `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### local LLM env 예시와 Project Chat 재현 절차

- Added `.env.local-llm.example` so teammates can start from a ready local_openai configuration for LM Studio chat and embedding models.
- Kept `.env.example` as the lightweight mock default, and updated README Quick Start to explain when to copy each env file.
- Documented that mock vectors are not reused by local_openai embedding search, so RAG Search and Project Chat require regenerating embeddings after provider/model changes.
- Important files: `.env.local-llm.example`, `README.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: markdown/link sanity checks and `git diff --check` passed.

### README 문서 허브 개편

- README를 짧은 진입 문서로 재구성하고, 상세 스크린샷/기능 설명/설치 운영 가이드를 별도 문서로 분리했습니다.
- GitHub에서 동작하는 상대 링크로 README의 Documentation 섹션을 구성해 필요한 문서를 바로 찾을 수 있게 했습니다.
- 기능별 화면 캡처는 `docs/application-preview.md`, 기능 흐름 설명은 `docs/feature-guide.md`, 설치/LLM/RAG 운영 기준은 `docs/setup-and-operations.md`로 이동했습니다.
- Important files: `README.md`, `docs/application-preview.md`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: markdown/link sanity checks and `git diff --check` passed.

### README feature screenshot coverage refresh

- Refreshed README feature screenshots for Project, Git Sync, Sample Data, and RAG Search so they show realistic sample project state, execution results, generated data previews, and RAG retrieval results.
- Added sequential validation screenshots for Developer Upload and Development Plan Upload, and added a Project Chat screenshot showing a question, answer, and verified source evidence summary.
- Important files: `README.md`, `docs/images/features/project.png`, `docs/images/features/git-sync.png`, `docs/images/features/sample-data.png`, `docs/images/features/rag-search.png`, `docs/images/features/project-chat.png`, `docs/images/features/developer-upload-validation.png`, `docs/images/features/development-plan-upload-validation.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected refreshed screenshots; captured RAG and Project Chat in mock mode to match the stored sample vectors; `git diff --check` passed.

### Project Chat source evidence expander fix

- Fixed Project Chat source evidence rendering so evidence details no longer create nested Streamlit expanders, which caused `StreamlitAPIException` when an answer had verified sources.
- Kept the evidence summary expander and rendered individual source chunks as labeled detail blocks inside it.
- Important files: `src/ui/project_chat_page.py`, `AI_CHANGELOG.md`.
- Verification: `.venv\Scripts\python.exe -m py_compile src\ui\project_chat_page.py` passed; `git diff --check` passed.

### README screenshot guidance

- Added `AGENTS.md` guidance for README screenshots to prioritize meaningful workflow states and feature value over empty/default/pre-execution screens.
- Documented that multi-step workflows can be split into sequential screenshots with short labels when one image cannot clearly explain the flow.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Program upload and code review walkthrough screenshots

- Re-captured the README Program Upload screenshots so the example shows the sample project's current program table and the Excel upload validation result instead of an empty/default project state.
- Split the README AI Code Review example into target selection, review result summary, and review detail screenshots so the actual review output, bug finding, refactoring suggestion, and review history are visible.
- Important files: `README.md`, `docs/images/features/program-upload.png`, `docs/images/features/program-upload-validation.png`, `docs/images/features/ai-code-review.png`, `docs/images/features/ai-code-review-result.png`, `docs/images/features/ai-code-review-detail.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected the refreshed screenshots and confirmed README references the new assets; `git diff --check` passed.

### Commit Impact walkthrough screenshots

- Split the README Commit Impact example into three sequential screenshots so the flow shows commit selection, impact summary, and detailed affected program/developer analysis.
- Re-captured the selected high-impact sample commit screen and added `commit-impact-summary.png` and `commit-impact-detail.png`.
- Important files: `README.md`, `docs/images/features/commit-impact.png`, `docs/images/features/commit-impact-summary.png`, `docs/images/features/commit-impact-detail.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected all three screenshots and confirmed the README references the new assets; `git diff --check` passed.

### Commit Impact README screenshot refresh

- Refreshed the README Commit Impact screenshot so it shows the selected high-impact sample commit, impact metrics, affected program analysis, and affected developer analysis instead of only the commit selection area.
- Kept README text unchanged; only the screenshot asset was updated.
- Important files: `docs/images/features/commit-impact.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected the refreshed screenshot and confirmed it shows `HIGH` impact with affected program/developer analysis; `git diff --check` passed.

### Agent commit boundary guidance

- Added `AGENTS.md` guidance to keep materially different work types in separate commits when practical.
- Clarified that real code bugs found during verification or documentation work should be committed separately from screenshots, docs, or bookkeeping refreshes when practical.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### 샘플 프로젝트 검증과 화면 캡처 갱신

- 앱 DB에 검증 전용 프로젝트 `AAA Sample Shop Rich Demo`를 구성하고 `C:\dev\ai-advisor-sample-shop`의 8개 프로그램/30개 커밋 샘플 repo와 `advisor_uploads` Excel 3종을 반영했습니다.
- mock LLM/embedding 기반으로 Git Sync, 프로그램/개발계획 적재, Mapping fallback, Risk Analysis, AI Progress, Commit Impact, RAG source indexing, Project Chat, AI Code Review 흐름을 검증했습니다.
- 검증 중 Spring MVC 샘플의 현재 소스 근거가 Project Chat에 잡히도록 RAG source_file 인덱싱 대상에 `.java`, `.jsp`를 추가하고 focused test를 보강했습니다.
- `docs/ai-technical-overview.md`에 current source indexing이 Java/JSP 등 샘플 프로젝트의 주요 텍스트/코드 파일을 포함한다는 설명을 추가했습니다.
- `docs/rich-sample-demo-walkthrough.md`와 `README.md`에 검증 전용 프로젝트명, mock 모드 Mapping 검증 주의점, Java/JSP source indexing 확인 기준을 보강했습니다.
- README 대표 이미지와 기능별 화면 캡처 전체를 새 샘플 데이터 기준으로 갱신했습니다.
- 검증 결과: 프로그램 8건, 커밋 30건, 관련 매핑 25건, unresolved risk 13건, source_file chunk/vector 70건, Project Chat verified source 8건, Code Review 1건 저장 확인.
- 검증: `.venv\Scripts\python.exe -m pytest tests\test_source_file_rag.py -q` 통과(`4 passed`), `.venv\Scripts\python.exe -m py_compile src\rag\chunker.py` 통과, Playwright로 README 기능별 화면 캡처 18종 갱신, `git diff --check` 통과.

### 샘플 프로젝트 검증 가이드 추가

- 8개 프로그램/30개 커밋 샘플 repo를 검증할 때 LLM/embedding 작업이 과도하게 늘어나지 않도록 `docs/rich-sample-demo-walkthrough.md`를 추가했습니다.
- 가이드에는 commit-based Mapping 우선 사용, 선택 커밋 1개 선검증, 후보 수 제한, RAG/Project Chat embedding 소량 실행, 추천 Code Review 대상 커밋, 예상 Risk Analysis 신호를 정리했습니다.
- `README.md`의 샘플 데이터 생성 섹션에서 전체 데모 검증이나 화면 캡처 갱신 전 해당 가이드를 먼저 확인하도록 안내했습니다.
- `ROADMAP.md`의 `Rich sample demo walkthrough and screenshots` 체크리스트에 권장 실행 흐름 문서화 항목을 추가했습니다.
- 검증: 문서 변경 범위 확인 및 `git diff --check` 통과.

### 샘플 프로젝트 검증과 스크린샷 작업 로드맵 등록

- 확장된 8개 프로그램/30개 커밋 샘플 데이터가 실제 앱 화면에서 잘 동작하는지 검증하고 README walkthrough 및 기능별 스크린샷을 맞추는 작업을 `ROADMAP.md`에 추가했습니다.
- Docker/deployment 작업보다 샘플 프로젝트 검증과 문서/스크린샷 정합성 작업을 먼저 볼 수 있도록 `P2 | Docs | Rich sample demo walkthrough and screenshots`를 `Planned`로 등록했습니다.
- 검증: 문서 변경 범위 확인 및 `git diff --check` 통과.

### README Home 화면 캡처 갱신

- README 대표 Home 이미지와 기능별 Home 캡처를 현재 Home 화면 문구 기준으로 갱신했습니다.
- 갱신한 이미지: `docs/images/ai-commit-advisor-home.png`, `docs/images/features/home.png`.
- 검증: 실행 중인 Streamlit 앱(`http://localhost:8501`) 기준으로 `.venv\Scripts\python.exe scripts\verify_home_ui.py --screenshot docs\images\features\home.png` 통과, 대표 이미지는 동일 캡처로 동기화, 이미지 육안 확인 통과.

### 확장 샘플 대상 repo 구현

- `scripts/create_sample_target_repo.py`의 샘플 대상 repo 생성 흐름을 확장해 8개 프로그램, 30개 Git commit, 6명의 가상 개발자 author를 생성하도록 했습니다.
- 주문, 재고, 결제, 매출, 대시보드, 쿠폰, 정산 계획 프로그램을 포함하고, 기능 추가/버그 유발/버그 수정/테스트 보강/리팩터링/문서 변경/교차 모듈 영향/미완료 기능 시나리오를 커밋 히스토리에 반영했습니다.
- Risk Analysis 데모를 위해 쿠폰 프로그램은 지연 80% 진행, 정산 내보내기 프로그램은 담당자 없음/지연/관련 커밋 없음 상태가 되도록 개발계획 override를 추가했습니다.
- AI Code Review 데모용 결제 0원 승인 위험 커밋과 대시보드 집계 over-count 위험 커밋, RAG/Project Chat용 업무 규칙 문서와 데모 가이드를 추가했습니다.
- `sample_data` Excel 3종을 새 샘플 repo 출력 기준으로 갱신했습니다.
- `README.md`와 `docs/sample-target-repo-demo-design.md`를 8개 프로그램/30개 커밋 기준으로 업데이트하고, 전체 데모에는 `advisor_uploads` Excel을 사용해야 리스크 계획 override가 포함된다는 안내를 추가했습니다.
- focused tests를 추가해 샘플 커밋 수, 리스크 데모 프로그램, 계획 override를 검증하도록 했습니다.
- 검증: `.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\generate_sample_development_data.py scripts\create_sample_target_repo.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`64 passed`), `git diff --check` 통과.

### 샘플 대상 repo 데모 시나리오 설계 문서 추가

- AI Commit Advisor의 전체 기능을 소개할 수 있도록 샘플 대상 repo의 목표 규모, 커밋 시나리오, 기능별 데모 신호를 정리한 `docs/sample-target-repo-demo-design.md`를 추가했습니다.
- 현재 샘플 repo의 장점과 한계를 정리하고, 권장 커밋 수를 25~40개, 우선 목표를 약 30개로 정의했습니다.
- Git Sync, Mapping, Program Detail, Commit Impact, Risk Analysis, RAG, Project Chat, AI Code Review, AI Progress별로 샘플 데이터가 보여줘야 할 조건을 문서화했습니다.
- `AGENTS.md`에 샘플 대상 repo, 샘플 커밋 히스토리, 샘플 데이터 생성, 데모 시나리오를 바꿀 때 설계 문서를 먼저 확인하라는 규칙을 추가했습니다.
- `AGENTS.md`에 커밋/푸시 전 변경 성격별로 관련 Markdown 문서 갱신 필요성을 확인하는 pre-commit documentation check를 추가했습니다.
- `ROADMAP.md`에 `Rich demo target repository scenario design` 작업을 등록했습니다.
- `README.md`의 샘플 데이터 생성 섹션에 현재 샘플 repo가 기본 기능 확인용 최소 데이터셋이며, 확장 시 설계 문서를 기준으로 한다는 안내를 추가했습니다.
- 검증: 문서 변경 범위 확인 및 `git diff --check` 통과.

### 가상 샘플 대상 프로젝트 생성 스크립트 추가

- AI Commit Advisor 앱 repo와 분리된 sibling Git repo `C:\dev\ai-advisor-sample-shop`를 생성하는 `scripts/create_sample_target_repo.py`를 추가했습니다.
- 생성 repo에는 Spring MVC Controller, Service, MyBatis Mapper interface/XML, JSP 화면으로 구성한 주문, 재고, 결제, 매출, 대시보드 예제 소스와 9개 Git commit, 6명의 한국인 가상 개발자 author, `샘플_프로그램목록.csv`, 업로드용 Excel 3종이 포함됩니다.
- 개발자 산출물의 role/skills는 업무 단위 개발 방식에 맞게 `PM`, `PL`, `개발자`, `QA`로 고정 프로필을 적용합니다.
- 샘플 데이터 생성기가 Spring/MyBatis 경로와 Python식 `controllers/services/repositories` 경로를 모두 더 자연스럽게 분류하도록 보완하고 focused tests를 추가했습니다.
- `샘플 데이터 생성` 화면의 기본 Git 경로를 `C:\dev\ai-advisor-sample-shop`로 바꾸고, README에 샘플 repo 생성/재생성/업로드 사용법을 추가했습니다.
- 검증: `.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\generate_sample_development_data.py scripts\create_sample_target_repo.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`61 passed`).

### Sidebar 메뉴 위치 흔들림 보정

- Sidebar 메뉴에서 선택 항목과 일반 버튼의 높이, margin, box sizing, 왼쪽 border 폭을 동일하게 맞춰 페이지 전환 시 메뉴 위치가 흔들리지 않도록 했습니다.
- 일반 메뉴 버튼에도 투명한 왼쪽 border를 적용해 선택 상태의 파란 border와 같은 공간을 항상 확보하도록 했습니다.
- `scripts/verify_home_ui.py`에 메뉴 클릭 전후 `Mapping` 항목의 위치와 폭이 안정적인지 확인하는 Playwright 검증을 추가했습니다.
- 검증: `.venv\Scripts\python.exe scripts\verify_home_ui.py` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\verify_home_ui.py` 통과.

### Home UI 검증 스크립트 추가

- Node Playwright가 없는 환경에서도 Home 화면을 검증할 수 있도록 Python Playwright 기반 `scripts/verify_home_ui.py`를 추가했습니다.
- 검증 스크립트는 Home의 짧아진 핵심 문구가 표시되는지, 제거한 설명투 문구가 남아 있지 않은지 확인하고 `.tmp/home-ui-check.png` 캡처를 생성합니다.
- `requirements.txt`에 `playwright==1.60.0`을 명시하고, `.tmp/`를 git 추적에서 제외했습니다.
- `README.md`의 로컬 검증 명령에 Home UI 검증 절차를 추가했습니다.
- 검증: `.venv\Scripts\python.exe scripts\verify_home_ui.py` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\verify_home_ui.py` 통과.

### Home 문구 톤 정리

- Home 상단 설명을 짧은 상태 요약 문구로 줄였습니다.
- 분석 파이프라인 표의 긴 설명 컬럼을 간결한 `메모` 컬럼으로 바꾸고, 항목명을 짧게 정리했습니다.
- 다음 권장 작업 문장을 실행 항목 중심의 짧은 문구로 바꿨습니다.
- `src/ui/home_page.py`, `ROADMAP.md`를 수정했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과.

### README 화면 캡처 갱신

- `README.md`의 기능별 화면 캡처 안내 문구를 현재 그룹형 사이드바 메뉴 기준으로 정리했습니다.
- Home 대표 이미지와 기능별 화면 캡처 전체를 현재 UI 기준으로 갱신했습니다.
- 갱신한 이미지: `docs/images/ai-commit-advisor-home.png`, `docs/images/features/*.png`.
- 검증: Streamlit 앱을 `http://localhost:8501`에서 실행해 응답 `200`을 확인하고, Playwright Chromium으로 README 참조 화면 전체를 캡처했습니다. 문서와 이미지 변경만 수행해 pytest는 생략했습니다.

## 2026-06-08

### Sidebar 메뉴 UX 개선

- 사이드바의 2단 `radio` 메뉴를 제거하고, 업무 영역별 그룹 제목과 메뉴 버튼을 사용하는 내비게이션으로 변경했습니다.
- 현재 선택된 화면은 좌측 강조선과 배경으로 표시하고, 현재 위치를 사이드바 상단에 별도로 노출했습니다.
- 기존 페이지 그룹과 화면 렌더러는 유지해 메뉴 구조와 분석 기능 동작은 바꾸지 않았습니다.
- `README.md`와 `ROADMAP.md`에 사이드바 메뉴 UX 개선 내용을 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`53 passed`).

### LLM/Embedding 배치 안전장치와 예상시간 표시

- RAG embedding 실행 전에 남은 chunk 수, 이번 실행 최대 처리 수, 예상 소요 시간을 표시하도록 했습니다.
- source_file 재인덱싱 후 embedding을 함께 생성하는 경우에도 예상 소요 시간을 표시하도록 했습니다.
- 로컬 LM Studio/embedding 서버 과부하를 줄이기 위해 RAG embedding 기본 배치 수를 500건에서 50건으로 낮췄습니다.
- 예상시간 계산 helper와 focused tests를 추가했습니다.
- `README.md`, `docs/ai-technical-overview.md`, `ROADMAP.md`에 로컬 LLM/embedding 제한 실행 운영 방식을 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`53 passed`).

### Home 분석 관제 화면 개선

- Home 상단 설명을 개발계획, Git 변경 이력, AI 매핑 결과, 리스크를 통합해 보는 업무용 분석 콘솔 관점으로 정리했습니다.
- 프로젝트 등록, 프로그램 수, 개발자 수, Git 커밋 수집, 매핑 분석 완료 커밋, 구현상태 분석 결과, 미해결 리스크를 보여주는 분석 파이프라인 상태 섹션을 추가했습니다.
- 현재 데이터 상태에 따라 프로젝트 등록, 프로그램 등록, Git 동기화, Mapping 실행, 구현상태 분석, Risk Analysis 실행 같은 다음 권장 작업을 안내하도록 했습니다.
- 기존 전체 KPI, 상태별 프로그램 수, 계획 vs AI 진척도, 상위 리스크 프로그램 차트는 유지했습니다.
- `README.md`와 `ROADMAP.md`에 Home 분석 관제 화면 설명을 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`50 passed`).

### CI 테스트 워크플로우 추가

- GitHub Actions `CI` workflow를 추가해 push와 pull_request에서 Python 3.11 환경으로 기본 검증을 실행하도록 했습니다.
- CI 단계는 checkout, setup-python, `pip install -r requirements.txt`, `python -m compileall src app.py`, `python -m pytest -q` 순서로 구성했습니다.
- `README.md`에 CI와 동일한 로컬 검증 명령을 정리했습니다.
- `ROADMAP.md`의 P2 CI Test Workflow 상태와 체크리스트를 갱신했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`50 passed`).

### Project Chat 답변 품질과 근거 부족 처리 개선

- Project Chat에서 검증된 `source_file` 근거가 없으면 "현재 검증된 소스 근거만으로는 답변하기 어렵습니다", "추가 인덱싱 또는 검색어 조정이 필요합니다"를 반환하고 추측성 LLM 답변을 생성하지 않도록 했습니다.
- LLM 프롬프트를 보수적으로 정리해 검증된 현재 소스 근거에 없는 내용을 현재 코드 사실처럼 말하지 않고, commit/commit_file 근거는 과거 변경 이력으로만 다루도록 했습니다.
- 답변별 근거 표시를 현재 소스 근거와 이력/참고 근거로 분리하고, 파일 경로, line range, verification status, source type, 사용 근거 수를 확인할 수 있게 했습니다.
- stale/invalid `source_file` 제외, 근거 부족 응답, verified citation metadata 유지 focused tests를 추가했습니다.
- `ROADMAP.md`에서 Project Chat 품질 개선 완료 항목만 체크하고 chat history persistence는 미완료로 유지했습니다.
- `README.md`에 Project Chat의 근거 부족 안내 동작을 반영했습니다.
- `docs/ai-technical-overview.md`에 근거 부족 처리와 현재 소스/이력 근거 분리 설명을 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`50 passed`).

### source_file 인덱스 상태 표시 세부 보완

- RAG와 Project Chat의 source_file 인덱스 상태에 현재 HEAD와 다른 indexed HEAD chunk 수를 별도 표시했습니다.
- RAG 화면에서 source_file chunk에 저장된 indexed HEAD 종류를 확인할 수 있게 했습니다.
- 경고 문구를 "현재 Git HEAD와 인덱싱 시점이 다를 수 있습니다", "최신 코드 기준 답변을 위해 source_file 재인덱싱을 권장합니다"처럼 업무 사용자가 이해하기 쉬운 문장으로 정리했습니다.
- indexed HEAD mismatch count와 metadata 부족 invalid 처리 focused tests를 추가했습니다.
- `docs/ai-technical-overview.md`에 source index status 표시 항목을 최신 UI 기준으로 보강했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`46 passed`).

### Mapping 피드백 리뷰 큐 문서 정리

- `docs/architecture.md`에 `mapping_feedback_service.py` 역할, Mapping 피드백 리뷰 큐 흐름, 주요 서비스 목록을 최신 구현에 맞게 추가했습니다.
- `docs/ai-technical-overview.md`의 traceability 설명에 매핑 리뷰 큐가 피드백 미완료, 판단불가, 낮은 관련도, 비관련 판정, 근거 부족 후보를 우선 검토하도록 돕는다는 내용을 추가했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### Mapping 피드백 리뷰 큐와 품질 지표 추가

- Mapping 화면의 `매핑 피드백` 모드에 전체/피드백 완료/미완료/리뷰 필요/판단불가/낮은 관련도 KPI를 추가했습니다.
- 피드백 미완료, 판단불가, 낮은 관련도, 비관련 판정, 근거 부족 등 검토가 필요한 매핑을 찾는 리뷰 큐를 추가했습니다.
- 리뷰 큐 필터와 프로그램명, program_id, commit message, commit hash 기반 검색을 추가했습니다.
- 리뷰 큐에서 선택한 매핑을 기존 피드백 보정 form으로 바로 수정할 수 있게 했습니다.
- `mapping_feedback_service.py`에 리뷰 큐 조회와 품질 집계 helper를 추가하고 focused tests를 보강했습니다.
- `README.md`의 Mapping 설명에 매핑 피드백 리뷰 큐를 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`43 passed`).

### AI Progress 문서 설명 정리

- `README.md` 주요 기능 목록에 AI Progress가 계획 진척도, 매핑 기반 AI 진척도, 저장된 프로그램 단위 구현상태 분석 요약을 함께 비교한다는 설명을 추가했습니다.
- `docs/architecture.md`의 AI Progress 화면 역할, 처리 흐름, AI 진척도 계산 규칙, 주요 UI/서비스 설명을 최신 구현에 맞게 정리했습니다.
- 저장된 `program_implementation_status` 결과는 업무 검토용 요약 근거이며 AI 진척도/진척도 차이/리스크 조건 계산을 대체하지 않는다는 점을 문서에 명시했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### AI Progress 구현상태 분석 결과 표시

- AI Progress summary row에 저장된 프로그램 단위 구현상태 분석 상태, 업무용 라벨, 요약, 분석 일시, 근거 커밋 수를 포함했습니다.
- 프로그램별 비교 테이블에 `구현상태 분석`, `구현상태 요약`, `분석 일시`, `근거 커밋 수` 컬럼을 추가했습니다.
- 선택한 프로그램 상세 영역에 구현상태 분석 요약을 표시하고, 저장 결과가 없으면 `구현상태 분석 결과 없음`으로 안내하도록 했습니다.
- AI 진척도는 매핑 결과의 구현상태를 수치화한 값이고, 구현상태 분석은 프로그램 단위 요약 결과라는 안내 문구를 추가했습니다.
- 기존 AI 진척도, progress gap, risk reason 계산 방식은 변경하지 않았습니다.
- `README.md`, `docs/ai-technical-overview.md`에 AI Progress의 두 지표 구분 설명을 최소 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`39 passed`).

### README 구현상태 분석 보수화 설명 정리

- `README.md`의 프로그램 단위 구현상태 분석 섹션에 커밋 수만으로 완료 판단을 하지 않는다는 원칙을 추가했습니다.
- `COMPLETED` 선택 기준, 테스트/예외처리/화면 연결/배포/운영 검증의 한계, `incomplete_features`에 검증 필요 사항을 남기는 방식을 정리했습니다.
- LLM 응답 실패 또는 JSON 파싱 실패 시 fallback이 완료 단정보다 담당자 검증이 필요한 추정 결과를 우선한다는 설명을 보강했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### 구현상태 분석 프롬프트와 fallback 보수화

- `ProgramImplementationAnalyzer`의 LLM 프롬프트를 한국어 중심으로 정리하고, 프로그램 계획/설명/관련 커밋/변경 파일/기존 매핑 근거를 사용하되 커밋 수만으로 판단하지 않도록 명시했습니다.
- 커밋만으로 테스트 완료, 예외처리, 화면 연결, 배포/운영 검증 완료를 확정할 수 없으며 불확실성은 `incomplete_features`에 남기도록 프롬프트를 보강했습니다.
- fallback 결과 문구를 한국어로 바꾸고, 완료 신호가 있어도 fallback에서는 담당자 검증이 필요한 `IN_PROGRESS`로 보수적으로 처리하도록 조정했습니다.
- 잘못된 status 값, 입력에 없는 evidence commit hash, mapping 없는 경우, 한국어 fallback 문구를 확인하는 focused tests를 추가했습니다.
- `docs/ai-technical-overview.md`에 구현상태 분석이 보수적 추정이며 업무 검증이 필요하다는 설명을 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`36 passed`).

### README Program Detail 설명 정리

- `README.md`의 Program Detail 설명에서 저장된 분석 결과 조회와 `구현상태 재분석` 버튼의 동작을 구분해 정리했습니다.
- 프로그램 단위 구현상태 분석의 내부 상태값과 화면 표시 라벨을 표로 정리했습니다.
- 구현상태 결과 카드에서 확인할 수 있는 항목과 담당자 확인 필요 안내를 README에 더 명확히 반영했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### Program Detail 구현상태 분석 결과 표시 개선

- Program Detail의 저장된 프로그램 단위 구현상태 분석 결과를 업무 담당자가 이해하기 쉬운 한글 추정 라벨로 표시했습니다.
- 분석 결과 영역에 AI 분석 근거와 담당자 확인 필요성을 안내하는 문구를 추가했습니다.
- 구현상태, 분석 일시, 근거 커밋 수, 상태 요약, 완료/미완료 추정 기능, 주요 근거 커밋을 카드 형태로 정리했습니다.
- evidence_commits가 없거나 예상하지 못한 형태여도 화면이 깨지지 않도록 표시 전용 정규화 helper를 추가했습니다.
- 구현상태 재분석 실패 시 Program Detail 전체 화면이 죽지 않고 오류를 표시한 뒤 기존 저장 결과를 계속 보여주도록 예외 처리를 보강했습니다.
- `README.md`의 Program Detail/구현상태 분석 설명을 실제 화면 표현에 맞게 최소 수정했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`31 passed`).

### source_file 재인덱싱 운영 기록 README 보강

- `README.md`에 source_file 재인덱싱과 embedding 생성을 분리해서 운영해야 하는 이유를 정리했습니다.
- LM Studio/local embedding 서버가 대량 chunk 처리 중 PC 자원을 오래 점유할 수 있으므로, embedding은 제한 수량으로 나눠 실행하도록 안내했습니다.
- 재인덱싱 또는 embedding 중 강제 종료되었을 때 PostgreSQL transaction rollback, 부분 완료 상태(`pending`, `failed`)의 의미, `orphan_vectors` 확인 방법을 문서화했습니다.
- 실제 점검에 사용한 `pg_isready`, source_file chunk/vector count, embedding_status 확인 SQL 예시를 README에 추가했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### source_file 재인덱싱 안전장치 보완

- `현재 소스 다시 인덱싱`이 기본으로 LM Studio/local embedding 서버를 대량 호출하지 않도록 변경했습니다.
- Project Chat의 재인덱싱은 chunk만 갱신하고, embedding 생성은 RAG 화면의 별도 선택 또는 Embedding 탭에서 제한 수량으로 실행하도록 분리했습니다.
- source_file refresh가 기존 chunk/vector를 먼저 전체 삭제하지 않고, 현재 HEAD 기준 chunk 생성 후 검증 불가 chunk/vector만 정리하도록 바꿨습니다.
- 갑작스러운 종료 시 기존 인덱스가 먼저 비워지는 위험을 줄이고, 삭제된 파일 근거는 성공적인 chunk 갱신 이후 제거하도록 했습니다.
- `README.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`의 재인덱싱 설명을 안전한 동작 기준으로 수정했습니다.
- 검증: `.venv\Scripts\python.exe -m pytest -q` 통과(`31 passed`), `.venv\Scripts\python.exe -m compileall app.py src` 통과.

### source_file 인덱스 상태 확인과 원클릭 재인덱싱

- RAG와 Project Chat 화면에 Current HEAD, Indexed HEAD, source_file chunk/vector 수, 현재 코드와 불일치/검증 불가 chunk 수를 표시했습니다.
- `src/rag/source_index_service.py`를 추가해 source_file 인덱스 상태 계산과 현재 HEAD 기준 재인덱싱을 공통 서비스로 분리했습니다.
- `현재 소스 다시 인덱싱` 버튼은 현재 Git HEAD 기준 source_file chunk를 갱신하고 검증되지 않는 오래된 chunk/vector를 정리합니다. embedding 자동 생성은 이후 안전장치 보완에서 기본 비활성화했습니다.
- 삭제된 파일이나 수정된 라인의 오래된 근거가 Project Chat 답변에 남지 않도록 재인덱싱 경로를 추가했습니다.
- `README.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`에 소스 인덱스 상태 확인과 재인덱싱 흐름을 반영했습니다.
- source_file 인덱스 refresh 필요 판단 테스트를 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m pytest -q` 통과(`31 passed`), `.venv\Scripts\python.exe -m compileall app.py src` 통과.

### AI 기술 개요 문서 추가

- `docs/ai-technical-overview.md`를 추가해 대외 소개용 AI 활용 흐름, 기능별 AI 사용 방식, RAG/Project Chat 안전장치, traceability, 현재 한계를 정리했습니다.
- `AGENTS.md`에는 AI-facing 동작 변경 시 `docs/ai-technical-overview.md`를 갱신하라는 운영 규칙만 남기고, RAG evidence 상세 용어는 기술 개요 문서로 분리했습니다.
- `README.md` 초반에 AI/LLM 활용 흐름 표와 AI 기술 개요 문서 링크를 추가했습니다.
- 공개 README에서는 `stale` 같은 내부 상태명 대신 현재 파일 일치 여부 검증이라는 표현으로 정리했습니다.

### 개발계획 관리 UX 개선

- 개발계획 업로드 화면을 `현재 계획`, `직접 수정`, `Excel 업로드`, `일괄 업데이트`, `양식` 탭 구조의 개발계획 관리 화면으로 바꿨습니다.
- 개발계획 Excel 양식 다운로드와 필수/선택 컬럼 안내를 추가했습니다.
- 업로드 파일을 저장하기 전에 미리보기, 검증 결과, 수정/오류 요약을 표시하도록 했습니다.
- 프로그램별 개발계획을 직접 수정하고, 선택한 프로그램들의 status/progress_rate를 일괄 업데이트할 수 있게 했습니다.
- 개발계획 관리 서비스와 focused tests를 추가했습니다.
- `ROADMAP.md`의 `Development plan management UX improvement` 작업을 `Done`으로 변경했습니다.

### 개발자 관리 UX 개선

- 개발자 목록 업로드 화면을 `현재 데이터`, `직접 추가`, `Excel 업로드`, `양식` 탭 구조의 개발자 관리 화면으로 바꿨습니다.
- 개발자 Excel 양식 다운로드와 필수/선택 컬럼 안내를 추가했습니다.
- 업로드 파일을 저장하기 전에 미리보기, 검증 결과, 신규/수정/오류 요약을 표시하도록 했습니다.
- 개발자를 직접 추가/수정/삭제할 수 있게 했고, 삭제 전 담당 프로그램 연결 해제 영향을 표시하도록 했습니다.
- 개발자 관리 서비스와 focused tests를 추가했습니다.
- `ROADMAP.md`의 `Developer management UX improvement` 작업을 `Done`으로 변경했습니다.

### 프로그램 관리 UX 2차 개선

- 프로그램 관리 화면에 `직접 추가` 탭을 추가해 Excel 없이 프로그램을 등록할 수 있게 했습니다.
- `현재 데이터` 탭에서 프로그램을 선택해 수정할 수 있게 했습니다.
- 프로그램 삭제 전 연결된 매핑, 리스크, 구현상태 분석 건수를 표시하고 확인 후 삭제하도록 했습니다.
- 프로그램 수동 관리 서비스와 입력 검증 테스트를 추가했습니다.
- `ROADMAP.md`의 `Program management UX improvement` 작업을 `Done`으로 변경했습니다.

### 프로그램 관리 UX 1차 개선

- `ROADMAP.md`의 `Program management UX improvement`를 `In Progress`로 전환하고 1차 완료 항목을 체크했습니다.
- 프로그램 관리 화면을 `현재 데이터`, `Excel 업로드`, `양식` 탭 구조로 바꿨습니다.
- 프로그램 Excel 양식 다운로드와 필수/선택 컬럼 안내를 추가했습니다.
- 업로드 파일을 저장하기 전에 컬럼 매핑, 미리보기, 검증 결과, 신규/수정/오류 요약을 표시하도록 했습니다.
- 필수값, 중복 `program_id`, 날짜 형식/순서, `progress_rate` 범위 검증을 추가했습니다.
- 오류가 있는 행은 저장에서 제외하고 검증 통과 행만 저장하도록 했습니다.
- 프로그램 import 검증 서비스와 focused tests를 추가했습니다.

### 로드맵 관리 문서 추가

- `ROADMAP.md`를 추가해 우선순위, 작업 상태, 체크리스트, 관련 AI 변경 로그, 커밋 해시를 추적하도록 했습니다.
- 데이터 관리 UX 개선을 P0 작업으로 등록했습니다.
- Project Chat/RAG/Mapping/운영 개선 후보를 P1/P2 작업으로 정리했습니다.
- `AGENTS.md`에 로드맵 확인, 상태 변경, 체크리스트 갱신, 완료 시 로그/커밋 연결 규칙을 추가했습니다.

### Project Chat 전용 메뉴 추가

- `Project Chat` 화면을 추가해 ChatGPT처럼 프로젝트에 대해 대화형으로 질문할 수 있게 했습니다.
- 기존 검증형 RAG chat 서비스를 재사용해 기본 답변 근거를 현재 파일 검증을 통과한 `source_file` chunk로 제한했습니다.
- 프로젝트별 대화 히스토리를 Streamlit session state에 유지하고, 답변별 검색 근거와 검증 상태를 확인할 수 있게 했습니다.
- 사이드바 `AI 분석` 그룹에 `Project Chat` 메뉴를 추가했습니다.

### README 문서 업데이트

- `README.md`에 Project Chat, 검증형 source_file RAG, Alembic migration, RAG metadata 설명을 반영했습니다.
- `docs/architecture.md`의 아키텍처 다이어그램, RAG 흐름, 기능 목록, 제한사항, 주요 UI/서비스 목록을 최신 구현에 맞게 수정했습니다.

### 현재 소스 검증형 RAG 검색 챗 추가

- RAG 인덱싱 대상에 `source_file`을 추가해 현재 Git HEAD 기준 실제 소스 파일 내용을 chunk로 저장하도록 했습니다.
- `source_file` metadata에 `file_path`, `line_start`, `line_end`, `content_hash`, `chunk_content_hash`, `indexed_head_hash`, `source_snapshot`을 저장하도록 했습니다.
- 검색 결과가 현재 파일의 같은 라인 범위와 hash를 유지하는지 확인하는 source verification 서비스를 추가했습니다.
- RAG Search 화면에 `source_file` source type과 검증 상태(`verified`, `stale`, `invalid`, `historical`) 표시를 추가했습니다.
- 검증된 현재 소스 chunk만 기본 근거로 사용하는 `Chat` 탭을 추가했습니다.
- 삭제되었거나 변경된 라인을 현재 코드처럼 답변하지 않도록 stale/invalid chunk를 답변 근거에서 제외했습니다.
- source file chunking과 verification 테스트를 추가했습니다.

### Alembic DB 마이그레이션 도입

- `alembic.ini`, `migrations/env.py`, migration template을 추가했습니다.
- 현재 애플리케이션 스키마를 baseline migration으로 분리했습니다.
- 매핑 피드백 컬럼 추가를 별도 migration으로 분리했습니다.
- `src/db/init_db.py`의 누적 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 목록을 제거하고 Alembic 실행 흐름으로 바꿨습니다.
- 기존 DB에 `alembic_version`이 없으면 현재 스키마를 baseline으로 stamp한 뒤 이후 migration을 적용하도록 했습니다.
- DB migration 사용법을 `docs/db-migrations.md`에 정리했습니다.

### 에이전트 작업 지침 추가

- 루트에 `AGENTS.md`를 추가해 코딩 에이전트가 의미 있는 변경 후 `AI_CHANGELOG.md`를 업데이트하도록 명시했습니다.
- DB 스키마 변경은 Alembic migration으로만 관리하고 `src/db/init_db.py`에 수동 `ALTER TABLE` 목록을 추가하지 않도록 명시했습니다.
- `README.md` 초반에 `AI_CHANGELOG.md`와 `AGENTS.md` 안내를 추가했습니다.

### 매핑 피드백 기능 추가

- `program_commit_mappings`에 사용자 피드백 컬럼을 추가했습니다.
- 매핑 화면에 `매핑 피드백` 모드를 추가했습니다.
- 사용자가 AI 매핑 결과의 관련 여부, 관련도 점수, 구현상태, 판단 근거를 보정할 수 있게 했습니다.
- 보정된 매핑값이 `Commit Impact`, `Program Detail`, `AI Progress`, `Risk Analysis`에서 사용되도록 관련 서비스 로직을 조정했습니다.

### 테스트 추가

- `pytest`를 개발 의존성에 추가했습니다.
- 매핑 후보 점수, LLM JSON 파싱, Git diff path 파싱, 상태 정규화, 피드백 상태 정규화 테스트를 추가했습니다.

### 검증

- `python -m py_compile app.py src\db\models.py src\db\init_db.py src\services\mapping_feedback_service.py src\services\commit_impact_service.py src\services\progress_service.py src\services\risk_service.py src\services\program_analysis_service.py src\ui\mapping_page.py` 통과.
- `.venv\Scripts\python.exe -m pytest -q` 통과.
- 테스트 결과: `7 passed`.

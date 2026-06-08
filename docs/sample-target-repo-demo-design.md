# Sample Target Repository Demo Design

## Purpose

The synthetic sample target repository exists to demonstrate AI Commit Advisor without using real customer or product code. It should be realistic enough for Git sync, program mapping, risk analysis, RAG, Project Chat, AI Code Review, and AI Progress to produce useful results.

The sample target repository is intentionally separate from this application repository.

- Application repository: `C:\dev\ai-commit-advisor`
- Sample target repository: `C:\dev\ai-advisor-sample-shop`
- Generator script: `scripts/create_sample_target_repo.py`
- Generated upload files: `C:\dev\ai-advisor-sample-shop\advisor_uploads`

## Current State

The current sample target is a synthetic Spring MVC + MyBatis retail operations project.

- Programs: 8
- Developers: 6
- Git commits: 30
- Main stack: Java, Spring MVC, JSP, MyBatis XML
- Current domains: orders, inventory, payments, reports, dashboard, coupon, settlement planning
- Generated files: program CSV and upload Excel files for developers, programs, and development plans

Strengths:

- The target repository is already isolated as a sibling Git repository.
- It has enough structure for Git sync, developer extraction, program upload, development plan upload, Mapping, RAG, Project Chat, Risk Analysis, AI Code Review, Commit Impact, and AI Progress checks.
- Package paths and program modules are clear, which helps candidate selection for program-commit mapping.
- The generated Excel files are aligned with the fake repository history.
- The history includes feature additions, bug-introducing changes, bug fixes, tests, refactoring, documentation, cross-module changes, and incomplete work.

Known limits:

- The sample is optimized for analysis value rather than successful Maven build execution.
- The code is synthetic and should not be treated as production implementation guidance.
- Some risk scenarios are created through generated development-plan overrides so Risk Analysis can demonstrate delayed, unassigned, and no-related-commit cases.

## Target Demo Scale

Recommended target size:

- Programs: 6 to 8
- Developers: 6 to 7
- Commits: 25 to 40
- Preferred working target: about 30 commits

Rationale:

- Fewer than 15 commits is useful for smoke testing but too small for a convincing demo.
- Around 30 commits gives each major program several implementation, fix, test, and documentation events.
- More than 70 commits can make local LLM and embedding demos slower without adding much presentation value.

## Product Features To Demonstrate

The sample should deliberately support these product workflows.

| Product feature | Sample data requirement | Demo signal |
|---|---|---|
| Git Sync | 25 to 40 commits with varied authors and dates | Commit table, changed files, diffs, author extraction |
| Developer management | PM, PL, developers, QA, optional operations role | Auto extraction plus meaningful roles and skills |
| Program upload | 6 to 8 business programs with modules, screens, and descriptions | Program table and mapping candidates |
| Development plan upload | Mixed complete, in-progress, delayed, and unassigned rows | AI Progress and Risk Analysis differences |
| Mapping | Program-specific and cross-module commits | Related program mappings with different relevance scores |
| Program Detail | Multiple commits per program and more than one contributor on some programs | Commit history, contribution split, evidence details |
| Commit Impact | Commits touching order, inventory, payment, and dashboard together | One commit affects multiple programs |
| Risk Analysis | No related commits, overdue incomplete work, progress gaps, no recent commits, missing assignee | Multiple risk types visible in one run |
| RAG Search | Current source, docs, commit messages, and diffs with searchable business terms | Source and history retrieval results |
| Project Chat | Current source and docs that answer realistic business questions | Answers with file and line evidence |
| AI Code Review | A latest or selected commit with concrete bug risk and refactoring opportunities | Bug findings and actionable suggestions |
| AI Progress | Mix of completed, in-progress, not-started, and uncertain programs | Plan progress versus AI-estimated implementation status |

## Commit Scenario Design

The expanded history should be intentionally designed. Each commit should have a reason to exist in the demo.

| Order | Scenario | Example commit message | Related programs | Demonstrates |
|---|---|---|---|---|
| 1 | Initial project setup | Initialize Spring MyBatis market operations project | All | Git Sync, RAG source indexing |
| 2 | Requirements baseline | Add program baseline and interface policy | All | RAG, Project Chat, planning context |
| 3 | Order skeleton | Add order creation controller and mapper | Order creation | Mapping, Program Detail |
| 4 | Order validation | Validate customer and cart input for order creation | Order creation | Code Review, Project Chat |
| 5 | Inventory reservation | Reserve inventory with MyBatis mapper | Inventory reservation | Mapping, database layer detection |
| 6 | Inventory shortage handling | Add shortage branch and reservation failure message | Inventory reservation, dashboard | Risk and cross-program impact |
| 7 | Payment authorization | Add payment authorization flow | Payment approval, order status | Commit Impact |
| 8 | Payment bug introduction | Relax amount validation for partner payments | Payment approval | AI Code Review high-value target |
| 9 | Payment bug fix | Reject zero and negative payment amounts | Payment approval | Bug fix history, review contrast |
| 10 | Order status history | Track order status transition history | Order status | Mapping, AI Progress |
| 11 | Invalid transition guard | Block invalid order status transitions | Order status | Project Chat, Code Review |
| 12 | Sales report query | Add sales report aggregation query | Sales report | RAG, database query search |
| 13 | Report correction | Exclude canceled payments from sales totals | Sales report, payment approval | Bug fix, cross-program impact |
| 14 | Dashboard view | Build operations dashboard JSP | Dashboard | Frontend/source search |
| 15 | Dashboard refresh endpoint | Add dashboard refresh API | Dashboard, orders, inventory, payments | Commit Impact |
| 16 | Risk indicator | Show payment waiting and inventory shortage indicators | Dashboard, inventory, payments | Program Detail |
| 17 | QA checklist | Add QA checklist for Spring MyBatis flows | All | Documentation, RAG |
| 18 | Unit tests | Add service tests for order and payment validation | Orders, payments | Test coverage signal |
| 19 | Refactoring | Extract common status constants | Orders, payments, dashboard | Refactoring review |
| 20 | Mapper cleanup | Normalize MyBatis result mappings | Orders, reports | Database review |
| 21 | Security hardening | Add basic operator role check to admin flows | Dashboard, reports | Code Review, risk discussion |
| 22 | Incomplete feature stub | Add coupon discount service skeleton | Coupon or payment | In-progress AI status |
| 23 | Unmapped program plan | Add return request program to plan without source implementation | Returns | No-related-commits risk |
| 24 | Missing assignee plan | Add settlement export plan without developer assignment | Settlement | Assignee missing risk |
| 25 | Stale activity | Leave report enhancement with old last commit | Reports | No recent commits risk |
| 26 | Ambiguous rename | Rename order status helper without behavior change | Orders | Mapping review queue |
| 27 | Documentation update | Document payment and inventory business rules | Payments, inventory | Project Chat citations |
| 28 | Latest risky change | Change dashboard summary query across modules | Dashboard, orders, inventory, payments | Best selected commit for AI Code Review |
| 29 | Latest fix | Fix dashboard summary over-counting | Dashboard, reports | Bug fix and Commit Impact |
| 30 | Final QA evidence | Add release verification checklist | All | RAG, AI Progress caveat |

The exact commit count can change during implementation, but the final history should preserve these scenario categories.

## Intentional Analysis Points

The sample should include both good and problematic changes.

- Normal feature addition commits.
- Bug-introducing commits with realistic review findings.
- Bug-fix commits that make history-based analysis meaningful.
- Refactoring commits that should not be mistaken for new feature completion.
- Test-only commits.
- Documentation-only commits.
- Cross-module commits touching multiple programs.
- Incomplete feature skeletons.
- Planned programs with no related commits.
- Plan rows with missing assignee information.
- Old related commits that trigger no-recent-commit risk.
- Ambiguous commits that can appear in Mapping review queues.

## Demo Questions

Project Chat should have current-source answers for questions like:

- How does order status move from payment waiting to paid?
- What happens when inventory is not available?
- Where is payment amount validation performed?
- Which query builds the daily sales report?
- What dashboard indicators are shown to operations users?
- Which business rules are documented for payment and inventory?

RAG Search should support terms like:

- `payment authorization`
- `inventory shortage`
- `order status history`
- `sales report canceled`
- `dashboard payment waiting`
- `operator role check`

AI Code Review should have recommended targets:

- A selected bug-introducing payment commit.
- A cross-module dashboard summary query change.
- A refactoring commit that should produce low-risk refactoring-focused feedback.

Risk Analysis should show at least these cases:

- Program has no related commits.
- Program is overdue and AI progress is incomplete.
- Plan progress is much higher than AI progress.
- Related commits exist but none are recent.
- Program assignment is missing or unclear.

AI Progress should show:

- Completed-looking programs with supporting implementation commits.
- In-progress programs with partial source evidence.
- Not-started programs with plan rows but no source commits.
- Unknown or ambiguous programs where evidence is insufficient.

## Implementation Checklist

When implementing this design:

- Update `scripts/create_sample_target_repo.py` to generate the richer commit history.
- Keep the sample target repository as a sibling repo outside `C:\dev\ai-commit-advisor`.
- Update or regenerate `sample_data` and `advisor_uploads` outputs when needed.
- Add or update tests for expected sample shape, developer profiles, program rows, and risk/demo scenarios.
- Update README sample usage instructions if the generation or recommended demo flow changes.
- Update `AI_CHANGELOG.md` with verification commands and results.

## Non-Goals

- Do not make the sample repository depend on real external services.
- Do not include real customer names, production code, secrets, or internal business data.
- Do not optimize the sample for buildability over analysis value; it should be plausible source code, but the main goal is AI Commit Advisor demonstration.

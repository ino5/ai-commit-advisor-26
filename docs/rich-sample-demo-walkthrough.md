# Rich Sample Demo Walkthrough

## Purpose

This guide explains how to verify and demonstrate AI Commit Advisor with the synthetic sample target repository without accidentally running excessive local LLM or embedding work.

Use this guide when working with:

- sample target repo: `C:\dev\ai-advisor-sample-shop`
- generator script: `scripts/create_sample_target_repo.py`
- demo upload files: `C:\dev\ai-advisor-sample-shop\advisor_uploads`

The sample repository is designed to show Git Sync, Mapping, Program Detail, Commit Impact, Risk Analysis, RAG, Project Chat, AI Code Review, and AI Progress with 8 programs and 30 commits.

## Safe Execution Rules

Follow these rules during demo verification.

- Prefer Mapping's commit-based analysis mode.
- Analyze one selected commit before running a batch.
- Keep candidate limits at the default value or lower.
- Do not start with full embedding generation if you only need to check the UI flow.
- Refresh source chunks before Project Chat/RAG checks, then generate embeddings in small batches.
- Run AI Code Review only against selected review-target commits.
- Use `LLM_PROVIDER=mock` when validating navigation, screen layout, and workflow only.
- Use a real local OpenAI-compatible LLM only when you need actual mapping/review/chat quality.

## Recommended Order

1. Recreate the sample repository when needed.

```powershell
.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force
```

2. In the app, register or update the project path.

```text
C:\dev\ai-advisor-sample-shop
```

3. Run Git sync.

Use full sync for a clean demo project. The expected sample commit count is 30.

4. Upload the generated Excel files from the sample repository.

Use these files, not freshly inferred generic output, for the full demo scenario:

```text
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_developers.xlsx
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_programs.xlsx
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_development_plan.xlsx
```

The `advisor_uploads` files include demo-specific plan overrides for delayed coupon work, missing settlement assignee, and no-related-commit risk scenarios.

5. Run Mapping safely.

- Select commit-based analysis.
- Analyze one selected commit first.
- If the result looks reasonable, run unprocessed commit batch analysis.
- Avoid program-based analysis for the first verification pass.

6. Run Risk Analysis.

Expected demo signals include:

- coupon discount work is delayed and partially implemented
- settlement export is delayed, unassigned, and has no related implementation commits
- older completed programs may show no-recent-commit signals depending on current date and mapping results

7. Check AI Progress.

Look for a mix of completed, delayed, partial, and no-evidence programs.

8. Check Commit Impact.

Recommended commits:

- `Change dashboard summary query across operations modules`
- `Fix dashboard summary over-counting`
- `Add payment authorization flow`

These commits should make cross-program impact easier to inspect.

9. Run AI Code Review on selected commits only.

Recommended review targets:

- `Relax partner payment validation for pilot channel`
- `Change dashboard summary query across operations modules`
- `Extract shared order status constants`

10. Run RAG and Project Chat with bounded embedding work.

Recommended flow:

- Refresh current source chunks first.
- Generate embeddings with a small limit.
- Search or ask a focused question.

Useful Project Chat questions:

- Where is payment amount validation performed?
- What happens when inventory is short?
- How does order status move after payment authorization?
- Which query builds the dashboard summary?
- Which sample programs are intentionally incomplete or risky?

## Screenshot Pass

When refreshing README screenshots, use the verified sample state above. The screenshots should reflect:

- 8 sample programs
- 30 sample commits
- Mapping results from commit-based analysis
- Risk Analysis with coupon and settlement demo signals
- Commit Impact examples from dashboard/payment commits
- AI Code Review examples from the recommended review targets

Record any screenshot refresh in `AI_CHANGELOG.md`.

## Troubleshooting

If Mapping appears slow:

- stop after the current commit finishes
- confirm commit-based mode is selected
- lower candidate limits
- switch to `LLM_PROVIDER=mock` for workflow-only verification

If RAG or Project Chat appears slow:

- refresh chunks without embedding first
- generate embeddings in smaller batches
- avoid selecting all source types until the workflow is verified

If Risk Analysis does not show the expected sample risks:

- confirm the project uses `C:\dev\ai-advisor-sample-shop`
- confirm the uploaded Excel files came from `advisor_uploads`
- confirm Mapping has produced related commit mappings
- rerun Risk Analysis after Mapping completes

# Source Indexing And Embedding Plan

## Purpose

This document captures the agreed direction for Project Chat source indexing, incremental embedding, and cloud embedding operation.

It is intended as handoff material for a new development session. It should be read before changing RAG, Project Chat, source indexing, embedding generation, or Git sync behavior.

## Conversation Context

The main concern is that Project Chat should stay useful on realistic SI projects without causing endless LLM or embedding calls.

Key points already agreed:

- Source indexing can become slow when the repository has many files.
- Full re-indexing should not run on every commit.
- Normal operation should use incremental indexing and embedding.
- Full re-indexing should remain available for recovery, branch changes, indexing rule changes, embedding model changes, or suspicious stale results.
- Cloud deployment needs explicit cost control because embedding API usage is billed by input tokens.
- Korean business questions should continue to benefit from uploaded standard terminology and deterministic query expansion.

## Current Implementation Summary

Current implementation is partially optimized, but it is not a complete commit-triggered incremental indexing pipeline yet.

### Git Commit Sync

Git commit sync is incremental.

- `src/services/git_service.py::sync_git_repository`
- Uses `project.last_synced_commit_hash`.
- Fetches commits with `since_commit_hash..HEAD` unless full sync is requested.
- Stores new `GitCommit` and `CommitFile` rows.

This means commit metadata and diffs are not always fully re-collected.

### Source File Chunking

Source file chunking is manually triggered.

- `src/rag/source_index_service.py::refresh_source_file_index`
- `src/rag/chunker.py::build_source_file_chunks`
- Triggered from Project Chat or RAG screens.

The current chunking implementation scans the repository tree with `repo_root.rglob("*")`, filters source-like files, and skips files when the same `file_path + content_hash + indexed_head_hash` already exists.

If a file changed, existing chunks for that file are deleted and new chunks are created.

This is content-aware and avoids duplicate chunks, but it still scans the repository. It does not yet use the changed-file list from Git sync to limit work to only added, modified, renamed, or deleted files.

### Embedding Generation

Embedding generation is missing-vector based.

- `src/rag/vector_store.py::embed_missing_chunks`
- Checks whether a `VectorItem` already exists for `chunk_id + embedding_model`.
- Creates vectors only for chunks that do not have vectors for the selected embedding model.

This prevents repeated embedding calls for unchanged chunks under the same model.

### Project Chat Retrieval

Project Chat retrieves from already-created vectors.

- `source_file` evidence is treated as current-code evidence only when verified.
- `commit` and `commit_file` evidence are historical/reference evidence when enabled.
- Korean questions can be expanded through project standard terms without an extra LLM rewrite call.

## Terminology

### Re-index Current Source

Re-indexing current source means rebuilding source-file chunks for the repository snapshot that Project Chat should treat as current.

It does not mean sending every file directly to the chat model. It means creating searchable chunks and, when requested, generating embeddings for those chunks.

### Top K

Top K is the number of most similar chunks retrieved for a question.

Low values are faster and less noisy, but can miss relevant evidence. High values bring more evidence, but can include irrelevant chunks and increase prompt size.

### Include Commit History

The Project Chat option to include commit history controls whether `commit` and `commit_file` vectors are included as historical/reference evidence.

Recommended use:

- Off: current code structure, method behavior, file responsibility, and implementation questions.
- On: change background, when a feature was added, why a behavior changed, or recent change risk questions.

This option exists because current-code questions and history questions need different evidence scopes.

## Desired Target Architecture

The target design is a two-level indexing model:

1. Incremental indexing for daily work.
2. Full re-indexing for recovery and large context changes.

### Incremental Path

Normal commit or Git sync flow should:

1. Detect newly synced commits.
2. Extract changed file paths from `CommitFile`.
3. For added or modified source files:
   - read only those files,
   - compute content hash,
   - delete old chunks for the file,
   - create new chunks,
   - mark embeddings as pending.
4. For deleted files:
   - delete source chunks,
   - delete related vectors through cascade or explicit cleanup.
5. For renamed files:
   - remove chunks for the old path,
   - index the new path if it is still an indexable source file.
6. Generate embeddings only for missing vectors, preferably with a configurable limit.
7. Update visible index status.

### Full Re-index Path

Full re-index should:

1. Clear or reconcile all `source_file` chunks for the project.
2. Scan the repository using current source-file include/exclude rules.
3. Rebuild chunks.
4. Generate embeddings with an explicit limit or background job.
5. Show progress and final counts.

Full re-index is recommended when:

- the branch changes significantly,
- the current HEAD is not represented in indexed chunks,
- source include/exclude rules change,
- chunking rules change,
- embedding provider/model/dimension changes,
- old or deleted source keeps appearing in evidence,
- the database or vector store is suspected to be inconsistent.

## Cloud Embedding Operation

In cloud deployment, embedding should be treated as a costed external operation unless using a self-hosted embedding model.

Supported direction:

- OpenAI-compatible embedding API for simple MVP operation.
- Self-hosted or vendor embedding service can be added later through the existing provider abstraction.
- Embedding calls must be cached by chunk and embedding model.
- File content hashes should prevent re-embedding unchanged source.
- Batch limits and estimated runtime should remain visible.

Environment expectations:

- `EMBEDDING_PROVIDER`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`
- `EMBEDDING_API_KEY`
- `PGVECTOR_DIMENSION`

Important operational rule:

Changing embedding model or vector dimension requires a deliberate re-embedding plan. Old vectors from another model should not be silently reused for search.

## Proposed Roadmap Work

### Phase 1 - Document And Expose Current Behavior

- Document current source indexing behavior and limitations.
- Make the UI wording clearer:
  - "Re-index current source" is a manual refresh.
  - It scans candidate files and skips unchanged content.
  - It does not automatically run on every commit.
- Show when full re-index is recommended.

### Phase 2 - Incremental Source Index Service

Add a service that can index a known set of changed paths.

Suggested API:

```python
refresh_changed_source_files(
    db,
    project,
    changed_files,
    *,
    embed_after_refresh=False,
    embedding_limit=100,
)
```

Expected behavior:

- `Added` and `Modified`: re-index changed path if source-like.
- `Deleted`: remove chunks and vectors for the path.
- `Renamed`: remove old path and index new path.
- Non-source paths: ignore safely.
- Empty files and oversized files: skip with count.

### Phase 3 - Connect Git Sync To Incremental Indexing

After Git sync saves new commits and commit files:

- Allow the user to run "Index changed files from latest sync".
- Later, optionally add an automatic mode with explicit limits.
- Keep full re-index as a separate action.

Automatic mode should be opt-in because cloud embedding can cost money and local embedding can consume CPU/GPU.

### Phase 4 - Status And Safety UX

Project Chat and RAG screens should show:

- current HEAD,
- latest indexed HEAD,
- source chunk count,
- source vector count,
- missing embedding count,
- stale/invalid chunk count,
- changed-file indexing recommendation,
- full re-index recommendation only when needed.

### Phase 5 - Tests

Add focused tests for:

- modified file re-index deletes old chunks and creates new chunks,
- deleted file removes chunks and vectors,
- renamed file handles old and new paths,
- unchanged file does not create new chunks or vectors,
- embedding generation only runs for missing vectors,
- model change creates a separate missing-vector workload,
- Project Chat excludes stale or invalid source chunks.

## Open Design Questions

- Should incremental indexing run immediately after Git sync, or only after the user clicks an action?
- Should cloud deployment use a background worker for embedding jobs?
- Should the app keep one active embedding model per project, or allow multiple stored models?
- How should branch identity be represented beyond `HEAD` hash?
- Should full re-index clear all source chunks first, or reconcile file-by-file to preserve unchanged vector rows?

## Recommended First Implementation

Start with manual incremental indexing from the latest synced commit files.

Reasoning:

- It reduces embedding cost without introducing background-job complexity.
- It keeps user control over cloud API usage.
- It fits the current Streamlit UI and existing `embed_missing_chunks` behavior.
- It can be tested with a small synthetic Git repo.

Do not make commit sync automatically call embedding APIs in the first pass.

## Files To Inspect Before Implementation

- `src/services/git_service.py`
- `src/rag/chunker.py`
- `src/rag/source_index_service.py`
- `src/rag/vector_store.py`
- `src/rag/chat_service.py`
- `src/ui/git_page.py`
- `src/ui/rag_page.py`
- `src/ui/project_chat_page.py`
- `tests/test_source_file_rag.py`
- `tests/test_project_chat_service.py`

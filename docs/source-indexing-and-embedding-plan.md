# 소스 인덱싱과 임베딩 운영 계획

## 목적

이 문서는 Project Chat의 소스 인덱싱, 증분 임베딩, cloud 임베딩 운영 방향을 정리한 개발 인수인계 문서입니다.

RAG, Project Chat, source indexing, embedding 생성, Git sync 동작을 변경하기 전에는 이 문서를 먼저 확인하세요.

## 논의 배경

핵심 관심사는 Project Chat이 현실적인 SI 프로젝트에서도 과도한 LLM/embedding 호출 없이 계속 유용해야 한다는 점입니다.

이미 합의된 방향은 다음과 같습니다.

- 저장소 파일이 많아지면 source indexing이 느려질 수 있습니다.
- 모든 commit마다 full re-indexing을 실행하면 안 됩니다.
- 일반 운영에서는 incremental indexing과 embedding을 사용해야 합니다.
- full re-indexing은 복구, branch 변경, indexing rule 변경, embedding model 변경, stale 결과가 의심되는 상황에 남겨 둡니다.
- cloud 배포에서는 embedding API가 입력 token 기준으로 과금될 수 있으므로 명시적인 비용 제어가 필요합니다.
- 한국어 업무 질문은 업로드된 표준용어와 deterministic query expansion의 이점을 계속 활용해야 합니다.

## 현재 구현 요약

현재 구현은 일부 최적화되어 있지만, commit-triggered incremental indexing pipeline이 완성된 상태는 아닙니다.

### Git Commit Sync

Git commit sync는 증분 방식입니다.

- `src/services/git_service.py::sync_git_repository`
- `project.last_synced_commit_hash`를 사용합니다.
- full sync가 아니면 `since_commit_hash..HEAD` 범위의 commit을 가져옵니다.
- 새 `GitCommit`, `CommitFile` row를 저장합니다.

따라서 commit metadata와 diff를 매번 전체 재수집하지는 않습니다.

### Source File Chunking

Source file chunking은 수동으로 실행됩니다.

- `src/rag/source_index_service.py::refresh_source_file_index`
- `src/rag/chunker.py::build_source_file_chunks`
- Project Chat 또는 RAG 화면에서 실행됩니다.

현재 chunking 구현은 `repo_root.rglob("*")`로 repository tree를 스캔하고, source-like file을 필터링한 뒤, 같은 `file_path + content_hash + indexed_head_hash` chunk가 이미 있으면 건너뜁니다.

파일 내용이 바뀌면 해당 파일의 기존 chunk를 삭제하고 새 chunk를 생성합니다.

이 방식은 content-aware라서 중복 chunk 생성을 피하지만, 여전히 repository 전체를 스캔합니다. Git sync에서 얻은 changed-file list를 사용해 added, modified, renamed, deleted file만 처리하는 구조는 아직 아닙니다.

### Embedding Generation

Embedding generation은 missing vector 기준입니다.

- `src/rag/vector_store.py::embed_missing_chunks`
- 선택된 `chunk_id + embedding_model` 조합의 `VectorItem`이 이미 있는지 확인합니다.
- 해당 embedding model 기준 vector가 없는 chunk에 대해서만 vector를 생성합니다.

이 방식은 같은 model에서 변경되지 않은 chunk의 embedding을 반복 호출하지 않게 합니다.

### Project Chat Retrieval

Project Chat은 이미 생성된 vector에서 검색합니다.

- `source_file` evidence는 현재 파일과 검증된 경우에만 current-code evidence로 취급합니다.
- `commit`, `commit_file` evidence는 옵션으로 포함될 때 historical/reference evidence로 취급합니다.
- 한국어 질문은 추가 LLM rewrite call 없이 project standard terms로 확장될 수 있습니다.

## 용어

### 현재 소스 재인덱싱

현재 소스 재인덱싱은 Project Chat이 현재 코드로 취급해야 하는 repository snapshot 기준으로 source-file chunk를 다시 만드는 작업입니다.

모든 파일을 chat model에 직접 보내는 작업이 아닙니다. 검색 가능한 chunk를 만들고, 사용자가 요청한 경우 해당 chunk의 embedding을 생성하는 작업입니다.

### Top K

Top K는 질문과 가장 유사한 chunk를 몇 개 가져올지 정하는 값입니다.

값이 낮으면 빠르고 noise가 적지만 관련 evidence를 놓칠 수 있습니다. 값이 높으면 더 많은 evidence를 가져오지만, 관련 없는 chunk가 섞이고 prompt 크기가 커질 수 있습니다.

### Include Commit History

Project Chat의 commit history 포함 옵션은 `commit`, `commit_file` vector를 historical/reference evidence로 포함할지 결정합니다.

권장 사용 기준:

- Off: 현재 코드 구조, method 동작, file 책임, 구현 방식 질문
- On: 기능이 언제 추가되었는지, 왜 동작이 바뀌었는지, 최근 변경 위험이 무엇인지 같은 이력 질문

이 옵션이 필요한 이유는 current-code question과 history question이 서로 다른 evidence scope를 요구하기 때문입니다.

## 목표 아키텍처

목표 설계는 두 단계 indexing model입니다.

1. 일상 작업용 incremental indexing
2. 복구와 큰 context 변경을 위한 full re-indexing

### Incremental Path

일반 commit 또는 Git sync 흐름은 다음과 같이 동작해야 합니다.

1. 새로 sync된 commit을 감지합니다.
2. `CommitFile`에서 changed file path를 추출합니다.
3. added 또는 modified source file에 대해:
   - 해당 파일만 읽습니다.
   - content hash를 계산합니다.
   - 해당 파일의 old chunk를 삭제합니다.
   - new chunk를 생성합니다.
   - embedding pending 상태로 둡니다.
4. deleted file에 대해:
   - source chunk를 삭제합니다.
   - cascade 또는 명시적 cleanup으로 관련 vector를 삭제합니다.
5. renamed file에 대해:
   - old path chunk를 제거합니다.
   - new path가 indexable source file이면 새로 index합니다.
6. missing vector에 대해서만 embedding을 생성하고, 가급적 configurable limit을 적용합니다.
7. 화면에 index status를 갱신합니다.

### Full Re-index Path

Full re-index는 다음과 같이 동작해야 합니다.

1. 해당 project의 모든 `source_file` chunk를 clear 또는 reconcile합니다.
2. 현재 source-file include/exclude rule로 repository를 스캔합니다.
3. chunk를 다시 생성합니다.
4. explicit limit 또는 background job으로 embedding을 생성합니다.
5. progress와 final count를 보여줍니다.

Full re-index가 권장되는 상황:

- branch가 크게 바뀐 경우
- current HEAD가 indexed chunk에 충분히 반영되지 않은 경우
- source include/exclude rule이 바뀐 경우
- chunking rule이 바뀐 경우
- embedding provider, model, dimension이 바뀐 경우
- 오래되었거나 삭제된 source가 evidence에 계속 나타나는 경우
- database 또는 vector store 불일치가 의심되는 경우

## Cloud Embedding 운영

Cloud 배포에서 embedding은 self-hosted embedding model을 쓰지 않는 한 비용이 발생하는 외부 작업으로 취급해야 합니다.

지원 방향:

- 단순 MVP 운영은 OpenAI-compatible embedding API를 사용합니다.
- self-hosted 또는 vendor embedding service는 기존 provider abstraction을 통해 나중에 추가할 수 있습니다.
- embedding call은 chunk와 embedding model 기준으로 cache되어야 합니다.
- file content hash로 변경되지 않은 source의 re-embedding을 막아야 합니다.
- batch limit과 estimated runtime은 계속 화면에 보여야 합니다.

환경 변수:

- `EMBEDDING_PROVIDER`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`
- `EMBEDDING_API_KEY`
- `PGVECTOR_DIMENSION`

중요 운영 규칙:

Embedding model 또는 vector dimension을 변경하면 의도적인 re-embedding 계획이 필요합니다. 다른 model로 만든 old vector를 search에 조용히 재사용하면 안 됩니다.

## 제안 로드맵

### Phase 1 - 현재 동작 문서화와 노출

- 현재 source indexing 동작과 한계를 문서화합니다.
- UI wording을 더 명확하게 만듭니다.
  - "현재 소스 재인덱싱"은 manual refresh입니다.
  - candidate file을 스캔하고 unchanged content는 건너뜁니다.
  - 모든 commit마다 자동 실행되지 않습니다.
- full re-index가 권장되는 상황을 보여줍니다.

### Phase 2 - Incremental Source Index Service

알려진 changed path 집합을 index할 수 있는 service를 추가합니다.

제안 API:

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

기대 동작:

- `Added`, `Modified`: source-like path이면 re-index합니다.
- `Deleted`: 해당 path의 chunk와 vector를 제거합니다.
- `Renamed`: old path를 제거하고 new path를 index합니다.
- Non-source path: 안전하게 무시합니다.
- Empty file과 oversized file: count만 기록하고 건너뜁니다.

### Phase 3 - Git Sync와 Incremental Indexing 연결

Git sync가 새 commit과 commit file을 저장한 뒤:

- 사용자가 "latest sync의 changed file index" 작업을 실행할 수 있게 합니다.
- 이후 optional automatic mode를 추가하되 explicit limit을 둡니다.
- full re-index는 별도 action으로 유지합니다.

Automatic mode는 opt-in이어야 합니다. Cloud embedding은 비용이 들 수 있고, local embedding은 CPU/GPU를 사용할 수 있기 때문입니다.

### Phase 4 - Status와 Safety UX

Project Chat과 RAG 화면은 다음 상태를 보여야 합니다.

- current HEAD
- latest indexed HEAD
- source chunk count
- source vector count
- missing embedding count
- stale/invalid chunk count
- changed-file indexing recommendation
- 필요한 경우에만 full re-index recommendation

### Phase 5 - Tests

다음 focused test를 추가합니다.

- modified file re-index가 old chunk를 삭제하고 new chunk를 생성하는지
- deleted file이 chunk와 vector를 제거하는지
- renamed file이 old path와 new path를 처리하는지
- unchanged file이 new chunk 또는 vector를 만들지 않는지
- embedding generation이 missing vector에 대해서만 실행되는지
- model change가 별도의 missing-vector workload를 만드는지
- Project Chat이 stale 또는 invalid source chunk를 제외하는지

## 열린 설계 질문

- Incremental indexing을 Git sync 직후 자동 실행할지, 사용자 click action으로 둘지?
- Cloud 배포에서 embedding job용 background worker가 필요한지?
- 앱이 project별 active embedding model 하나만 유지할지, 여러 stored model을 허용할지?
- `HEAD` hash 외에 branch identity를 어떻게 표현할지?
- Full re-index가 모든 source chunk를 먼저 clear할지, file-by-file reconcile로 unchanged vector row를 보존할지?

## 권장 첫 구현

최신 sync commit file을 기준으로 manual incremental indexing부터 시작합니다.

이유:

- background job complexity 없이 embedding cost를 줄일 수 있습니다.
- cloud API usage에 대한 사용자 제어권을 유지합니다.
- 현재 Streamlit UI와 기존 `embed_missing_chunks` 동작에 잘 맞습니다.
- 작은 synthetic Git repo로 테스트할 수 있습니다.

첫 번째 구현에서는 commit sync가 embedding API를 자동 호출하게 만들지 않습니다.

## 구현된 MVP 동작

현재 구현된 첫 번째 버전은 `manual incremental indexing`입니다. 사용자가 Git Sync를 실행해 commit과 `CommitFile` row를 저장한 뒤, RAG 검색 또는 Project Chat 화면에서 `최근 Git sync 변경 파일만 인덱싱`을 누르면 최근 indexed HEAD 이후 DB에 저장된 변경 파일만 source_file chunk로 갱신합니다.

증분 인덱싱은 다음 원칙을 지킵니다.

- repository 전체를 `rglob("*")`로 다시 스캔하지 않고, Git sync가 저장한 changed file path만 처리합니다.
- `Added`, `Modified`, `Copied`는 해당 파일이 source-like text/code file일 때만 기존 path chunk를 교체하고 새 chunk를 만듭니다.
- `Deleted`는 해당 path의 `source_file` chunk와 연결된 vector를 함께 제거합니다.
- `Renamed`는 old path chunk/vector를 제거하고 new path가 source-like file이면 새 chunk를 만듭니다. 기존 DB에는 old path 컬럼이 없으므로 API 입력의 `old_file_path`를 우선 사용하고, `CommitFile.diff_text`의 `rename from ...` line을 보조적으로 읽습니다.
- binary, image, Excel, virtualenv, cache, oversized file, empty file, repository 밖으로 벗어나는 path는 chunk를 만들지 않고 skipped count로 처리합니다.
- 새 chunk metadata는 `embedding_status=pending`으로 저장합니다.
- `embed_after_refresh` 기본값은 `False`입니다. 즉 증분 인덱싱 버튼은 embedding API를 자동 호출하지 않습니다.
- embedding은 `RAG 검색 > Embedding`에서 현재 embedding model 기준 missing vector만 제한 수량으로 생성합니다.

이 MVP는 Git sync 직후 자동으로 실행되지 않습니다. Cloud embedding 비용과 local LM Studio CPU/GPU 부하를 사용자가 통제할 수 있도록 수동 action으로 둡니다. 이후 자동 모드를 추가하더라도 opt-in, batch limit, 예상 runtime 안내가 필요합니다.

사용자가 선택할 수 있는 action은 다음과 같이 구분합니다.

| Action | 처리 범위 | embedding 호출 | 권장 상황 |
|---|---|---|---|
| `최근 Git sync 변경 파일만 인덱싱` | 최근 indexed HEAD 이후 Git sync에 저장된 changed file path | 자동 호출 안 함 | 일반적인 commit sync 후 최신 변경분만 반영 |
| `현재 소스 다시 인덱싱` | 현재 include/exclude rule에 맞는 repository 전체 source file scan | Project Chat에서는 호출 안 함, RAG에서는 사용자가 체크한 경우만 제한 호출 | 최초 구축, branch 대폭 변경, stale/invalid chunk가 많음, 복구 필요 |
| `RAG 검색 > Embedding` | vector가 없는 selected source_type chunk | 사용자가 지정한 limit만 호출 | chunk 갱신 뒤 RAG/Project Chat 검색 품질 확인 |

현재 구현 파일:

- `src/rag/source_index_service.py`: `ChangedSourceFile`, `refresh_changed_source_files`, `get_changed_source_files_since_latest_index`
- `src/rag/chunker.py`: `build_source_file_chunks_for_paths`
- `src/ui/rag_page.py`: RAG Index tab의 manual incremental indexing button
- `src/ui/project_chat_page.py`: Project Chat 상단 source index status의 manual incremental indexing button
- `tests/test_incremental_source_index_service.py`: modified, deleted, renamed, non-source changed file 검증

## 구현 전 확인할 파일

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

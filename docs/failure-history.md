# Failure History

이 문서는 프로젝트 전반에서 발생한 실패, 시행착오, 운영상 누락, 검증 누락 중 재발 방지 가치가 있는 사례를 기록합니다. 범위는 CI에 한정하지 않습니다. 기능 설계, UX, 데이터, schema, RAG/LLM, embedding, sample data, 문서, 배포, local 검증, GitHub Actions, 운영 절차에서 배운 내용을 남깁니다.

단순한 일시적 네트워크 실패, 사용자가 즉시 취소한 run, 방향을 바꾸지 않은 read-only 조사, 재현 불가능하고 조치가 없는 현상은 기록하지 않습니다.

## 기록 기준

다음 중 하나에 해당하면 이 문서에 항목을 추가합니다.

- 기능 설계나 구현이 실제 사용 시나리오를 충분히 반영하지 못했습니다.
- local에서는 통과했지만 CI, 다른 PC, demo, 운영 환경에서는 실패했습니다.
- 테스트, schema, migration, dependency, workflow, 환경 변수, 외부 service, sample data 전제가 누락됐습니다.
- LLM/RAG/embedding 동작이 stale evidence, 비용, hallucination, 검증 불가 근거 같은 안전 문제를 만들었습니다.
- 사용자 문서만 보고는 기능 목적, 사용 조건, 복구 방법, 한계를 이해하기 어려웠습니다.
- 실패를 해결하기 위해 코드, 테스트, workflow, 문서, agent policy, 운영 절차를 변경했습니다.
- 같은 종류의 실수를 피하기 위한 명확한 예방 규칙이 생겼습니다.

각 항목은 가능한 한 다음 정보를 포함합니다.

- 날짜
- 관련 기능, 문서, run/job URL, commit
- 증상
- 직접 원인
- 배경 또는 구조적 원인
- 왜 사전 검증에서 놓쳤는지
- 수정 내용
- 재발 방지 규칙
- 남은 한계 또는 후속 확인 사항
- 검증 명령과 결과

## 2026-06-09 / 2026-06-10 - Incremental source indexing tests failed in CI

분류:

- Test/CI environment
- RAG source indexing
- pgvector service dependency

관련 run:

- `https://github.com/ino5/ai-commit-advisor-26/actions/runs/27214745786/job/80353181820`
- Workflow: `CI`
- Job: `test`
- Failed step: `Run tests`
- Failed commit shown by GitHub: `1b8dd93 Document incremental source indexing operations`
- Fix commit: `140c2d2 Add database service to CI`

### 증상

GitHub Actions job page에서 `Run tests` 단계가 `Process completed with exit code 1`로 실패했습니다. 공개 페이지에서는 상세 pytest log가 로그인 없이 보이지 않았지만, job summary에는 `Run tests` 실패와 Node.js 20 deprecation warning이 함께 표시되었습니다.

Node.js 20 warning은 `actions/checkout@v4`, `actions/setup-python@v5`에 대한 GitHub Actions platform warning이었고, 이번 실패의 직접 원인은 아니었습니다.

### 직접 원인

`tests/test_incremental_source_index_service.py`가 추가되면서 source indexing test가 실제 PostgreSQL/pgvector DB를 사용하게 되었습니다.

Local 개발 환경에는 `docker-compose.yml`의 `pgvector/pgvector:pg16` 컨테이너가 떠 있었기 때문에 다음 명령이 통과했습니다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

하지만 기존 GitHub Actions workflow에는 PostgreSQL service가 없었습니다.

```yaml
steps:
  - name: Run tests
    run: python -m pytest -q
```

따라서 CI runner에서 pytest가 DB 연결 또는 migration 초기화가 필요한 테스트를 실행할 때 실패했습니다.

### 배경 또는 구조적 원인

증분 source indexing 기능은 `DocumentChunk`, `VectorItem`, pgvector column, Alembic migration 상태를 함께 다루는 기능입니다. 수정/삭제/rename 처리에서 vector cleanup을 검증하려면 순수 unit test보다 DB-backed integration test가 더 적합했습니다.

문제는 테스트의 성격이 바뀌었는데도 CI workflow의 실행 전제 조건은 Python-only 상태로 남아 있었다는 점입니다.

### 사전 검증에서 놓친 이유

로컬 검증은 실제 DB가 있는 개발 PC 기준으로 수행됐고, CI workflow의 service dependency까지 함께 검토하지 않았습니다. 테스트가 순수 unit test에서 DB-backed integration test로 확장됐는데, CI 실행 환경은 사전에 DB 없는 workflow였습니다.

### 수정 내용

`.github/workflows/ci.yml`에 pgvector PostgreSQL service를 추가했습니다.

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    env:
      POSTGRES_DB: ai_commit_advisor
      POSTGRES_USER: ai_user
      POSTGRES_PASSWORD: ai_password
    ports:
      - 5432:5432
    options: >-
      --health-cmd "pg_isready -U ai_user -d ai_commit_advisor"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
env:
  DATABASE_URL: postgresql+psycopg2://ai_user:ai_password@localhost:5432/ai_commit_advisor
  PGVECTOR_DIMENSION: "768"
  LLM_PROVIDER: mock
  EMBEDDING_PROVIDER: mock
```

이 변경으로 CI가 local test 환경과 같은 DB 전제 조건을 갖게 되었습니다. LLM과 embedding은 CI에서 외부 server에 의존하지 않도록 mock provider를 명시했습니다.

### 재발 방지 규칙

- DB, pgvector, Docker service, external API, browser, local model server가 필요한 테스트를 추가하면 같은 commit 또는 같은 change set에서 CI workflow 전제 조건도 함께 확인합니다.
- local에서 통과한 테스트라도 CI가 같은 service를 제공하는지 확인합니다.
- CI에서 외부 LLM/embedding server가 필요하지 않도록 기본 provider는 mock으로 고정합니다.
- 자동 검증 실패를 사용자가 보고하거나 agent가 확인하면 원인과 조치 내용을 이 문서에 기록합니다.
- GitHub Actions warning과 failure를 구분합니다. Warning은 별도 개선 후보로 기록하되, 실패 원인으로 단정하지 않습니다.

### 남은 한계

- GitHub Actions 상세 log는 비로그인 공개 화면에서 제한적으로만 보입니다. 가능한 경우 GitHub CLI 또는 로그인된 UI로 raw log를 확인해야 합니다.
- Node.js 20 deprecation warning은 직접 실패 원인은 아니지만, 이후 GitHub Actions runtime 변경 전에 `actions/checkout`, `actions/setup-python` 버전 또는 runner 정책을 별도 점검할 수 있습니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m compileall src tests
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

결과:

- `compileall` passed
- `pytest` passed with 78 tests
- `git diff --check` passed without whitespace errors

GitHub Actions verification:

- Fix commit `140c2d2` was pushed to `main`.
- The new workflow run was queued with the PostgreSQL service configuration.

## 2026-06-10 - GitHub hosted runner acquisition failure

분류:

- GitHub Actions platform
- CI operation
- External infrastructure

관련 run:

- Workflow: `CI`
- Run: `docs: explain RAG chat rationale #42`
- Commit shown by GitHub: `731c436`
- 증상 annotation:
  - `The job was not acquired by Runner of type hosted even after multiple attempts`
  - `Internal server error. Correlation ID: 6837253b-ba61-49c9-b3d3-ffc082e3424c`

### 증상

GitHub Actions summary에서 job duration이 약 15분으로 표시됐지만, 실제 실패 annotation은 test command나 pytest assertion이 아니라 hosted runner 배정 실패와 GitHub internal server error였습니다.

### 직접 원인

GitHub-hosted runner가 job을 가져가지 못했습니다. 이 경우 repository code, workflow step, dependency 설치, pytest 결과와 무관하게 GitHub Actions platform 단계에서 실패할 수 있습니다.

### 배경 또는 구조적 원인

CI workflow는 GitHub-hosted `ubuntu-latest` runner에 의존합니다. Runner pool 또는 GitHub Actions service에 일시적인 문제가 있으면 workflow file이 올바르고 local verification이 통과해도 job이 시작되지 못할 수 있습니다.

### 사전 검증에서 놓친 이유

Local verification은 code와 test 실행 가능성을 확인하지만, GitHub-hosted runner acquisition 자체는 local에서 재현하거나 사전에 검증할 수 없습니다.

### 수정 내용

`.github/workflows/ci.yml`에 `workflow_dispatch`를 추가했습니다. 이제 push 없이도 Actions UI에서 CI를 수동 재실행할 수 있습니다.

```yaml
on:
  push:
  pull_request:
  workflow_dispatch:
```

### 재발 방지 규칙

- Annotation이 runner acquisition, internal server error, GitHub platform error를 가리키면 code/test failure로 단정하지 않습니다.
- 먼저 같은 commit에서 workflow를 rerun하거나 `workflow_dispatch`로 수동 실행합니다.
- 반복되면 GitHub status와 Actions service 상태를 확인합니다.
- `Run tests`, `Compile Python files`, dependency install 같은 실제 step log가 실패한 경우에만 code, test, workflow dependency 문제로 조사합니다.

### 남은 한계

- GitHub-hosted runner 장애는 repository 안에서 완전히 방지할 수 없습니다.
- `workflow_dispatch`는 재실행 편의를 높일 뿐, GitHub platform 장애 자체를 해결하지는 않습니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m compileall src app.py
.\.venv\Scripts\python.exe -m pytest -q
```

결과:

- `compileall` passed
- `pytest` passed with 80 tests

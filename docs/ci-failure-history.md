# CI Failure History

이 문서는 GitHub Actions, local verification, deployment smoke check 같은 자동 검증 실패 중 재발 방지 가치가 있는 사례를 기록합니다. 단순한 일시적 네트워크 실패나 사용자가 즉시 취소한 run은 기록하지 않고, 테스트/환경/문서/운영 정책을 바꿔야 하는 실패를 남깁니다.

## 기록 기준

다음 중 하나에 해당하면 이 문서에 항목을 추가합니다.

- CI 실패가 코드, 테스트, schema, dependency, workflow, 환경 변수, 외부 service 누락 때문에 발생했습니다.
- local에서는 통과했지만 CI에서는 실패해 실행 환경 차이를 확인했습니다.
- 실패를 해결하기 위해 workflow, Docker service, test fixture, 문서, agent policy를 변경했습니다.
- 같은 종류의 실수를 피하기 위한 명확한 예방 규칙이 생겼습니다.

각 항목은 가능한 한 다음 정보를 포함합니다.

- 날짜와 관련 run/job URL
- 실패한 commit 또는 workflow run
- 증상
- 직접 원인
- 왜 사전에 잡히지 않았는지
- 수정 내용
- 재발 방지 규칙
- 검증 명령과 결과

## 2026-06-09 / 2026-06-10 - Incremental source indexing tests failed in CI

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

### 사전에 잡히지 않은 이유

로컬 검증은 실제 DB가 있는 개발 PC 기준으로 수행됐고, CI workflow의 service dependency까지 함께 검토하지 않았습니다. 테스트가 순수 unit test에서 DB-backed integration test로 확장됐는데, CI 실행 환경은 여전히 DB 없는 Python-only workflow였습니다.

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
- CI 실패를 사용자가 보고하거나 agent가 확인하면 원인과 조치 내용을 이 문서에 기록합니다.
- GitHub Actions warning과 failure를 구분합니다. Warning은 별도 개선 후보로 기록하되, 실패 원인으로 단정하지 않습니다.

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

# Failure History

이 문서는 프로젝트 전반에서 발생한 실패, 시행착오, 운영상 누락, 검증 누락 중 재발 방지 가치가 있는 사례를 기록합니다. 범위는 CI에 한정하지 않습니다. 기능 설계, UX, 데이터, schema, RAG/LLM, embedding, sample data, 문서, 배포, local 검증, GitHub Actions, 운영 절차에서 배운 내용을 남깁니다.

실패나 incident가 아닌 설계, 운영, 검증, 자동화, 문서 구조 결정은 [Engineering Decisions](engineering-decisions.md)에 기록합니다. 실패 이력이 더 넓은 운영 기준으로 이어질 때는 두 문서를 서로 연결합니다.

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

## 2026-06-10 - Commit-based Mapping malformed JSON blocked complete sample verification

분류:

- Mapping
- LLM output robustness
- Sample demo verification

관련 기능 및 문서:

- `src/services/mapping_service.py`
- `tests/test_mapping_service.py`
- `docs/ai-technical-overview.md`
- `AI_CHANGELOG.md`

### 증상

48개 commit 샘플 프로젝트에서 commit-based Mapping을 실행했을 때 `Add QA checklist for Spring MyBatis flows` commit 1건이 `failed` 상태로 남았습니다. 재시도해도 `LLM response did not match commit-based mapping JSON format` 오류가 반복되어 Mapping 화면에 실패 커밋 1건이 보였고, 분석 완료 상태의 스크린샷을 찍기 어려웠습니다.

### 직접 원인

commit-based Mapping은 LLM에게 `{"related_programs": [...]}` shape을 요구했지만, local LLM이 해당 commit에서 요구 JSON shape을 지키지 않았습니다. 기존 commit-based 경로는 JSON 파싱 실패를 바로 commit failure로 처리했습니다.

### 배경 또는 구조적 원인

program-based Mapping에는 token similarity fallback이 있었지만 commit-based Mapping에는 같은 fallback이 없었습니다. 문서/QA/test-only commit처럼 여러 프로그램과 느슨하게 관련된 commit은 LLM이 설명형 응답으로 벗어날 가능성이 더 큽니다.

### 사전 검증에서 놓친 이유

샘플 데이터 확장 직후에는 Git sync, upload, count, focused unit test 중심으로 확인했고, 전체 48개 commit에 대한 real local LLM commit-based Mapping batch를 먼저 돌리지 않았습니다.

### 수정 내용

commit-based Mapping에서 LLM 응답을 요구 JSON으로 파싱하지 못하면 후보 프로그램과 commit message, changed file path, diff snippet의 token similarity로 보수적인 fallback mapping을 저장하도록 변경했습니다. fallback 사용 사실은 mapping reason과 `raw_response.fallback`에 남깁니다.

### 재발 방지 규칙

- 샘플 스크린샷 갱신 전에는 Git sync/upload뿐 아니라 Mapping, Risk Analysis, AI Progress, RAG, Project Chat까지 핵심 분석 상태를 먼저 검증합니다.
- LLM batch 분석은 한 항목의 malformed response가 전체 downstream 검증을 막지 않도록 fallback 또는 부분 성공 처리를 갖춰야 합니다.
- fallback은 완전한 AI 판단이 아니므로 reason/raw metadata에 사용 사실을 남깁니다.

### 남은 한계 또는 후속 확인 사항

fallback은 token overlap 기반이므로 false positive 가능성이 있습니다. Mapping feedback review queue에서 낮은 관련도, weak reason, unrelated decision을 계속 검토해야 합니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -m pytest tests\test_mapping_service.py -q` passed with 4 tests.
- 48개 sample commit Mapping 재검증 결과: completed 48, failed 0, mappings 59.
- Risk Analysis 재실행 결과: unresolved risk 12건.
- AI Progress 확인 결과: 8개 program, plan average 90.6%, AI average 50.0%, implementation status 8건.

## 2026-06-10 - Parallel screenshot capture triggered Alembic migration context collision

분류:

- Screenshot verification
- Streamlit startup
- Alembic migration concurrency

관련 기능 및 문서:

- `src/db/init_db.py`
- `scripts/capture_feature_screenshot.py`
- `AI_CHANGELOG.md`

### 증상

Application Preview 캡처를 병렬로 실행하던 중 새 Streamlit browser session에서 `KeyError: 'script'`가 표시됐습니다. traceback은 `init_db() -> run_migrations() -> alembic.command.upgrade()` 종료 시 Alembic `EnvironmentContext._remove_proxy()`에서 발생했습니다.

### 직접 원인

여러 Streamlit session이 거의 동시에 page load를 시작하면서 `load_projects()`가 각각 `init_db()`를 호출했고, 같은 Python process 안에서 Alembic migration command가 중복 실행됐습니다. Alembic proxy context는 이 동시 실행에 안전하지 않았습니다.

### 배경 또는 구조적 원인

`init_db()`는 앱 화면 진입마다 migration을 다시 호출했습니다. 단일 사용자의 순차 실행에서는 잘 드러나지 않았지만, screenshot automation을 병렬로 돌리면 같은 process에서 migration 초기화가 겹칠 수 있었습니다.

### 사전 검증에서 놓친 이유

기존 캡처 자동화는 feature를 순차 실행하는 전제를 주로 사용했습니다. 이번 작업에서 시간을 줄이려고 여러 screenshot command를 병렬 실행하면서 Streamlit startup path의 동시성 문제가 드러났습니다.

### 수정 내용

`init_db()`에 process-local lock과 initialized flag를 추가해 같은 process에서는 migration을 한 번만 실행하도록 했습니다. 캡처는 병렬 대신 순차 실행으로 진행했습니다.

### 재발 방지 규칙

- Streamlit app startup에서 migration 같은 global side effect는 process-local lock으로 보호합니다.
- screenshot automation은 앱 초기화 경로를 건드리는 경우 병렬 실행을 피하거나, 각 worker가 독립 process/server를 쓰도록 합니다.
- GitHub Actions warning이나 generic Playwright wrapper message보다 실제 traceback의 failed step을 기준으로 원인을 기록합니다.

### 남은 한계 또는 후속 확인 사항

process-local lock은 같은 Python process 안의 중복 migration을 막습니다. 여러 app process가 동시에 시작되는 운영 배포에서는 DB migration을 app startup 밖의 deployment step으로 분리하는 정책을 별도로 검토할 수 있습니다.

### 검증 명령과 결과

- 확인용 Streamlit 서버 재시작 후 sequential screenshot capture가 성공했습니다.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature rag-search --url http://localhost:8537 --surface local --project-name "AAA Sample Shop Rich Demo 48"` passed.

## 2026-06-10 - Sidebar active menu jitter returned after CSS-only stabilization

분류:

- UX
- Streamlit sidebar navigation
- Visual verification gap

관련 문서:

- `app.py`
- `scripts/capture_feature_screenshot.py`
- `docs/engineering-decisions.md`
- `ROADMAP.md`
- `AI_CHANGELOG.md`

### 증상

사이드바 메뉴 클릭 시 선택 항목의 색상만 바뀌는 것이 아니라 위치와 간격이 미묘하게 깨져 보였습니다. 이전에 `Sidebar 메뉴 위치 흔들림 보정` 작업으로 높이, margin, box sizing, 왼쪽 border 폭을 맞췄지만, 사용자가 다시 같은 종류의 어색함을 확인했습니다.

read-only 계측에서 `Dashboard` 같은 항목이 비활성 버튼일 때와 활성 custom `div`일 때 같은 메뉴 슬롯 안에서 `y` 위치가 약 16px 달라지는 사례가 확인됐습니다.

### 직접 원인

활성 메뉴는 `st.sidebar.markdown('<div class="nav-active">...')`로 렌더링했고, 비활성 메뉴는 `st.sidebar.button(...)`으로 렌더링했습니다. 두 항목은 CSS 값 일부가 같아도 Streamlit wrapper, button 내부 `p` 구조, margin 적용 위치가 달랐습니다.

### 배경 또는 구조적 원인

이전 보정은 active/inactive box sizing을 맞추는 CSS 조정에 집중했습니다. 하지만 상태에 따라 DOM 구조가 달라지는 설계 자체는 유지됐기 때문에, Streamlit 내부 구조나 특정 선택 상태에서 다시 시각 차이가 드러날 수 있었습니다.

### 사전 검증에서 놓친 이유

기존 Playwright 검증은 클릭 전후 `Mapping` 항목의 `x`, `y`, `width`가 크게 밀리는지 확인했습니다. 이 검증은 메뉴 전체가 이동하는 문제는 잡지만, 선택된 항목 자체가 비활성 버튼에서 활성 `div`로 바뀌며 슬롯 위치와 텍스트 기준선이 달라지는 문제는 충분히 확인하지 못했습니다.

### 수정 내용

사이드바 메뉴 항목을 활성/비활성 상태와 관계없이 모두 `st.button`으로 렌더링하도록 변경했습니다. 선택된 메뉴를 다시 클릭하면 상태 변경과 rerun을 하지 않습니다.

검증 스크립트는 custom `.nav-active` markup이 남아 있으면 실패하고, `Home`, `Dashboard`, `AI Progress` 항목의 클릭 전후 box 위치, 크기, text relative offset, 인접 간격이 바뀌면 실패하도록 보강했습니다.

### 재발 방지 규칙

- 같은 역할의 UI 항목은 상태가 달라도 같은 Streamlit 컴포넌트 구조로 렌더링합니다.
- CSS 보정으로 시각 차이를 줄이기 전에 DOM 구조가 갈라져 있는지 먼저 확인합니다.
- 메뉴 안정성 검증은 주변 항목 이동뿐 아니라 선택 항목 자체의 box, text offset, adjacent spacing을 확인합니다.
- active highlight를 다시 추가하려면 같은 button 구조 위에서 구현하거나, 동일 wrapper 구조를 유지하는 설계를 먼저 검증합니다.

### 남은 한계

- 메뉴 행 자체의 active highlight는 제거됐고, 현재 선택 상태는 사이드바 상단 `현재 위치` 경로로 확인합니다.
- Streamlit이 button DOM 구조를 크게 바꾸면 검증 스크립트 selector도 함께 조정해야 합니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py src scripts
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8518 --screenshot .tmp\sidebar-structure-home.png --surface local
git diff --check
```

결과:

- `compileall` passed for `app.py`, `src`, and `scripts`.
- Home screenshot verification passed against local Streamlit port 8518 and confirmed sidebar structure stability.
- `git diff --check` passed with only Git line-ending warnings.

## 2026-06-10 - Engineering decision review was missed during maintainability planning

분류:

- Agent policy
- Documentation workflow
- Engineering decision review

관련 문서:

- `AGENTS.md`
- `docs/engineering-decisions.md`
- `ROADMAP.md`
- `AI_CHANGELOG.md`

### 증상

사이드바 메뉴 위치 흔들림 재발을 read-only로 조사한 뒤, 사용자가 유지보수성 관점의 처리 계획을 요청했습니다. 초기 계획은 `AI_CHANGELOG.md`, `ROADMAP.md`, 검증 스크립트 보강을 중심으로 정리됐지만, `docs/engineering-decisions.md` 검토가 바로 포함되지 않았습니다.

사용자가 "기능 개선하면 적는 md"와 `AGENTS.md` 기준을 다시 지적한 뒤에야, 이 작업이 반복 가능한 유지보수 원칙과 검증 정책을 바꾸는 engineering decision 후보라는 점을 명확히 반영했습니다.

### 직접 원인

에이전트가 변경을 "사이드바 UX 버그와 CSS/렌더링 구조 개선"으로 좁게 분류했고, 사용자가 유지보수성을 핵심 판단 기준으로 제시한 시점에도 `docs/engineering-decisions.md`를 필수 검토 후보로 즉시 승격하지 않았습니다.

### 배경 또는 구조적 원인

`AGENTS.md`에는 이미 Engineering Decisions 기준과 Pre-Commit Documentation Check가 있었지만, 의미 있는 작업을 제안하거나 시작하기 전에 문서 영향도를 한 번에 분류하는 명시적 게이트는 없었습니다.

그 결과 개별 문서 기준은 존재했지만, 계획 단계에서 "이 변경은 앞으로 반복될 정책이나 유지보수 원칙을 만드는가?"라는 질문이 빠질 수 있었습니다.

### 사전 검증에서 놓친 이유

read-only 조사와 계획 수립 단계였기 때문에 코드 검증이나 commit 전 체크리스트를 아직 실행하지 않았습니다. 하지만 문서 영향도 검토는 구현 후가 아니라 계획 단계에서 필요한 작업이었고, 기존 체크리스트는 그 타이밍을 충분히 강제하지 못했습니다.

### 수정 내용

`AGENTS.md`에 `Documentation Impact Gate`를 추가했습니다. 에이전트는 의미 있는 code, UX, test, behavior, automation, operations, documentation 작업을 제안하거나 시작하기 전에 `AI_CHANGELOG.md`, `ROADMAP.md`, `docs/engineering-decisions.md`, `docs/failure-history.md`, user-facing docs, architecture, AI technical overview, DB migration, sample project design 문서 영향도를 명시적으로 분류해야 합니다.

또한 사용자가 유지보수성, future reuse, verification policy, structural tradeoff, operating policy, agent behavior 관점으로 변경을 설명하면 `docs/engineering-decisions.md`를 필수 검토 후보로 취급하도록 했습니다.

### 재발 방지 규칙

- 작업 계획을 세울 때 문서 영향도 분류를 별도 단계로 수행합니다.
- 유지보수성이나 반복 가능한 검증·운영·문서화 정책을 다루는 변경은 `docs/engineering-decisions.md`를 먼저 검토합니다.
- 재발, 검증 공백, agent-caused mistake가 드러난 경우 `docs/failure-history.md` 기록 여부를 계획 단계에서 판단합니다.
- 문서를 업데이트하지 않는 경우에는 계획, 최종 응답, commit note 중 한 곳에 이유를 남깁니다.

### 남은 한계

- 문서 영향도 게이트는 판단 누락을 줄이는 정책입니다. 모든 변경에 대해 모든 문서를 수정하라는 뜻은 아니므로, 에이전트가 변경 범위와 문서 역할을 계속 구분해야 합니다.
- 작은 read-only 조사만으로 끝나는 경우에는 기록하지 않아도 되지만, 조사 결과가 작업 방향이나 운영 정책을 바꾸면 다시 문서 영향도 분류를 해야 합니다.

### 검증

Local verification:

```powershell
Get-Content -Path AGENTS.md -Encoding UTF8
Get-Content -Path docs\engineering-decisions.md -Encoding UTF8
Get-Content -Path docs\failure-history.md -Encoding UTF8
rg -n "Documentation Impact Gate|Documentation impact gate|Engineering decision review" AGENTS.md docs AI_CHANGELOG.md ROADMAP.md
git diff --check
```

결과:

- `Get-Content -Encoding UTF8` rendered the new Korean and English policy text correctly.
- `rg` confirmed the new gate, engineering decision, failure-history entry, roadmap task, and changelog references.
- `git diff --check` passed with only Git line-ending warnings.

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

## 2026-06-10 - Docker app could not verify host Git repository paths

분류:

- Docker deployment
- Project Chat/RAG source verification
- Screenshot verification

관련 기능:

- Docker app service
- Project Chat persisted history screenshot
- `docs/images/features/project-chat.png`

### 증상

Docker app(`http://localhost:8501`)에서 Project Chat 캡처를 갱신했을 때, 샘플 프로젝트의 `결제금액 검증은 어디에서 수행되나요?` 질문에 대해 원래 답변이 가능해야 하는데 `현재 검증된 소스 근거만으로는 답변하기 어렵습니다`가 표시됐습니다.

Project Chat status도 Current HEAD가 `-`로 보이고 source_file chunk 70건이 `검증 불가`로 표시됐습니다.

### 직접 원인

DB에 저장된 프로젝트 Git 경로는 Windows host 기준 `C:\dev\ai-advisor-sample-shop`였습니다. 그러나 Docker app 컨테이너는 Linux filesystem에서 실행되므로 해당 경로를 직접 읽을 수 없었습니다.

그 결과 Git HEAD 확인, source_file line 검증, Project Chat source verification이 모두 실패했습니다.

### 배경 또는 구조적 원인

Docker 배포 기능을 추가하면서 PostgreSQL과 Streamlit app 실행은 컨테이너화했지만, 앱이 분석 대상 로컬 Git 저장소를 어떻게 읽을지는 명시하지 않았습니다. 로컬 Python 실행에서는 Windows 경로가 바로 동작했기 때문에 이 차이가 캡처 검증 전까지 드러나지 않았습니다.

### 사전 검증에서 놓친 이유

Docker smoke check는 Streamlit health endpoint와 DB migration 성공만 확인했습니다. Project Chat이 실제 host Git repository file을 읽어 source_file chunk를 검증하는 흐름은 Docker 컨테이너 기준으로 확인하지 않았습니다.

### 수정 내용

Docker app에 host repo mount와 path mapping을 추가했습니다.

```yaml
volumes:
  - C:/dev:/host-dev:ro
environment:
  REPO_PATH_HOST_PREFIX: "C:\\dev"
  REPO_PATH_CONTAINER_PREFIX: /host-dev
```

앱은 DB에 저장된 `C:\dev\...` 경로를 파일 접근 시 `/host-dev/...`로 변환합니다. 이 변환은 Git 명령, source_file 인덱싱, source verification, Project Chat current source 검증에 적용됩니다.

또한 Python slim base image에는 Git binary가 기본 포함되어 있지 않으므로 Dockerfile에 `git` 설치를 추가했습니다. Git Sync와 현재 HEAD 확인은 GitPython만으로는 충분하지 않고 컨테이너 안의 `git` command가 필요합니다.

### 재발 방지 규칙

- Docker 앱에서 RAG 또는 Project Chat을 검증할 때는 health endpoint뿐 아니라 Current HEAD와 source_file verification 상태를 확인합니다.
- DB에 저장된 repo path가 host OS 경로라면 컨테이너 mount와 path prefix mapping이 함께 설정되어야 합니다.
- Project Chat 캡처는 단순 UI 표시뿐 아니라 실제 답변 근거가 정상인지 확인한 뒤 갱신합니다.

### 남은 한계

- 기본 Compose 설정은 `C:/dev` 아래 저장소를 대상으로 합니다. 다른 drive나 directory를 쓰는 환경에서는 mount와 `REPO_PATH_*` 환경 변수를 변경해야 합니다.
- 읽기 전용 mount이므로 컨테이너에서 대상 repo 파일을 수정하는 기능에는 적합하지 않습니다. 현재 Git Sync/RAG/Project Chat 검증은 읽기 작업이므로 충분합니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/utils/config.py src/utils/repo_path.py src/services/git_service.py src/rag/source_verifier.py src/rag/source_index_service.py src/rag/chunker.py
.\.venv\Scripts\python.exe -m pytest tests/test_repo_path.py tests/test_source_file_rag.py tests/test_source_index_service.py tests/test_project_chat_service.py -q
docker compose config
docker compose up -d --build app
```

Docker verification:

- app container can read `/host-dev/ai-advisor-sample-shop`
- Project Chat source index status shows Current HEAD matching Indexed HEAD for the sample project

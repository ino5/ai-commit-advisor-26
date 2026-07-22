# DB 마이그레이션

이 프로젝트는 PostgreSQL schema migration에 Alembic을 사용합니다.

Neo4j Knowledge Graph는 PostgreSQL schema가 아니라 탐색용 read model입니다. Graph node/edge는 `Knowledge Graph` 화면의 동기화 action이 PostgreSQL 분석 데이터와 앱 서버 Git 저장소의 현재 Java 소스 구조를 읽어 다시 구성합니다.

## 마이그레이션 적용

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Streamlit 앱도 `init_db()`를 호출하며, 이 과정에서 Alembic migration이 자동 적용됩니다.

## 기존 로컬 DB 처리

이미 application table이 있지만 `alembic_version`이 없는 DB라면, `init_db()`는 현재 schema를 baseline revision으로 stamp한 뒤 이후 migration을 적용합니다.

Baseline revision:

```text
20260608_0001
```

Baseline 이후 revision은 정상적으로 실행됩니다. 예를 들어 mapping feedback column은 다음 revision에서 관리됩니다.

```text
20260608_0002_add_mapping_feedback
```

현재 주요 후속 revision:

| Revision | 목적 |
|---|---|
| `20260608_0002_add_mapping_feedback` | Mapping 피드백 컬럼 추가 |
| `20260609_0003_add_standard_terms` | 프로젝트별 표준용어/표준단어 테이블 추가 |
| `20260610_0004_add_project_chat_sessions` | Project Chat session/message 저장 테이블 추가 |
| `20260614_0005` | `project_developers` 프로젝트-개발자 연결 테이블 추가 |
| `20260614_0006` | `resource_metric_snapshots` 자원관리 지표 snapshot 테이블 추가 |
| `20260614_0007` | `projects`에 Git remote URL과 branch 필드 추가 |
| `20260615_0008` | `pl_briefing_history` PL Briefing 저장 이력 테이블 추가 |
| `20260615_0009` | `ai_invocation_logs` AI 호출 telemetry 테이블 추가 |
| `20260615_0010` | 프로젝트별 Neo4j graph sync 상태 테이블 추가 |
| `20260722_0011` | Git commit hash unique 범위를 프로젝트 단위로 변경 |

`20260614_0005`는 `developers` 전역 마스터와 `programs.developer_id` 구조를 바꾸지 않고, 프로젝트별 개발자 목록을 위한 연결 테이블만 추가합니다. 기존 프로그램 담당자 연결이 있는 데이터는 migration 중 `project_developers`로 백필되어, 기존 프로젝트의 담당 개발자가 현재 프로젝트 개발자 목록에서 계속 보입니다.

`20260614_0006`은 Dashboard의 자원관리 추세 분석을 위해 `resource_metric_snapshots`를 추가합니다. 이 테이블은 현재 계산된 핵심 지표와 raw summary를 사용자가 저장한 시점별로 보관하며, 프로젝트 삭제 시 함께 삭제됩니다.

`20260614_0007`은 프로젝트/Git 설정에서 서버 저장소 clone/fetch를 실행할 수 있도록 `projects.git_remote_url`, `projects.git_branch`를 추가합니다. 인증 정보는 저장하지 않으며, private repository 접근은 서버 OS의 SSH key나 credential helper 같은 앱 밖의 운영 설정을 사용합니다.

`20260615_0008`은 Dashboard `AI Resource Radar`에서 생성한 PL Briefing을 다시 확인할 수 있도록 `pl_briefing_history`를 추가합니다. 이 테이블은 provider/model/mode, 구조화된 briefing 섹션, 화면 표시용 Markdown, Radar evidence payload, raw LLM response를 저장하며, 프로젝트 삭제나 분석 데이터 초기화 시 함께 삭제됩니다.

`20260615_0009`는 AI 검증과 운영 관측을 위해 `ai_invocation_logs`를 추가합니다. 이 테이블은 Mapping, Project Chat, AI Code Review, PL Briefing 같은 AI 호출의 provider/model, feature, latency, prompt/response length, validation status, fallback/error metadata를 저장하며, 프로젝트 삭제나 분석 데이터 초기화 시 함께 삭제됩니다.

`20260615_0010`은 Neo4j read model의 Repo HEAD, DB sync HEAD, 마지막 commit DB ID, 동기화 상태와 node/edge 수를 프로젝트별로 저장하는 `project_graph_sync_state`를 추가합니다.

`20260722_0011`은 `git_commits.commit_hash`의 전역 unique constraint를 제거하고 기존 `(project_id, commit_hash)` unique constraint만 유지합니다. 같은 remote history를 여러 프로젝트에 수집하면 프로젝트마다 별도 commit/file DB ID가 만들어지며, 한 프로젝트를 다시 수집할 때만 중복으로 처리됩니다. RAG는 `document_chunks.project_id`와 프로젝트별 source DB ID, vector는 chunk FK, Neo4j는 `p{project_id}:` node ID를 이미 사용하므로 별도 schema migration은 추가하지 않습니다.

### `20260722_0011` 적용 전 중복 수집 이력 복구

이 revision은 앞으로의 소유권 이동을 막지만, 이전 Git Sync가 이미 바꾼 `GitCommit.project_id`와 stale 후속 분석을 자동으로 추정 복구하지 않습니다. 같은 저장소를 여러 프로젝트에 전체 수집한 적이 있다면 다음 순서를 사용합니다.

1. PostgreSQL dump를 만들고 복구 가능한 위치와 파일 크기를 확인합니다.
2. 관련 프로젝트를 모두 식별합니다. Mapping의 program project와 commit project가 다른 행, commit/commit_file chunk의 project와 원본 DB ID project가 다른 행이 있으면 영향 대상으로 봅니다.
3. revision `20260722_0011`까지 upgrade합니다.
4. 영향 프로젝트 각각에서 `분석 데이터 초기화`를 실행합니다. 프로젝트 설정, 프로그램/개발계획, 표준용어, 개발자 연결은 유지하고 Git/Mapping/Risk/RAG/vector/저장 AI 결과와 graph sync 상태를 비웁니다.
5. 각 프로젝트에서 Git 전체 수집, Mapping·구현상태·Risk, 전체 source indexing/embedding, Knowledge Graph 전체 동기화를 다시 실행합니다.
6. 같은 hash가 프로젝트별로 다른 `GitCommit.id`와 `p{project_id}:commit:<hash>` node ID를 가지며, 각 프로젝트의 RAG 검색이 자기 chunk만 반환하는지 확인합니다.

서로 다른 프로젝트에 같은 hash가 저장된 뒤 `20260722_0011`을 downgrade하면 전역 unique constraint를 다시 만들 수 없습니다. downgrade가 꼭 필요하면 먼저 어떤 프로젝트 데이터를 보존할지 정하고 중복 hash 행과 후속 데이터를 정리해야 합니다. 자동 병합은 Mapping과 저장 AI 근거의 소유권을 잘못 추정할 수 있으므로 제공하지 않습니다.

## 새 마이그레이션 생성

```powershell
.\.venv\Scripts\alembic.exe revision -m "describe schema change"
```

Schema 변경은 생성된 `migrations/versions/*.py` 파일에 작성합니다. 새 schema-upgrade `ALTER TABLE` 목록을 `src/db/init_db.py`에 추가하지 마세요.

## Neo4j graph 변경 기준

Neo4j에 저장하는 node, edge, property, constraint를 바꿀 때는 Alembic migration을 만들지 않습니다. 대신 다음 기준을 따릅니다.

- PostgreSQL 원본 schema가 바뀌면 Alembic migration을 추가합니다.
- Neo4j sync 상태처럼 PostgreSQL에 저장하는 metadata table이나 column이 필요하면 Alembic migration을 추가합니다.
- Neo4j graph projection만 바뀌면 `src/services/neo4j_graph_service.py`와 관련 테스트를 수정하고, 기존 graph는 `Knowledge Graph` 화면에서 다시 동기화합니다.
- Neo4j constraint는 동기화 시점에 `CREATE CONSTRAINT ... IF NOT EXISTS`로 준비합니다.
- 프로젝트 분석 데이터 초기화나 프로젝트 삭제는 `NEO4J_ENABLED=true`인 경우 선택 프로젝트의 Neo4j node를 best-effort로 정리합니다.
- 운영 환경에서 Neo4j 비밀번호, database, volume 정책을 바꾸는 작업은 migration이 아니라 배포/운영 변경으로 기록합니다.

이 분리는 PostgreSQL을 source of truth로 유지하고, Neo4j를 관계 탐색과 Project Chat GraphRAG 보조 근거를 위한 재생성 가능한 read model로 다루기 위한 결정입니다.

## 현재 Revision 확인

```powershell
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe heads
```

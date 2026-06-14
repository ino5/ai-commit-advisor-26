# DB 마이그레이션

이 프로젝트는 PostgreSQL schema migration에 Alembic을 사용합니다.

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

`20260614_0005`는 `developers` 전역 마스터와 `programs.developer_id` 구조를 바꾸지 않고, 프로젝트별 개발자 목록을 위한 연결 테이블만 추가합니다. 기존 프로그램 담당자 연결이 있는 데이터는 migration 중 `project_developers`로 백필되어, 기존 프로젝트의 담당 개발자가 현재 프로젝트 개발자 목록에서 계속 보입니다.

`20260614_0006`은 Dashboard의 자원관리 추세 분석을 위해 `resource_metric_snapshots`를 추가합니다. 이 테이블은 현재 계산된 핵심 지표와 raw summary를 사용자가 저장한 시점별로 보관하며, 프로젝트 삭제 시 함께 삭제됩니다.

`20260614_0007`은 프로젝트/Git 설정에서 서버 저장소 clone/fetch를 실행할 수 있도록 `projects.git_remote_url`, `projects.git_branch`를 추가합니다. 인증 정보는 저장하지 않으며, private repository 접근은 서버 OS의 SSH key나 credential helper 같은 앱 밖의 운영 설정을 사용합니다.

`20260615_0008`은 Dashboard `AI Resource Radar`에서 생성한 PL Briefing을 다시 확인할 수 있도록 `pl_briefing_history`를 추가합니다. 이 테이블은 provider/model/mode, 구조화된 briefing 섹션, 화면 표시용 Markdown, Radar evidence payload, raw LLM response를 저장하며, 프로젝트 삭제나 분석 데이터 초기화 시 함께 삭제됩니다.

`20260615_0009`는 AI Evidence와 운영 관측을 위해 `ai_invocation_logs`를 추가합니다. 이 테이블은 Mapping, Project Chat, AI Code Review, PL Briefing 같은 AI 호출의 provider/model, feature, latency, prompt/response length, validation status, fallback/error metadata를 저장하며, 프로젝트 삭제나 분석 데이터 초기화 시 함께 삭제됩니다.

## 새 마이그레이션 생성

```powershell
.\.venv\Scripts\alembic.exe revision -m "describe schema change"
```

Schema 변경은 생성된 `migrations/versions/*.py` 파일에 작성합니다. 새 schema-upgrade `ALTER TABLE` 목록을 `src/db/init_db.py`에 추가하지 마세요.

## 현재 Revision 확인

```powershell
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe heads
```

# 설치와 운영

이 문서는 AI Commit Advisor의 설치, 실행, 환경 변수, DB migration, LLM/embedding 운영 기준을 정리합니다.

## 실행 환경

- Python 3.11 이상
- Docker Desktop
- PostgreSQL + pgvector
- 선택: LM Studio 또는 OpenAI-compatible 로컬 LLM/embedding 서버

## 설치 및 실행

### 1. 환경 파일 생성

가볍게 앱 흐름만 확인하려면 mock 설정을 사용합니다.

```powershell
Copy-Item .env.example .env
```

실제 LLM/RAG/Project Chat 품질을 검증하려면 로컬 LLM 설정 예시를 사용합니다.

```powershell
Copy-Item .env.local-llm.example .env
```

local LLM 모드에서는 LM Studio에서 chat 모델과 embedding 모델을 먼저 로드해야 합니다. `.env`를 바꾼 뒤에는 Streamlit 앱을 재시작해야 합니다.

### 2. PostgreSQL + pgvector 실행

```powershell
docker compose up -d
```

### 3. Python 가상환경 준비

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

cmd.exe:

```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

이미 `.venv`가 만들어져 있으면 활성화만 하면 됩니다.

### 4. DB 초기화 및 마이그레이션

```powershell
python -m src.db.init_db
```

DB schema는 Alembic migration으로 관리됩니다. 빈 DB는 최신 migration까지 생성되고, 기존 DB에 `alembic_version`이 없으면 현재 schema를 baseline으로 stamp한 뒤 이후 migration만 적용합니다.

직접 migration을 실행하려면:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

자세한 내용은 [DB Migrations](db-migrations.md)를 참고하세요.

### 5. Streamlit 실행

```powershell
streamlit run app.py
```

가상환경 활성화 없이 실행하려면:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Docker 앱 배포

### 도입 배경과 기대 효과

기존 실행 방식은 PostgreSQL은 Docker Compose로 띄우고 Streamlit 앱은 로컬 Python 가상환경에서 직접 실행하는 흐름이었습니다. 이 방식은 개발 중에는 빠르지만, 다른 환경에서 재현하거나 서버에 올릴 때 Python 버전, 패키지 설치, DB 접속 주소, migration 적용 방식이 사람마다 달라질 수 있습니다.

앱 Dockerfile과 Compose `app` service는 이 차이를 줄이기 위해 추가했습니다. 목표는 다음과 같습니다.

- 처음 실행하는 사람도 `docker compose up`만으로 PostgreSQL + Streamlit 앱 조합을 재현합니다.
- 서버 배포 시 앱 시작 전에 DB schema 초기화와 Alembic migration을 같은 방식으로 실행합니다.
- mock LLM/embedding 기본값으로 먼저 화면과 DB 연결을 확인한 뒤, 필요할 때 local/OpenAI-compatible provider로 전환합니다.
- 배포 후 health endpoint로 최소 기동 상태를 빠르게 확인합니다.

### Compose 전체 실행

기본 Compose 실행은 PostgreSQL과 Streamlit 앱을 함께 띄웁니다.

```powershell
docker compose up -d --build
```

앱은 `http://localhost:8501`에서 열립니다. Compose의 `app` service는 `postgres` healthcheck가 통과한 뒤 시작됩니다.

실행 상태 확인:

```powershell
docker compose ps
```

로그 확인:

```powershell
docker compose logs app
```

종료:

```powershell
docker compose down
```

DB volume까지 삭제해 깨끗한 상태로 다시 시작해야 할 때만 다음 명령을 사용합니다.

```powershell
docker compose down -v
```

### 앱 이미지 단독 빌드

Compose 없이 이미지 빌드만 확인하려면 다음 명령을 사용합니다.

```powershell
docker build -t ai-commit-advisor:local .
```

### Docker 환경 변수

`docker-compose.yml`의 `app.environment`는 컨테이너 내부 실행 기준입니다. 로컬 Python 실행의 `.env`와 달리 DB host는 `127.0.0.1`이 아니라 Compose service 이름인 `postgres`를 사용합니다.

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://ai_user:ai_password@postgres:5432/ai_commit_advisor` | 앱 컨테이너가 Compose PostgreSQL에 접속하는 SQLAlchemy URL입니다. |
| `PGVECTOR_DIMENSION` | `1536` | 새 DB에서 `vector_items.embedding` column을 만들 때 사용할 vector 차원입니다. 실제 embedding 모델 차원과 같아야 합니다. |
| `LLM_PROVIDER` | `mock` | 기본은 외부 LLM 없이 동작 확인이 가능한 mock입니다. |
| `LLM_BASE_URL` | `http://host.docker.internal:1234/v1` | 컨테이너에서 Windows host의 LM Studio에 접근할 때 쓰는 OpenAI-compatible base URL입니다. |
| `LLM_API_KEY` | 빈 값 | local LM Studio는 보통 비워 둡니다. |
| `LLM_MODEL` | `qwen2.5-coder-7b-instruct` | local/OpenAI-compatible provider 전환 시 사용할 chat model 이름입니다. |
| `EMBEDDING_PROVIDER` | `mock` | 기본은 mock embedding입니다. 실제 RAG 품질 검증 시 `local_openai` 등으로 바꿉니다. |
| `EMBEDDING_BASE_URL` | `http://host.docker.internal:1234/v1` | 컨테이너에서 Windows host의 embedding server에 접근할 때 쓰는 base URL입니다. |
| `EMBEDDING_API_KEY` | 빈 값 | local embedding server는 보통 비워 둡니다. |
| `EMBEDDING_MODEL` | `text-embedding-nomic-embed-text-v1` | 실제 embedding provider 전환 시 사용할 embedding model 이름입니다. |
| `PORT` | `8501` | Dockerfile의 Streamlit 실행 port입니다. Compose는 host `8501`을 container `8501`에 연결합니다. |

실제 LM Studio를 Compose 앱에서 사용하려면 provider를 바꿉니다.

```yaml
LLM_PROVIDER: local_openai
EMBEDDING_PROVIDER: local_openai
PGVECTOR_DIMENSION: "768"
```

`PGVECTOR_DIMENSION`은 embedding 모델 출력 차원과 반드시 맞춰야 합니다. 이미 다른 차원으로 DB가 만들어진 뒤에는 단순 환경 변수 변경만으로 기존 `vector_items.embedding` column 차원이 바뀌지 않습니다. 이 경우 새 DB volume으로 다시 시작하거나 schema migration 전략을 별도로 잡아야 합니다.

### Migration 시작 동작

Dockerfile의 기본 command는 앱 시작 전에 다음 순서로 실행됩니다.

```text
python -m src.db.init_db
streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT}
```

`src.db.init_db`는 PostgreSQL 연결을 확인한 뒤 Alembic migration을 최신 revision까지 적용합니다. 빈 DB에는 현재 schema를 만들고, 기존 DB에는 `alembic_version` 상태를 기준으로 누락 migration만 적용합니다. 따라서 Compose 배포에서는 앱 컨테이너가 시작될 때 schema 초기화와 migration 적용이 자동으로 수행됩니다.

운영 중 migration 실패가 보이면 먼저 `docker compose logs app`에서 실패 revision과 DB 접속 정보를 확인하세요. schema 변경은 `migrations/versions/`의 Alembic migration으로 관리해야 하며, `src/db/init_db.py`에 임의 `ALTER TABLE` 목록을 추가하지 않습니다.

### 배포 스모크 체크

앱과 DB가 함께 정상 기동했는지 확인하는 최소 절차입니다.

```powershell
docker compose up -d --build
docker compose ps
```

PostgreSQL healthcheck:

```powershell
docker exec ai_commit_advisor_postgres pg_isready -U ai_user -d ai_commit_advisor
```

Streamlit health endpoint:

```powershell
Invoke-WebRequest http://localhost:8501/_stcore/health -UseBasicParsing
```

정상이라면 Streamlit health endpoint가 HTTP 200 응답을 반환합니다. 이후 브라우저에서 `http://localhost:8501`을 열어 Home 화면이 표시되는지 확인합니다.

## LLM 설정

기본 `.env.example`은 mock입니다. 실제 LLM 호출 없이 동작 확인용 fallback 결과를 생성합니다.

```env
LLM_PROVIDER=mock
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_API_KEY=
LLM_MODEL=exaone-3.5-2.4b-instruct
```

LM Studio를 사용할 경우 `.env.local-llm.example`을 복사하거나 `.env`를 아래처럼 설정합니다.

1. LM Studio에서 모델을 로드합니다.
2. Local Server를 켭니다.
3. 서버 주소가 `http://127.0.0.1:1234`인지 확인합니다.
4. `.env`를 아래처럼 설정합니다.

```env
LLM_PROVIDER=local_openai
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_API_KEY=
LLM_MODEL=qwen2.5-coder-7b-instruct
```

일부 모델은 LM Studio prompt template 문제로 `prediction-error` 또는 Jinja template 오류가 날 수 있습니다. 이 경우 `lmstudio-community` 모델을 사용하거나 해당 모델의 Prompt Template을 수정하세요.

## Embedding / RAG 설정

기본값은 mock embedding입니다. 실제 검색 품질을 보려면 OpenAI-compatible embedding 서버를 사용하세요.

```env
EMBEDDING_PROVIDER=local_openai
EMBEDDING_BASE_URL=http://127.0.0.1:1234/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
PGVECTOR_DIMENSION=768
```

LM Studio를 사용할 경우 embedding 모델을 로드하고 Local Server를 켠 뒤, RAG 화면의 `Embedding 연결 테스트`로 `/v1/embeddings` 응답과 vector dimension을 확인합니다. `PGVECTOR_DIMENSION`은 사용하는 embedding 모델의 출력 차원과 같아야 하며, 이미 다른 차원으로 생성된 `vector_items.embedding` 컬럼은 DB를 새로 만들거나 migration해야 합니다.

mock embedding으로 생성된 vector는 local_openai embedding 검색에 사용되지 않습니다. `LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `PGVECTOR_DIMENSION`을 바꾼 뒤에는 현재 모델 기준으로 embedding을 다시 생성해야 RAG Search와 Project Chat이 같은 근거를 검색할 수 있습니다.

Project Chat을 실제 LLM 모드로 검증하는 권장 순서:

1. LM Studio에서 chat 모델과 embedding 모델을 로드합니다.
2. `Copy-Item .env.local-llm.example .env`로 local LLM 설정을 적용합니다.
3. Streamlit 앱을 재시작합니다.
4. RAG 검색 화면에서 `Embedding 연결 테스트`를 실행합니다.
5. RAG 검색 화면의 Embedding 영역에서 source_file chunk의 embedding을 생성합니다.
6. Project Chat에서 질문하고 `답변 근거 보기`를 펼쳐 현재 소스 근거를 확인합니다.
7. 답변을 기록으로 남겨야 하면 `근거 복사용 Markdown` 내용을 회의록, 리뷰 문서, 이슈에 붙여 넣습니다.

## source_file 재인덱싱 운영 주의사항

LM Studio 같은 로컬 embedding 서버는 한 번에 많은 chunk를 처리하면 CPU/GPU와 메모리를 오래 점유할 수 있습니다. 그래서 현재 소스 재인덱싱과 embedding 생성을 분리합니다.

- `RAG 검색 > 최근 Git sync 변경 파일만 인덱싱`: 최근 indexed HEAD 이후 Git Sync가 DB에 저장한 changed file path만 source_file chunk로 갱신합니다. 일반적인 개발 흐름에서는 이 버튼을 먼저 사용합니다. embedding은 자동 실행하지 않습니다.
- `Project Chat > 최근 Git sync 변경 파일만 인덱싱`: Chat 화면에서 같은 증분 인덱싱을 실행합니다. 답변 전 source index 상태가 오래되었을 때 빠르게 최신 sync 변경분만 반영할 수 있습니다.
- `Project Chat > 현재 소스 다시 인덱싱`: 현재 HEAD 기준으로 source_file chunk만 갱신합니다. embedding은 자동 실행하지 않습니다.
- `RAG 검색 > 현재 소스 다시 인덱싱`: 기본값은 chunk 갱신만 수행합니다. `재인덱싱 후 embedding도 바로 생성`을 직접 체크한 경우에만 제한 수량으로 embedding을 생성합니다.
- `RAG 검색 > Embedding`: 남은 pending chunk를 별도로 처리할 때 사용합니다. 화면에서 남은 작업 수와 예상 소요 시간을 확인한 뒤 여러 번 나눠 실행하세요.

### 증분 인덱싱과 전체 재인덱싱 선택 기준

| 상황 | 권장 action | 이유 |
|---|---|---|
| Git Sync로 최신 commit을 가져온 직후 | `최근 Git sync 변경 파일만 인덱싱` | 변경된 파일만 읽으므로 대형 repo에서도 빠르고 embedding 비용이 자동 발생하지 않습니다. |
| 특정 파일 수정, 삭제, rename만 반영하면 되는 경우 | `최근 Git sync 변경 파일만 인덱싱` | `Added`, `Modified`, `Deleted`, `Renamed` path만 chunk 교체/삭제합니다. |
| 처음 source_file index를 만드는 경우 | `현재 소스 다시 인덱싱` | 기준 chunk가 없으면 전체 source file scan이 필요합니다. |
| branch를 크게 바꾸었거나 include/exclude/chunking rule이 바뀐 경우 | `현재 소스 다시 인덱싱` | 최근 commit file 목록만으로는 전체 repository snapshot을 보정하기 어렵습니다. |
| stale/invalid chunk가 많이 보이거나 삭제된 파일이 계속 evidence에 나타나는 경우 | `현재 소스 다시 인덱싱` | 전체 scan과 검증 cleanup으로 오래된 chunk/vector를 정리합니다. |
| chunk는 최신인데 검색 결과가 없거나 embedding model을 바꾼 경우 | `RAG 검색 > Embedding` | 현재 model 기준 missing vector만 제한 수량으로 생성해야 합니다. |

증분 인덱싱의 처리 방식은 다음과 같습니다.

1. 화면에서 현재 `Current HEAD`, `Indexed HEAD`, stale/invalid chunk 수를 확인합니다.
2. Git Sync가 최신 commit을 저장한 상태라면 `최근 Git sync 변경 파일만 인덱싱`을 실행합니다.
3. app은 최근 indexed HEAD 이후 DB에 저장된 `CommitFile` row를 읽습니다.
4. source-like text/code file만 chunk 대상으로 삼고, binary/image/Excel/cache/virtualenv/oversized file은 건너뜁니다.
5. 수정된 파일은 기존 path chunk와 vector를 제거한 뒤 새 chunk를 만들고 `embedding_status=pending`으로 둡니다.
6. 삭제된 파일은 해당 path의 chunk와 vector를 제거합니다.
7. rename은 old path를 제거하고 new path가 source-like file이면 새 chunk를 만듭니다.
8. 검색 품질 확인이 필요하면 `RAG 검색 > Embedding`에서 pending chunk를 작은 limit으로 나누어 처리합니다.

중요한 비용 제어 규칙:

- Git Sync는 commit/diff metadata만 저장하며 embedding API를 호출하지 않습니다.
- `최근 Git sync 변경 파일만 인덱싱`은 chunk만 갱신하며 embedding API를 호출하지 않습니다.
- Project Chat의 source index 버튼도 embedding API를 호출하지 않습니다.
- embedding API 호출은 `RAG 검색 > Embedding` 또는 RAG Index 화면에서 사용자가 명시적으로 선택한 제한 수량에서만 발생합니다.
- embedding provider/model/dimension을 바꾸면 기존 vector를 조용히 재사용하지 말고 현재 model 기준 missing vector를 다시 생성하세요.

Project Chat 대화는 프로젝트별 DB session으로 저장됩니다. `새 대화`와 `대화 초기화`는 기존 이력을 삭제하지 않고 새 session을 만들며, 이전 session은 `대화 이력`에서 다시 선택할 수 있습니다.

재인덱싱이나 embedding 중 앱 또는 LM Studio를 강제 종료하면 PostgreSQL은 열린 transaction을 롤백합니다. 다만 이미 commit된 chunk/vector와 아직 처리되지 않은 chunk가 섞여 `pending` 또는 `failed` 상태가 남을 수 있습니다. 이 상태는 부분 완료 상태이며, RAG 화면에서 인덱스 상태를 확인한 뒤 embedding을 제한 수량으로 이어서 실행하면 됩니다.

강제 종료 후 상태 점검 예시:

```powershell
docker exec ai_commit_advisor_postgres pg_isready -U ai_user -d ai_commit_advisor
```

```powershell
@'
from sqlalchemy import text
from src.db.database import SessionLocal

with SessionLocal() as db:
    for name, sql in {
        "source_file_chunks": "select count(*) from document_chunks where source_type = 'source_file'",
        "source_file_vectors": "select count(*) from vector_items v join document_chunks c on c.id = v.chunk_id where c.source_type = 'source_file'",
        "orphan_vectors": "select count(*) from vector_items v left join document_chunks c on c.id = v.chunk_id where c.id is null",
    }.items():
        print(f"{name}: {db.execute(text(sql)).scalar()}")

    rows = db.execute(text("""
        select coalesce(raw_metadata->>'embedding_status', 'null') as status, count(*)
        from document_chunks
        where source_type = 'source_file'
        group by 1
        order by 1
    """)).all()
    for status, count in rows:
        print(f"{status}: {count}")
'@ | .\.venv\Scripts\python.exe -
```

`orphan_vectors`가 0이면 vector가 없는 chunk는 있어도 참조가 깨진 vector는 없는 상태입니다. `pending`은 아직 embedding이 생성되지 않은 chunk, `failed`는 embedding 호출 실패가 기록된 chunk입니다.

## 로컬 검증 명령

```powershell
.\.venv\Scripts\python.exe -m compileall src app.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "from src.db.init_db import init_db; init_db(); print('init ok')"
streamlit run app.py
```

GitHub Actions의 `CI` workflow도 기본 검증으로 `python -m compileall src app.py`와 `python -m pytest -q`를 실행합니다.

Home 화면 문구와 기본 렌더링을 확인하려면 Streamlit 실행 후 아래 명령을 사용합니다. Chromium 브라우저가 없으면 먼저 `.\.venv\Scripts\python.exe -m playwright install chromium`을 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\verify_home_ui.py
```

검증이 끝나면 `.tmp/home-ui-check.png`에 캡처가 생성됩니다.

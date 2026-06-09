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

## source_file 재인덱싱 운영 주의사항

LM Studio 같은 로컬 embedding 서버는 한 번에 많은 chunk를 처리하면 CPU/GPU와 메모리를 오래 점유할 수 있습니다. 그래서 현재 소스 재인덱싱과 embedding 생성을 분리합니다.

- `Project Chat > 현재 소스 다시 인덱싱`: 현재 HEAD 기준으로 source_file chunk만 갱신합니다. embedding은 자동 실행하지 않습니다.
- `RAG 검색 > 현재 소스 다시 인덱싱`: 기본값은 chunk 갱신만 수행합니다. `재인덱싱 후 embedding도 바로 생성`을 직접 체크한 경우에만 제한 수량으로 embedding을 생성합니다.
- `RAG 검색 > Embedding`: 남은 pending chunk를 별도로 처리할 때 사용합니다. 화면에서 남은 작업 수와 예상 소요 시간을 확인한 뒤 여러 번 나눠 실행하세요.

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

# AI Commit Advisor

로컬 Git 저장소의 커밋, 변경 파일, diff를 수집하고 프로그램 목록과 비교해 프로그램-커밋 매핑 후보를 추천하는 Streamlit 기반 PoC입니다.

현재 버전은 mock 분석과 OpenAI-compatible 로컬 LLM 서버를 지원합니다. LM Studio 같은 로컬 LLM 서버를 연결하면 Mapping, Code Review, Project Chat 화면에서 실제 LLM 기반 분석을 실행할 수 있습니다.

AI 지원 변경 이력은 `AI_CHANGELOG.md`에 기록합니다. 코딩 에이전트 작업 규칙은 `AGENTS.md`를 참고하세요.

AI 기술 활용 방식과 대외 소개용 흐름은 `docs/ai-technical-overview.md`에 정리되어 있습니다.

## AI / LLM 활용 흐름

AI Commit Advisor는 개발계획, Git 변경 이력, 현재 소스 코드를 하나의 분석 흐름으로 연결합니다. LLM은 판단이 필요한 비교/요약/리뷰에 사용하고, RAG와 규칙 분석은 근거 검색과 일관된 리스크 탐지에 사용합니다.

| 단계 | 입력 데이터 | AI/LLM 활용 | 결과 |
|---|---|---|---|
| Git 수집 | commit message, author, changed files, diff | 분석 대상 변경 이력 구성 | `git_commits`, `commit_files` 저장 |
| RAG 인덱싱 | 현재 소스 파일, 프로그램 정보, 커밋 메시지, diff | embedding 생성 후 pgvector 검색 기반 구축, 현재 HEAD와 인덱스 상태 비교 | `document_chunks`, `vector_items` 저장 |
| 프로그램-커밋 매핑 | 프로그램 목록, 커밋, 변경 파일, RAG 후보 | LLM이 관련 프로그램과 구현상태를 판단 | 관련도, 구현상태, 판단 근거 저장 |
| 구현상태 분석 | 프로그램 계획, 관련 커밋, 매핑 결과 | LLM이 프로그램 단위 구현 상태를 요약 | NOT_STARTED / IN_PROGRESS / COMPLETED / UNKNOWN |
| Project Chat | 현재 소스 검색 결과 | LLM이 검증된 소스 근거로 질문에 답변 | 파일 경로와 라인 근거가 포함된 답변 |
| AI Code Review | working tree, staged diff, commit diff | LLM이 변경 의도, 위험, 버그, 리팩토링 포인트 분석 | 리뷰 요약, 버그 후보, 개선 제안 |
| Risk Analysis | 일정, 진척도, 커밋 활동, AI 매핑 결과 | 규칙 기반으로 누락/지연/불확실성 탐지 | 위험 프로그램과 evidence 저장 |

Project Chat은 현재 파일 내용과 일치하는 소스 chunk만 기본 근거로 사용합니다. 커밋 diff는 변경 이력으로 취급하며 현재 코드 근거와 구분합니다. RAG와 Project Chat 화면에서는 현재 Git HEAD와 인덱싱 시점 HEAD를 비교해 재인덱싱 필요 여부를 보여주고, 버튼 한 번으로 현재 소스 chunk를 다시 만들 수 있습니다. embedding 생성은 PC 부하를 줄이기 위해 별도 실행하거나 제한 수량으로만 실행합니다.

## 화면 미리보기

![AI Commit Advisor dashboard](docs/images/ai-commit-advisor-home.png)

## 기능별 화면 캡처

아래 캡처는 그룹형 사이드바 메뉴와 현재 화면 구성을 기준으로 갱신한 데스크톱 화면입니다.

<details>
<summary>Home</summary>

개발계획, Git 변경 이력, AI 매핑 결과, 리스크를 통합해 분석 상태를 확인하는 관제 화면입니다. 분석 파이프라인 상태와 다음 권장 작업을 함께 표시해 업무 흐름상 필요한 후속 작업을 판단할 수 있습니다.

![Home](docs/images/features/home.png)

</details>

<details>
<summary>Project</summary>

![Project](docs/images/features/project.png)

</details>

<details>
<summary>Developer</summary>

![Developer](docs/images/features/developer.png)

</details>

<details>
<summary>Program Detail</summary>

![Program Detail](docs/images/features/program-detail.png)

</details>

<details>
<summary>개발자 목록 업로드</summary>

![Developer Upload](docs/images/features/developer-upload.png)

</details>

<details>
<summary>프로그램 목록 업로드</summary>

![Program Upload](docs/images/features/program-upload.png)

</details>

<details>
<summary>개발계획 업로드</summary>

![Development Plan Upload](docs/images/features/development-plan-upload.png)

</details>

<details>
<summary>Git 동기화</summary>

![Git Sync](docs/images/features/git-sync.png)

</details>

<details>
<summary>샘플 데이터 생성</summary>

![Sample Data](docs/images/features/sample-data.png)

</details>

<details>
<summary>Mapping</summary>

![Mapping](docs/images/features/mapping.png)

</details>

<details>
<summary>Risk Analysis</summary>

![Risk Analysis](docs/images/features/risk-analysis.png)

</details>

<details>
<summary>Commit Impact</summary>

![Commit Impact](docs/images/features/commit-impact.png)

</details>

<details>
<summary>RAG 검색</summary>

![RAG Search](docs/images/features/rag-search.png)

</details>

<details>
<summary>AI Code Review</summary>

![AI Code Review](docs/images/features/ai-code-review.png)

</details>

<details>
<summary>Dashboard</summary>

![Dashboard](docs/images/features/dashboard.png)

</details>

<details>
<summary>개발계획 대시보드</summary>

![Planning Dashboard](docs/images/features/planning-dashboard.png)

</details>

<details>
<summary>AI Progress</summary>

![AI Progress](docs/images/features/ai-progress.png)

</details>

<details>
<summary>설정</summary>

![Settings](docs/images/features/settings.png)

</details>

## 주요 기능

- 프로젝트 등록 및 로컬 Git 저장소 경로 관리
- Git 저장소 전체 커밋 수집 및 증분 동기화
- 커밋별 변경 파일과 diff 저장
- 개발자 관리: Git author 기반 자동 추출, 현재 데이터 검색, 직접 추가/수정/삭제, Excel 양식 다운로드, 업로드 전 검증
- 프로그램 관리: 현재 데이터 검색, 직접 추가/수정/삭제, Excel 양식 다운로드, 업로드 전 검증/미리보기, 신규/수정 요약
- 개발계획 관리: 현재 계획 조회, 직접 수정, 일괄 업데이트, Excel 양식 다운로드, 업로드 전 검증
- 프로그램 상세 분석 화면: 특정 프로그램의 계획, AI 진척도, 관련 커밋, 개발자 기여, 리스크 확인
- 커밋 영향도 분석 화면: 특정 커밋이 영향을 주는 프로그램, 개발자, 모듈, 파일 확인
- 누락/위험 프로그램 자동 탐지: 계획, Git 커밋, LLM 매핑 결과 기반 규칙 분석
- 커밋 기준 프로그램-커밋 매핑 분석
- 기존 프로그램 기준 매핑 분석 유지
- 검증형 RAG 기반 Project Chat: 현재 소스 파일 근거로 프로젝트 질의응답
- RAG 검색: 현재 소스 파일, 프로그램 정보, 커밋 메시지, 변경 파일/diff 검색
- 현재 소스 인덱스 상태 확인: Current HEAD, Indexed HEAD, 불일치/검증 불가 chunk 수 표시와 원클릭 chunk 재인덱싱
- 실시간 AI 코드리뷰: 작업트리, staged 변경, 최신 커밋, 특정 커밋 분석
- 코드리뷰 버그 탐지, 리팩토링 제안, 리뷰 기록 저장
- 개발계획 대시보드 및 개발자 통계 대시보드
- AI Progress: 계획 진척도, 매핑 기반 AI 진척도, 저장된 프로그램 단위 구현상태 분석 요약 비교
- 그룹형 사이드바 메뉴: 업무 흐름별 화면 이동과 현재 위치 표시
- 테스트용 샘플 Excel 데이터 생성

## 실행 환경

- Python 3.11 이상
- Docker Desktop
- PostgreSQL + pgvector
- 선택: LM Studio 또는 OpenAI-compatible 로컬 LLM 서버

## 기술 스택

아래 내용은 현재 저장소의 `requirements.txt`, `docker-compose.yml`, `.env.example`, `app.py`, `src` 코드 구조를 기준으로 정리했습니다.

### Backend

- 사용 중: Python 기반 애플리케이션
- 사용 중: SQLAlchemy ORM (`src/db/database.py`, `src/db/models.py`)
- 사용 중: `python-dotenv`, `pydantic-settings` 기반 환경 설정 (`src/utils/config.py`)
- 사용 중: Git 데이터 수집 및 코드리뷰 대상 추출은 Python `subprocess`로 Git CLI를 호출 (`src/services/git_service.py`, `src/services/code_review_service.py`)
- 설치됨/예정: `GitPython`은 `requirements.txt`에 설치되어 있으나 현재 코드에서는 직접 import되지 않습니다.

### Frontend / UI

- 사용 중: Streamlit 단일 앱 (`app.py`, `src/ui`)
- 사용 중: pandas 기반 테이블/데이터 가공 (`src/ui`, `src/services/excel_service.py`)
- 사용 중: Plotly Express 기반 대시보드 차트 (`src/ui/dashboard_page.py`, `src/ui/risk_page.py` 등)

### Database

- 사용 중: PostgreSQL (`DATABASE_URL=postgresql+psycopg2://...`)
- 사용 중: SQLAlchemy + `psycopg2-binary`
- 사용 중: JSONB, 관계형 테이블, pgvector Vector 컬럼 (`src/db/models.py`)
- 사용 중: Alembic 기반 DB migration (`alembic.ini`, `migrations/versions`)

### AI / LLM / Embedding

- 사용 중: mock LLM provider (`LLM_PROVIDER=mock`)
- 사용 중: OpenAI-compatible 로컬 LLM HTTP API (`local_openai`, `/chat/completions`) (`src/services/llm_client.py`)
- 사용 중: mock embedding provider (`EMBEDDING_PROVIDER=mock`)
- 사용 중: OpenAI-compatible embedding HTTP API (`openai`, `local`, `local_openai`, `/embeddings`) (`src/rag/embedding_client.py`)
- 사용 중: 별도 LLM SDK 없이 Python 표준 라이브러리 `urllib`로 HTTP 호출
- 사용 중/선택: LM Studio 같은 로컬 OpenAI-compatible embedding 서버 연동 (`.env.example`, RAG 화면의 연결 테스트)

### Vector Store / Search

- 사용 중: PostgreSQL pgvector 확장 (`docker-compose.yml`, `src/db/init_db.py`)
- 사용 중: `pgvector.sqlalchemy.Vector` 임베딩 컬럼 (`src/db/models.py`)
- 사용 중: cosine distance 기반 유사도 검색 (`src/rag/vector_store.py`)
- 사용 중: 현재 소스 파일, 프로그램 정보, 커밋 메시지, 변경 파일/diff를 chunk로 구성하고 embedding 저장 (`src/rag/chunker.py`, `src/ui/rag_page.py`)
- 사용 중: 현재 소스 chunk의 file path, line range, content hash, indexed HEAD hash 메타데이터 저장
- 사용 중: 검색 결과 source_file chunk가 현재 파일과 일치하는지 검증 (`src/rag/source_verifier.py`)
- 사용 중: RAG Search 화면에서 검색어, 조회 chunk 목록, 유사도 점수, 출처, 원문 일부 표시
- 사용 중: Project Chat 화면에서 검증된 현재 소스 chunk만 기본 근거로 사용해 질의응답
- 사용 중: RAG Search와 Project Chat 화면에서 현재 소스 인덱스 상태 확인 및 원클릭 재인덱싱

### Infrastructure / Deployment

- 사용 중: Docker Compose로 PostgreSQL + pgvector 실행 (`docker-compose.yml`)
- 사용 중: `pgvector/pgvector:pg16` Docker 이미지
- 사용 중: 로컬 Streamlit 실행 (`streamlit run app.py`)
- 현재 없음: 애플리케이션용 `Dockerfile`, `package.json`, 프론트엔드 빌드 설정은 저장소에 없습니다.

### Development Tools

- 사용 중: `requirements.txt` 기반 Python 의존성 관리
- 사용 중: `.env.example` 기반 로컬 환경 변수 템플릿
- 사용 중: `openpyxl` 기반 Excel 업로드/샘플 파일 생성 (`src/services/excel_service.py`, `src/ui/sample_data_page.py`)
- 사용 중: 샘플 데이터 생성 스크립트 (`scripts/generate_sample_development_data.py`)

## 설치 및 실행

### 1. 환경 파일 생성

```powershell
Copy-Item .env.example .env
```

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

DB 스키마는 Alembic migration으로 관리됩니다. 빈 DB는 최신 migration까지 생성되고, 기존 DB에 `alembic_version`이 없으면 현재 스키마를 baseline으로 stamp한 뒤 이후 migration만 적용합니다.

직접 migration을 실행하려면:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

자세한 내용은 `docs/db-migrations.md`를 참고하세요.

### 5. Streamlit 실행

```powershell
streamlit run app.py
```

가상환경 활성화 없이 실행하려면:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## LLM 설정

기본값은 mock입니다. 실제 LLM 호출 없이 규칙 기반 fallback 결과를 생성합니다.

```env
LLM_PROVIDER=mock
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_API_KEY=
LLM_MODEL=exaone-3.5-2.4b-instruct
```

LM Studio를 사용할 경우:

1. LM Studio에서 모델을 로드합니다.
2. Local Server를 켭니다.
3. 서버 주소가 `http://127.0.0.1:1234`인지 확인합니다.
4. `.env`를 아래처럼 설정합니다.

```env
LLM_PROVIDER=local_openai
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_API_KEY=
LLM_MODEL=exaone-3.5-2.4b-instruct
```

일부 모델은 LM Studio의 prompt template 문제로 `prediction-error` 또는 Jinja template 오류가 날 수 있습니다. 이 경우 `lmstudio-community` 모델을 사용하거나 해당 모델의 Prompt Template을 수정하세요.

## Embedding / RAG 설정

기본값은 mock embedding입니다. 실제 검색 품질을 보려면 OpenAI-compatible embedding 서버를 사용하세요.

```env
EMBEDDING_PROVIDER=local_openai
EMBEDDING_BASE_URL=http://127.0.0.1:1234/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1
PGVECTOR_DIMENSION=768
```

LM Studio를 사용할 경우 embedding 모델을 로드하고 Local Server를 켠 뒤, RAG 화면의 `Embedding 연결 테스트`로 `/v1/embeddings` 응답과 vector dimension을 확인합니다. `PGVECTOR_DIMENSION`은 사용하는 embedding 모델의 출력 차원과 같아야 하며, 이미 다른 차원으로 생성된 `vector_items.embedding` 컬럼은 DB를 새로 만들거나 마이그레이션해야 합니다.

RAG 화면의 `RAG 인덱싱 실행`은 다음 데이터를 chunk로 만들고, 아직 저장되지 않은 chunk/vector만 생성합니다.

- 현재 소스 파일: 프로젝트의 로컬 Git 저장소 HEAD 기준 텍스트 파일
- 프로그램 정보: `programs`
- 커밋 메시지: `git_commits`
- 변경 파일/diff: `commit_files`

현재 소스 파일 chunk에는 `file_path`, `line_start`, `line_end`, `content_hash`, `chunk_content_hash`, `indexed_head_hash` 메타데이터가 저장됩니다. Search 탭은 검색어, 조회된 chunk 목록, cosine 유사도 점수, chunk 출처(source_file/program/commit/commit_file), 현재 파일 일치 여부, 원문 일부를 함께 표시합니다.

Project Chat은 현재 파일과 일치한다고 검증된 `source_file` chunk만 기본 답변 근거로 사용합니다. 인덱싱 후 파일이 수정되었거나 삭제된 근거는 답변에서 제외합니다. 검증된 현재 소스 근거가 없으면 추측성 답변을 만들지 않고 추가 인덱싱 또는 검색어 조정이 필요하다고 안내합니다. 커밋 이력은 옵션으로 검색 후보에 포함할 수 있지만, 현재 코드 근거로는 사용하지 않습니다.

RAG와 Project Chat 화면의 `현재 소스 다시 인덱싱` 버튼은 현재 Git HEAD 기준으로 `source_file` chunk를 갱신하고, 검증되지 않는 오래된 chunk/vector만 정리합니다. 파일 삭제처럼 기존 증분 인덱싱으로 남을 수 있는 오래된 근거도 이 경로에서 제거됩니다. LM Studio 같은 local embedding 서버 부하를 줄이기 위해 Project Chat의 재인덱싱은 embedding을 자동 생성하지 않으며, RAG 화면에서도 명시적으로 선택한 경우에만 제한 수량으로 embedding을 생성합니다.

### source_file 재인덱싱 운영 주의사항

LM Studio 같은 로컬 embedding 서버는 한 번에 많은 chunk를 처리하면 CPU/GPU와 메모리를 오래 점유할 수 있습니다. 그래서 현재 소스 재인덱싱과 embedding 생성을 분리합니다.

- `Project Chat > 현재 소스 다시 인덱싱`: 현재 HEAD 기준으로 source_file chunk만 갱신합니다. embedding은 자동 실행하지 않습니다.
- `RAG 검색 > 현재 소스 다시 인덱싱`: 기본값은 chunk 갱신만 수행합니다. `재인덱싱 후 embedding도 바로 생성`을 직접 체크한 경우에만 제한 수량으로 embedding을 생성합니다.
- `RAG 검색 > Embedding`: 남은 pending chunk를 별도로 처리할 때 사용합니다. 기본 실행 단위는 로컬 LLM/embedding 서버 부하를 줄이기 위해 작게 잡고, 화면에서 남은 작업 수와 예상 소요 시간을 확인한 뒤 여러 번 나눠 실행하세요.

RAG 화면은 embedding 실행 전에 남은 chunk 수, 이번 실행 최대 처리 수, 예상 소요 시간을 표시합니다. 예상 시간은 PC 성능, LM Studio 모델 상태, CPU/GPU 사용량에 따라 달라질 수 있으므로 보수적인 운영 참고값으로 사용하세요.

재인덱싱이나 embedding 중 앱/LM Studio를 강제 종료하면 DB가 바로 깨지는 것은 아닙니다. PostgreSQL은 열린 transaction을 롤백합니다. 다만 이미 commit된 chunk/vector와 아직 처리되지 않은 chunk가 섞여 `pending` 또는 `failed` 상태가 남을 수 있습니다. 이 상태는 부분 완료 상태이며, RAG 화면에서 인덱스 상태를 확인한 뒤 embedding을 제한 수량으로 이어서 실행하면 됩니다.

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

## 권장 사용 순서

### 1. Project

프로젝트를 등록하고 로컬 Git 저장소 경로를 입력합니다.

```text
프로젝트명: Default Project
로컬 Git 저장소 경로: C:\dev\green-market
```

프로그램 목록, Git 커밋, 매핑 결과는 모두 프로젝트 단위로 묶입니다.

### 2. Git

프로젝트를 선택한 뒤 Git 커밋을 수집합니다.

- `전체 수집`: 저장소의 모든 커밋 수집
- `증분 동기화`: 마지막 동기화 이후 새 커밋만 수집

저장 데이터:

- `git_commits`: commit hash, message, author, committed_at, merge 여부
- `commit_files`: 변경 파일, 변경 유형, diff_text

diff는 길이를 제한해 저장하고 바이너리 파일은 diff를 생략합니다.

### 3. Developer / 개발자 관리

Developer 화면에서는 Git 수집 후 개발자 자동 추출을 실행하고, 개발자 관리 화면에서는 직접 추가/수정/삭제 또는 Excel 업로드를 수행합니다.

- 같은 email은 같은 개발자로 처리
- email이 없으면 author name 기준으로 처리
- 변경 파일 경로를 보고 role/skills를 추정

개발자 관리 화면 기능:

- 현재 개발자 검색/조회
- 개발자 직접 추가 및 수정
- 삭제 전 담당 프로그램 수 표시 후 담당 연결 해제
- Excel 양식 다운로드
- 업로드 전 미리보기와 신규/수정/오류 요약

### 4. 프로그램 관리

프로그램 관리 화면에서 현재 등록된 프로그램을 조회하고, 직접 추가/수정/삭제하거나, Excel 양식을 내려받고 업로드 전 검증 후 저장할 수 있습니다.

필수 컬럼:

- `program_id`
- `program_name`

선택 컬럼:

- `screen_name`
- `module`
- `description`
- `developer_name`
- `developer_email`
- `planned_start_date`
- `planned_end_date`
- `status`
- `progress_rate`

엑셀 컬럼명이 다르면 화면에서 컬럼 매핑을 직접 선택할 수 있습니다. `program_id`가 이미 있으면 update 처리합니다.

업로드 저장 전 확인 항목:

- 필수 컬럼 매핑 여부
- 필수 값 누락
- 파일 안의 중복 `program_id`
- 날짜 형식과 계획 시작/종료일 순서
- `progress_rate` 0~100 범위
- 신규/수정/오류/저장 가능 행 수 요약

수동 관리:

- `직접 추가` 탭에서 Excel 없이 프로그램을 한 건씩 등록
- `현재 데이터` 탭에서 검색 후 선택한 프로그램 수정
- 삭제 전 연결된 매핑, 리스크, 구현상태 분석 건수 표시

### 5. 개발계획 관리

개발계획 관리 화면에서 기존 프로그램의 담당자, 일정, 상태, 진행률을 조회/수정합니다. Excel 업로드뿐 아니라 단건 직접 수정과 status/progress_rate 일괄 업데이트도 지원합니다.

주요 컬럼:

- `program_id`
- `developer_id`
- `planned_start_date`
- `planned_end_date`
- `actual_start_date`
- `actual_end_date`
- `status`
- `progress_rate`

업로드 저장 전 확인 항목:

- 등록된 `program_id`인지 확인
- 등록된 `developer_id`인지 확인
- 파일 안의 중복 `program_id`
- 날짜 형식과 시작/종료일 순서
- `progress_rate` 0~100 범위

### 6. Mapping

프로그램 목록과 Git 커밋 정보를 LLM으로 분석해 관련 프로그램-커밋 매핑을 저장합니다.

#### 커밋 기준 분석

기본 추천 방식입니다. 전체 실행 시간을 줄이기 위해 커밋 하나를 기준으로 후보 프로그램만 먼저 추립니다.

흐름:

1. Git 커밋 하나를 선택합니다.
2. 커밋의 message, changed files, diff_text snippets를 가져옵니다.
3. 프로그램 목록에서 규칙/토큰 유사도 기반으로 후보 프로그램 TOP N개를 추립니다.
4. LLM에는 커밋 1개와 후보 프로그램 TOP N개만 한 번에 전달합니다.
5. LLM은 관련 프로그램을 0개 이상 선택해 JSON으로 반환합니다.
6. 결과를 `program_commit_mappings`에 저장합니다.

LLM 출력 형식:

```json
{
  "related_programs": [
    {
      "program_id": "P001",
      "relevance_score": 85,
      "implementation_status": "일부구현",
      "reason": "커밋 메시지와 변경 파일이 해당 프로그램의 서비스/화면과 관련됨"
    }
  ]
}
```

성능/재실행 정책:

- 모든 프로그램 x 모든 커밋 조합을 LLM에 보내지 않습니다.
- 기본값은 커밋 1개당 후보 프로그램 TOP 10입니다.
- diff_text는 파일별 앞부분만 사용하고 입력 길이를 제한합니다.
- 이미 같은 `program_id + commit_id` 매핑이 있으면 새로 만들지 않고 업데이트합니다.
- 커밋 분석이 성공하면 `git_commits.mapping_analysis_status = completed`로 표시합니다.
- LLM 실패 또는 JSON 파싱 실패 시 해당 커밋은 `failed`로 기록하고 다음 커밋으로 넘어갑니다.
- 일괄 분석은 이미 `completed`인 커밋을 건너뛰므로 중단 후 재시작할 수 있습니다.

화면 기능:

- 분석 모드 선택: `커밋 기준 분석`, `프로그램 기준 분석`
- 기본값: `커밋 기준 분석`
- 커밋 목록에서 특정 커밋 선택
- 선택한 커밋 1개 분석
- 아직 완료되지 않은 커밋 일괄 분석
- 진행률, 실패 수, 현재 커밋 표시
- 매핑 피드백 리뷰 큐: 피드백 미완료, 판단불가, 낮은 관련도, 비관련 판정, 근거 부족 매핑을 우선 검토
- 매핑 피드백 KPI: 전체/완료/미완료/리뷰 필요/판단불가/낮은 관련도 매핑 수 표시
- 리뷰 큐에서 선택한 매핑을 기존 피드백 보정 form으로 바로 수정

#### 프로그램 기준 분석

기존 방식입니다. 프로그램별로 후보 커밋을 추리고 각 프로그램-커밋 조합을 LLM으로 분석합니다. 정확도를 더 세밀하게 보고 싶을 때 사용할 수 있지만, 커밋과 프로그램 수가 많으면 실행 시간이 길어질 수 있습니다.

### 7. Program Detail

특정 프로그램을 선택해 개발 현황을 한 화면에서 확인합니다. 새 메뉴 구조에서는 `프로젝트 관리 > Program Detail`에서 사용할 수 있습니다.

주요 기능:

- 프로그램 목록 조회
- `program_name` 검색
- 상태/담당자 필터
- 프로그램 기본 정보 표시
- AI 진척도와 구현상태별 매핑 수 표시
- 관련 커밋 목록 조회 및 관련도순 정렬
- 구현상태/개발자별 관련 커밋 필터
- 커밋 상세: commit message, changed files, diff snippet, LLM 판단 근거
- 관련 개발자 수, 개발자별 커밋 수, 기여 비율 차트
- 첫 커밋일, 마지막 커밋일, 최근 30일/90일 커밋 수
- 계획 종료일 경과, 관련 커밋 없음, 판단불가만 존재 조건 기반 Risk Level 표시
- 저장된 프로그램 단위 구현상태 분석 결과를 업무용 추정 라벨, 분석 일시, 상태 요약, 완료/미완료 추정 기능, 주요 근거 커밋으로 표시

기본 조회는 저장된 `program_commit_mappings`, `git_commits`, `commit_files`, `program_implementation_status` 데이터를 사용합니다. `구현상태 재분석` 버튼을 누르면 해당 프로그램만 다시 분석하며, 관련 커밋 목록이 이전 분석과 같으면 기존 결과를 재사용합니다.

### 8. Commit Impact

특정 Git 커밋이 어떤 프로그램, 개발자, 모듈, 파일에 영향을 주는지 분석합니다. 새 메뉴 구조에서는 `AI 분석 > Commit Impact`에서 사용할 수 있습니다.

주요 기능:

- commit message 검색
- author 검색
- 날짜 필터
- 영향 프로그램 목록 조회
- 관련도 점수, 구현 상태, LLM 판단 근거 표시
- 변경 파일 목록과 diff snippet 확인
- 관련 프로그램 담당자와 최근 같은 영역 작업자 분석
- 영향 프로그램 수, 영향 개발자 수, 영향 파일 수 KPI
- 영향도 점수 `LOW`, `MEDIUM`, `HIGH` 계산

새로운 LLM 호출은 하지 않고, 기존 `program_commit_mappings`, `git_commits`, `commit_files`, `programs` 데이터를 재사용합니다.

### 9. Risk Analysis

프로그램 목록, 개발계획, Git 커밋, LLM 매핑 결과를 기반으로 누락 가능성이 있는 프로그램과 위험 프로그램을 자동 탐지합니다. 새 메뉴 구조에서는 `AI 분석 > Risk Analysis`에서 사용할 수 있습니다.

탐지 규칙:

- 프로그램은 등록되어 있지만 관련 커밋이 없음
- 계획 종료일이 지났지만 AI 진척도 < 100
- 계획 진척도와 AI 진척도 차이가 30 이상
- LLM 매핑 결과가 모두 판단불가
- 최근 14일 동안 관련 커밋이 없음
- 담당자가 없거나 개발자 정보가 불명확함

Risk Level:

- `LOW`: 단순 주의 필요
- `MEDIUM`: 일정 지연 가능성 또는 AI 진척도 낮음
- `HIGH`: 계획 종료일 경과와 관련 커밋/AI 진척도/담당자 문제가 함께 나타나는 경우

화면 기능:

- 프로젝트 선택
- 리스크 분석 실행
- 탐지 결과 `risk_findings` 저장
- unresolved 리스크 조회
- 선택 리스크 resolved 처리
- 전체/HIGH/MEDIUM/LOW 리스크 수
- 리스크 유형별 차트
- 개발자별 리스크 프로그램 수 차트
- 리스크 프로그램 목록

새로운 LLM 호출은 하지 않고 기존 DB 데이터와 `program_commit_mappings` 결과만 사용합니다. Program Detail 화면에는 해당 프로그램의 unresolved 리스크가 표시되고, AI Progress 화면에는 저장된 리스크 수와 HIGH 리스크 목록이 표시됩니다.

### 10. AI Code Review

로컬 Git 저장소의 변경 사항 또는 커밋을 LLM으로 리뷰합니다. 새 메뉴 구조에서는 `AI 분석 > AI Code Review`에서 사용할 수 있습니다.

지원 대상:

- 작업트리 변경: 아직 stage하지 않은 `git diff`
- Staged 변경: `git diff --cached`
- 최신 커밋: `HEAD`
- 특정 커밋: 커밋 해시 또는 rev 입력

리뷰 결과:

- 커밋/변경 의도 분석
- 영향 범위와 위험도
- 버그 후보 탐지
- 리팩토링 제안
- 최근 리뷰 기록 조회

리뷰 결과는 `code_review_results` 테이블에 저장됩니다. `LLM_PROVIDER=mock`이면 동작 확인용 mock 리뷰가 생성되고, `LLM_PROVIDER=local_openai`이면 LM Studio 같은 OpenAI-compatible 서버로 실제 리뷰를 요청합니다.

### 11. 개발계획 대시보드

`programs` 테이블 기준으로 개발계획 현황을 조회합니다.

- 프로그램 목록 조회
- 상태별 프로그램 수 차트
- 개발자별 배정 프로그램 수 차트
- 계획 종료일이 지났지만 완료되지 않은 프로그램 목록
- 전체 계획 대비 완료율
- 평균 진행률

### 12. AI Progress

계획 진척도와 LLM 매핑 결과 기반 AI 진척도를 비교하고 리스크를 추적합니다.

- AI 진척도: `program_commit_mappings`의 구현상태를 수치화한 값
- 구현상태 분석: `program_implementation_status`에 저장된 프로그램 단위 AI 분석 결과
- 프로그램별 비교 테이블에서 구현상태 분석 라벨, 요약, 분석 일시, 근거 커밋 수 확인
- 프로그램 상세 영역에서 선택한 프로그램의 구현상태 분석 요약과 관련 커밋 매핑 상세 확인
- 저장된 구현상태 분석 결과가 없으면 `분석없음` 또는 `구현상태 분석 결과 없음`으로 표시

AI 진척도 계산 방식은 기존 매핑 기반 수치를 유지하며, 구현상태 분석 결과는 수치를 대체하지 않고 업무 검토용 요약 근거로 함께 표시합니다.

### 13. Dashboard

Git author 기반 개발자 통계를 보여줍니다.

- 개발자별 커밋 수
- 개발자별 변경 파일 수

## 샘플 데이터 생성

`샘플 데이터 생성` 메뉴에서 로컬 Git 저장소 경로를 입력하면 테스트용 Excel 파일을 생성하고 다운로드할 수 있습니다.

생성 파일:

- `sample_developers.xlsx`
- `sample_programs.xlsx`
- `sample_development_plan.xlsx`

CLI로 생성:

```powershell
python scripts\generate_sample_development_data.py --repo-path C:\dev\green-market --output-dir sample_data
```

저장소 루트의 기존 프로그램 목록 CSV를 우선 사용하려면:

```powershell
python scripts\generate_sample_development_data.py --repo-path C:\dev\green-market --output-dir sample_data --use-existing-program-csv --program-csv-path C:\dev\green-market\programs.csv
```

## 주요 테이블

- `projects`: 프로젝트 정보, Git 저장소 경로, 마지막 동기화 상태
- `developers`: 개발자 목록, email, role, skills
- `programs`: 프로그램 목록과 개발계획 정보
- `git_commits`: Git 커밋 메타데이터, 매핑 분석 상태
- `commit_files`: 커밋별 변경 파일과 diff
- `program_commit_mappings`: 프로그램-커밋 매핑 분석 결과와 사용자 피드백 보정값
- `program_implementation_status`: 프로그램 단위 구현상태 분석 결과, 요약, 완료/미완료 기능, 근거 커밋, 분석 시각
- `analysis_runs`: 분석 실행 이력, 상태, 처리/실패 카운터
- `code_review_results`: AI 코드리뷰 결과, 버그 탐지, 리팩토링 제안, 원본 응답
- `risk_findings`: 규칙 기반 리스크 탐지 결과, evidence, resolved 상태
- `document_chunks`: RAG용 chunk 원문과 출처/상태 메타데이터. `source_file` chunk는 파일 경로, 라인 범위, content hash, indexed HEAD hash를 저장합니다.
- `vector_items`: chunk별 embedding vector 저장. 같은 `chunk_id + embedding_model`은 앱에서 중복 저장하지 않습니다.

## 프로그램 단위 구현상태 분석

### 기능 목적

프로그램-커밋 매핑 결과 이후 단계에서 개발계획에 등록된 각 프로그램의 현재 구현상태를 판단합니다. 커밋 수만 보지 않고 프로그램 설명, 개발계획 정보, 관련 커밋 메시지, 변경 파일, 기존 커밋 매핑 분석 결과를 함께 사용합니다.

저장되는 내부 상태 값:

| 내부 상태 | 화면 라벨 | 의미 |
|---|---|---|
| `NOT_STARTED` | 구현전 추정 | 관련 구현 근거가 거의 없다고 추정 |
| `IN_PROGRESS` | 진행중 추정 | 구현 근거는 있으나 완료 여부가 불확실 |
| `COMPLETED` | 구현완료 추정 | 관련 커밋과 매핑 근거상 구현 완료 가능성이 높음 |
| `UNKNOWN` | 판단불가 | 근거가 부족하거나 상충됨 |
| 그 외 값 | 판단불가 | 예상하지 못한 값은 안전하게 판단불가로 표시 |

판단 원칙:

- 커밋 수만으로 완료 여부를 판단하지 않습니다.
- `COMPLETED`는 프로그램 설명/계획 범위와 관련된 핵심 구현 근거가 충분하고, 미완료 신호가 뚜렷하지 않을 때만 선택하도록 프롬프트를 구성합니다.
- 커밋 메시지와 변경 파일만으로 테스트 완료, 예외처리 완료, 화면 연결 완료, 배포/운영 검증 완료를 확정하지 않습니다.
- 확인되지 않은 테스트/배포/운영 검증 항목은 `incomplete_features`에 검증 필요 사항으로 남깁니다.
- LLM 응답 실패 또는 JSON 파싱 실패 시 fallback 결과를 저장하며, 완료 신호가 있어도 담당자 검증이 필요한 `IN_PROGRESS` 중심으로 보수적으로 표시합니다.

### 분석 흐름

1. `program_commit_mappings`에서 프로그램별 관련 커밋을 조회합니다.
2. `ProgramImplementationAnalyzer`가 프로그램 정보와 관련 커밋 근거를 구성합니다.
3. LLM 설정이 있으면 한국어 프롬프트로 구현상태, 요약, 완료 기능, 미완료/검증 필요 기능, 근거 커밋을 JSON 형식으로 요청합니다.
4. LLM 응답이 없거나 JSON 파싱에 실패하면 매핑 상태, 관련도 점수, 커밋 근거 기반 fallback 결과를 저장합니다. fallback은 실제 완료 단정 대신 담당자 검증이 필요한 추정 결과를 우선합니다.
5. 관련 커밋 해시 목록을 정렬해 SHA-256 시그니처로 저장하고, 다음 분석 시 동일하면 재분석을 건너뜁니다.

### 저장 구조

분석 결과는 `program_implementation_status` 테이블에 프로그램당 1건으로 저장됩니다.

- `program_id`: `programs.id` 외래키
- `status`: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `UNKNOWN`
- `summary`: 상태 판단 요약
- `completed_features`: 완료된 것으로 보이는 기능 JSON 배열
- `incomplete_features`: 미완료 또는 불확실한 기능 JSON 배열
- `evidence_commits`: 주요 근거 커밋 JSON 배열
- `commit_hash_signature`: 재분석 방지용 커밋 해시 목록 시그니처
- `analyzed_at`: 분석 시각
- `raw_response`: LLM 원문 응답 또는 fallback 메타데이터

### 자동 분석 시점

Mapping 화면에서 커밋 기준 또는 프로그램 기준 프로그램-커밋 매핑 작업이 완료되면 자동으로 프로젝트 전체 프로그램의 구현상태 분석을 실행합니다. 이미 저장된 분석의 `commit_hash_signature`가 현재 관련 커밋 목록과 같으면 해당 프로그램은 건너뜁니다.

### 수동 재분석 방법

`Program Detail` 화면에서 프로그램을 선택한 뒤 `구현상태 재분석` 버튼을 누르면 해당 프로그램만 분석합니다. 관련 커밋 목록이 이전 분석과 같으면 기존 결과를 재사용하고 재분석하지 않습니다.

Program Detail의 구현상태 분석 결과 카드에서 다음 정보를 조회할 수 있습니다.

- 구현상태 추정 라벨
- 분석 일시
- 근거 커밋 수
- 상태 요약
- 완료된 것으로 보이는 기능
- 미완료 또는 불확실한 기능
- 주요 근거 커밋: short hash, full hash, reason

이 결과는 프로그램 정보, 관련 커밋, 매핑 근거를 기반으로 한 AI 분석 결과입니다. 화면에서는 `구현전 추정`, `진행중 추정`, `구현완료 추정`, `판단불가`처럼 단정이 아닌 추정 라벨로 표시하며, 실제 완료 여부는 담당자 확인이 필요합니다.

### 로컬 검증 명령

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

화면 테스트 순서:

1. Project, Git, 프로그램 목록 또는 개발계획 데이터를 준비합니다.
2. Mapping 화면에서 커밋 기준 매핑 또는 프로그램 기준 매핑을 실행합니다.
3. 매핑 완료 후 `program_implementation_status`에 결과가 생성되는지 확인합니다.
4. Program Detail 화면에서 구현상태 분석 결과를 확인합니다.
5. `구현상태 재분석` 버튼을 눌러 해당 프로그램만 재분석 또는 skip 처리되는지 확인합니다.

## 프로젝트 구조

```text
app.py
src/
  db/
    database.py
    init_db.py
    models.py
  services/
    developer_service.py
    excel_service.py
    git_service.py
    code_review_service.py
    commit_impact_service.py
    llm_client.py
    mapping_service.py
    program_analysis_service.py
    program_implementation_analyzer.py
    risk_service.py
  ui/
    dashboard_page.py
    code_review_page.py
    commit_impact_page.py
    developer_page.py
    developer_upload_page.py
    development_plan_upload_page.py
    git_page.py
    home_page.py
    mapping_page.py
    planning_dashboard_page.py
    program_detail_page.py
    project_page.py
    project_chat_page.py
    rag_page.py
    risk_page.py
    sample_data_page.py
    upload_page.py
  rag/
    chunker.py
    chat_service.py
    embedding_client.py
    retriever.py
    source_verifier.py
    vector_store.py
  utils/
    config.py
scripts/
  generate_sample_development_data.py
docker-compose.yml
requirements.txt
.env.example
```

## 참고

- RAG/embedding은 mock과 OpenAI-compatible 서버를 모두 지원합니다. 실제 검색 품질 평가는 LM Studio 등 로컬 embedding 서버와 모델 차원 설정이 맞아야 합니다.
- Project Chat은 현재 소스 검증을 통과한 `source_file` chunk만 기본 답변 근거로 사용합니다.
- 현재 소스 파일을 수정하거나 브랜치/HEAD가 바뀐 뒤에는 RAG 또는 Project Chat 화면의 인덱스 상태를 확인하고 필요 시 `현재 소스 다시 인덱싱`을 실행하세요.
- LLM 매핑 분석과 AI 코드리뷰는 `.env`의 `LLM_PROVIDER` 설정에 따라 mock 또는 로컬 LLM을 사용합니다.
- Streamlit 실행 중 `.env`를 바꾸면 앱을 재시작해야 반영됩니다.

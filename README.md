# AI Commit Advisor

로컬 Git 저장소의 커밋/변경 파일/diff를 수집하고, 프로그램 목록과 비교해 프로그램별 관련 커밋을 추천하는 Streamlit 기반 PoC입니다.

현재 버전은 실제 LLM 연결 전 mock 분석도 가능하고, LM Studio 같은 OpenAI-compatible 로컬 LLM 서버와 연결해 프로그램-커밋 매핑 분석을 실행할 수 있습니다.

## 주요 기능

- 프로젝트 등록 및 로컬 Git 저장소 경로 관리
- Git 저장소 전체 커밋 수집 및 증분 동기화
- Git author 기반 개발자 자동 추출 및 role/skills 관리
- 프로그램 목록 Excel 업로드
- 개발계획 Excel 업로드
- Git 로그 기반 테스트용 샘플 Excel 데이터 생성
- 프로그램 목록과 Git 커밋의 LLM 기반 매핑 분석
- 개발계획 대시보드 및 개발자 통계 대시보드

## 실행 환경

- Python 3.11 이상
- Docker Desktop
- PostgreSQL + pgvector
- 선택: LM Studio 또는 OpenAI-compatible 로컬 LLM 서버

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

### 4. DB 초기화/스키마 보강

```powershell
python -m src.db.init_db
```

### 5. Streamlit 실행

```powershell
streamlit run app.py
```

가상환경 활성화 없이 바로 실행하려면:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## LLM 설정

기본값은 mock입니다. 외부 호출 없이 fallback 규칙으로 매핑 결과를 생성합니다.

```env
LLM_PROVIDER=mock
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_API_KEY=
LLM_MODEL=exaone-3.5-2.4b-instruct
```

LM Studio를 사용하는 경우:

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

소형 로컬 모델은 context가 작을 수 있으므로 Mapping 화면의 `프로그램별 분석할 커밋 후보 수`는 3~5 정도를 권장합니다.

## 권장 사용 순서

### 1. Project

프로젝트를 등록하고 로컬 Git 저장소 경로를 입력합니다.

예:

```text
프로젝트명: Default Project
로컬 Git 저장소 경로: C:\dev\green-market
```

프로그램 목록, Git 커밋, 매핑 결과는 모두 프로젝트 단위로 묶입니다. 같은 프로젝트를 선택해야 대시보드와 Mapping 화면에서 데이터가 함께 보입니다.

### 2. Git

프로젝트를 선택한 뒤 Git 커밋을 수집합니다.

- `전체 수집`: 저장소의 모든 커밋 수집
- `증분 동기화`: 마지막 동기화 이후 새 커밋만 수집

저장 데이터:

- `git_commits`: commit hash, message, author, committed_at, merge 여부
- `commit_files`: 변경 파일, 변경 유형, diff_text

diff는 5000자까지 저장하고, 바이너리 파일은 diff를 생략합니다.

### 3. Developer

Git 수집 후 `개발자 자동 추출`을 실행합니다.

기준:

- 같은 email은 같은 개발자로 처리
- email이 없으면 author name 기준
- 변경 파일 경로를 보고 role/skills를 추정

화면에서 role, skills를 수정할 수 있습니다.

### 4. 프로그램 목록 업로드

프로그램 목록 Excel을 업로드합니다.

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

엑셀 컬럼명이 달라도 화면에서 컬럼 매핑을 직접 선택할 수 있습니다. `program_id`가 이미 있으면 update 처리합니다.

### 5. 개발계획 업로드

개발계획 Excel을 업로드해 기존 프로그램에 담당자/일정/상태/진행률을 업데이트합니다.

주요 컬럼:

- `program_id`
- `developer_id`
- `planned_start_date`
- `planned_end_date`
- `actual_start_date`
- `actual_end_date`
- `status`
- `progress_rate`

### 6. Mapping

프로그램 목록과 Git 커밋 정보를 LLM으로 분석해 관련 커밋을 추천합니다.

입력:

- 프로그램: `program_id`, `program_name`, `description`, `module`, `screen_name`
- 커밋: message, changed files, diff_text snippets

출력/저장:

- 관련도 점수 0~100
- 관련 커밋 여부
- 판단 근거
- 구현 상태: `구현됨`, `일부구현`, `판단불가`

결과는 `program_commit_mappings`에 저장됩니다.

`프로그램별 분석할 커밋 후보 수`는 모든 커밋을 LLM에 보내지 않기 위한 제한값입니다. 예를 들어 프로그램 239개, 커밋 275개를 전부 비교하면 65,725건이므로, 먼저 파일 경로/토큰 유사도로 후보를 추리고 프로그램당 상위 N개만 분석합니다.

### 7. 개발계획 대시보드

`programs` 테이블 기준으로 개발계획 현황을 조회합니다.

- 프로그램 목록 조회
- 상태별 프로그램 수 차트
- 개발자별 배정 프로그램 수 차트
- 계획 종료일이 지났지만 완료되지 않은 프로그램 목록
- 전체 계획 대비 완료율
- 평균 진행률

### 8. Dashboard

Git author 기반 개발자 통계를 보여줍니다.

- 개발자별 커밋 수
- 개발자별 변경 파일 수

## 샘플 데이터 생성

`샘플 데이터 생성` 메뉴에서 로컬 Git 저장소 경로를 입력하면 테스트용 Excel 파일을 생성하고 다운로드할 수 있습니다.

생성 파일:

- `sample_developers.xlsx`
- `sample_programs.xlsx`
- `sample_development_plan.xlsx`

이 데이터는 실제 업무 데이터가 아니라 Git 로그 기반 가상 샘플 데이터입니다. 랜덤성은 고정 seed로 재현 가능하게 작성되어 있습니다.

CLI로 생성:

```powershell
python scripts\generate_sample_development_data.py --repo-path C:\dev\green-market --output-dir sample_data
```

저장소 루트의 기존 프로그램 목록 CSV를 우선 사용하려면:

```powershell
python scripts\generate_sample_development_data.py --repo-path C:\dev\green-market --output-dir sample_data --use-existing-program-csv --program-csv-path C:\dev\green-market\프로그램목록.csv
```

## 주요 테이블

- `projects`: 프로젝트 정보, Git 저장소 경로, 마지막 동기화 상태
- `developers`: 개발자 목록, email, role, skills
- `programs`: 프로그램 목록과 개발계획 정보
- `git_commits`: Git 커밋 메타데이터
- `commit_files`: 커밋별 변경 파일과 diff
- `program_commit_mappings`: 프로그램-커밋 매핑 분석 결과
- `analysis_runs`: 분석 실행 이력
- `document_chunks`: RAG용 chunk 원문과 메타데이터
- `vector_items`: 향후 임베딩 벡터 저장

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
    llm_client.py
    mapping_service.py
  ui/
    dashboard_page.py
    developer_page.py
    developer_upload_page.py
    development_plan_upload_page.py
    git_page.py
    home_page.py
    mapping_page.py
    planning_dashboard_page.py
    project_page.py
    rag_page.py
    sample_data_page.py
    upload_page.py
  rag/
    chunker.py
    embedding_client.py
    retriever.py
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

- 현재 RAG/embedding 기능은 골격만 있으며 실제 검색/임베딩 분석은 아직 확장 대상입니다.
- LLM 매핑 분석은 `.env`의 `LLM_PROVIDER` 설정에 따라 mock 또는 로컬 LLM을 사용합니다.
- Streamlit 실행 중 `.env`를 바꾸면 앱을 재시작해야 반영됩니다.

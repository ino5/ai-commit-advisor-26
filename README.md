# AI Commit Advisor

회사 학습용 LLM/RAG 기반 AI PoC 프로젝트입니다.

이 프로젝트는 엑셀 프로그램 목록과 로컬 Git 커밋/diff 정보를 수집하고, 향후 LLM/RAG를 이용해 프로그램별 관련 커밋 추천, 개발 진척도, 누락 기능, 리스크 분석으로 확장하기 위한 기본 실행 환경입니다.

## V1 범위

- Streamlit 기반 PoC 대시보드
- PostgreSQL + pgvector Docker 환경
- SQLAlchemy DB 연결 및 기본 테이블 모델
- 엑셀 업로드, Git 수집, RAG, LLM 매핑 기능을 붙이기 위한 stub 구조
- DB 연결 테스트 버튼

아직 실제 LLM 매핑, 실제 임베딩 API 호출, 실제 RAG 검색 로직은 구현하지 않았습니다.

## 프로젝트 구조

```text
app.py
src/
  db/
    database.py
    models.py
    init_db.py
  services/
    excel_service.py
    git_service.py
    llm_client.py
    mapping_service.py
  rag/
    chunker.py
    embedding_client.py
    vector_store.py
    retriever.py
  ui/
    home_page.py
    project_page.py
    upload_page.py
    git_page.py
    rag_page.py
    dashboard_page.py
  utils/
    config.py
docker-compose.yml
requirements.txt
.env.example
```

## 실행 방법

### 1. 환경변수 파일 생성

```powershell
Copy-Item .env.example .env
```

### 2. PostgreSQL + pgvector 실행

```powershell
docker compose up -d
```

### 3. Python 가상환경 생성 및 패키지 설치

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

cmd.exe를 사용하는 경우에는 아래 명령을 사용합니다.

```cmd
.venv\Scripts\activate
```

이미 `.venv`가 만들어져 있다면 활성화만 하면 됩니다.

### 4. DB 테이블 생성

```powershell
python -m src.db.init_db
```

### 5. Streamlit 실행

```powershell
streamlit run app.py
```

가상환경을 활성화하지 않고 바로 실행하려면 아래 명령을 사용할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 Streamlit 화면이 뜨면 Home 화면의 `DB 연결 테스트` 버튼으로 연결 상태를 확인할 수 있습니다.

## 주요 테이블

- `projects`: 프로젝트 정보와 로컬 Git 저장소 경로
- `developers`: Git author 기반 개발자 목록과 가상 role/skills
- `programs`: 엑셀 프로그램 목록
- `git_commits`: Git 커밋 정보
- `commit_files`: 커밋별 변경 파일과 diff
- `program_commit_mappings`: 프로그램과 커밋의 AI 매핑 결과
- `analysis_runs`: 분석 실행 이력
- `document_chunks`: RAG용 chunk 원문과 메타데이터
- `vector_items`: 향후 임베딩 벡터 저장

## 테스트용 가상 개발계획 데이터

`scripts/generate_sample_development_data.py`는 로컬 Git 저장소의 실제 commit author, commit date, 변경 파일 경로를 분석해 ai-commit-advisor 업로드 테스트용 Excel 파일을 생성합니다. 생성된 role, skills, 계획일자, 상태, 진행률은 실제 업무 데이터가 아니라 고정 seed 기반의 가상 추정값입니다.

```powershell
python scripts\generate_sample_development_data.py --repo-path C:\dev\green-market --output-dir sample_data
```

Streamlit의 `샘플 데이터 생성` 메뉴에서도 로컬 Git 저장소 경로를 입력해 같은 형식의 Excel 파일을 생성하고 바로 다운로드할 수 있습니다. 기본 생성 방식은 실제 업무 데이터가 아니라 Git 로그 기반 가상 샘플 데이터이며, 프로그램 목록은 파일 경로, Controller, Service, Mapper/Repository 이름을 기준으로 생성합니다.

`저장소의 기존 프로그램목록 CSV를 우선 사용` 옵션을 켜면 입력한 Git 저장소 루트에서 `*프로그램목록*.csv` 파일을 자동 검색합니다. 화면에서 발견된 CSV 경로를 확인하거나 CSV 경로를 직접 입력할 수 있습니다. CLI에서는 아래처럼 명시할 수 있습니다.

```powershell
python scripts\generate_sample_development_data.py --repo-path C:\dev\green-market --output-dir sample_data --use-existing-program-csv --program-csv-path C:\dev\green-market\프로그램목록.csv
```

생성 파일:

- `sample_data/sample_developers.xlsx`
- `sample_data/sample_programs.xlsx`
- `sample_data/sample_development_plan.xlsx`

업로드 순서:

1. `개발자 목록 업로드`에서 `sample_developers.xlsx` 저장
2. `프로그램 목록 업로드`에서 `sample_programs.xlsx` 저장
3. `개발계획 업로드`에서 `sample_development_plan.xlsx` 저장
4. `개발계획 대시보드`에서 집계 확인

## 다음 단계 후보

- 엑셀 컬럼 매핑 및 `programs` 저장 로직 구현
- Git 커밋/diff 수집 후 `git_commits`, `commit_files` 저장
- `document_chunks` 생성 배치 구현
- 실제 embedding provider 연동
- pgvector 기반 유사도 검색 구현
- LLM 기반 프로그램-커밋 매핑 프롬프트와 결과 저장 구현

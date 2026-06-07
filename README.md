# AI Commit Advisor

로컬 Git 저장소의 커밋, 변경 파일, diff를 수집하고 프로그램 목록과 비교해 프로그램-커밋 매핑 후보를 추천하는 Streamlit 기반 PoC입니다.

현재 버전은 mock 분석과 OpenAI-compatible 로컬 LLM 서버를 지원합니다. LM Studio 같은 로컬 LLM 서버를 연결하면 Mapping 화면에서 실제 LLM 기반 분석을 실행할 수 있습니다.

## 주요 기능

- 프로젝트 등록 및 로컬 Git 저장소 경로 관리
- Git 저장소 전체 커밋 수집 및 증분 동기화
- 커밋별 변경 파일과 diff 저장
- Git author 기반 개발자 자동 추출 및 role/skills 관리
- 프로그램 목록 Excel 업로드
- 개발계획 Excel 업로드
- 프로그램 상세 분석 화면: 특정 프로그램의 계획, AI 진척도, 관련 커밋, 개발자 기여, 리스크 확인
- 커밋 영향도 분석 화면: 특정 커밋이 영향을 주는 프로그램, 개발자, 모듈, 파일 확인
- 커밋 기준 프로그램-커밋 매핑 분석
- 기존 프로그램 기준 매핑 분석 유지
- 실시간 AI 코드리뷰: 작업트리, staged 변경, 최신 커밋, 특정 커밋 분석
- 코드리뷰 버그 탐지, 리팩토링 제안, 리뷰 기록 저장
- 개발계획 대시보드 및 개발자 통계 대시보드
- 테스트용 샘플 Excel 데이터 생성

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

### 4. DB 초기화 및 스키마 보강

```powershell
python -m src.db.init_db
```

기존 DB가 있어도 필요한 컬럼은 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 방식으로 보강됩니다.

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

### 3. Developer

Git 수집 후 개발자 자동 추출을 실행합니다.

- 같은 email은 같은 개발자로 처리
- email이 없으면 author name 기준으로 처리
- 변경 파일 경로를 보고 role/skills를 추정

화면에서 role, skills를 직접 수정할 수 있습니다.

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

엑셀 컬럼명이 다르면 화면에서 컬럼 매핑을 직접 선택할 수 있습니다. `program_id`가 이미 있으면 update 처리합니다.

### 5. 개발계획 업로드

개발계획 Excel을 업로드해 기존 프로그램의 담당자, 일정, 상태, 진행률을 업데이트합니다.

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

새로운 LLM 호출은 하지 않고, 기존 `program_commit_mappings`, `git_commits`, `commit_files` 데이터를 사용합니다.

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

### 9. AI Code Review

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

### 10. 개발계획 대시보드

`programs` 테이블 기준으로 개발계획 현황을 조회합니다.

- 프로그램 목록 조회
- 상태별 프로그램 수 차트
- 개발자별 배정 프로그램 수 차트
- 계획 종료일이 지났지만 완료되지 않은 프로그램 목록
- 전체 계획 대비 완료율
- 평균 진행률

### 11. Dashboard

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
- `program_commit_mappings`: 프로그램-커밋 매핑 분석 결과
- `analysis_runs`: 분석 실행 이력, 상태, 처리/실패 카운터
- `code_review_results`: AI 코드리뷰 결과, 버그 탐지, 리팩토링 제안, 원본 응답
- `document_chunks`: RAG용 chunk 원문과 메타데이터
- `vector_items`: 향후 embedding vector 저장

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

- 현재 RAG/embedding 기능은 골격 중심이며 실제 검색/임베딩 분석은 확장 예정입니다.
- LLM 매핑 분석과 AI 코드리뷰는 `.env`의 `LLM_PROVIDER` 설정에 따라 mock 또는 로컬 LLM을 사용합니다.
- Streamlit 실행 중 `.env`를 바꾸면 앱을 재시작해야 반영됩니다.

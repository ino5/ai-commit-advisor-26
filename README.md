# AI Commit Advisor

AI Commit Advisor는 로컬 Git 저장소의 커밋, 변경 파일, diff, 개발계획 데이터를 연결해 프로그램-커밋 매핑, 영향도 분석, 리스크 탐지, RAG 검색, Project Chat, AI 코드리뷰를 지원하는 Streamlit 기반 PoC입니다.

기본값은 mock 분석이며, LM Studio 같은 OpenAI-compatible 로컬 LLM/embedding 서버를 연결하면 Mapping, AI Code Review, Project Chat, RAG 검색에서 실제 AI 기반 분석을 실행할 수 있습니다.

![AI Commit Advisor dashboard](docs/images/ai-commit-advisor-home.png)

## Key Features

- 로컬 Git 저장소 커밋, 변경 파일, diff 수집과 증분 동기화
- 개발자, 프로그램 목록, 개발계획 Excel 업로드와 화면 기반 직접 관리
- LLM 기반 프로그램-커밋 Mapping과 사용자 피드백 보정
- Commit Impact, Program Detail, AI Progress 기반 구현 현황 추적
- 규칙 기반 Risk Analysis로 누락, 지연, 불확실한 프로그램 탐지
- 현재 소스 검증형 RAG Search와 Project Chat
- 작업트리, staged 변경, 최신/특정 커밋 대상 AI Code Review
- 샘플 Git 저장소와 Excel 데이터 생성으로 전체 기능 데모 가능

## Quick Start

가볍게 앱 흐름만 확인하려면 mock 설정을 사용합니다.

```powershell
Copy-Item .env.example .env
docker compose up -d
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.db.init_db
streamlit run app.py
```

실제 LLM/RAG/Project Chat 품질을 검증하려면 로컬 LLM 설정 예시를 사용합니다.

```powershell
Copy-Item .env.local-llm.example .env
```

local LLM 모드에서는 LM Studio에서 chat 모델과 embedding 모델을 먼저 로드해야 합니다. RAG/Project Chat 사용 전에는 현재 embedding 모델 기준으로 source_file embedding을 생성하세요.

가상환경 활성화 없이 실행하려면:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

자세한 설치, DB migration, LLM/embedding 설정, 운영 주의사항은 [Setup and Operations](docs/setup-and-operations.md)를 참고하세요.

## Sample Project

실제 업무 프로젝트를 건드리지 않고 전체 흐름을 검증하려면 샘플 대상 Git 저장소를 생성합니다.

```powershell
.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py
```

기본 생성 위치는 `C:\dev\ai-advisor-sample-shop`입니다. 샘플 repo는 8개 프로그램, 30개 commit, Spring MVC + MyBatis 예제 소스, 업로드용 Excel 3종을 포함합니다.

전체 데모 순서와 과도한 LLM/embedding 호출을 피하는 실행 기준은 [Rich Sample Demo Walkthrough](docs/rich-sample-demo-walkthrough.md)를 먼저 확인하세요. 샘플 repo 설계와 기능별 데모 포인트는 [Sample Target Repo Demo Design](docs/sample-target-repo-demo-design.md)에서 관리합니다.

## Screenshots

대표 화면은 아래와 같습니다. 기능별 전체 캡처는 [Screenshot Gallery](docs/screenshot-gallery.md)에서 확인할 수 있습니다.

![Home](docs/images/features/home.png)

## Documentation

- [Feature Guide](docs/feature-guide.md): 주요 화면, 기능 흐름, 분석 결과가 무엇을 의미하는지 설명합니다.
- [Screenshot Gallery](docs/screenshot-gallery.md): 샘플 프로젝트 기준 기능별 화면 캡처를 모아 둔 갤러리입니다.
- [Setup and Operations](docs/setup-and-operations.md): 설치, 실행, 환경 변수, DB migration, LLM/embedding 운영 가이드입니다.
- [Rich Sample Demo Walkthrough](docs/rich-sample-demo-walkthrough.md): 팀원이 샘플 프로젝트로 기능을 검증할 때 따르는 안전 실행 순서입니다.
- [Sample Target Repo Demo Design](docs/sample-target-repo-demo-design.md): 샘플 Git 저장소 목표, commit 시나리오, 기능별 데모 포인트입니다.
- [AI Technical Overview](docs/ai-technical-overview.md): Mapping, RAG, Project Chat, Code Review, Risk Analysis 등 AI 동작 방식입니다.
- [Architecture](README_ARCHITECTURE.md): 모듈 구조, 데이터 흐름, 서비스 책임입니다.
- [DB Migrations](docs/db-migrations.md): Alembic 기반 DB schema 관리 기준입니다.
- [AI Change Log](AI_CHANGELOG.md): AI 에이전트가 수행한 변경 이력입니다.
- [Agent Instructions](AGENTS.md): 코딩 에이전트 작업 규칙입니다.

## Project Structure

```text
app.py
src/
  db/
  rag/
  services/
  ui/
  utils/
scripts/
docs/
docker-compose.yml
requirements.txt
.env.example
.env.local-llm.example
```

## Notes

- RAG/embedding은 mock과 OpenAI-compatible 서버를 모두 지원합니다. 실제 검색 품질 평가는 embedding 모델과 `PGVECTOR_DIMENSION` 설정이 맞아야 합니다.
- Project Chat은 현재 소스 검증을 통과한 `source_file` chunk만 기본 답변 근거로 사용합니다.
- 현재 소스 파일을 수정하거나 브랜치/HEAD가 바뀐 뒤에는 RAG 또는 Project Chat 화면의 인덱스 상태를 확인하고 필요 시 현재 소스를 다시 인덱싱하세요.
- LLM 매핑 분석과 AI 코드리뷰는 `.env`의 `LLM_PROVIDER` 설정에 따라 mock 또는 로컬 LLM을 사용합니다.

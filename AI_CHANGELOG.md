# AI Change Log

## 2026-06-08

### source_file 인덱스 상태 확인과 원클릭 재인덱싱

- RAG와 Project Chat 화면에 Current HEAD, Indexed HEAD, source_file chunk/vector 수, 현재 코드와 불일치/검증 불가 chunk 수를 표시했습니다.
- `src/rag/source_index_service.py`를 추가해 source_file 인덱스 상태 계산과 현재 HEAD 기준 재인덱싱을 공통 서비스로 분리했습니다.
- `현재 소스 다시 인덱싱` 버튼은 기존 source_file chunk/vector를 정리한 뒤 현재 Git HEAD 기준으로 chunk와 embedding을 다시 생성합니다.
- 삭제된 파일이나 수정된 라인의 오래된 근거가 Project Chat 답변에 남지 않도록 재인덱싱 경로를 추가했습니다.
- `README.md`, `README_ARCHITECTURE.md`, `docs/ai-technical-overview.md`에 소스 인덱스 상태 확인과 재인덱싱 흐름을 반영했습니다.
- source_file 인덱스 refresh 필요 판단 테스트를 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m pytest -q` 통과(`31 passed`), `.venv\Scripts\python.exe -m compileall app.py src` 통과.

### AI 기술 개요 문서 추가

- `docs/ai-technical-overview.md`를 추가해 대외 소개용 AI 활용 흐름, 기능별 AI 사용 방식, RAG/Project Chat 안전장치, traceability, 현재 한계를 정리했습니다.
- `AGENTS.md`에는 AI-facing 동작 변경 시 `docs/ai-technical-overview.md`를 갱신하라는 운영 규칙만 남기고, RAG evidence 상세 용어는 기술 개요 문서로 분리했습니다.
- `README.md` 초반에 AI/LLM 활용 흐름 표와 AI 기술 개요 문서 링크를 추가했습니다.
- 공개 README에서는 `stale` 같은 내부 상태명 대신 현재 파일 일치 여부 검증이라는 표현으로 정리했습니다.

### 개발계획 관리 UX 개선

- 개발계획 업로드 화면을 `현재 계획`, `직접 수정`, `Excel 업로드`, `일괄 업데이트`, `양식` 탭 구조의 개발계획 관리 화면으로 바꿨습니다.
- 개발계획 Excel 양식 다운로드와 필수/선택 컬럼 안내를 추가했습니다.
- 업로드 파일을 저장하기 전에 미리보기, 검증 결과, 수정/오류 요약을 표시하도록 했습니다.
- 프로그램별 개발계획을 직접 수정하고, 선택한 프로그램들의 status/progress_rate를 일괄 업데이트할 수 있게 했습니다.
- 개발계획 관리 서비스와 focused tests를 추가했습니다.
- `ROADMAP.md`의 `Development plan management UX improvement` 작업을 `Done`으로 변경했습니다.

### 개발자 관리 UX 개선

- 개발자 목록 업로드 화면을 `현재 데이터`, `직접 추가`, `Excel 업로드`, `양식` 탭 구조의 개발자 관리 화면으로 바꿨습니다.
- 개발자 Excel 양식 다운로드와 필수/선택 컬럼 안내를 추가했습니다.
- 업로드 파일을 저장하기 전에 미리보기, 검증 결과, 신규/수정/오류 요약을 표시하도록 했습니다.
- 개발자를 직접 추가/수정/삭제할 수 있게 했고, 삭제 전 담당 프로그램 연결 해제 영향을 표시하도록 했습니다.
- 개발자 관리 서비스와 focused tests를 추가했습니다.
- `ROADMAP.md`의 `Developer management UX improvement` 작업을 `Done`으로 변경했습니다.

### 프로그램 관리 UX 2차 개선

- 프로그램 관리 화면에 `직접 추가` 탭을 추가해 Excel 없이 프로그램을 등록할 수 있게 했습니다.
- `현재 데이터` 탭에서 프로그램을 선택해 수정할 수 있게 했습니다.
- 프로그램 삭제 전 연결된 매핑, 리스크, 구현상태 분석 건수를 표시하고 확인 후 삭제하도록 했습니다.
- 프로그램 수동 관리 서비스와 입력 검증 테스트를 추가했습니다.
- `ROADMAP.md`의 `Program management UX improvement` 작업을 `Done`으로 변경했습니다.

### 프로그램 관리 UX 1차 개선

- `ROADMAP.md`의 `Program management UX improvement`를 `In Progress`로 전환하고 1차 완료 항목을 체크했습니다.
- 프로그램 관리 화면을 `현재 데이터`, `Excel 업로드`, `양식` 탭 구조로 바꿨습니다.
- 프로그램 Excel 양식 다운로드와 필수/선택 컬럼 안내를 추가했습니다.
- 업로드 파일을 저장하기 전에 컬럼 매핑, 미리보기, 검증 결과, 신규/수정/오류 요약을 표시하도록 했습니다.
- 필수값, 중복 `program_id`, 날짜 형식/순서, `progress_rate` 범위 검증을 추가했습니다.
- 오류가 있는 행은 저장에서 제외하고 검증 통과 행만 저장하도록 했습니다.
- 프로그램 import 검증 서비스와 focused tests를 추가했습니다.

### 로드맵 관리 문서 추가

- `ROADMAP.md`를 추가해 우선순위, 작업 상태, 체크리스트, 관련 AI 변경 로그, 커밋 해시를 추적하도록 했습니다.
- 데이터 관리 UX 개선을 P0 작업으로 등록했습니다.
- Project Chat/RAG/Mapping/운영 개선 후보를 P1/P2 작업으로 정리했습니다.
- `AGENTS.md`에 로드맵 확인, 상태 변경, 체크리스트 갱신, 완료 시 로그/커밋 연결 규칙을 추가했습니다.

### Project Chat 전용 메뉴 추가

- `Project Chat` 화면을 추가해 ChatGPT처럼 프로젝트에 대해 대화형으로 질문할 수 있게 했습니다.
- 기존 검증형 RAG chat 서비스를 재사용해 기본 답변 근거를 현재 파일 검증을 통과한 `source_file` chunk로 제한했습니다.
- 프로젝트별 대화 히스토리를 Streamlit session state에 유지하고, 답변별 검색 근거와 검증 상태를 확인할 수 있게 했습니다.
- 사이드바 `AI 분석` 그룹에 `Project Chat` 메뉴를 추가했습니다.

### README 문서 업데이트

- `README.md`에 Project Chat, 검증형 source_file RAG, Alembic migration, RAG metadata 설명을 반영했습니다.
- `README_ARCHITECTURE.md`의 아키텍처 다이어그램, RAG 흐름, 기능 목록, 제한사항, 주요 UI/서비스 목록을 최신 구현에 맞게 수정했습니다.

### 현재 소스 검증형 RAG 검색 챗 추가

- RAG 인덱싱 대상에 `source_file`을 추가해 현재 Git HEAD 기준 실제 소스 파일 내용을 chunk로 저장하도록 했습니다.
- `source_file` metadata에 `file_path`, `line_start`, `line_end`, `content_hash`, `chunk_content_hash`, `indexed_head_hash`, `source_snapshot`을 저장하도록 했습니다.
- 검색 결과가 현재 파일의 같은 라인 범위와 hash를 유지하는지 확인하는 source verification 서비스를 추가했습니다.
- RAG Search 화면에 `source_file` source type과 검증 상태(`verified`, `stale`, `invalid`, `historical`) 표시를 추가했습니다.
- 검증된 현재 소스 chunk만 기본 근거로 사용하는 `Chat` 탭을 추가했습니다.
- 삭제되었거나 변경된 라인을 현재 코드처럼 답변하지 않도록 stale/invalid chunk를 답변 근거에서 제외했습니다.
- source file chunking과 verification 테스트를 추가했습니다.

### Alembic DB 마이그레이션 도입

- `alembic.ini`, `migrations/env.py`, migration template을 추가했습니다.
- 현재 애플리케이션 스키마를 baseline migration으로 분리했습니다.
- 매핑 피드백 컬럼 추가를 별도 migration으로 분리했습니다.
- `src/db/init_db.py`의 누적 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 목록을 제거하고 Alembic 실행 흐름으로 바꿨습니다.
- 기존 DB에 `alembic_version`이 없으면 현재 스키마를 baseline으로 stamp한 뒤 이후 migration을 적용하도록 했습니다.
- DB migration 사용법을 `docs/db-migrations.md`에 정리했습니다.

### 에이전트 작업 지침 추가

- 루트에 `AGENTS.md`를 추가해 코딩 에이전트가 의미 있는 변경 후 `AI_CHANGELOG.md`를 업데이트하도록 명시했습니다.
- DB 스키마 변경은 Alembic migration으로만 관리하고 `src/db/init_db.py`에 수동 `ALTER TABLE` 목록을 추가하지 않도록 명시했습니다.
- `README.md` 초반에 `AI_CHANGELOG.md`와 `AGENTS.md` 안내를 추가했습니다.

### 매핑 피드백 기능 추가

- `program_commit_mappings`에 사용자 피드백 컬럼을 추가했습니다.
- 매핑 화면에 `매핑 피드백` 모드를 추가했습니다.
- 사용자가 AI 매핑 결과의 관련 여부, 관련도 점수, 구현상태, 판단 근거를 보정할 수 있게 했습니다.
- 보정된 매핑값이 `Commit Impact`, `Program Detail`, `AI Progress`, `Risk Analysis`에서 사용되도록 관련 서비스 로직을 조정했습니다.

### 테스트 추가

- `pytest`를 개발 의존성에 추가했습니다.
- 매핑 후보 점수, LLM JSON 파싱, Git diff path 파싱, 상태 정규화, 피드백 상태 정규화 테스트를 추가했습니다.

### 검증

- `python -m py_compile app.py src\db\models.py src\db\init_db.py src\services\mapping_feedback_service.py src\services\commit_impact_service.py src\services\progress_service.py src\services\risk_service.py src\services\program_analysis_service.py src\ui\mapping_page.py` 통과.
- `.venv\Scripts\python.exe -m pytest -q` 통과.
- 테스트 결과: `7 passed`.

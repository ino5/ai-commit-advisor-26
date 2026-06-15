# AI 변경 이력

## 2026-06-15

### Application Preview expanded sections

- `docs/application-preview.md`의 화면별 `<details>` 접힘 구조를 제거하고 모든 screenshot 설명과 이미지를 기본 펼침 상태로 보이게 했습니다.
- 각 화면 이름은 `Preview Screens` 아래 `###` heading으로 정리해 문서 목차와 스크롤 탐색이 자연스럽게 유지되도록 했습니다.
- Roadmap에 Application Preview 펼침 작업을 등록했습니다.
- 주요 파일: `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `Select-String -Path docs\application-preview.md -Pattern '<details|</details>|<summary' -Encoding UTF8` 결과 없음으로 접힘 태그 제거 확인; heading 확인으로 `Preview Screens` 아래 화면별 `###` heading 확인; Application Preview image/link 존재 확인 PowerShell script 통과(`application-preview links OK`); `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Local setup prerequisites guide

- `docs/setup-and-operations.md`에 로컬 실행 전 준비물 섹션을 추가해 Python 3.11+, Git, Docker Desktop, LM Studio 준비 기준을 실행 전 체크리스트로 정리했습니다.
- mock 모드와 local LLM 모드의 차이를 설치 전에 이해할 수 있도록 설명하고, 처음에는 mock으로 앱/DB/Git 흐름을 확인한 뒤 실제 AI 품질 검증 단계에서 LM Studio를 연결하도록 안내했습니다.
- LM Studio에서 준비할 chat 모델 `qwen2.5-coder-7b-instruct`와 embedding 모델 `text-embedding-nomic-embed-text-v1.5`, `.env.local-llm.example`의 `PGVECTOR_DIMENSION=768` 연결 관계를 문서화했습니다.
- Roadmap에 로컬 준비물 가이드 작업을 등록했습니다.
- 주요 파일: `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `Select-String -Path docs\setup-and-operations.md -Pattern '^## |^### ' -Encoding UTF8`로 새 `로컬 실행 전 준비물` 섹션과 하위 항목 순서 확인; `docs/setup-and-operations.md` 상대 링크 존재 확인 PowerShell script 통과(`setup-and-operations links OK`); `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### README preview-first section ordering

- README 상단 흐름을 `Application Preview`, `빠른 시작`, `샘플 프로젝트`가 먼저 보이도록 재배치했습니다.
- 상세 설명 성격의 `주요 기능`, `Git 저장소 접근 모델`, `아키텍처 요약`은 실행/미리보기 진입점 뒤로 내려 README 첫 스캔 흐름을 정리했습니다.
- 문서 목록에서 `Application Preview`, 사용 가이드, 기능 가이드, 설치/운영 문서를 먼저 찾을 수 있도록 링크 순서를 조정했습니다.
- Roadmap에 README 문서 순서 조정 작업을 완료 항목으로 기록했습니다.
- 주요 파일: `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `Select-String -Path README.md -Pattern '^## ' -Encoding UTF8`로 `Application Preview`, `빠른 시작`, `샘플 프로젝트`, `주요 기능`, `Git 저장소 접근 모델`, `아키텍처 요약`, `문서`, `프로젝트 구조`, `참고 사항` 순서 확인; README 상대 링크 존재 확인 PowerShell script 통과(`README links OK`); `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### First-run and empty-state preparation guide

- `first_run_service.py`를 추가해 프로젝트/Git/프로그램/Mapping/source/vector/Knowledge Graph 준비 상태를 공통 `FirstRunAction` 목록으로 계산하도록 했습니다.
- Home의 `다음 작업`을 단순 문구에서 상태, 현재 값, 다음 조치, 이동 버튼, 보조 설명이 있는 준비 작업 목록으로 바꿨습니다.
- `AI 운영 현황 > 운영 준비` 탭에 같은 `다음 준비 작업` 영역을 추가해 처음 실행하거나 데이터가 비어 있을 때 어떤 화면에서 상태를 채워야 하는지 바로 이동할 수 있게 했습니다.
- README, 기능 가이드, Application Preview, AI 기술 개요, 아키텍처, 운영 가이드, engineering decision, Roadmap을 first-run/empty-state 안내 기준으로 갱신했습니다.
- 주요 파일: `src/services/first_run_service.py`, `src/ui/home_page.py`, `src/ui/ai_evidence_page.py`, `tests/test_first_run_service.py`, `README.md`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\first_run_service.py src\ui\home_page.py src\ui\ai_evidence_page.py tests\test_first_run_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_first_run_service.py tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 10개 테스트 통과; Browser로 `http://127.0.0.1:8513/?project_id=4`의 Home에서 `다음 작업`, `Mapping`, `Knowledge Graph`, 이동 버튼 표시와 `StreamlitAPIException`/`Traceback` 미표시 확인; 같은 URL의 `AI 운영 현황 > 운영 준비`에서 `다음 준비 작업`, Mapping/Knowledge Graph 안내, 이동 버튼 표시와 예외 미표시 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 156개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Graph-aware weekly report

- `AI 운영 현황 > 주간 보고서` Markdown에 Knowledge Graph freshness, node/edge summary, class/import/impact path 요약, 주요 `program -> commit -> file -> class` path table을 추가했습니다.
- AI Resource Radar, 미해결 리스크, AI Progress gap 항목에 프로그램별 graph path 근거를 함께 표시하고, Neo4j가 꺼져 있거나 graph preview가 실패해도 보고서 생성이 계속되도록 했습니다.
- 보고서 metadata에 PL Briefing provider/model/mode/validation, 최근 provider/model 목록, 호출 fallback/실패 수, Knowledge Graph 상태, Project Chat GraphRAG assistant message/evidence 사용량을 남기도록 했습니다.
- README, 기능 가이드, Application Preview, AI 기술 개요, 아키텍처, 운영 가이드, engineering decision, Roadmap을 graph-aware weekly report 기준으로 갱신했습니다.
- 주요 파일: `src/services/ai_evidence_service.py`, `tests/test_ai_evidence_service.py`, `README.md`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\ai_evidence_service.py tests\test_ai_evidence_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 6개 테스트 통과; Browser로 `http://127.0.0.1:8512/?project_id=4`의 `AI 운영 현황 > 주간 보고서`에서 text area value 기준 `Knowledge Graph 영향 요약`, `주요 Graph Impact Path`, `보고서 Metadata`, `Project Chat GraphRAG` 표시와 `StreamlitAPIException`/`Traceback` 미표시 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 152개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Graph-aware Project Chat question templates

- Project Chat `대화` 영역에 `관계 질문` 템플릿을 추가했습니다. 템플릿은 프로그램 구현 근거, 커밋 영향 범위, class/domain 연결, 리스크 근거처럼 Neo4j graph evidence가 잘 드러나는 질문을 바로 실행하도록 돕습니다.
- 템플릿 버튼은 `get_project_graph_freshness` 결과가 `latest`일 때만 활성화됩니다. `stale`, `missing`, `failed`, `skipped` 상태에서는 현재 상태와 `Knowledge Graph`에서 실행해야 할 보정 경로를 안내합니다.
- 템플릿 실행은 현재 Project Chat session에 사용자 질문으로 들어가며, 답변은 기존 Project Chat flow처럼 verified source evidence와 graph evidence 정책을 사용합니다.
- README, 기능 가이드, AI 기술 개요, 아키텍처, 운영 가이드, engineering decision, Roadmap을 관계 질문 템플릿의 목적과 최신성 gate 기준으로 갱신했습니다.
- 주요 파일: `src/ui/project_chat_page.py`, `tests/test_project_chat_page.py`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\project_chat_page.py tests\test_project_chat_page.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_page.py tests\test_project_chat_service.py tests\test_project_chat_history_service.py tests\test_documentation_images.py -q` 12개 테스트 통과; Browser로 `http://127.0.0.1:8510/?project_id=4`의 `Project Chat` 화면에서 `관계 질문`, `프로그램 구현 근거`, `커밋 영향 범위`, `클래스 연결`, `도메인 연결`, `리스크 근거` 표시와 `StreamlitAPIException`/`Traceback` 미표시 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 152개 테스트 통과; 금지 용어 검색 매치 없음; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Source parser accuracy expansion

- Knowledge Graph와 Project Chat GraphRAG가 사용하는 Java source 구조 추출을 보강했습니다. parser는 주석/문자열을 제거한 뒤 `package`, `import`, `class`, `interface`, `enum`, `record`, annotation type을 읽고, static import는 class 기준으로 정규화합니다.
- nested member type qualified name을 `Outer.Inner` 형태로 저장해 클래스 관계도와 graph seed가 내부 type을 더 정확히 사용할 수 있게 했습니다. method 내부 local class, 주석, 문자열 안의 가짜 선언은 graph node로 만들지 않습니다.
- generated source, build output, test fixture, `package-info.java`, `module-info.java`를 Java class/import graph에서 제외하고, type 선언을 찾지 못한 Java 파일 수를 `GraphPayload.warnings`와 `Neo4jSyncResult.warnings`로 분리했습니다. `Knowledge Graph` 화면은 이 값을 `동기화 준비 경고`와 sync result warning으로 표시합니다.
- README, 기능 가이드, AI 기술 개요, 아키텍처, 설치/운영 가이드, engineering decision, Roadmap을 경량 Java parser와 coverage warning 정책 기준으로 갱신했습니다.
- 주요 파일: `src/services/neo4j_graph_service.py`, `src/ui/knowledge_graph_page.py`, `tests/test_neo4j_graph_service.py`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\neo4j_graph_service.py src\ui\knowledge_graph_page.py tests\test_neo4j_graph_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_documentation_images.py -q` 17개 테스트 통과; Browser로 `http://127.0.0.1:8509/?project_id=4`의 `AI 운영 현황 -> Knowledge Graph` 이동 후 `Knowledge Graph`, `Graph 상태`, `동기화 대상 요약`, `클래스 관계도` 표시와 `StreamlitAPIException`/`Traceback` 미표시 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 149개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Neo4j production hardening

- Neo4j Knowledge Graph full sync와 incremental sync를 batch write 기반으로 바꿨습니다. `NEO4J_WRITE_BATCH_SIZE`로 node/edge batch 크기를 조절하고, 각 write batch와 연결 확인에는 `NEO4J_RETRY_ATTEMPTS`, `NEO4J_RETRY_BACKOFF_SECONDS` 기준 retry/backoff를 적용합니다.
- 동기화 결과와 `project_graph_sync_state.raw_metadata`에 요청 node/edge 수, batch 수, 완료 batch 수, written count, retry count, retry error, failed operation을 남기도록 했습니다. 실패 메시지는 일부 batch가 반영됐을 수 있음을 알리고 `전체 재동기화`로 복구하도록 안내합니다.
- `Knowledge Graph` 화면의 동기화 결과에 `Neo4j 동기화 실행 세부` expander를 추가해 운영자가 batch/retry/partial failure 상태를 확인할 수 있게 했습니다.
- `.env` 예시와 `docker-compose.yml`에 Neo4j batch/retry 설정을 추가하고, README, 기능 가이드, AI 기술 개요, 아키텍처, 설치/운영 가이드, engineering decision, Roadmap을 운영 안정화 정책 기준으로 갱신했습니다.
- 주요 파일: `src/services/neo4j_graph_service.py`, `src/ui/knowledge_graph_page.py`, `src/utils/config.py`, `tests/test_neo4j_graph_service.py`, `.env.example`, `.env.local-llm.example`, `docker-compose.yml`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\neo4j_graph_service.py src\ui\knowledge_graph_page.py src\utils\config.py tests\test_neo4j_graph_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_documentation_images.py -q` 15개 테스트 통과; Browser로 `http://127.0.0.1:8508/?project_id=4`의 `AI 운영 현황 -> Knowledge Graph` 이동 후 `Knowledge Graph`, `Graph 상태`, `동기화 대상 요약`, `최신 변경분만 Neo4j 반영`, `전체 재동기화` 표시와 `StreamlitAPIException`/`Traceback` 미표시 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `docker compose config -q` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 147개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Git Sync follow-up action orchestrator

- `Git 동기화` 화면에 `동기화 후 다음 작업` 패널을 추가했습니다. Git Sync가 commit/diff 수집만 담당한다는 경계를 유지하면서, 이후 현재 소스 근거 갱신, 검색 준비, Mapping, Risk Analysis, Knowledge Graph 갱신을 현재 프로젝트 상태 기준 권장 순서로 보여줍니다.
- `git_followup_service.py`를 추가해 Repo HEAD/DB Sync HEAD, source index stale 여부, missing embedding, Mapping 미완료/실패 commit, Risk Finding, Knowledge Graph freshness를 조합해 후속 작업 상태를 계산하도록 했습니다. 각 항목은 상태, 현재 값, 예상 소요, 비용/부하 주의, 이동할 화면을 제공합니다.
- Git Sync 화면은 권장 순서와 `나중에 해도 됨` 항목을 나눠 표시하고, 각 작업을 자동 실행하지 않고 관련 화면으로 이동하는 재시작 가능한 action을 제공합니다. embedding/LLM/Neo4j 작업은 사용자가 명시적으로 실행해야 합니다.
- Application Preview의 Git 동기화 screenshot과 screenshot capture 기준을 새 패널 기준으로 갱신했습니다. Browser 검증 중 Streamlit expander 중첩 오류를 발견해 수정하고, 재발 방지를 위해 `docs/failure-history.md`에 기록했습니다.
- README, 기능 가이드, AI 기술 개요, 아키텍처, 운영 가이드, engineering decision, Roadmap을 Git Sync 후속 작업 흐름 기준으로 갱신했습니다.
- 주요 파일: `src/services/git_followup_service.py`, `src/ui/git_page.py`, `src/utils/runtime_estimator.py`, `tests/test_git_followup_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/git-sync.png`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/application-preview.md`, `docs/engineering-decisions.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\git_followup_service.py src\ui\git_page.py src\utils\runtime_estimator.py scripts\capture_feature_screenshot.py tests\test_git_followup_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_git_followup_service.py tests\test_runtime_estimator.py tests\test_documentation_images.py -q` 6개 테스트 통과; Browser로 `http://127.0.0.1:8507`의 `Git 동기화` 화면에서 `동기화 후 다음 작업`, `권장 순서`, `현재 소스 근거 갱신`, `검색 준비 생성`, `Mapping 분석`, `Risk Analysis 재계산` 표시와 `StreamlitAPIException` 미표시 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://127.0.0.1:8507 --feature git-sync --surface local --height 1400 --project-name "AAA Sample Shop Rich Demo (4)" --expect-text "동기화 후 다음 작업" --expect-text "현재 소스 근거 갱신" --expect-text "Mapping 분석" --forbid-text "StreamlitAPIException"` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 144개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Local LLM verification routine

- mock 실행과 실제 local LLM/embedding 실행을 구분할 수 있도록 `scripts/run_local_ai_verification.py`를 추가했습니다. 이 script는 project 기준으로 embedding 연결 확인, PL Briefing, Project Chat, AI Code Review, 선택적 Mapping을 실행하고 provider/model/base URL, fallback 여부, invocation telemetry, 결과 요약을 Markdown으로 남깁니다.
- `AI 운영 현황`에 `실제 LLM 검증` 탭을 추가해 local provider로 성공한 최근 호출, embedding live check, 주요 LLM 기능 coverage, fallback/failure 상태를 pass/warn/fail로 확인할 수 있게 했습니다. 탭 상단에는 검증 대상 LLM/Embedding 설정을 노출해 화면만 봐도 어떤 provider/model 기준인지 알 수 있습니다.
- local verification은 유료 외부 API나 CI 의존성을 만들지 않도록 mock DB/telemetry 기반 테스트로 검증하고, 실제 모델 실행 절차는 `docs/local-llm-verification.md`에 별도 문서화했습니다.
- README, 기능 가이드, Application Preview 설명, AI 기술 개요, 아키텍처, 운영 가이드, engineering decision, Roadmap을 local LLM verification 흐름에 맞게 갱신했습니다.
- 주요 파일: `scripts/run_local_ai_verification.py`, `src/services/ai_evidence_service.py`, `src/ui/ai_evidence_page.py`, `tests/test_ai_evidence_service.py`, `docs/local-llm-verification.md`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/application-preview.md`, `docs/engineering-decisions.md`, `scripts/capture_feature_screenshot.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\ai_evidence_service.py src\ui\ai_evidence_page.py scripts\run_local_ai_verification.py scripts\capture_feature_screenshot.py tests\test_ai_evidence_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 6개 테스트 통과; `.\.venv\Scripts\python.exe scripts\run_local_ai_verification.py --help` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 142개 테스트 통과; Browser로 `http://127.0.0.1:8506`의 `AI 운영 현황 > 실제 LLM 검증`에서 `검증 대상 설정`, `Local LLM 설정`, `Local Embedding 설정`, `실제 LLM 검증 요약`, `Embedding live check`, `LLM 기능 live coverage`, `Fallback / failure`, `최근 live verification 호출` 표시 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Project-level AI quality scorecard

- `AI 운영 현황 > 품질 점검`을 sample project 중심 존재 확인에서 현재 프로젝트 기준 품질 상태판으로 확장했습니다. Mapping 판단불가/낮은 관련도/짧은 reason/피드백 미완료/fallback, Project Chat verified source 사용률/insufficient evidence/excluded count, PL Briefing provider/model/validation/repair/fallback, AI Code Review 결과 분포, Knowledge Graph class/import/impact path와 freshness를 함께 표시합니다.
- `EvidenceStatusRow`에 이동 대상 정보를 추가하고, 품질 점검의 주의/실패 항목에서 `Mapping`, `Project Chat`, `Dashboard`, `AI Code Review`, `Knowledge Graph` 등 관련 화면으로 바로 이동할 수 있게 했습니다.
- Knowledge Graph 품질 신호는 전체 소스 graph를 다시 파싱하지 않고 Neo4j 저장 graph readback과 preview를 사용해 `AI 운영 현황` 진입 비용을 줄였습니다.
- 사용자-facing 기능 가이드, Application Preview 설명, AI 기술 개요, 아키텍처, engineering decision, Roadmap을 프로젝트 AI 품질 점검 기준으로 갱신했습니다.
- 주요 파일: `src/services/ai_evidence_service.py`, `src/ui/ai_evidence_page.py`, `tests/test_ai_evidence_service.py`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\ai_evidence_service.py src\ui\ai_evidence_page.py tests\test_ai_evidence_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 5개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 141개 테스트 통과; Browser로 `http://127.0.0.1:8505`의 `AI 운영 현황 > 품질 점검`에서 `프로젝트 AI 품질 점검`, `verified_source=`, `feedback_pending=`, `fallback=`, `Mapping로 이동` 표시와 `Mapping` 화면 이동 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Knowledge Graph exploration UI

- `Knowledge Graph` 화면에 `관계 탐색` 탭을 추가해 Neo4j에 저장된 프로그램, 클래스, 도메인, 커밋 node를 선택하고 주변 path를 조회할 수 있게 했습니다. 탐색은 최대 3-depth와 최대 path 수로 제한해 대형 graph 전체를 한 번에 펼치지 않습니다.
- Neo4j graph 탐색 service를 추가해 node 후보, 선택 node detail, node properties, related count, relationship type filter, path row를 read query로 조회하도록 했습니다. 관계 필터는 선택한 edge type이 포함된 path를 좁혀 보는 보조 조건으로 동작합니다.
- README, Application Preview 설명, 기능 가이드, AI 기술 개요, 아키텍처, screenshot capture 기준, Roadmap을 선택 node 주변 관계 탐색 기준으로 갱신했습니다.
- 주요 파일: `src/services/neo4j_graph_service.py`, `src/ui/knowledge_graph_page.py`, `tests/test_neo4j_graph_service.py`, `scripts/capture_feature_screenshot.py`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\neo4j_graph_service.py src\ui\knowledge_graph_page.py tests\test_neo4j_graph_service.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py -q` 11개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_documentation_images.py -q` 12개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 141개 테스트 통과; Browser로 `http://127.0.0.1:8504`의 `Knowledge Graph` 화면에서 `Graph 상태`, `동기화 대상 요약`, `관계 탐색` 탭 표시와 `NEO4J_ENABLED=false` 환경의 비활성 안내 렌더링 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### AI operations graph status

- `AI 운영 현황` 상단의 `연결된 AI` 영역에 Neo4j 연결 상태, Knowledge Graph freshness, Neo4j 저장 graph readback, 최근 Project Chat GraphRAG evidence 상태를 추가했습니다. Graph 상태가 준비되지 않았거나 오래된 경우 LLM/embedding 상태와 별도로 원인을 확인할 수 있습니다.
- `Knowledge Graph로 이동` shortcut action을 추가해 graph 관련 경고가 보일 때 바로 `Knowledge Graph` 화면으로 이동하도록 했습니다.
- AI 운영 상태 service에서 `get_neo4j_connection_status`, `get_project_graph_freshness`, `get_neo4j_project_summary`, 최근 `project_chat_messages.raw_metadata.graph_evidence_metadata`를 조합해 `Neo4j`, `Knowledge Graph`, `Graph Readback`, `Project Chat GraphRAG` 상태 row를 구성하도록 했습니다.
- Application Preview capture 기준, README, 기능 가이드, AI 기술 개요, 아키텍처, 운영 가이드, Roadmap을 graph 운영 상태 표시 기준으로 갱신했습니다.
- 주요 파일: `src/services/ai_evidence_service.py`, `src/ui/ai_evidence_page.py`, `tests/test_ai_evidence_service.py`, `scripts/capture_feature_screenshot.py`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\ai_evidence_service.py src\ui\ai_evidence_page.py tests\test_ai_evidence_service.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 5개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 139개 테스트 통과; Browser로 `http://127.0.0.1:8503`의 `AI 운영 현황` 화면에서 `Neo4j`, `Knowledge Graph`, `Graph Readback`, `Project Chat GraphRAG`, `Knowledge Graph로 이동` 표시 확인; `Knowledge Graph로 이동` 클릭 후 `Knowledge Graph` 화면의 `Graph 상태`, `동기화 대상 요약` 표시 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Knowledge Graph freshness and incremental Neo4j sync

- `project_graph_sync_state` PostgreSQL metadata table을 추가해 Repo HEAD, DB Sync HEAD, Graph HEAD, sync mode, node/edge count, 마지막 commit row, mapping update 기준을 저장하도록 했습니다. Schema 변경은 Alembic migration `20260615_0010_add_project_graph_sync_state.py`로 처리했습니다.
- `Knowledge Graph` 화면에 `Graph 상태`를 추가해 `최신`, `갱신 필요`, `저장 필요`, `실패`, `미사용` 상태와 Repo HEAD/DB Sync HEAD/Graph HEAD를 비교해 보여줍니다. 동기화 action도 `최신 변경분만 Neo4j 반영`, `전체 재동기화`, `Neo4j 저장 상태 조회`로 구분했습니다.
- Neo4j full sync가 성공/실패 metadata를 저장하도록 변경하고, incremental sync를 추가했습니다. 증분 반영은 변경된 Java file path의 current source class/import 관계를 제거 후 재생성하고, `MAPPED_TO_COMMIT` edge는 현재 DB mapping 기준으로 refresh합니다. 과거 commit이 file을 건드린 `TOUCHES_FILE` historical relation은 삭제하지 않습니다.
- Neo4j edge에 `graph_scope` property를 추가해 `current_source`, `historical_git`, `analysis`, `project_structure` 성격을 구분했습니다. Project Chat GraphRAG는 기존처럼 저장 graph를 보조 근거로 사용하되, Knowledge Graph 화면에서 stale 여부를 먼저 확인할 수 있습니다.
- 프로젝트 reset/delete lifecycle에 `ProjectGraphSyncState` 삭제를 포함해 분석 데이터를 초기화한 뒤 과거 graph sync 상태가 남지 않도록 했습니다.
- README, Application Preview 설명, 기능 가이드, AI 기술 개요, 아키텍처, 운영 가이드, DB migration guidance, engineering decision, demo user guide, Roadmap을 최신성/증분 동기화 기준으로 갱신했습니다.
- 주요 파일: `src/services/neo4j_graph_service.py`, `src/ui/knowledge_graph_page.py`, `src/db/models.py`, `src/services/project_management_service.py`, `migrations/versions/20260615_0010_add_project_graph_sync_state.py`, `tests/test_neo4j_graph_service.py`, `tests/test_project_management_service.py`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/db-migrations.md`, `docs/application-preview.md`, `docs/demo-user-guide.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\neo4j_graph_service.py src\ui\knowledge_graph_page.py src\db\models.py src\services\project_management_service.py tests\test_neo4j_graph_service.py tests\test_project_management_service.py migrations\versions\20260615_0010_add_project_graph_sync_state.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m alembic upgrade head` 통과; `.\.venv\Scripts\python.exe -m alembic heads`와 `.\.venv\Scripts\python.exe -m alembic current`에서 `20260615_0010 (head)` 확인; `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_project_management_service.py -q` 13개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 137개 테스트 통과; 실제 Docker Neo4j/PostgreSQL 환경에서 임시 Git repo 기반 full sync `completed 9/18`, incremental sync `completed 10/22`, freshness `latest` 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Project Chat GraphRAG context injection

- `Project Chat`이 verified `source_file` 근거를 확보한 뒤 Neo4j graph read model에서 `program -> commit -> file -> class` 영향 경로, `class -> imports -> class` 관계, domain summary를 보조 근거로 조회하도록 추가했습니다. Graph evidence는 현재 코드 사실을 대체하지 않으며, verified source가 없으면 기존 insufficient-evidence 정책을 유지합니다.
- 질문, 표준용어 확장 쿼리, 검색된 파일/class/commit metadata에서 graph seed를 추출하고, Project Chat prompt에는 graph context를 별도 섹션으로 넣었습니다. Mock/LLM 호출 telemetry에도 graph evidence count/status/error metadata를 남깁니다.
- Project Chat 화면, RAG 소스 Q&A, citation export, 저장 대화 재열람, `AI 운영 현황 > 근거 추적`에서 source evidence와 graph evidence를 분리해 확인할 수 있게 했습니다. Graph evidence는 `project_chat_messages.raw_metadata`에 저장하므로 PostgreSQL schema migration은 추가하지 않았습니다.
- GraphRAG 보조 근거의 안전 정책과 사용자 흐름을 README, 기능 가이드, AI 기술 개요, 아키텍처, 운영 가이드, DB migration guidance, Application Preview 설명, engineering decision에 반영했습니다.
- 주요 파일: `src/services/neo4j_graph_service.py`, `src/rag/chat_service.py`, `src/rag/chat_history_service.py`, `src/ui/project_chat_page.py`, `src/ui/rag_page.py`, `src/services/ai_evidence_service.py`, `src/ui/ai_evidence_page.py`, `tests/test_neo4j_graph_service.py`, `tests/test_project_chat_service.py`, `tests/test_project_chat_history_service.py`, `tests/test_ai_evidence_service.py`, `README.md`, `docs/ai-technical-overview.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `docs/db-migrations.md`, `docs/application-preview.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\neo4j_graph_service.py src\rag\chat_service.py src\rag\chat_history_service.py src\ui\project_chat_page.py src\ui\rag_page.py src\services\ai_evidence_service.py src\ui\ai_evidence_page.py tests\test_neo4j_graph_service.py tests\test_project_chat_service.py tests\test_project_chat_history_service.py tests\test_ai_evidence_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_service.py tests\test_project_chat_history_service.py tests\test_neo4j_graph_service.py tests\test_ai_evidence_service.py -q` 16개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 134개 테스트 통과; `.\.venv\Scripts\python.exe -c "import inspect, streamlit as st; print(inspect.signature(st.json))"`에서 `expanded` 인자 지원 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Graph/AI 후속 개선 후보 Roadmap 정리

- 새 세션에서 바로 후속 작업을 고를 수 있도록 `ROADMAP.md` `Candidate Tasks`에 GraphRAG, Knowledge Graph 신선도/증분 Neo4j 동기화, AI 운영 현황 graph 상태, 그래프 탐색 UI, AI 품질 점검, local LLM 검증 루틴, Git Sync 후속 작업 흐름, Neo4j 운영 안정화, source parser 정확도, 질문 템플릿, graph-aware 보고서, 첫 사용/빈 상태 개선 후보를 정리했습니다.
- 특히 `Knowledge Graph freshness and incremental Neo4j sync` 후보에는 current source graph, historical git graph, analysis graph를 구분하는 설계, 변경 파일별 증분 반영 흐름, 삭제/rename 시 끊어야 하는 관계와 보존해야 하는 이력 관계, stale 표시 UI, 테스트 항목을 상세히 기록했습니다.
- 주요 파일: `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "Project Chat GraphRAG context injection|Knowledge Graph freshness and incremental Neo4j sync|current source graph|historical git graph|최신 변경분만 Neo4j 반영|Graph-Aware Weekly Report" ROADMAP.md`로 후보 섹션 반영 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Knowledge Graph 저장 그래프 조회와 탭별 screenshot 보강

- `Knowledge Graph` 화면의 클래스 관계도, 영향 경로, 노드/엣지 탭이 Neo4j에 저장된 graph read model을 우선 조회하도록 변경했습니다. 저장된 graph가 없을 때만 기존 동기화 대상 preview를 fallback으로 보여줍니다.
- Neo4j 저장 graph에서 class import 관계와 commit-program-file-class 영향 경로를 읽는 `get_neo4j_project_preview`를 추가하고, Cypher alias 충돌로 impact path 조회가 실패하던 문제를 수정했습니다.
- `Application Preview`에 Neo4j 연결/동기화 화면뿐 아니라 클래스 관계도, 커밋 영향 경로, 노드/엣지 저장 상태 screenshot을 각각 추가했습니다. screenshot 자동화도 `Neo4j 저장 그래프 기준`, `Neo4j에서 조회한 저장 상태입니다.`, `IMPORTS_CLASS`, `MAPPED_TO_COMMIT` 같은 실제 readback 증거를 확인하도록 강화했습니다.
- README, 기능 가이드, AI 기술 개요, 아키텍처, 실패 이력, Application Preview 설명을 저장 graph 재조회 기준으로 갱신했습니다.
- 주요 파일: `src/services/neo4j_graph_service.py`, `src/ui/knowledge_graph_page.py`, `tests/test_neo4j_graph_service.py`, `scripts/capture_feature_screenshot.py`, `docs/application-preview.md`, `docs/images/features/knowledge-graph.png`, `docs/images/features/knowledge-graph-class.png`, `docs/images/features/knowledge-graph-impact.png`, `docs/images/features/knowledge-graph-nodes-edges.png`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/failure-history.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\neo4j_graph_service.py src\ui\knowledge_graph_page.py scripts\capture_feature_screenshot.py tests\test_neo4j_graph_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_documentation_images.py -q` 5개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 130개 테스트 통과; `get_neo4j_project_preview(4)`에서 `status=completed`, class 관계 17개, 영향 경로 47개 조회 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8502 --feature knowledge-graph --surface local --height 1400 --project-name "AAA Sample Shop Rich Demo (4)" --expect-text "Neo4j 저장 확인" --expect-text "Neo4j에 node" --expect-text "연결" --expect-text "ON" --forbid-text "NEO4J_ENABLED=false"` 통과; `knowledge-graph-class`, `knowledge-graph-impact`, `knowledge-graph-nodes-edges` screenshot 캡처 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Knowledge Graph preview 증거 보강

- `Application Preview`의 Knowledge Graph 설명과 screenshot을 Neo4j 미연결 preview가 아니라 실제 Neo4j 연결/동기화 완료 상태로 갱신했습니다.
- screenshot capture 기준도 `NEO4J_ENABLED=false` 상태를 금지하고, `Neo4j 동기화` 버튼 실행 후 `Neo4j에 node ... edge ... 동기화` 성공 메시지와 node/edge count가 보이도록 강화했습니다.
- 주요 파일: `scripts/capture_feature_screenshot.py`, `docs/application-preview.md`, `docs/images/features/knowledge-graph.png`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8502 --feature knowledge-graph --surface local --height 1400 --project-name "AAA Sample Shop Rich Demo (4)" --expect-text "Neo4j에 node" --expect-text "연결" --expect-text "ON" --forbid-text "NEO4J_ENABLED=false"` 통과; 캡처 결과에서 Neo4j `연결`, `ON`, `neo4j` database, `node 158개`, `edge 442개` 동기화 성공 메시지와 node/edge count 표를 확인했습니다. `.\.venv\Scripts\python.exe -m py_compile scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_documentation_images.py -q` 1개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Neo4j Knowledge Graph 기반 추가

- Neo4j를 프로젝트 관계 탐색용 read model로 추가하고, `Knowledge Graph` 화면에서 프로젝트, 프로그램, 커밋, 파일, Java class, 도메인 관계를 preview하거나 Neo4j에 동기화할 수 있게 했습니다.
- graph payload는 PostgreSQL의 프로젝트/프로그램/커밋/매핑 데이터와 앱 서버 Git 저장소의 Java package/class/import 구조를 함께 사용해 `project`, `program`, `commit`, `file`, `class`, `domain` node와 `MAPPED_TO_COMMIT`, `TOUCHES_FILE`, `CONTAINS_CLASS`, `IMPORTS_CLASS`, `TOUCHES_DOMAIN` 관계를 구성합니다.
- Docker Compose에 Neo4j service를 추가하고, `.env` 예시와 설정 객체에 `NEO4J_*` 환경 변수를 추가했습니다. 로컬 Python Quick Start와 Docker 앱 모두 Neo4j 동기화를 사용할 수 있도록 기본 활성화했습니다.
- 로컬 Python Quick Start도 Neo4j를 기본으로 함께 실행하도록 `.env.example`, `.env.local-llm.example`, README, 설치/운영 가이드를 조정했습니다. Neo4j 없이 실행해야 할 때만 `NEO4J_ENABLED=false`로 끄도록 안내합니다.
- 실제 Neo4j 동기화 검증 중 schema constraint 생성과 graph write를 같은 transaction에서 실행하면 Neo4j 5가 실패하는 문제를 확인해, schema 준비와 write transaction을 분리하고 재발 방지 테스트와 실패 이력을 추가했습니다.
- 프로젝트 분석 데이터 초기화와 프로젝트 삭제 시 Neo4j graph read model도 best-effort로 정리하도록 lifecycle을 맞췄습니다.
- README, 기능 가이드, Application Preview, 아키텍처, AI 기술 개요, 설치/운영, DB migration guidance, sample project 설계, engineering decision을 갱신하고 `docs/images/features/knowledge-graph.png` screenshot을 추가했습니다.
- 주요 파일: `app.py`, `src/ui/knowledge_graph_page.py`, `src/services/neo4j_graph_service.py`, `src/services/project_management_service.py`, `src/utils/config.py`, `docker-compose.yml`, `.env.example`, `.env.local-llm.example`, `requirements.txt`, `tests/test_neo4j_graph_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/knowledge-graph.png`, `README.md`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/setup-and-operations.md`, `docs/db-migrations.md`, `docs/demo-user-guide.md`, `docs/sample-target-repo-demo-design.md`, `docs/engineering-decisions.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py scripts\capture_feature_screenshot.py tests\test_neo4j_graph_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_project_management_service.py tests\test_documentation_images.py -q` 8개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 129개 테스트 통과; `docker compose config -q` 통과; `docker compose up -d neo4j`와 `docker compose ps neo4j`로 Neo4j container 기동 확인; `get_neo4j_connection_status()`에서 `connected=True` 확인; 실제 Neo4j sync에서 `nodes=1076`, `edges=10263`, `sync_status=completed`, `summary_status=completed` 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature knowledge-graph --surface local --height 1400 --expect-text "Knowledge Graph" --expect-text "동기화 대상 요약" --expect-text "도메인 묶음" --expect-text "클래스 관계도" --expect-text "영향 경로"` 통과; 금지 표현 검색 매칭 없음; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### AI 운영 현황 메뉴와 연결 상태 요약

- 사용자-facing 메뉴명과 화면 제목을 `AI 운영 현황`으로 바꾸고, 기존 검증 중심 화면을 LLM/embedding 연결 상태와 AI 실행 근거를 함께 보는 운영 상태판으로 정리했습니다.
- `연결된 AI` 요약을 추가해 LLM provider/model, embedding provider/model/dimension, 최근 AI 호출, 검색 준비, 호출 요약을 첫 화면에서 확인할 수 있게 했습니다.
- 탭 이름을 `운영 준비`, `근거 추적`, `품질 점검`, `주간 보고서`, `호출 기록`으로 정리하고, 준비/점검 요약 제목도 새 메뉴 성격에 맞췄습니다.
- README, 기능 가이드, AI 기술 개요, Application Preview, 아키텍처, engineering decision, screenshot capture 기준과 `docs/images/features/ai-evidence.png`를 갱신했습니다.
- 주요 파일: `app.py`, `src/ui/ai_evidence_page.py`, `src/services/ai_evidence_service.py`, `tests/test_ai_evidence_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/ai-evidence.png`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 3개 테스트 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature ai-evidence --surface local --height 1400 --expect-text "AI 운영 현황" --expect-text "연결된 AI" --expect-text "운영 준비" --expect-text "운영 준비 요약" --expect-text "호출 기록"` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 126개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### AI 검증 메뉴 목적과 제품 용어 정리

- 사용자-facing 메뉴명을 `AI 검증`으로 바꾸고, 화면 설명을 AI 분석 결과의 준비 상태, 근거 추적, 품질 점검, 보고서, 호출 telemetry를 확인하는 역할로 정리했습니다.
- 기존 readiness helper를 `get_ai_readiness_rows`로 바꿔 코드 식별자도 제품 용어와 맞췄습니다.
- README, 기능 가이드, AI 기술 개요, Application Preview, 아키텍처, 운영/샘플 문서, 변경 이력, 로드맵에서 남아 있던 내부 단계 표현을 제거하고 자연스러운 검증/운영 표현으로 정리했습니다.
- `AI 검증` 메뉴의 존재 이유를 "새 분석을 만드는 곳"이 아니라 "흩어진 AI 실행 결과의 근거, model/provider, fallback, scorecard, 보고서, telemetry를 한곳에서 확인하는 검증 흐름"으로 문서화했습니다.
- 주요 파일: `app.py`, `src/ui/ai_evidence_page.py`, `src/services/ai_evidence_service.py`, `tests/test_ai_evidence_service.py`, `tests/test_resource_metrics_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/ai-evidence.png`, `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_resource_metrics_service.py tests\test_documentation_images.py -q` 12개 테스트 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature ai-evidence --surface local --height 1400 --expect-text "AI 검증" --expect-text "검증 준비" --expect-text "AI 실행 바로가기"` 통과; 제거 대상 영문 약어, 이전 메뉴명, 이전 readiness helper 검색에서 매칭 없음; 어색한 중복 한국어 표현 검색에서 매칭 없음; `.\.venv\Scripts\python.exe -m pytest -q` 126개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### 검증 용어 정리

- 사용자-facing UI, README, 기능 가이드, Application Preview, 샘플 프로젝트 문서, 자동 캡처 기준에서 행사 중심 한국어 표현을 검증, 운영 준비, 분석 재실행, 근거 확인 중심 표현으로 정리했습니다.
- `AI 검증`의 첫 탭과 요약 제목을 `검증 준비`, `검증 준비 요약`으로 바꾸고, 화면 caption과 screenshot을 새 표현 기준으로 갱신했습니다.
- 과거 문서와 engineering decision에서 어색하게 남은 중복 표현을 정리하고, 앞으로 검증 설명은 검증/운영 준비 표현을 우선한다는 결정을 `docs/engineering-decisions.md`에 남겼습니다.
- 주요 파일: `AGENTS.md`, `README.md`, `src/ui/ai_evidence_page.py`, `src/ui/project_page.py`, `src/services/ai_evidence_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/ai-evidence.png`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/sample-target-repo-demo-design.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 3개 테스트 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature ai-evidence --surface local --height 1400 --expect-text "AI 실행 바로가기" --expect-text "검증 준비" --expect-text "검증 준비 요약"` 통과; `$term = [string]([char]0xC2DC) + [string]([char]0xC5F0); rg -n $term .` 매칭 없음; `.\.venv\Scripts\python.exe -m pytest -q` 126개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### AI 검증 실행 cockpit 개선

- `AI 검증`의 `검증 준비` 탭에 `AI 실행 바로가기`를 추가해 Mapping, Risk Analysis, PL Briefing, source_file 검색 준비를 같은 화면에서 바로 실행할 수 있게 했습니다.
- 검증 준비 상태와 AI Scorecard에 `전체/통과/주의/실패` 요약 지표를 추가하고, `주의/실패 우선 확인` 영역을 먼저 보여주도록 정리했습니다.
- 우선 확인 항목은 표에서 잘리지 않도록 알림형 항목으로 표시하고, 전체 상태 표는 접힌 `전체 항목` 영역에서 확인하도록 했습니다.
- AI 검증 서비스에 상태 요약/우선순위 정렬 helper와 검증용 shortcut 실행 결과 wrapper를 추가하고, 관련 단위 테스트를 보강했습니다.
- 기능 가이드, AI 기술 개요, 아키텍처 설명, Application Preview 문구와 `docs/images/features/ai-evidence.png` screenshot을 새 화면 기준으로 갱신했습니다.
- 주요 파일: `src/ui/ai_evidence_page.py`, `src/services/ai_evidence_service.py`, `tests/test_ai_evidence_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/ai-evidence.png`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/architecture.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_ai_evidence_service.py tests\test_documentation_images.py -q` 3개 테스트 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature ai-evidence --surface local --height 1400 --expect-text "AI 실행 바로가기" --expect-text "주의/실패 우선 확인" --expect-text "Source Index"` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 126개 테스트 통과; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### AX AI 검증과 telemetry 구현

- 후보로 발굴했던 6개 개선을 실제 기능으로 승격해 `AI 검증` 화면에 검증 준비 상태, evidence trace, AI scorecard, 주간 보고서 다운로드, AI 호출 telemetry를 추가했습니다.
- `ai_invocation_logs` 테이블과 기록 서비스를 추가해 PL Briefing, commit-based Mapping, Project Chat, AI Code Review의 provider/model, latency, prompt/response length, validation/fallback/error metadata를 저장하도록 했습니다.
- PL Briefing 구조화 응답에 validation을 추가하고, local LLM 응답이 schema를 지키지 못하면 repair prompt를 1회 시도한 뒤 실패 시 fallback reason을 남기도록 했습니다.
- `AI 검증`은 PL Briefing, Mapping, Project Chat, AI Code Review의 저장 근거와 raw metadata를 읽기 전용으로 보여주고, sample project 기준 pass/warn/fail scorecard와 Markdown 주간 점검 보고서를 제공합니다.
- 프로젝트 reset/delete lifecycle에 AI 호출 telemetry를 포함하고, 아키텍처/AI 기술 개요/기능 가이드/DB migration/engineering decision/Application Preview/README를 갱신했습니다.
- 주요 파일: `app.py`, `src/ui/ai_evidence_page.py`, `src/services/ai_evidence_service.py`, `src/services/ai_invocation_service.py`, `src/services/ai_resource_radar_service.py`, `src/rag/chat_service.py`, `src/services/mapping_service.py`, `src/services/code_review_service.py`, `src/services/project_management_service.py`, `src/db/models.py`, `migrations/versions/20260615_0009_add_ai_invocation_logs.py`, `tests/test_ai_evidence_service.py`, `tests/test_resource_metrics_service.py`, `tests/test_project_management_service.py`, `tests/test_documentation_images.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/ai-evidence.png`, `README.md`, `docs/ai-technical-overview.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/db-migrations.md`, `docs/engineering-decisions.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m alembic upgrade head` 통과; `.\.venv\Scripts\python.exe -m alembic heads`와 `.\.venv\Scripts\python.exe -m alembic current`에서 `20260615_0009 (head)` 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_service.py tests\test_resource_metrics_service.py tests\test_project_management_service.py tests\test_ai_evidence_service.py tests\test_documentation_images.py tests\test_feedback_and_review_services.py -q` 27개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 125개 테스트 통과; `ai-evidence` screenshot capture에서 `AI 검증`, `검증 준비`, `Evidence Trace`, `AI Scorecard`, `주간 보고서`, `Telemetry` 표시 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### 구조화 PL Briefing 이력과 검증 안정화

- `PL Briefing` LLM 응답을 자유형 Markdown 대신 `summary`, `priority_items`, `meeting_questions`, `next_actions` 구조로 받아 앱이 일관된 Markdown을 조립하도록 변경했습니다.
- 생성된 briefing을 `pl_briefing_history`에 저장해 provider/model/mode, 구조화 섹션, rendered text, Radar evidence payload, raw response를 다시 확인할 수 있게 했습니다.
- Dashboard에서 최근 저장된 PL Briefing과 이력 표를 보여주고, 프로젝트 reset/delete 시 briefing 이력도 함께 정리되도록 lifecycle을 맞췄습니다.
- Application Preview와 사용 가이드 검증 screenshot을 최근 저장/이력 표시 기준으로 갱신하고, screenshot smoke 기준도 구조화 섹션과 저장 상태를 확인하도록 보강했습니다.
- PL Briefing 구조화/저장 정책과 DB migration, 아키텍처, AI 기술 설명, 기능 가이드, engineering decision을 함께 갱신했습니다.
- 주요 파일: `src/services/ai_resource_radar_service.py`, `src/ui/dashboard_page.py`, `src/db/models.py`, `src/services/project_management_service.py`, `migrations/versions/20260615_0008_add_pl_briefing_history.py`, `tests/test_resource_metrics_service.py`, `scripts/capture_feature_screenshot.py`, `docs/ai-technical-overview.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/db-migrations.md`, `docs/engineering-decisions.md`, `docs/application-preview.md`, `docs/sample-project-usage-verification.md`, `docs/images/features/dashboard-pl-briefing.png`, `docs/images/features/dashboard-pl-briefing-actions.png`, `docs/images/usage-verification/12-pl-briefing.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m alembic heads`와 `.\.venv\Scripts\python.exe -m alembic current`에서 `20260615_0008 (head)` 확인; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py tests\test_project_management_service.py tests\test_documentation_images.py -q` 13개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 123개 테스트 통과; `dashboard-pl-briefing`, `dashboard-pl-briefing-actions`, usage verification `12-pl-briefing` screenshot capture에서 `provider=local_openai`, `mode=LLM 생성`, 최근 저장된 PL Briefing, PL Briefing 이력, 요약/우선 확인 항목/회의 질문/다음 액션 표시 확인; `git diff --check` 통과(Windows 줄끝 변환 경고만 출력).

### Application Preview 스크롤 영역 screenshot 보강

- `Application Preview`에서 아래쪽 workflow 상태가 잘리던 화면들을 더 큰 viewport 또는 full-page 기준으로 다시 캡처했습니다.
- `PL Briefing`은 요약/우선 확인 항목 이미지와 별도로 `회의 질문`, `다음 액션`이 보이는 하단 전용 screenshot을 추가했습니다.
- `dashboard-pl-briefing-actions` 캡처 시나리오에 crop 처리를 추가해 긴 PL Briefing 화면에서 하단 action 구간을 재현 가능하게 저장하도록 했습니다.
- 주요 파일: `scripts/capture_feature_screenshot.py`, `requirements.txt`, `docs/application-preview.md`, `docs/images/features/dashboard-pl-briefing-actions.png`, `docs/images/features/dashboard-pl-briefing.png`, `docs/images/features/dashboard-overview.png`, `docs/images/features/dashboard-radar.png`, `docs/images/features/dashboard.png`, `docs/images/features/project-operations.png`, `docs/images/features/project-chat.png`, `docs/images/features/git-history-detail.png`, `docs/images/features/risk-analysis-list.png`, `docs/images/features/program-detail-analysis.png`, `docs/images/features/ai-progress-detail.png`, `docs/images/features/rag-search-results.png`, `docs/images/features/project-chat-answer.png`, `docs/images/usage-verification/12-pl-briefing.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile scripts\capture_feature_screenshot.py` 통과; `dashboard-pl-briefing`은 `--height 5200`으로 `회의 질문`, `다음 액션` 표시 확인; `dashboard-pl-briefing-actions`는 crop 결과를 눈으로 확인; 주요 하단 화면 screenshot을 `--height 1800` 기준으로 재캡처; `PIL.Image` 크기 확인에서 PL Briefing 3600/5200px, 주요 상세 화면 1800px 캡처 확인.

### PL Briefing 문구 자연화

- `PL Briefing` 생성 prompt와 표시 후처리에서 `한국어 브리핑`처럼 번역체로 보이는 제목 표현을 피하고, 화면 제목을 `PL 주간 점검 브리핑`으로 자연스럽게 정리했습니다.
- local LLM이 이전 제목 표현이나 어색한 우선순위 표현을 반환해도 표시 전 자연스러운 표현으로 보정하도록 했습니다.
- Application Preview와 사용 가이드 검증용 `PL Briefing` screenshot을 새 표현 기준으로 다시 캡처했습니다.
- 주요 파일: `src/services/ai_resource_radar_service.py`, `scripts/capture_feature_screenshot.py`, `tests/test_resource_metrics_service.py`, `docs/ai-technical-overview.md`, `docs/sample-project-usage-verification.md`, `docs/images/features/dashboard-pl-briefing.png`, `docs/images/usage-verification/12-pl-briefing.png`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py::test_pl_briefing_cleans_common_mixed_language_terms -q` 통과; `dashboard-pl-briefing` screenshot capture에서 `PL 주간 점검 브리핑` 표시와 `한국어 브리핑`, `고도의 우선순위`, JSON code fence 미표시 확인.

### PL Briefing 실제 LLM 검증 증거 보강

- Dashboard `PL Briefing 생성` 경로를 `LLM_PROVIDER=local_openai`, `LLM_MODEL=qwen2.5-coder-7b-instruct` 환경에서 실제 호출해 `provider=local_openai, mode=LLM 생성` 상태와 PL 점검 브리핑 본문이 표시되는지 확인했습니다.
- 일부 local LLM이 Markdown 요청에도 JSON/code fence나 혼합 언어 표현을 반환할 수 있어, `PL Briefing` 화면 표시 전 JSON/code fence를 Markdown 브리핑 섹션으로 정리하고 흔한 혼합 표기를 보정하도록 했습니다. 이 정규화는 새 근거를 만들지 않고 표시 품질만 보정합니다.
- `dashboard-pl-briefing` screenshot 시나리오를 추가하고, Application Preview와 사용 가이드 검증 증거에 실제 LLM 브리핑 결과 이미지를 추가했습니다.
- 주요 파일: `src/services/ai_resource_radar_service.py`, `scripts/capture_feature_screenshot.py`, `tests/test_resource_metrics_service.py`, `tests/test_documentation_images.py`, `docs/application-preview.md`, `docs/ai-technical-overview.md`, `docs/sample-project-usage-verification.md`, `docs/images/features/dashboard-pl-briefing.png`, `docs/images/usage-verification/12-pl-briefing.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `Invoke-RestMethod -Uri http://127.0.0.1:1234/v1/models -Method Get`로 local LLM model 노출 확인; `.\.venv\Scripts\python.exe` 서비스 호출로 `briefing_provider=local_openai`, `briefing_used_llm=True` 확인; `dashboard-pl-briefing` screenshot capture에서 `provider=local_openai, mode=LLM 생성`, `요약`, `회의 질문`, `기반으로 이번` 표시와 JSON code fence/`本周`/`기반으로이번` 미표시 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py tests\test_documentation_images.py -q` 9개 테스트 통과; `git diff --check` 통과(Windows 줄끝 경고만 출력).

## 2026-06-14

### Application Preview 메뉴 순서 정렬

- `docs/application-preview.md`의 화면 preview 순서를 실제 사이드바 메뉴 순서와 동일하게 정렬했습니다.
- 순서는 `개요`의 Home, Dashboard, AI Progress부터 `프로젝트 설정`, `산출물 관리`, `분석 실행`, `분석 결과`, `관리` 그룹 순서를 따릅니다.
- 주요 파일: `docs/application-preview.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "<summary>" docs\application-preview.md`로 Home, Dashboard, AI Progress, 프로젝트 설정, 산출물 관리, 분석 실행, 분석 결과, 설정 순서 확인; `.\.venv\Scripts\python.exe -m pytest tests\test_documentation_images.py -q` 1개 테스트 통과; `git diff --check` 통과.

### Application Preview AI Resource Radar screenshot 보강

- `AI Resource Radar`가 Application Preview에서 바로 보이도록 전용 `dashboard-radar` screenshot 시나리오와 이미지를 추가했습니다.
- `docs/application-preview.md` Dashboard 섹션에 `Dashboard AI Resource Radar` 이미지를 추가해 PL 우선순위 표와 `PL Briefing 생성` action을 바로 확인할 수 있게 했습니다.
- `ROADMAP.md` Candidate Tasks 섹션에 남아 있던 빈 표 머리를 제거하고 후보 없음 문장만 남겼습니다.
- 주요 파일: `scripts/capture_feature_screenshot.py`, `docs/application-preview.md`, `docs/images/features/dashboard-radar.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature dashboard-radar --project-name "AAA Sample Shop Usage Verification 20260614" --surface local --expect-text "AI Resource Radar" --expect-text "PL Briefing 생성"` 통과; `.\.venv\Scripts\python.exe -m py_compile scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_documentation_images.py -q` 1개 테스트 통과; `rg -n "dashboard-radar|Dashboard AI Resource Radar|AI Resource Radar screenshot 보강|\| Priority \| Area \| Candidate \|" docs\application-preview.md scripts\capture_feature_screenshot.py AI_CHANGELOG.md ROADMAP.md`로 새 이미지 참조와 빈 후보 표 제거 확인; `git diff --check` 통과.

### AI Resource Radar와 PL Briefing 추가

- Dashboard에 `AI Resource Radar`를 추가해 AI 매핑/진척도, 미해결 리스크, 예상 지연, 난이도, cross-program commit, 관련 commit 부재, workload 신호를 설명 가능한 우선순위 점수로 보여주게 했습니다.
- `PL Briefing 생성` action을 추가해 Radar evidence를 LLM이 한국어 주간 점검 브리핑으로 요약하게 했고, `mock` provider나 LLM 실패 시 deterministic fallback briefing을 보여주도록 했습니다.
- Radar와 briefing 정책을 `docs/ai-technical-overview.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `docs/application-preview.md`에 문서화하고 Dashboard screenshot을 갱신했습니다.
- 주요 파일: `src/services/ai_resource_radar_service.py`, `src/ui/dashboard_page.py`, `tests/test_resource_metrics_service.py`, `scripts/capture_feature_screenshot.py`, `docs/ai-technical-overview.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `docs/application-preview.md`, `docs/images/features/dashboard.png`, `docs/images/features/dashboard-overview.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\ai_resource_radar_service.py src\ui\dashboard_page.py tests\test_resource_metrics_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py -q` 6개 테스트 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature dashboard-overview --project-name "AAA Sample Shop Usage Verification 20260614" --surface local --expect-text "AI Resource Radar" --expect-text "PL Briefing 생성"` 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature dashboard --project-name "AAA Sample Shop Usage Verification 20260614" --surface local --expect-text "AI Resource Radar" --expect-text "자원관리 지표"` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 121개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_documentation_images.py -q` 1개 테스트 통과.

### AX AI 후보 작업 기록

- `ROADMAP.md` Candidate Tasks에 `AI Resource Radar`와 `PL Briefing from AI Resource Radar` 후보를 추가했습니다.
- 두 후보 모두 AX Use Case에서 AI 기술이 프로젝트 자원관리 판단 보조로 더 두드러지게 보이도록 하는 후속 개선으로 정리했습니다.
- `AI Resource Radar`는 설명 가능한 위험/자원 병목 랭킹과 embedding 기반 유사 근거 검색 방향을, `PL Briefing`은 그 근거를 LLM이 한국어 회의 브리핑으로 요약하는 방향을 기록했습니다.
- 주요 파일: `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "AI Resource Radar|PL Briefing from AI Resource Radar|AX AI 후보 작업 기록|현재 승인 대기 중인 후보 작업은 없습니다" ROADMAP.md AI_CHANGELOG.md`로 후보 2개와 변경이력 반영 확인; `git diff --check` 통과.

### AI 기술 적용 요약 문서화

- `docs/ai-technical-overview.md`에 AX Use Case 기준 AI 적용 요약을 추가해 LLM, embedding/vector search, source-grounded RAG, 한국어 업무용어 확장, AI-derived risk/resource analytics, human-in-the-loop 보정, local provider 운영 제어를 한눈에 볼 수 있게 했습니다.
- 실제 LLM/embedding/RAG 호출이 일어나는 영역과, 그 AI-derived evidence를 활용하는 규칙/계산형 분석 영역을 구분해 설명했습니다.
- README의 `AI 기술 개요` 링크 설명을 보강해 AI 기술 정리 문서로 바로 이어지게 했습니다.
- 주요 파일: `docs/ai-technical-overview.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "AX Use Case 기준 AI 적용 요약|LLM 기반 프로그램-커밋 매핑|Embedding/vector search|Source-grounded RAG|AI-derived risk analytics|AI-derived resource metrics|AI technology application summary|AI 기술 적용 요약 문서화" docs\ai-technical-overview.md README.md ROADMAP.md AI_CHANGELOG.md`로 핵심 요약/로드맵/변경이력 반영 확인; `git diff --check` 통과.

### Roadmap 빈 후보 작업 표 정리

- `ROADMAP.md`의 `Candidate Tasks` 섹션에서 행 없는 빈 표를 제거하고, 현재 승인 대기 중인 후보 작업이 없다는 문장으로 대체했습니다.
- 주요 파일: `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "\| Priority \| Area \| Candidate \||현재 승인 대기 중인 후보 작업은 없습니다|## P3 - Server-Managed" ROADMAP.md`로 빈 후보 표 제거와 다음 섹션 위치 확인; `git diff --check` 통과.

### Engineering decision superseded 표시 정리

- `docs/engineering-decisions.md`의 2026-06-10 `App-server Git repository operating model` 결정을 `Superseded`로 표시했습니다.
- 앱 서버 기준 Git 저장소 모델은 유지하되, remote URL 기반 clone/fetch를 관리하지 않는다는 이전 범위 제한은 2026-06-14 `서버 저장소 clone/fetch는 인증정보 저장 없이 지원한다` 결정으로 대체되었음을 명시했습니다.
- 주요 파일: `docs/engineering-decisions.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "manage하지 않는|관리하지 않는 것입니다|별도 보안/운영 결정 후 구현|당분간 운영자나 외부 스크립트 책임|App-server Git repository operating model \(Superseded\)|서버 저장소 clone/fetch는 인증정보 저장 없이 지원한다" docs\engineering-decisions.md`로 superseded 표시와 충돌 문구 정리 확인; `git diff --check` 통과.

### Project 화면 Application Preview 보강

- `프로젝트/Git 설정` screenshot을 현재 화면으로 다시 캡처하고, 서버 저장소 상태와 `서버 저장소 clone/fetch`, `분석 데이터 초기화`가 보이는 운영 action screenshot을 추가했습니다.
- Project screenshot 캡처 시나리오가 새 Project 운영 컨트롤을 필수 텍스트로 검증하도록 보강했습니다.
- `docs/application-preview.md`의 Project 섹션에 기본 설정 화면과 운영 action 구간 설명을 추가했습니다.
- 주요 파일: `scripts/capture_feature_screenshot.py`, `docs/application-preview.md`, `docs/images/features/project.png`, `docs/images/features/project-operations.png`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature project --project-name "AAA Sample Shop Usage Verification 20260614" --surface local --expect-text "Git remote URL" --expect-text "서버 저장소 clone/fetch" --expect-text "분석 데이터 초기화"` 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://localhost:8501 --feature project-operations --project-name "AAA Sample Shop Usage Verification 20260614" --surface local --expect-text "서버 저장소 clone/fetch" --expect-text "분석 데이터 초기화" --expect-text "프로젝트 삭제"` 통과; `.\.venv\Scripts\python.exe -m py_compile scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_documentation_images.py -q` 1개 테스트 통과; `git diff --check` 통과.

### README Git 저장소 접근 모델 보정

- README의 Git 저장소 접근 모델 설명을 사내 서버에 미리 clone된 저장소만 전제하지 않도록 수정했습니다.
- 서버 저장소는 운영자가 미리 준비할 수도 있고, 프로젝트/Git 설정의 `Git remote URL`과 branch 기반 `서버 저장소 clone/fetch`로 준비할 수도 있음을 명시했습니다.
- 주요 파일: `README.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "clone되어 있어야|서버 저장소 clone/fetch|미리 clone" README.md`로 README Git 접근 설명 확인; `git diff --check` 통과.

### 데모 사용 가이드 reset/fetch 안내 정리

- 반복 검증에서 기존 샘플 프로젝트를 다시 사용할 때 `프로젝트 삭제`보다 `분석 데이터 초기화`를 먼저 사용하도록 `docs/demo-user-guide.md` 안내를 바꿨습니다.
- Git 동기화는 앱 서버에 준비된 저장소의 commit/diff를 DB에 수집하는 단계이고, 원격 저장소 준비는 `서버 저장소 clone/fetch`에서 처리한다는 설명을 추가했습니다.
- 주요 파일: `docs/demo-user-guide.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "기존 샘플 프로젝트를 삭제|삭제한 뒤 같은 경로|원격 저장소에서 fetch하는 기능이 아니라" docs\demo-user-guide.md` 결과 없음; `git diff --check` 통과.

### Git remote URL 인증정보 차단

- 프로젝트/Git 설정에서 HTTPS remote URL에 userinfo가 포함되거나 URL에 password가 포함된 경우 저장하지 않도록 검증을 추가했습니다.
- 서버 저장소 clone/fetch 실행 전에도 같은 검증을 적용해 기존에 저장된 위험한 remote URL이 실행되지 않도록 했습니다.
- clone 성공 메시지에서 remote URL 원문을 표시하지 않도록 바꿔 검증 화면과 로그에 토큰성 문자열이 노출될 가능성을 줄였습니다.
- 주요 파일: `src/services/git_remote_service.py`, `src/ui/project_page.py`, `tests/test_git_remote_service.py`, `docs/engineering-decisions.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\git_remote_service.py src\ui\project_page.py tests\test_git_remote_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_git_remote_service.py -q` 5개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 119개 테스트 통과.

### 샘플 데이터 생성 안내 문구 정리

- 샘플 데이터 생성 화면의 caption에서 고정 seed 재현성 문구를 제거하고, 사용자가 알아야 할 업로드 테스트용 샘플이라는 설명만 남겼습니다.
- 생성 로직의 seed 값은 유지하고, UI에서 구현 세부사항만 노출하지 않도록 `SEED` import를 정리했습니다.
- 주요 파일: `src/ui/sample_data_page.py`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\sample_data_page.py` 통과; `rg -n "랜덤성|seed\\(|SEED" src\ui\sample_data_page.py` 결과 없음; `git diff --check` 통과.

### Server-managed clone/fetch workflow

- `projects`에 `git_remote_url`, `git_branch`를 추가하는 Alembic migration을 만들고, 프로젝트/Git 설정에서 Git remote URL과 branch를 저장할 수 있게 했습니다.
- `clone_or_update_project_repository` service를 추가해 앱 서버 저장소 경로가 없으면 clone하고, 기존 Git 저장소가 있으면 `origin` fetch 후 branch를 `origin/<branch>`로 reset할 수 있게 했습니다.
- repository별 lock 파일과 dirty working tree guard를 추가했습니다. access token, SSH key, password는 앱에 저장하지 않고 서버 OS의 Git 인증 설정을 사용한다는 운영 경계를 문서화했습니다.
- 주요 파일: `migrations/versions/20260614_0007_add_project_git_remote_fields.py`, `src/db/models.py`, `src/services/git_remote_service.py`, `src/ui/project_page.py`, `tests/test_git_remote_service.py`, `docs/git-repository-operating-model.md`, `docs/server-repository-update-runbook.md`, `docs/setup-and-operations.md`, `docs/architecture.md`, `docs/db-migrations.md`, `docs/engineering-decisions.md`, `docs/demo-user-guide.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py tests migrations\versions\20260614_0007_add_project_git_remote_fields.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_git_remote_service.py -q` 3개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 117개 테스트 통과; stale clone/fetch 정책 문구 검색 결과 현재 변경과 무관한 후속 작업 문맥만 남음; `git diff --check` 통과.

### Project reset action after delete flow

- `프로젝트/Git 설정`에 `분석 데이터 초기화` action을 추가해 프로젝트명, Git 저장소 경로, 프로그램/개발계획, 표준용어/표준단어, 프로젝트 개발자 연결은 유지하고 분석/수집 결과만 삭제할 수 있게 했습니다.
- `get_project_reset_impact`, `reset_project_analysis_data`를 추가해 초기화 전 유지/삭제 대상 건수를 보여주고, Git commit, 변경 파일/diff, 매핑, 분석 실행 이력, 구현상태 분석, 리스크, 자원관리 snapshot, RAG chunk/vector, Project Chat, AI Code Review, 마지막 Git 동기화 상태를 정리합니다.
- 프로젝트 삭제와 분석 데이터 초기화의 사용 시점과 보존 정책을 feature guide, architecture, engineering decision에 문서화했습니다.
- 주요 파일: `src/services/project_management_service.py`, `src/ui/project_page.py`, `tests/test_project_management_service.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\project_management_service.py src\ui\project_page.py tests\test_project_management_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_management_service.py -q` 4개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 114개 테스트 통과; `git diff --check` 통과.

### Project-scoped UI state namespacing

- `project_scoped_key(project_id, name)` helper를 추가해 프로젝트별 Streamlit widget state key를 일관되게 만들 수 있게 했습니다.
- Mapping, Program Detail, Commit Impact, Git History, Risk Analysis, AI Progress, RAG 검색 화면의 프로그램/커밋/필터/검색/질문 선택값을 프로젝트별 key로 분리했습니다.
- 프로젝트 전환 시 이전 프로젝트의 프로그램, 커밋, 리스크, RAG 조건이 새 프로젝트 화면에 남아 보이지 않도록 feature guide, architecture, engineering decision에 UI state 정책을 기록했습니다.
- 주요 파일: `src/ui/project_context.py`, `src/ui/mapping_page.py`, `src/ui/program_detail_page.py`, `src/ui/commit_impact_page.py`, `src/ui/git_history_page.py`, `src/ui/risk_page.py`, `src/ui/ai_progress_page.py`, `src/ui/rag_page.py`, `tests/test_project_context.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\project_context.py src\ui\mapping_page.py src\ui\program_detail_page.py src\ui\commit_impact_page.py src\ui\risk_page.py src\ui\ai_progress_page.py src\ui\git_history_page.py src\ui\rag_page.py tests\test_project_context.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_context.py -q` 6개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 112개 테스트 통과; `git diff --check` 통과.

### Roadmap commit hash tracking cleanup

- `ROADMAP.md` Priority Overview에서 `Commit` 컬럼을 제거하고, Roadmap은 작업 상태와 관련 `AI_CHANGELOG.md` heading만 추적하도록 정리했습니다.
- `ROADMAP.md` Management Rules와 `AGENTS.md`에서 commit hash 기록 요구를 제거하고, commit-level traceability는 Git history를 사용하도록 했습니다.
- 이전 `Roadmap owns commit hash tracking` engineering decision을 `Superseded`로 표시하고, 새 결정인 `Roadmap은 commit hash를 직접 관리하지 않는다`를 추가했습니다.
- 주요 파일: `ROADMAP.md`, `AGENTS.md`, `docs/engineering-decisions.md`, `AI_CHANGELOG.md`.
- 검증: `ROADMAP.md` Priority Overview가 5컬럼으로 정리됐는지 확인; `rg -n 'heading and commit hash|Priority \\| Area \\| Task \\| Status \\| Related AI Change Log \\| Commit' ROADMAP.md AGENTS.md` 결과 없음; `git diff --check` 통과.

### Roadmap 완료 작업 commit 기록 정리

- `ROADMAP.md` Priority Overview에서 완료 상태지만 commit 칸이 비어 있던 항목을 실제 완료 commit 기준으로 채웠습니다.
- 기능, 아키텍처, AI 동작 변경은 없고 Roadmap 추적 정보만 정리했습니다.
- 주요 파일: `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "\| Done \| [^|]+ \|  \|" ROADMAP.md` 결과 없음; `git diff --check` 통과.

### README 대표 screenshot source 통합

- README 최상단 대표 screenshot이 stale 상태로 남던 원인을 확인하고, `docs/images/features/home.png`를 단일 source로 사용하도록 정리했습니다.
- README 중간 `스크린샷` 섹션의 중복 Home 이미지를 제거하고, 상세 화면은 Application Preview로 안내하게 했습니다.
- 더 이상 참조하지 않는 `docs/images/ai-commit-advisor-home.png`, `docs/images/ai-commit-advisor-home-48.png`를 삭제했습니다.
- README가 legacy `ai-commit-advisor-home*.png`를 다시 참조하지 않도록 `tests/test_documentation_images.py`를 추가했습니다.
- 원인과 재발 방지 기준을 `docs/failure-history.md`, `docs/engineering-decisions.md`에 기록했습니다.
- 주요 파일: `README.md`, `tests/test_documentation_images.py`, `docs/failure-history.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m pytest tests\test_documentation_images.py -q` 1개 테스트 통과; `rg -n "ai-commit-advisor-home" README.md docs\application-preview.md docs\feature-guide.md docs\setup-and-operations.md` 결과 없음; legacy 대표 이미지 파일 2개 삭제 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 111개 테스트 통과; `git diff --check` 통과.

### Application Preview 하단 기능 screenshot 보강

- 긴 화면에서 한 장의 screenshot만으로 하단 기능이 덜 보이는 문제를 줄이기 위해 Program Detail, Risk Analysis, RAG 검색, Project Chat, Dashboard, AI Progress에 보강 screenshot을 추가했습니다.
- `scripts/capture_feature_screenshot.py`에 하단/결과 구간 캡처 시나리오를 추가했습니다.
- `docs/application-preview.md`에서 긴 화면은 요약/결과/상세 구간을 나눠 보여주도록 caption과 image reference를 보강했습니다.
- 주요 파일: `scripts/capture_feature_screenshot.py`, `docs/application-preview.md`, `docs/images/features/program-detail-analysis.png`, `docs/images/features/risk-analysis-list.png`, `docs/images/features/rag-search-results.png`, `docs/images/features/project-chat-answer.png`, `docs/images/features/dashboard-overview.png`, `docs/images/features/ai-progress-detail.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: 추가 screenshot 시나리오 7개 캡처 통과; Application Preview image reference가 실제 파일과 일치하는지 확인; 보강 screenshot contact sheet 육안 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 110개 테스트 통과; `git diff --check` 통과.

### Sidebar 메뉴 구조 문서화

- `docs/feature-guide.md`에 현재 `app.py`의 sidebar group 기준 메뉴 목록과 각 화면의 사용 목적을 표로 추가했습니다.
- README의 기능 가이드 링크 설명에 사이드바 메뉴 구조를 포함한다고 명시했습니다.
- 주요 파일: `docs/feature-guide.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: 현재 `app.py` sidebar 화면명이 `docs/feature-guide.md`에 모두 반영됐는지 확인; `git diff --check` 통과.

### Application Preview 현재 메뉴 screenshot 갱신

- Application Preview와 README 대표 화면이 현재 접이식 sidebar 메뉴 구조를 보여주도록 `docs/images/features` 주요 screenshot을 다시 캡처했습니다.
- 현재 캡처 자동화가 재현하지 못하는 예전 세부 상태 screenshot(`AI Code Review` 결과/상세, `Commit Impact` summary/detail, 업로드 검증 결과 이미지)은 Application Preview 참조에서 제거하고 파일도 정리했습니다.
- `scripts/capture_feature_screenshot.py`가 접이식 sidebar group을 열고 이동할 수 있게 하고, 로컬 Playwright browser가 없을 때 시스템 Chrome/Edge를 fallback으로 사용할 수 있게 보강했습니다.
- 캡처 중 발견된 `Risk Analysis`의 `st.dataframe(...).rename(...)` 렌더링 오류를 수정했습니다.
- 주요 파일: `scripts/capture_feature_screenshot.py`, `src/ui/risk_page.py`, `docs/application-preview.md`, `docs/images/features/*.png`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\risk_page.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature all --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local --forbid-text "가정값" --forbid-text "고객가치 KPI" --forbid-text "자원관리 KPI 추세" --forbid-text "rename() is not a valid Streamlit command"` 통과; Application Preview 이미지 참조에서 삭제한 old screenshot 경로가 남지 않는지 `rg`로 확인; 전체 feature contact sheet 육안 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 110개 테스트 통과; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### Dashboard 가치 지표 용어 정리

- Dashboard 자원관리 영역의 `가정값`, `자원관리 KPI 추세` 표현을 `현재 계산 기준의 참고 추정값`, `자원관리 참고 지표 추세`로 정리했습니다.
- README, Application Preview, 사용 가이드, feature guide, architecture, AI technical overview, DB migration guide에서 Dashboard 가치 지표를 `고객가치 KPI`보다 사용자에게 가까운 `고객가치 참고 지표`/`핵심 지표` 중심으로 설명하게 했습니다.
- 앱 화면과 사용자-facing 문서에서는 내부 단계 표현, `KPI`, `planning signal` 같은 내부자 용어를 줄이고, 기술 문서에서는 계산 기준과 한계를 유지한다는 engineering decision을 추가했습니다.
- `BusinessValueMetric.assumption`에 내부 단계 표현이 다시 노출되지 않도록 회귀 테스트를 추가했습니다.
- 주요 파일: `src/ui/dashboard_page.py`, `src/services/resource_metrics_service.py`, `tests/test_resource_metrics_service.py`, `README.md`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/demo-user-guide.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/db-migrations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\dashboard_page.py src\services\resource_metrics_service.py tests\test_resource_metrics_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py -q` 4개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 110개 테스트 통과; Chrome headless로 Dashboard에서 `현재 계산 기준` 표시와 기존 `가정값`, `고객가치 KPI`, `자원관리 KPI 추세` 미노출 확인; `git diff --check` 통과.

### Application Preview Dashboard 설명 문구 정리

- `docs/application-preview.md`의 Dashboard 설명을 짧은 문장 중심으로 바꿔 첫 독자가 화면 목적을 먼저 이해할 수 있게 했습니다.
- 자원관리 지표가 개인 평가나 확정 절감액이 아니라 PL의 병목/일정 리스크 확인용 참고 지표라는 경계는 유지했습니다.
- 주요 파일: `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: 문서 문구 변경으로 별도 코드 테스트는 수행하지 않았고, `git diff --check` 통과를 확인했습니다.

### 샘플 프로젝트 commit 날짜 정규화

- `scripts/create_sample_target_repo.py`의 48개 commit history 기준 시작일을 `2026-04-25 09:30 KST`로 조정해 마지막 commit 날짜가 `2026-06-14`를 넘지 않게 했습니다.
- 샘플 commit 날짜 범위를 `docs/sample-target-repo-demo-design.md`에 명시하고, 미래 날짜 commit이 Git History/Commit Impact 신뢰도를 떨어뜨릴 수 있다는 설계 기준을 추가했습니다.
- 샘플 history의 마지막 commit 날짜를 검증하는 테스트를 추가했습니다.
- 주요 파일: `scripts/create_sample_target_repo.py`, `tests/test_sample_data_generation.py`, `docs/sample-target-repo-demo-design.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile scripts\create_sample_target_repo.py tests\test_sample_data_generation.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_sample_data_generation.py -q` 13개 테스트 통과; 임시 샘플 repo 생성 후 `git log -1 --format='%ad|%s' --date=short` 결과 `2026-06-14|Add sample demo guide for advisor walkthrough`, `git rev-list --count HEAD` 결과 48 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\create_sample_target_repo.py` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 110개 테스트 통과; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### Sidebar 접이식 그룹 정리

- 사이드바의 업무 그룹을 항상 펼쳐진 목록 대신 `st.expander` 기반 접이식 그룹으로 바꿨습니다.
- 현재 위치의 그룹만 기본으로 펼쳐지게 해 일반 데스크톱 높이에서 하단 메뉴를 찾기 위한 스크롤 부담을 줄였습니다.
- 기존 sidebar group label CSS를 제거하고 expander summary 스타일을 맞췄습니다.
- feature guide, Application Preview, architecture 설명을 접이식 sidebar 그룹 기준으로 갱신했습니다.
- 주요 파일: `app.py`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/architecture.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile app.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 109개 테스트 통과; Browser에서 `개요` 그룹 기본 펼침, `분석 실행` 그룹 수동 펼침, `Project Chat` 이동 후 `분석 실행` 그룹 기본 펼침 확인; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### Home 요약 우선순위 정리

- Home 화면에서 현재 프로젝트 KPI를 분석 상태 표보다 먼저 표시하도록 렌더링 순서를 바꿨습니다.
- 상단 흐름을 `KPI -> 다음 작업 -> 분석 상태 -> 차트/리스크 상세` 순서로 정리해 첫 화면에서 운영 요약과 다음 행동을 먼저 확인하게 했습니다.
- feature guide와 Application Preview 설명을 새 정보 우선순위에 맞게 갱신했습니다.
- 주요 파일: `src/ui/home_page.py`, `docs/feature-guide.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\home_page.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 109개 테스트 통과; Browser에서 Home 본문 순서가 `총 프로그램` KPI, `다음 작업`, `분석 상태` 순서로 렌더링되는지 확인; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### 프로그램 관리 현재 프로젝트 저장 흐름 정리

- 프로그램 관리 화면에서 `새 프로젝트명으로 저장` 옵션을 제거하고, 현재 프로젝트가 없으면 `프로젝트/Git 설정`에서 먼저 프로젝트를 등록하도록 안내하게 했습니다.
- 직접 추가와 Excel 업로드 저장을 프로젝트명 lookup/create가 아니라 현재 `project_id` 기준으로 수행하도록 `save_programs_for_project_id`, `save_manual_program_for_project` 경로를 추가했습니다.
- 기존 이름 기반 저장 함수는 호환용으로 유지하면서, 프로그램 관리 UI는 새 프로젝트를 만들지 않는 현재 프로젝트 전용 흐름으로 정리했습니다.
- feature guide, architecture, engineering decisions, roadmap에서 프로그램 목록의 새 프로젝트 저장 예외 설명을 제거하고 현재 프로젝트 기준 관리 정책으로 갱신했습니다.
- 주요 파일: `src/ui/upload_page.py`, `src/services/excel_service.py`, `src/services/program_management_service.py`, `tests/test_program_management_service.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\excel_service.py src\services\program_management_service.py src\ui\upload_page.py tests\test_program_management_service.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_program_management_service.py -q` 5개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 109개 테스트 통과; Browser에서 프로그램 관리 화면의 현재 프로젝트 표시, 탭 렌더링, `새 프로젝트명으로 저장` 미노출 확인; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### 완료 상태 액션 우선순위 정리

- Git 동기화 화면 제목을 메뉴명과 맞추고, 일반 운영 흐름의 기본 액션을 `증분 동기화` primary로 정리했습니다. `전체 수집`은 보조 액션으로 낮추고 DB가 Repo HEAD와 같을 때 최신 상태 안내를 표시합니다.
- Mapping 커밋 기준 분석에서 미완료/실패 커밋이 없으면 완료 메시지를 먼저 보여주고, 재분석/선택 분석 컨트롤은 접힌 영역으로 이동했습니다.
- RAG 검색과 Project Chat에서 코드 근거가 최신이면 `최신 변경분 반영` 버튼을 secondary로 낮추고, RAG 한 번에 준비 화면에서 남은 검색 준비가 0건이면 완료 안내를 표시합니다.
- feature guide에 증분 동기화와 완료 상태 재실행 기준을 반영했습니다.
- 주요 파일: `src/ui/git_page.py`, `src/ui/mapping_page.py`, `src/ui/rag_page.py`, `src/ui/project_chat_page.py`, `docs/feature-guide.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\git_page.py src\ui\mapping_page.py src\ui\rag_page.py src\ui\project_chat_page.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 108개 테스트 통과; Browser에서 Git 동기화 최신 안내, Mapping 완료/재분석 접힘, RAG 검색 준비 완료 안내, Project Chat 준비 완료 렌더링 확인; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### 분석 화면 표시 정리

- AI Code Review, Git History, Commit Impact, AI Progress, Program Detail, Risk Analysis의 기본 화면에서 raw dictionary/JSON과 내부 risk/code label 노출을 줄였습니다.
- 커밋 요약, 커밋 상세, 프로그램 요약은 `항목/값` 표로 표시하고, `datetime.date(...)`, `commit_hash`, `is_merge_commit`, `app_server_git_repo_path`, `Risk Level`, `Risk Type` 같은 디버그형 표기가 기본 화면에 보이지 않도록 정리했습니다.
- 리스크 수준/유형 필터와 차트/표 컬럼을 한국어 업무 라벨로 바꾸고, commit hash, program ID, file path처럼 근거 추적에 필요한 식별자는 유지했습니다.
- 분석 화면 표시 정책을 feature guide, architecture, engineering decisions, roadmap에 문서화했습니다.
- 주요 파일: `src/ui/display_utils.py`, `src/ui/code_review_page.py`, `src/ui/git_history_page.py`, `src/ui/commit_impact_page.py`, `src/ui/ai_progress_page.py`, `src/ui/program_detail_page.py`, `src/ui/risk_page.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\display_utils.py src\ui\code_review_page.py src\ui\git_history_page.py src\ui\commit_impact_page.py src\ui\ai_progress_page.py src\ui\program_detail_page.py src\ui\risk_page.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest -q` 108개 테스트 통과; Browser에서 Git History, Commit Impact, AI Progress, Risk Analysis, AI Code Review의 새 한국어 요약/필터 렌더링과 주요 raw key 미노출 확인; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### 현재 프로젝트 선택 유지

- 사이드바의 `현재 프로젝트` 선택값을 Streamlit session state뿐 아니라 URL `project_id` query parameter에도 저장하도록 변경했습니다.
- 브라우저 새로고침이나 `?project_id=...` URL 재진입 시 해당 프로젝트가 유효하면 먼저 복원하고, 삭제되었거나 잘못된 값이면 기존 session state 또는 첫 프로젝트로 복구하도록 했습니다.
- 현재 프로젝트 복원 정책을 feature guide, architecture, engineering decisions, roadmap에 문서화했습니다.
- 주요 파일: `src/ui/project_context.py`, `tests/test_project_context.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\project_context.py tests\test_project_context.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_context.py -q` 5개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 108개 테스트 통과; Browser에서 `http://localhost:8501/?project_id=197` 진입 및 reload 후 `AAA Sample Shop Usage Verification 20260614 (197)` 유지 확인; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### 자원관리 가치 지표 문구 정리

- Dashboard 자원관리 지표의 `AI 리뷰 절감 추정`, `추가 MM 회피 노출` 표현을 `리뷰 시간 절감 가능성`, `추가 투입 예방 가능성`으로 정리했습니다.
- 두 지표가 확정 비용 절감액이 아니라 계산 가정으로 계산한 의사결정 보조 추정값임을 Dashboard 설명과 metric 도움말에 노출했습니다.
- 자원관리 추세 분석 표와 스크린샷 검증 기준도 새 사용자-facing 문구로 맞췄습니다.
- 사용 가이드, feature guide, Application Preview, AI technical overview에 검증 계산 가정과 해석 경계를 반영했습니다.
- 주요 파일: `src/ui/dashboard_page.py`, `src/services/resource_metrics_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/dashboard.png`, `docs/demo-user-guide.md`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/ai-technical-overview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\dashboard_page.py src\services\resource_metrics_service.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py tests\test_project_management_service.py -q` 6개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 106개 테스트 통과; Browser에서 Dashboard의 `리뷰 시간 절감 가능성`, `추가 투입 예방 가능성` 렌더링과 기존 `AI 리뷰 절감 추정`, `추가 MM 회피 노출` 미노출 확인, tooltip target 18개 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature dashboard --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; 갱신 screenshot 육안 확인 통과; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### Project/RAG 컨텍스트 도움말 툴팁 추가

- 전역 `현재 프로젝트` 선택, Project Chat의 `TOP K`, `커밋 이력도 참고에 포함`, `최신 변경분 반영`, `전체 소스 다시 읽기`, 저장된 대화/새 대화 control에 물음표 도움말을 추가했습니다.
- RAG 검색의 근거/검색 준비 metric, `근거 조각 크기`, `겹치는 글자 수`, `검색 준비 최대 처리 수`, `TOP K`, source filter, 검색 준비 실행 버튼에 물음표 도움말을 추가했습니다.
- 항상 보이는 설명문을 늘리지 않고, 헷갈리는 control에서만 마우스 hover로 의미와 사용 기준을 확인하도록 정리했습니다.
- feature guide와 Application Preview에 물음표 도움말 사용 기준을 반영했습니다.
- 주요 파일: `src/ui/project_context.py`, `src/ui/project_chat_page.py`, `src/ui/rag_page.py`, `docs/feature-guide.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\project_context.py src\ui\project_chat_page.py src\ui\rag_page.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_history_service.py tests\test_project_chat_service.py tests\test_source_index_service.py -q` 14개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 106개 테스트 통과; Browser에서 Project Chat tooltip target 17개, RAG 검색 tooltip target 29개 렌더링과 Project Chat/RAG 주요 화면 문구 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature project-chat --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature rag-search --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; 갱신 screenshot 육안 확인 통과.

### Project Chat 근거 갱신 안내 UX 정리

- Project Chat 상단의 `chunk`, `embedding`, `source_file` 중심 안내를 `답변 근거 상태`, `최신 변경분 반영`, `전체 소스 다시 읽기` 중심의 사용자-facing 문구로 정리했습니다.
- 소스 근거, 검색 준비, 코드 반영 상태, 추가 준비 필요를 요약 metric으로 보여주고, Git/HEAD/chunk/vector 상세는 접힌 `기술 상세` 영역으로 이동했습니다.
- `어떤 버튼을 누르면 되나요?` 도움말을 추가해 일반 사용자는 최신 변경분 반영과 전체 소스 다시 읽기 중 무엇을 선택할지 먼저 알 수 있게 했습니다.
- Project Chat에서 안내하는 후속 작업과 맞도록 RAG 검색 화면도 `한 번에 준비`, `근거 만들기`, `검색 준비`, `검색 확인`, `소스 Q&A` 흐름으로 정리하고 `Embedding 생성`, `Chunk 생성` 같은 주요 버튼/탭 문구를 사용자 작업 중심으로 바꿨습니다.
- feature guide, setup/operations, Application Preview, demo user guide, architecture, AI technical overview, source indexing plan, server repository runbook, screenshot capture 기준을 새 UI 문구로 갱신했습니다.
- Project Chat과 RAG 검색 Application Preview screenshot을 새 문구 기준으로 갱신했습니다.
- 주요 파일: `src/ui/project_chat_page.py`, `src/ui/rag_page.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/project-chat.png`, `docs/images/features/rag-search.png`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/application-preview.md`, `docs/demo-user-guide.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/source-indexing-and-embedding-plan.md`, `docs/server-repository-update-runbook.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_history_service.py tests\test_project_chat_service.py tests\test_source_index_service.py -q` 14개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 106개 테스트 통과; Browser에서 Project Chat의 `답변 근거 상태`, `소스 근거`, `검색 준비`, `코드 반영 상태`, `최신 변경분 반영`, `전체 소스 다시 읽기` 렌더링과 기존 `Project Chat의 재인덱싱은 PC 부하`, `chunk만 갱신합니다` 문구 미노출 확인; Browser에서 RAG 검색의 `한 번에 준비`, `근거 만들기`, `검색 준비`, `검색 확인`, `검색 준비 연결 테스트`, `검색 준비 실행` 렌더링과 기존 `Embedding 생성`, `Chunk 생성` 미노출 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature project-chat --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature rag-search --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; `git diff --check` 통과(Windows 줄바꿈 경고만 확인).

### Project Chat 대화 관리 UX 정리

- Project Chat의 `대화 초기화`와 `새 대화`가 모두 새 session을 만드는 중복 액션으로 보이던 문제를 정리했습니다.
- 별도 header action을 제거하고, `대화 관리` 영역 안에서 `저장된 대화` 선택과 `새 대화 시작`을 함께 배치했습니다.
- 빈 session은 선택 목록에서 `빈 대화`로 표시해 새 대화 생성 버튼과 혼동되지 않도록 했습니다.
- feature guide, setup/operations, Application Preview 설명과 screenshot capture 기준을 새 UI 문구로 갱신하고 Project Chat screenshot을 갱신했습니다.
- 주요 파일: `src/ui/project_chat_page.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/project-chat.png`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\ui\project_chat_page.py scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_history_service.py tests\test_project_chat_service.py -q` 6개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 106개 테스트 통과; Browser에서 `대화 관리`, `저장된 대화`, `새 대화 시작` 렌더링과 `대화 초기화` 미노출 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature project-chat --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; `git diff --check` 통과.

### 자원관리 지표 시계열 snapshot과 추세 분석

- `resource_metric_snapshots` 테이블과 Alembic migration을 추가해 Dashboard 자원관리 지표의 기준 시점 snapshot을 저장할 수 있게 했습니다.
- `resource_metrics_service.py`에 현재 지표 snapshot 저장, 최근 snapshot 조회, JSON-safe raw summary payload 생성을 추가했습니다.
- Dashboard 자원관리 지표에 `현재 지표 저장` 수동 저장 영역과 `추세 분석` 탭을 추가해 예상 지연 프로그램, HIGH/미해결 리스크, 평균 업무량, 평균 난이도, AI 리뷰 절감 추정, 추가 MM 회피 노출을 시간순으로 볼 수 있게 했습니다.
- 프로젝트 삭제 영향 계산과 삭제 처리에 자원관리 snapshot을 포함했습니다.
- README, 사용 가이드, feature guide, architecture, AI technical overview, DB migration guide, Application Preview, engineering decisions, roadmap을 저장형 snapshot과 수동 추세 분석 기준으로 갱신했습니다.
- 주요 파일: `migrations/versions/20260614_0006_add_resource_metric_snapshots.py`, `src/db/models.py`, `src/services/resource_metrics_service.py`, `src/services/project_management_service.py`, `src/ui/dashboard_page.py`, `src/ui/project_page.py`, `tests/test_resource_metrics_service.py`, `tests/test_project_management_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/dashboard.png`, `README.md`, `docs/demo-user-guide.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/db-migrations.md`, `docs/application-preview.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\db\models.py src\services\resource_metrics_service.py src\ui\dashboard_page.py tests\test_resource_metrics_service.py migrations\versions\20260614_0006_add_resource_metric_snapshots.py` 통과; `.\.venv\Scripts\alembic.exe upgrade head` 통과; `.\.venv\Scripts\alembic.exe heads`와 `.\.venv\Scripts\alembic.exe current` 모두 `20260614_0006 (head)` 확인; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py tests\test_project_management_service.py -q` 6개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 106개 테스트 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; Browser에서 Dashboard의 `현재 자원관리 지표 snapshot 저장`, `추세 분석`, `예상 지연 프로그램` 렌더링 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature dashboard --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; `git diff --check` 통과.

### AI Code Review 서버 저장소 대상 설명 정리

- 중앙 앱 서버 모델에서는 AI Code Review의 기본 대상이 개발자 개인 PC의 working tree/staged 변경이 아니라 앱 서버 Git 저장소의 최신/특정 커밋임을 UI와 문서에 명확히 했습니다.
- `AI Code Review` 화면의 리뷰 대상 순서를 `최신 커밋`, `특정 커밋`, `서버 작업트리 변경`, `서버 Staged 변경` 순서로 바꾸고, 서버 작업트리/staged 옵션은 분석용 서버 clone에 local 변경이 남아 있을 때만 의미가 있다는 안내를 추가했습니다.
- README, 사용 가이드, feature guide, architecture, AI technical overview, Application Preview, engineering decisions, roadmap을 같은 운영 모델 기준으로 정리했습니다.
- 주요 파일: `src/ui/code_review_page.py`, `src/services/code_review_service.py`, `README.md`, `docs/demo-user-guide.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/engineering-decisions.md`, `docs/images/features/ai-code-review.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_feedback_and_review_services.py -q` 8개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 105개 테스트 통과; Browser에서 AI Code Review 화면의 `최신 커밋 (권장)`, `특정 커밋`, `서버 작업트리 변경`, `서버 Staged 변경`, 중앙 앱 서버 안내문 렌더링 확인; `git diff --check` 통과.

### 예상 종료일과 자원관리 Dashboard

- `resource_metrics_service.py`에 프로그램별 예상 종료일, 예상 지연일, forecast confidence, forecast level 계산을 추가했습니다.
- Risk Analysis가 예상 지연일 7일 이상인 프로그램을 `FORECAST_DELAY` 리스크로 저장하도록 확장했습니다.
- Dashboard에 자원관리 지표 영역을 추가해 미해결/HIGH 리스크, 예상 지연 프로그램, AI 리뷰 절감 추정, 추가 MM 회피 노출, 개발자별 업무량·난이도, 예상 지연/난이도 프로그램 목록을 볼 수 있게 했습니다.
- 사용 가이드, README, feature guide, architecture, AI technical overview, Application Preview 설명을 새 Dashboard와 예상 종료 지표 기준으로 갱신했습니다.
- 관련 로드맵 항목 `Forecasted completion and proactive delay risk`, `Developer workload and difficulty dashboard`, `AX customer value KPI documentation`을 완료 처리했습니다.
- 주요 파일: `src/services/resource_metrics_service.py`, `src/services/risk_service.py`, `src/ui/dashboard_page.py`, `tests/test_resource_metrics_service.py`, `scripts/capture_feature_screenshot.py`, `docs/images/features/dashboard.png`, `README.md`, `docs/demo-user-guide.md`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\resource_metrics_service.py src\services\risk_service.py src\ui\dashboard_page.py tests\test_resource_metrics_service.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests scripts\capture_feature_screenshot.py` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py -q` 3개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 105개 테스트 통과; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature dashboard --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local` 통과; Browser에서 Dashboard의 `자원관리 지표`, `예상 지연 프로그램`, `개발자별 부하` 렌더링 확인.

### 사용 가이드 제목 정리

- `docs/demo-user-guide.md`의 제목을 `AI Commit Advisor 사용 가이드`로 바꾸고, 샘플 프로젝트는 가이드의 대상이 아니라 설명 예시임을 첫 문단에 명확히 했습니다.
- README 문서 허브와 사용 가이드 내부 링크명을 `사용 가이드`, `사용 가이드 검증 결과`로 정리했습니다.
- `docs/sample-project-usage-verification.md`도 사용자 가이드는 샘플 프로젝트를 예시로 절차를 설명하고, 검증 증거는 별도 문서에서 관리한다는 구조로 맞췄습니다.
- 앞으로 같은 문서가 샘플 프로젝트 전용 가이드처럼 되돌아가지 않도록 `AGENTS.md` 내부 지침을 보강했습니다.
- 주요 파일: `docs/demo-user-guide.md`, `docs/sample-project-usage-verification.md`, `README.md`, `AGENTS.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "AI Commit Advisor 샘플 프로젝트 사용 가이드|\\[샘플 프로젝트 사용 가이드\\]|# 샘플 프로젝트 사용 가이드|샘플 프로젝트 사용 가이드 검증 결과|sample-project-only|사용 가이드" README.md docs\demo-user-guide.md docs\sample-project-usage-verification.md AGENTS.md`로 새 제목과 링크명 확인; `git diff --check` 통과.

### AX 자원관리 metric foundation

- AX Use Case의 개발자별 업무량, 진행도, 업무 난이도, 고객가치 KPI 확장을 위한 계산형 metric foundation을 추가했습니다.
- `resource_metrics_service.py`에서 프로그램별 난이도/업무량 근거, 개발자별 업무량·난이도 집계, 고객가치 KPI를 기존 `Program`, `GitCommit`, `CommitFile`, `ProgramCommitMapping`, `RiskFinding`, `CodeReviewResult` 데이터로 계산합니다.
- 첫 구현은 저장형 snapshot이나 Alembic migration 없이 조회 시점 계산형으로 두고, 예상 종료 일정과 전용 자원 대시보드는 후속 로드맵 작업에서 확장하도록 했습니다.
- 지표가 개인 성과 확정 평가가 아니라 PL 의사결정 보조 신호라는 해석 경계를 feature guide, AI technical overview, engineering decision log에 기록했습니다.
- 주요 파일: `src/services/resource_metrics_service.py`, `tests/test_resource_metrics_service.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `.\.venv\Scripts\python.exe -m py_compile src\services\resource_metrics_service.py tests\test_resource_metrics_service.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_resource_metrics_service.py -q` 2개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 104개 테스트 통과.

### AX 자원관리 로드맵 등록

- AX Use Case 명세 대비 현재 제품의 충족/미충족 항목을 바탕으로 자원관리 정렬 작업을 `ROADMAP.md`에 등록했습니다.
- 첫 실행 단위인 `AX resource management metrics foundation`을 `In Progress`로 두고, 예상 종료 일정, 개발자 업무량/난이도 대시보드, 고객가치 KPI 문서화를 후속 작업으로 분리했습니다.
- `AGENTS.md`의 문서 영향도 검토, 사용자-facing 문서 갱신, `AI_CHANGELOG.md` 갱신 정책이 이미 존재함을 반영해 별도 정책 변경은 하지 않았습니다.
- 주요 파일: `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "AX resource management metrics foundation|Forecasted completion|Developer workload and difficulty|AX customer value" ROADMAP.md AI_CHANGELOG.md` 통과; `git diff --check` 통과.

### 샘플 프로젝트 사용 가이드 실제 검증 결과 추가

- `AGENTS.md`에 샘플 프로젝트 사용 가이드의 end-to-end 검증 증거를 사용자용 가이드와 분리해 보관하는 정책을 추가했습니다.
- `AAA Sample Shop Usage Verification 20260614` 프로젝트를 새로 만들고 local LLM/embedding 환경에서 Git sync, Excel 데이터 저장, RAG chunk/vector 생성, Mapping, Risk Analysis, Project Chat, AI Code Review를 실제 실행했습니다.
- 검증 결과를 `docs/sample-project-usage-verification.md`에 정리하고, 단계별 화면 증거를 `docs/images/usage-verification/`에 저장했습니다.
- README와 샘플 프로젝트 사용 가이드의 관련 문서 목록에서 검증 결과 문서로 이동할 수 있게 링크를 추가했습니다.
- 주요 파일: `AGENTS.md`, `ROADMAP.md`, `README.md`, `docs/demo-user-guide.md`, `docs/sample-project-usage-verification.md`, `docs/images/usage-verification/*.png`, `AI_CHANGELOG.md`.
- 검증: local LM Studio `/v1/models`에서 `qwen2.5-coder-7b-instruct`와 `text-embedding-nomic-embed-text-v1.5` 확인; `docker compose ps`에서 PostgreSQL healthy 확인; 사용 가이드 실행 결과 Git commit 48개, 변경 파일 105개, 프로그램 8개, 표준용어 10개, chunk/vector 296개, Mapping 실패 0개, risk 14개, Project Chat `PaymentService.java` 근거 답변, AI Code Review completed 확인; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py ...` 캡처 명령 통과; `Get-ChildItem docs\images\usage-verification | Measure-Object` 11개 확인; `rg -n "sample-project-usage-verification|usage-verification|AAA Sample Shop Usage Verification 20260614" README.md docs\demo-user-guide.md docs\sample-project-usage-verification.md AI_CHANGELOG.md ROADMAP.md AGENTS.md` 통과; `git diff --check` 통과.

### README 대표 아키텍처 구조도 추가

- README 상단에 `Python App: AI Commit Advisor`, 저장소, 분석 대상 프로젝트, AI Provider를 큰 덩어리로 보여주는 Mermaid 구조도를 추가했습니다.
- 상세 모듈과 데이터 흐름은 기존 `docs/architecture.md`로 이어지도록 링크를 함께 남겼습니다.
- 주요 파일: `README.md`, `AI_CHANGELOG.md`.
- 검증: `npx -y @mermaid-js/mermaid-cli -i .tmp\readme-architecture.mmd -o .tmp\readme-architecture.svg` 통과; `git diff --check` 통과; GitHub README에서 Mermaid diagram 렌더링 확인.

### 샘플 프로젝트 사용 가이드 명칭 정리

- `docs/demo-user-guide.md`의 사용자-facing 제목과 본문에서 `검증 사용 가이드` 톤을 빼고 `샘플 프로젝트 사용 가이드`로 정리했습니다.
- README 문서 허브의 링크명도 `샘플 프로젝트 사용 가이드`로 바꾸고, 사용자가 샘플 프로젝트 흐름을 따라가는 문서로 설명했습니다.
- 이 문서가 데모 walkthrough로도 쓰일 수 있다는 내용은 사용자용 문서가 아니라 `AGENTS.md` 내부 지침에만 남겼습니다.
- 주요 파일: `docs/demo-user-guide.md`, `README.md`, `AGENTS.md`, `AI_CHANGELOG.md`.
- 검증: `docs/demo-user-guide.md`, `README.md`, `AGENTS.md`에서 샘플 프로젝트 사용 가이드 명칭과 내부 지침 분리가 반영된 것을 확인; `git diff --check` 통과.

### 아키텍처 큰 흐름 다이어그램 보강

- `docs/architecture.md` 상단에 사용자가 흔히 기대하는 큰 박스/화살표 중심의 전체 흐름 다이어그램을 추가했습니다.
- 첫 다이어그램을 처음 보는 사람용 최상위 구조도로 재정리하고, `Python App: AI Commit Advisor` 내부를 화면단, 백단, RAG로 나눈 뒤 외부의 저장소, 분석 대상 프로젝트, AI Provider와 어떻게 연결되는지 보이게 했습니다.
- `ai-commit-advisor` 프로젝트, 분석 대상 프로젝트, GitHub/사내 Git 원격 저장소, 앱 서버 clone, RAG layer가 어떻게 연결되는지 별도 다이어그램으로 보강했습니다.
- 상세 서비스/ERD 다이어그램은 기존 구조를 유지하고, 빠른 이해용 요약 섹션만 앞에 추가했습니다.
- 주요 파일: `docs/architecture.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "Python App: AI Commit Advisor|화면단|백단|저장소|분석 대상 프로젝트|AI Provider" docs\architecture.md AI_CHANGELOG.md` 통과; `git diff --check` 통과.

### Activation 없는 Quick Start 정리

- README Quick Start를 `Activate.ps1` 없이 `.venv\Scripts\python.exe -m ...` 명령으로 실행하도록 바꿨습니다.
- 가상환경 activation 명령이 PowerShell, cmd.exe, Git Bash마다 다르다는 점을 setup/operations 문서에 설명하고, 기본 설치/DB 초기화/Streamlit 실행/복구 절차를 activation 없는 명령으로 통일했습니다.
- `.venv` Quick Start 실패 이력에 터미널별 activation 명령 차이와 재발 방지 규칙을 보강했습니다.
- 주요 파일: `README.md`, `docs/setup-and-operations.md`, `docs/failure-history.md`, `AI_CHANGELOG.md`.
- 검증: `git diff --check` 통과. Windows 줄바꿈 경고만 확인했습니다.

### Windows `.venv` Quick Start 실패 이력과 복구 가이드

- VS Code 로컬 실행에서 `.venv`의 native package가 깨져 `pydantic_core`, `psycopg2`, `pandas` import 오류가 발생한 사례를 실패 이력에 기록했습니다.
- 기존 `.venv`가 있을 때 Quick Start를 다시 수행하는 사용자가 복구할 수 있도록 setup/operations 문서에 `.venv` 재생성 절차와 `pip check` 확인 절차를 추가했습니다.
- 이번 실패가 코드 회귀가 아니라 로컬 가상환경 손상과 Quick Start 검증 범위 누락에서 나온 문제였음을 기록했습니다.
- 주요 파일: `docs/failure-history.md`, `docs/setup-and-operations.md`, `AI_CHANGELOG.md`.
- 검증: `git diff --check` 통과. Windows 줄바꿈 경고만 확인했습니다.

### AI 변경 이력 한국어 작성 정책

- 새 `AI_CHANGELOG.md` 항목은 기본적으로 한국어로 작성하도록 agent 작업 정책을 명확히 했습니다.
- 경로, 명령어, 환경 변수, API 이름, model/provider 이름, table/class/function 이름처럼 원문이 더 정확한 기술 식별자는 그대로 유지하도록 했습니다.
- 기존 영문 이력은 전체 소급 번역하지 않고, 수정하는 항목부터 한국어로 정리하는 기준을 남겼습니다.
- 주요 파일: `AGENTS.md`, `docs/engineering-decisions.md`, `AI_CHANGELOG.md`.
- 검증: `git diff --check` 통과. Windows 줄바꿈 경고만 확인했습니다.

### 로드맵 커밋 해시 기록 정책

- 완료된 로드맵 작업의 commit hash는 `ROADMAP.md`에 기록하고, `AI_CHANGELOG.md`는 변경 요약, 주요 파일, 검증 결과에 집중하도록 정책을 명확히 했습니다.
- 완료된 `프로젝트 개발자 연결 모델` 작업의 commit hash를 로드맵에 추가했습니다.
- 문서 정책을 나눈 이유를 engineering decision log에 기록했습니다.
- 주요 파일: `ROADMAP.md`, `docs/engineering-decisions.md`, `AI_CHANGELOG.md`.
- 검증: `git diff --check` 통과. Windows 줄바꿈 경고만 확인했습니다.

### 프로젝트 개발자 연결 모델

- `developers`와 `programs.developer_id`의 기존 호환성을 유지하면서, 프로젝트와 전역 개발자를 연결하는 `project_developers` membership 테이블을 추가했습니다.
- 프로젝트 개발자 연결 helper와 프로젝트 범위 개발자 목록 조회를 추가했고, Git author 추출, 직접 추가, Excel 업로드가 현재 프로젝트가 있을 때 개발자를 프로젝트에 연결하도록 했습니다.
- 개발자 관리 UI의 기본 화면은 현재 프로젝트 개발자를 보여주고, 별도 `전역 마스터` 탭에서 전체 전역 개발자 마스터를 볼 수 있게 했습니다.
- membership 생성, 중복 방지, 여러 프로젝트에서 같은 개발자 재사용, 프로젝트/개발자 삭제 cascade, 프로젝트 삭제 영향 범위를 DB 기반 테스트로 검증했습니다.
- 전역 개발자 마스터와 프로젝트 개발자 연결의 차이를 architecture, feature guide, engineering decision, DB migration 문서에 정리했습니다.
- 주요 파일: `migrations/versions/20260614_0005_add_project_developers.py`, `src/db/models.py`, `src/services/project_developer_service.py`, `src/services/developer_service.py`, `src/services/developer_management_service.py`, `src/ui/developer_upload_page.py`, `tests/test_developer_management_service.py`, `tests/test_project_management_service.py`, `docs/architecture.md`, `docs/feature-guide.md`, `docs/engineering-decisions.md`, `docs/db-migrations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `docker compose up -d postgres` 통과; `.\.venv\Scripts\python.exe -m py_compile src\db\models.py src\services\developer_service.py src\services\developer_management_service.py src\services\project_developer_service.py src\ui\developer_upload_page.py migrations\versions\20260614_0005_add_project_developers.py` 통과; `.\.venv\Scripts\alembic.exe upgrade head` 통과; `.\.venv\Scripts\alembic.exe heads`와 `.\.venv\Scripts\alembic.exe current` 모두 `20260614_0005 (head)` 확인; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_developer_management_service.py tests\test_project_management_service.py -q` 11개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 102개 테스트 통과; `git diff --check` 통과. Windows 줄바꿈 경고만 확인했습니다.

### 프로젝트 삭제와 데모 재실행 안전장치

- 전역 `developers` 마스터는 유지하면서 프로젝트 소유 데이터를 삭제하고 삭제 영향 건수를 보여주는 project management service를 추가했습니다.
- 삭제 영향 건수 표시, 프로젝트명 재입력 확인, 삭제 후 현재 프로젝트 선택 복구를 포함한 `프로젝트/Git 설정` 삭제 flow를 추가했습니다.
- 삭제 영향, cascade cleanup, 다른 프로젝트 보존, 개발자 보존을 DB 기반 focused test로 검증했습니다.
- 삭제 정책을 feature guide, demo user guide, architecture, engineering decisions에 문서화했습니다.
- 주요 파일: `src/services/project_management_service.py`, `src/ui/project_page.py`, `tests/test_project_management_service.py`, `docs/feature-guide.md`, `docs/demo-user-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `docker compose up -d postgres` 통과; `.\.venv\Scripts\python.exe -c "from src.db.init_db import init_db; init_db(); print('init ok')"` 통과; `.\.venv\Scripts\python.exe -m py_compile src\services\project_management_service.py src\ui\project_page.py tests\test_project_management_service.py` 통과; `.\.venv\Scripts\python.exe -m compileall src app.py tests` 통과; `.\.venv\Scripts\python.exe -m pytest tests\test_project_management_service.py tests\test_project_context.py -q` 5개 테스트 통과; `.\.venv\Scripts\python.exe -m pytest -q` 97개 테스트 통과; `git diff --check` 통과. Windows 줄바꿈 경고만 확인했습니다.

### 프로젝트 삭제와 개발자 범위 로드맵

- 샘플 프로젝트 데모를 반복 실행하기 위한 안전한 구현 순서를 기록했습니다. 먼저 프로젝트 삭제/데모 재실행 안전장치를 추가하고, 이후 전역 개발자 마스터를 깨지 않는 프로젝트 개발자 연결을 도입하는 흐름입니다.
- 개발자 범위 candidate를 넓은 미결 질문에서 향후 `project_developers` membership 테이블을 사용하는 호환성 우선 방향으로 구체화했습니다.
- 주요 파일: `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "Project delete and demo reset safety|Project developer membership model|project_developers" ROADMAP.md AI_CHANGELOG.md` 통과; `git diff --check`에서 Windows 줄바꿈 경고만 확인했고 공백 오류는 없었습니다.

### 데모 사용자 가이드

- 프로젝트 등록과 Git sync부터 Mapping, Risk Analysis, AI Progress, Program Detail, Git History, Commit Impact, RAG, Project Chat, AI Code Review까지 샘플 프로젝트 검증 흐름을 설명하는 사용자용 검증 가이드를 추가했습니다.
- 발표자가 문서 허브에서 바로 찾을 수 있도록 README에 가이드 링크를 추가했습니다.
- 샘플 walkthrough에 남아 있던 예상 commit 수 30개 표현을 48개 기준으로 수정했습니다.
- 주요 파일: `docs/demo-user-guide.md`, `README.md`, `docs/rich-sample-demo-walkthrough.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- 검증: `rg -n "demo-user-guide|검증 사용 가이드|예상 샘플 commit 수|30입니다|48입니다" README.md docs\demo-user-guide.md docs\rich-sample-demo-walkthrough.md`에서 README 링크, 새 가이드 제목, 48-commit 문구를 확인했고 오래된 30-commit 문구는 없었습니다. `git diff --check`에서 Windows 줄바꿈 경고만 확인했고 공백 오류는 없었습니다.

## 2026-06-10

### CI Git default branch test fix

- Made Git repository status tests deterministic on Linux CI by explicitly creating or renaming temporary test repositories to the `main` branch before pushing to `origin/main`.
- Recorded the CI failure lesson that Git-dependent tests must not rely on each developer machine's global `init.defaultBranch`.
- Important files: `tests/test_git_repository_status_service.py`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: Linux container reproduction with Git installed failed before the fix on `test_repository_status_reports_upstream_ahead_behind` because `git push -u origin main` had no local `main` ref; `.\.venv\Scripts\python.exe -m compileall src app.py tests` passed; `.\.venv\Scripts\python.exe -m pytest tests\test_git_repository_status_service.py -q` passed with 4 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 95 tests; Linux container verification with Git installed and CI-like env passed with 95 tests.

### Commit-based mapping fallback and verified application screenshots

- Ran the 48-commit sample project through the core demo pipeline before refreshing screenshots: Git sync data, commit-based Mapping, Risk Analysis, AI Progress, RAG indexing/retrieval, and Project Chat.
- Added a commit-based Mapping fallback so malformed LLM JSON responses use conservative token-similarity evidence instead of leaving a single commit in failed state and blocking downstream verification.
- Added a process-local DB initialization lock so concurrent Streamlit sessions do not run Alembic migrations at the same time during screenshot automation.
- Extended screenshot automation with project selection, tab/action support, and realistic RAG search input.
- Refreshed Application Preview screenshots for Home, Mapping, Risk Analysis, AI Progress, RAG Search, Project Chat, Git History, and Git History detail against `AAA Sample Shop Rich Demo 48`.
- Refreshed the README top representative screenshot `docs/images/ai-commit-advisor-home.png` from the same verified Home state so README and Application Preview show the same sample project status.
- Added `docs/images/ai-commit-advisor-home-48.png` and updated README to use that versioned file name so GitHub/browser image cache cannot keep showing the previous representative screenshot.
- Updated AI behavior documentation, Application Preview context, roadmap tracking, and failure history for the verified demo flow and the two reusable failure lessons.
- Important files: `src/services/mapping_service.py`, `src/db/init_db.py`, `scripts/capture_feature_screenshot.py`, `tests/test_mapping_service.py`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/failure-history.md`, `docs/images/ai-commit-advisor-home.png`, `docs/images/ai-commit-advisor-home-48.png`, `docs/images/features/*.png`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py scripts` passed; `.\.venv\Scripts\python.exe -m pytest tests\test_mapping_service.py -q` passed with 4 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 95 tests; 48-commit Mapping verification completed 48 commits with 0 failed and 59 mappings; Risk Analysis produced 12 unresolved risks; AI Progress produced 8 implementation-status rows with plan average 90.6%, AI average 50.0%, and gap 40.6%; RAG indexing built and embedded 296 chunks with 0 failures; Project Chat answered `결제금액 검증은 어디에서 수행되나요?` with 8 sources including `PaymentService.java`; screenshot capture passed for `home`, `mapping`, `risk-analysis`, `ai-progress`, `rag-search`, `project-chat`, `git-history`, and `git-history-detail`; `git diff --check` passed with only Windows line-ending warnings.

### Sample project commit history expansion

- Expanded the generated 샘플 프로젝트 history from 30 to 48 commits while keeping the existing 8-program Spring MVC + MyBatis shape.
- Added meaningful follow-up scenarios for payment audit and amount limits, inventory release, dashboard stale-payment warning, settlement export partial evidence, return backlog documentation, sales-report tax correction, coupon partial completion, operator audit evidence, QA checklists, and Project Chat citation prompts.
- Updated sample design and walkthrough documentation to describe the new 35-50 commit target range and 48-commit generated dataset.
- Regenerated the sibling sample project repository at `C:\dev\ai-advisor-sample-shop` with 48 commits and refreshed upload Excel files.
- Important files: `scripts/create_sample_target_repo.py`, `tests/test_sample_data_generation.py`, `docs/sample-target-repo-demo-design.md`, `docs/rich-sample-demo-walkthrough.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m py_compile scripts\create_sample_target_repo.py` passed; `.\.venv\Scripts\python.exe -m pytest tests\test_sample_data_generation.py -q` passed with 12 tests; `.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force` passed and regenerated `C:\dev\ai-advisor-sample-shop`; `git -C C:\dev\ai-advisor-sample-shop rev-list --count HEAD` returned `48`; `git -C C:\dev\ai-advisor-sample-shop status --short` returned no changes; upload files `sample_developers.xlsx`, `sample_development_plan.xlsx`, `sample_programs.xlsx`, and `sample_standard_terms.xlsx` exist; local Streamlit web verification on `http://localhost:8537` created `AAA Sample Shop 48 Web Test (97)`, Git full sync stored 48 commits and 105 changed files, the same import/save services used by the Excel upload screens stored 8 programs, 8 development-plan rows, and 10 standard terms, Home displayed 8 programs and 48 commits, Git History displayed 48 commits and 105 changed files, Program management displayed 8 programs, and Standard Terms displayed 10 rows; `.\.venv\Scripts\python.exe -m compileall scripts src app.py` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 94 tests.

### Server repository status display

- Added `src/services/git_repository_status_service.py` to read app-server Git repository branch, HEAD, upstream, ahead/behind, working tree changes, storage-root allowance, and DB sync mismatch status without mutating the repo.
- Added a shared `src/ui/git_status_panel.py` status panel.
- Updated `Git 동기화` to show full repository status before sync actions, including Repo HEAD, DB sync commit, branch, upstream, ahead/behind, dirty file count, and guidance when DB sync is stale.
- Updated `프로젝트/Git 설정` to show a compact repository status summary for the selected project.
- Added focused tests for clean repo status, dirty working tree detection, missing path handling, and upstream ahead/behind detection.
- Updated feature, setup/operations, architecture, and roadmap documentation.
- Important files: `src/services/git_repository_status_service.py`, `src/ui/git_status_panel.py`, `src/ui/git_page.py`, `src/ui/project_page.py`, `tests/test_git_repository_status_service.py`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/architecture.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest tests/test_git_repository_status_service.py -q` passed with 4 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 94 tests.

### Git History Application Preview screenshot

- Added Git History scenarios to `scripts/capture_feature_screenshot.py` so the commit list/activity graph state and commit detail/diff preview state can be recaptured.
- Captured `docs/images/features/git-history.png` against the local Streamlit app using the `AAA Sample Shop Rich Demo` project with 30 commits and 77 changed files.
- Captured `docs/images/features/git-history-detail.png` to show selected commit metadata, changed files, saved diff preview, and full-diff control.
- Updated `docs/application-preview.md` to include both Git History screenshots.
- Important files: `scripts/capture_feature_screenshot.py`, `docs/application-preview.md`, `docs/images/features/git-history.png`, `docs/images/features/git-history-detail.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature git-history --url http://127.0.0.1:8531 --screenshot docs\images\features\git-history.png --surface local --height 1700 --expect-text "AAA Sample Shop Rich Demo" --expect-text "변경 파일" --expect-text "저장된 diff preview"` passed; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature git-history-detail --url http://127.0.0.1:8531 --screenshot docs\images\features\git-history-detail.png --surface local --height 1000 --expect-text "AAA Sample Shop Rich Demo" --expect-text "저장된 diff preview" --expect-text "전체 diff"` passed; visual inspection confirmed the screenshots show meaningful Git History states.

### Git History viewer

- Added `src/services/git_history_service.py` for project-scoped commit listing, commit detail lookup, changed-file diff preview data, and safe full `git show` retrieval for DB-registered commits.
- Added `src/ui/git_history_page.py` with message, author, file path, date, and limit filters; commit KPI summary; daily and author commit charts; selected commit details; changed file diff preview; and optional full diff lookup from the app-server Git repository.
- Added the `Git History` navigation entry under `분석 결과`.
- Added focused tests for message/author/file filtering, commit detail retrieval, full diff lookup, and missing-commit safety behavior.
- Updated README, feature guide, architecture docs, and roadmap tracking for the new Git History screen.
- Important files: `app.py`, `src/services/git_history_service.py`, `src/ui/git_history_page.py`, `tests/test_git_history_service.py`, `README.md`, `docs/feature-guide.md`, `docs/architecture.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py scripts\update_server_repos.py` passed; `.\.venv\Scripts\python.exe -m pytest tests/test_git_history_service.py -q` passed with 2 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 90 tests.

### Server repository update runbook and script

- Added `scripts/update_server_repos.py` for internal server operators to update pre-cloned repositories under `REPO_STORAGE_ROOT`.
- Kept the script credential-free: it does not clone repositories or store Git secrets, and defaults to `git fetch --prune` without hard reset.
- Added explicit `--reset`, `--branch`, `--force`, `--dry-run`, and `--repo` options so branch reset is deliberate and dirty working trees are not reset unless forced.
- Added `docs/server-repository-update-runbook.md` with manual commands, script usage, dry-run examples, and the recommended sequence before app Git Sync.
- Linked the runbook from README, setup/operations, Git repository operating model, and engineering decision docs.
- Promoted and completed the roadmap task for the server repository update runbook/script.
- Important files: `scripts/update_server_repos.py`, `docs/server-repository-update-runbook.md`, `README.md`, `docs/git-repository-operating-model.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m py_compile scripts\update_server_repos.py` passed; `.\.venv\Scripts\python.exe scripts\update_server_repos.py --help` passed; dry-run against a temporary Git repository under `.tmp\server-repo-update-check` passed; `git diff --check` passed with only line-ending warnings.

### App-server Git repository operating model

- Reframed Git repository access from browser-user local paths to app-server-accessible repository paths for internal-network server operation.
- Added optional `REPO_STORAGE_ROOT` configuration and project path validation so server deployments can restrict registered Git repositories to an approved storage root.
- Updated Git/project UI labels and messages to use app-server Git repository wording.
- Added `docs/git-repository-operating-model.md` and linked it from README to explain the server-path model, recommended repo storage layout, Docker path mapping, Git Sync boundaries, and security notes.
- Added the same app-server path clarification to README Quick Start and setup/operations local execution guidance so first-time local users understand that their PC is the app server.
- Documented sample project path handling for local Python, default Windows Docker Compose, and internal-server demo runs.
- Documented the recommended operating policy that repository clone/fetch/reset remains an operator or external script responsibility for now, while AI Commit Advisor analyzes pre-cloned app-server repository paths and performs DB Git Sync.
- Added a roadmap candidate for a server repository update runbook/script before any app-managed clone/fetch workflow.
- Updated setup/operations, feature guide, architecture, engineering decision, environment examples, Docker Compose, and roadmap documentation.
- Preserved `git_repo_path` as the internal DB/model name for compatibility while clarifying its meaning in user-facing docs.
- Important files: `src/utils/config.py`, `src/utils/repo_path.py`, `src/ui/project_page.py`, `src/ui/git_page.py`, `src/ui/code_review_page.py`, `src/ui/rag_page.py`, `src/ui/sample_data_page.py`, `tests/test_repo_path.py`, `README.md`, `docs/git-repository-operating-model.md`, `docs/setup-and-operations.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/sample-target-repo-demo-design.md`, `docs/architecture.md`, `docs/feature-guide.md`, `docs/engineering-decisions.md`, `docker-compose.yml`, `.env.example`, `.env.local-llm.example`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest tests/test_repo_path.py -q` passed with 5 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed with 88 tests.

### Roadmap candidate task tracking

- Added a `Candidate Tasks` section to `ROADMAP.md` for unresolved product, UX, state-management, and architecture concerns that should be preserved without marking them active.
- Recorded follow-up candidates for project-scoped UI state namespacing, program management project-flow cleanup, and developer management scope decision.
- Updated `AGENTS.md` so agents add candidate tasks when the user wants to preserve a concern without starting implementation, and promote candidates into active roadmap tasks before implementation.
- Recorded the documentation/roadmap management decision in `docs/engineering-decisions.md`.
- Important files: `ROADMAP.md`, `AGENTS.md`, `docs/engineering-decisions.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path ROADMAP.md -Encoding UTF8`, `Get-Content -Path AGENTS.md -Encoding UTF8`, and `Get-Content -Path docs\engineering-decisions.md -Encoding UTF8` rendered the new sections correctly; `rg -n "Candidate Tasks|Project-scoped UI state namespacing|Program management project flow cleanup|Developer management scope decision" ROADMAP.md AGENTS.md docs\engineering-decisions.md AI_CHANGELOG.md` confirmed expected references; `git diff --check` passed with only line-ending warnings.

### Home current project focus

- Changed Home from an all-project aggregate into a current-project command screen that uses the shared sidebar project context.
- Scoped Home pipeline status, next actions, KPIs, progress charts, and risk program table to the selected project.
- Kept app-level project count and developer count as secondary context while project-specific program, commit, mapping, implementation status, and risk counts use the current project.
- Updated feature and architecture documentation, refreshed the Home Application Preview screenshot, and tracked the UX task in `ROADMAP.md`.
- Important files: `src/ui/home_page.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/images/features/home.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 85 tests; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8524 --screenshot docs\images\features\home.png --surface local --expect-text "현재 프로젝트: AAA Sample Shop Rich Demo (4)" --expect-text "현재 프로젝트의 계획, 커밋, 진척도, 리스크 현황"` passed and confirmed Home shows current-project counts such as 8 programs and 30 commits for the sample project.

### Global project context

- Added `src/ui/project_context.py` as the shared UI helper for current project selection, validation, deleted-selection recovery, and sidebar rendering.
- Moved the current project selector into the sidebar and converted project-scoped pages to use the shared context instead of repeated page-level `프로젝트 선택` controls.
- Kept `프로젝트/Git 설정` as the project creation/editing exception and synchronized saved projects back to the global current project.
- Updated `프로그램 관리` so the global project is the default target while preserving an explicit `새 프로젝트명으로 저장` exception for legacy upload/create flows.
- Added focused tests for project context selection retention, invalid selection recovery, and no-project cleanup.
- Updated feature, architecture, engineering decision, roadmap, changelog, and Home preview screenshot documentation for the new project-selection flow.
- Important files: `app.py`, `src/ui/project_context.py`, `src/ui/*_page.py`, `tests/test_project_context.py`, `docs/feature-guide.md`, `docs/architecture.md`, `docs/engineering-decisions.md`, `docs/images/features/home.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src app.py` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 85 tests; Browser verification on `http://localhost:8522` confirmed Home, Dashboard, and Mapping show the sidebar current project without duplicated page-level project selectors, while `프로젝트/Git 설정` keeps its expected project selector; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8522 --screenshot docs\images\features\home.png --surface local` passed.

### AI Agent onboarding guide

- Added `docs/agent-onboarding.md`, a beginner-friendly Korean guide for developers using AI Agent workflows with this project.
- Explained that `AGENTS.md` is durable project guidance loaded by Codex from the project folder, not text that needs to be repeated in every prompt.
- Clarified when users should mention `ROADMAP.md`, documentation checks, verification constraints, or exclusions directly in a prompt.
- Linked the onboarding guide from README and tracked the documentation task in `ROADMAP.md`.
- Generalized README and onboarding wording around `AI Agent` users instead of naming Codex beginners or teammates in the entry description.
- Shortened the guide title and README description so the onboarding link reads like a project document rather than a generic AI Agent introduction.
- Important files: `docs/agent-onboarding.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Test-Path docs\agent-onboarding.md` returned `True`; `rg -n "AI Agent 작업 안내|AGENTS.md를 매번" README.md docs\agent-onboarding.md AI_CHANGELOG.md ROADMAP.md` confirmed the expected references; `Get-Content -Path README.md -Encoding UTF8` rendered the README document link correctly; `git diff --check` passed with only Git line-ending warnings.

### Sidebar navigation structure stabilization

- Rendered active and inactive sidebar menu items through the same `st.button` path instead of mixing Streamlit buttons with custom `.nav-active` markup.
- Removed custom active menu `div` CSS and made repeated clicks on the current page a no-op without rerun.
- Expanded Home screenshot verification so sidebar checks fail when custom `.nav-active` markup returns or when menu item boxes, text offsets, or adjacent spacing change after navigation.
- Recorded the maintainability decision in `docs/engineering-decisions.md` and the previous CSS-only stabilization gap in `docs/failure-history.md`.
- Important files: `app.py`, `scripts/capture_feature_screenshot.py`, `docs/engineering-decisions.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall app.py src scripts` passed; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8518 --screenshot .tmp\sidebar-structure-home.png --surface local` passed; `git diff --check` passed with only Git line-ending warnings.

### Documentation impact gate policy

- Added a `Documentation Impact Gate` to `AGENTS.md` so meaningful code, UX, test, behavior, automation, operations, and documentation work must classify documentation impact before implementation.
- Made `docs/engineering-decisions.md` a required review candidate when a request is framed around maintainability, future reuse, verification policy, structural tradeoffs, operating policy, or agent behavior.
- Recorded the policy rationale in `docs/engineering-decisions.md` and the missed engineering-decision review in `docs/failure-history.md`.
- Added a roadmap task for the documentation impact gate policy work.
- Important files: `AGENTS.md`, `docs/engineering-decisions.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8`, `Get-Content -Path docs\engineering-decisions.md -Encoding UTF8`, and `Get-Content -Path docs\failure-history.md -Encoding UTF8` rendered the new policy, decision, and failure-history entries correctly; `rg -n "Documentation Impact Gate|Documentation impact gate|Engineering decision review|engineering-decisions.md" AGENTS.md docs AI_CHANGELOG.md ROADMAP.md` confirmed the expected references; `git diff --check` passed with only Git line-ending warnings.

### Sidebar 메뉴 계층 크기 조정

- Sidebar 중메뉴가 하위 메뉴보다 살짝 크게 보이도록 그룹 제목은 `0.9rem`, 하위 메뉴와 선택 메뉴는 `0.86rem`으로 조정했습니다.
- Streamlit button 내부 텍스트에도 같은 크기와 line-height를 적용해 메뉴 클릭 전후 글자 크기가 달라 보이지 않도록 했습니다.
- Home Application Preview screenshot을 새 사이드바 계층 스타일이 보이도록 다시 캡처했습니다.
- 기능 가이드와 Application Preview 문서에 사이드바 중메뉴/하위 메뉴 계층 의도를 반영했습니다.
- Important files: `app.py`, `docs/images/features/home.png`, `docs/feature-guide.md`, `docs/application-preview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall app.py src` passed; `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8511 --screenshot docs\images\features\home.png --surface local` passed; browser inspection on local port 8511 confirmed group labels render at 14.4px and child menu items render at 13.76px; clicking `Dashboard` confirmed active and inactive child menu text both render at 13.76px with 18.576px line-height before and after selection.

### Reader-facing wording policy simplification

- Simplified the `AGENTS.md` natural Korean documentation wording policy by removing preferred phrase examples.
- Kept the principle that user-facing Korean docs should use reader-facing product terms instead of literal internal repository or data-generation terminology.
- Kept the guidance to preserve stable technical file paths while making link labels and surrounding explanation natural.
- Important files: `AGENTS.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8` rendered the simplified policy correctly; targeted search confirmed the preferred phrase examples were removed from `AGENTS.md`; `git diff --check` passed with only Git line-ending warnings.

### Natural wording policy generalization

- Generalized the `AGENTS.md` natural Korean documentation wording policy so it no longer lists awkward phrases one by one.
- Kept the preferred `샘플 프로젝트`, `데모용 샘플 프로젝트`, `샘플 프로젝트 Git 저장소`, and `샘플 프로젝트 설계` guidance while describing the avoid rule as a general principle.
- Important files: `AGENTS.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: targeted `AGENTS.md` search confirmed the explicit awkward-phrase list was removed; `Get-Content -Path AGENTS.md -Encoding UTF8` rendered the generalized policy correctly; `git diff --check` passed with only Git line-ending warnings.

### Sample project wording cleanup

- Added `AGENTS.md` guidance to avoid literal sample/demo wording such as `샘플 대상 저장소`, `합성 샘플 저장소`, and `sample target repo` in user-facing Korean documentation.
- Updated README, sample project design, and sample verification guide prose to use `샘플 프로젝트`, `데모용 샘플 프로젝트`, and `샘플 프로젝트 Git 저장소` where appropriate.
- Recorded the wording decision in `docs/engineering-decisions.md`.
- Kept code identifiers and existing file names unchanged to avoid unnecessary path churn.
- Important files: `AGENTS.md`, `README.md`, `docs/sample-target-repo-demo-design.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/source-indexing-and-embedding-plan.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: targeted wording search across README and user-facing docs returned no matches for the awkward sample-target/synthetic-target wording; `Get-Content -Encoding UTF8` confirmed README, sample project design, and sample verification guide render Korean text correctly; `git diff --check` passed with only Git line-ending warnings.

### Application Preview rename

- Renamed the previous screenshot-focused document to `docs/application-preview.md`.
- Updated README, Feature Guide, setup/operations guidance, `AGENTS.md`, and engineering decision references to use `Application Preview`.
- Renamed the agent screenshot policy section to `Application Preview Screenshot Guidance`.
- Replaced stale Markdown path references so current documentation searches point to the new document path.
- Important files: `docs/application-preview.md`, `README.md`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `AGENTS.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: legacy gallery naming and path searches returned no matches; local `Test-Path` checks passed for `docs\application-preview.md` and updated Markdown files; `Get-Content -Path docs\application-preview.md -Encoding UTF8` rendered the renamed Korean document correctly; `git diff --check` passed with only Git line-ending warnings.

### Architecture document path cleanup

- Moved the root architecture guide to `docs/architecture.md` so detailed project documentation lives under `docs/`.
- Updated README and `AGENTS.md` references to use the new architecture document path.
- Replaced stale architecture document path references in Markdown history so current path searches do not point to the removed root file.
- Recorded the documentation structure rationale in `docs/engineering-decisions.md`.
- Important files: `docs/architecture.md`, `README.md`, `AGENTS.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `rg -n "README_ARCHITECTURE\\.md" .` returned no matches; `rg -n "docs/architecture\\.md|architecture\\.md|Architecture document path cleanup|아키텍처" README.md AGENTS.md AI_CHANGELOG.md ROADMAP.md docs` confirmed the new references; local `Test-Path` checks passed for `docs\architecture.md` and updated Markdown files; `Get-Content -Path docs\architecture.md -Encoding UTF8` rendered the moved Korean document correctly; `git diff --check` passed with only Git line-ending warnings.

### Feature screenshot capture automation

- Added `scripts/capture_feature_screenshot.py`, an extensible Playwright-based capture tool with starter scenarios for `home` and `project-chat`.
- Kept `scripts/verify_home_ui.py` as a compatibility wrapper around the new Home scenario.
- Documented capture commands, runtime surface labeling, and `--expect-text` / `--forbid-text` state checks in setup and operations guidance.
- Updated the engineering decisions log with the implemented script and initial scenario scope.
- Important files: `scripts/capture_feature_screenshot.py`, `scripts/verify_home_ui.py`, `docs/setup-and-operations.md`, `docs/engineering-decisions.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m py_compile scripts\\capture_feature_screenshot.py scripts\\verify_home_ui.py` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --help` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --feature home --url http://localhost:8501 --screenshot .tmp\\feature-home-check.png --surface local` passed; `.\\.venv\\Scripts\\python.exe scripts\\verify_home_ui.py --url http://localhost:8501 --screenshot .tmp\\home-wrapper-check.png` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --feature project-chat --url http://localhost:8501 --screenshot .tmp\\project-chat-scenario-check.png --surface local` passed; `.\\.venv\\Scripts\\python.exe scripts\\capture_feature_screenshot.py --feature all --url http://localhost:8501 --output-dir .tmp\\feature-captures --surface local` passed and wrote only under `.tmp`; `git diff --check` passed.

### Engineering decisions documentation log

- Added `docs/engineering-decisions.md` to record non-failure engineering, operations, verification, automation, deployment, and documentation-structure decisions with rationale and tradeoffs.
- Recorded the screenshot capture automation direction as the first decision, including why future capture work should use extensible feature scenarios instead of one-off manual flows.
- Updated `AGENTS.md`, README, and failure-history guidance so agents can distinguish changelog entries, failure history, and decision history.
- Added a roadmap task for the decision log documentation work.
- Important files: `docs/engineering-decisions.md`, `AGENTS.md`, `README.md`, `docs/failure-history.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path docs\engineering-decisions.md -Encoding UTF8` rendered the new Korean decision log correctly; `rg -n "engineering-decisions|Engineering Decisions|Engineering decisions documentation log|Engineering Decisions Log" README.md AGENTS.md docs\failure-history.md AI_CHANGELOG.md ROADMAP.md` confirmed the expected links and policy references; local `Test-Path` checks passed for the linked Markdown files; `git diff --check` passed with only Git line-ending warnings.

### Ignore Codex attachment staging folder

- Added `.codex-remote-attachments/` to `.gitignore` so uploaded chat attachment files do not appear as untracked project changes.
- Important files: `.gitignore`, `AI_CHANGELOG.md`.
- Verification: `git status --short --branch` no longer lists `.codex-remote-attachments/` as an untracked path; `git diff --check` passed.

### Verification surface selection agent policy

- Added `AGENTS.md` guidance for choosing local `.venv` verification versus Docker verification based on the behavior being changed.
- Clarified that ordinary app source changes should not trigger Docker image rebuilds by default, while Dockerfile, Compose, mount, env, startup migration, healthcheck, and container-only bugs require Docker verification.
- Added guidance to keep Docker build log inspection targeted because build logs are long, and to state which surface was verified when local Python and Docker can differ.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8` confirmed the new policy text; `git diff --check` passed.

### Project Chat verified answer screenshot recapture

- Re-captured the Project Chat screenshot after confirming Docker source verification was fixed.
- The refreshed screenshot shows matching Current HEAD and Indexed HEAD, a successful answer for `결제금액 검증은 어디에서 수행되나요?`, visible `PaymentService.java` evidence, and `근거 복사용 Markdown`.
- Important files: `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: Playwright verified `대화 이력`, the payment validation question, `PaymentService.java`, current source evidence count, and `근거 복사용 Markdown` were visible; visually inspected the screenshot; `git diff --check` passed.

### Docker repository path mapping for Project Chat verification

- Added repository path prefix mapping so Docker app containers can read host Git repositories stored in the DB as Windows paths such as `C:\dev\ai-advisor-sample-shop`.
- Mounted `C:/dev` into the app container as `/host-dev` and added `REPO_PATH_HOST_PREFIX` / `REPO_PATH_CONTAINER_PREFIX` environment variables in Compose.
- Installed `git` in the Docker image because Git Sync and current HEAD checks need the Git command inside the app container.
- Applied mapped repo paths to Git commands, source_file chunking, source index status, and Project Chat source verification.
- Added focused tests for repository path mapping.
- Documented the Docker host repo mount behavior in setup/operations, architecture, and failure history.
- Re-captured the Project Chat screenshot after Docker source verification was restored so the answer shows verified `PaymentService.java` evidence instead of an insufficient-evidence state.
- Important files: `Dockerfile`, `src/utils/config.py`, `src/utils/repo_path.py`, `src/services/git_service.py`, `src/rag/source_verifier.py`, `src/rag/source_index_service.py`, `src/rag/chunker.py`, `tests/test_repo_path.py`, `docker-compose.yml`, `docs/setup-and-operations.md`, `docs/architecture.md`, `docs/failure-history.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m py_compile src/utils/config.py src/utils/repo_path.py src/services/git_service.py src/rag/source_verifier.py src/rag/source_index_service.py src/rag/chunker.py` passed; `.\\.venv\\Scripts\\python.exe -m pytest tests/test_repo_path.py tests/test_source_file_rag.py tests/test_source_index_service.py tests/test_project_chat_service.py -q` passed; `docker compose config` passed; Docker app verified the sample Project Chat source index with matching Current HEAD and Indexed HEAD, invalid/stale/mismatch counts at 0, and visible `PaymentService.java` answer evidence; `git diff --check` passed.

### CI manual rerun trigger for hosted runner failures

- Added `workflow_dispatch` to the GitHub Actions CI workflow so CI can be manually rerun from the Actions UI without creating another push.
- Documented the GitHub-hosted runner acquisition failure for `docs: explain RAG chat rationale #42`, including how to distinguish platform runner failures from code/test failures.
- Important files: `.github/workflows/ci.yml`, `docs/failure-history.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m compileall src app.py` passed; `.\\.venv\\Scripts\\python.exe -m pytest -q` passed with 80 tests; `git diff --check` passed.

### Project Chat persisted history screenshot refresh

- Refreshed the Project Chat screenshot so the gallery shows the newly added persisted `대화 이력`, saved question/answer rendering, verified current source evidence, and `근거 복사용 Markdown` export area.
- Added a short Application Preview caption describing the captured Project Chat state.
- Important files: `docs/images/features/project-chat.png`, `docs/application-preview.md`, `AI_CHANGELOG.md`.
- Verification: Playwright captured `docs/images/features/project-chat.png` from `http://localhost:8501` after verifying `대화 이력`, `결제금액 검증은 어디에서 수행되나요?`, `근거 복사용 Markdown`, and answer evidence were visible; visually inspected the refreshed screenshot; `git diff --check` passed.

### Korean text encoding agent policy

- Added `AGENTS.md` guidance for reading Korean Markdown and UTF-8 text on Windows with explicit UTF-8 commands.
- Clarified that garbled PowerShell output should not be treated as file corruption until the file is re-read with explicit UTF-8.
- Added guardrails to avoid rewriting Korean prose just to fix terminal-output mojibake.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `Get-Content -Path AGENTS.md -Encoding UTF8` rendered Korean policy text correctly; `git diff --check` passed.

### Korean documentation wording cleanup

- Cleaned up awkward Korean wording in Markdown documentation where English terms had been translated too literally.
- Renamed the sample walkthrough wording to `샘플 프로젝트 검증 가이드`.
- Replaced reader-limiting wording with more general reader-focused phrasing where the document is not team-only.
- Replaced literal safety-sequence wording with `권장 실행 흐름` or direct explanations about avoiding excessive LLM/embedding work.
- Important files: `README.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/sample-target-repo-demo-design.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: searched Markdown for the awkward sample-guide and reader-limiting phrases; `git diff --check` passed.

### Application Dockerfile and deployment guide

- Added an application `Dockerfile` so the Streamlit app can be built and run with a repeatable Python 3.11 container image.
- Added `.dockerignore` to keep local virtualenvs, caches, secrets, generated screenshots, and database data out of the Docker build context.
- Expanded `docker-compose.yml` with a Streamlit `app` service, PostgreSQL healthcheck, mock LLM/embedding defaults, and container-to-host local LLM base URLs.
- Documented Docker deployment rationale, environment variables, migration startup behavior, and smoke-check commands in the setup/operations guide.
- Updated README Quick Start to distinguish local Python execution with `docker compose up -d postgres` from full Docker app execution with `docker compose up -d --build`.
- Updated the architecture document with the Docker deployment structure and startup migration flow.
- Important files: `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `README.md`, `docs/architecture.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `docker compose config` passed; `docker build -t ai-commit-advisor:local .` passed; `docker compose up -d --build app` passed; `Invoke-WebRequest http://localhost:8501/_stcore/health -UseBasicParsing` returned HTTP 200; `docker compose ps` showed `ai_commit_advisor_app` and `ai_commit_advisor_postgres` healthy; `docker exec ai_commit_advisor_postgres pg_isready -U ai_user -d ai_commit_advisor` reported accepting connections.

### Project Chat database history and citation export

- Added database-backed Project Chat sessions and messages so project conversations survive Streamlit session resets and can be reopened by project.
- Added Alembic migration `20260610_0004_add_project_chat_sessions` for `project_chat_sessions` and `project_chat_messages`.
- Added a Project Chat history service for session creation, message persistence, UI conversion, and copy-friendly Markdown citation export.
- Updated the Project Chat UI with project-level `대화 이력`, `새 대화`, persisted message rendering, and `근거 복사용 Markdown` for assistant answers.
- Updated README, feature guide, architecture, setup/operations, and AI technical overview documentation to explain persisted chat history, citation export, and traceability.
- Important files: `src/db/models.py`, `migrations/versions/20260610_0004_add_project_chat_sessions.py`, `src/rag/chat_history_service.py`, `src/ui/project_chat_page.py`, `tests/test_project_chat_history_service.py`, `README.md`, `docs/architecture.md`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/ai-technical-overview.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m py_compile src/db/models.py src/rag/chat_history_service.py src/ui/project_chat_page.py migrations/versions/20260610_0004_add_project_chat_sessions.py` passed; `.\\.venv\\Scripts\\python.exe -m compileall src tests` passed; `.\\.venv\\Scripts\\python.exe -m pytest -q` passed with 80 tests; `git diff --check` passed without whitespace errors; Browser verification against `http://localhost:8512` confirmed Project Chat history controls render.

### Feature rationale documentation policy

- Added `AGENTS.md` guidance that meaningful new features, workflows, AI behavior, operational behavior, and major UX changes require rationale documentation in an appropriate Markdown file.
- Clarified that rationale documentation should explain why the feature was introduced, the user or operational gap it addresses, expected effect, usage timing, tradeoffs, limitations, and related verification or failure-history lessons.
- Added feature rationale documentation to the pre-commit documentation checklist.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Project failure history documentation and agent policy

- Added `docs/failure-history.md` to record reusable project-wide failure root causes, fixes, prevention rules, remaining limits, and verification results.
- Documented the incremental source indexing CI failure as the first entry, where DB-backed tests were added without a pgvector PostgreSQL service in GitHub Actions.
- Added `AGENTS.md` policy requiring failure history updates when product, UX, AI behavior, RAG/embedding, data, schema, migration, sample data, documentation, test, dependency, workflow, environment, deployment, or operational mistakes reveal reusable learning.
- Linked the failure history document from the README documentation hub.
- Important files: `docs/failure-history.md`, `AGENTS.md`, `README.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed; README documentation links for the new file passed local path checks.

## 2026-06-09

### CI database service for incremental source indexing tests

- Added a pgvector PostgreSQL service to the GitHub Actions CI workflow so database-backed source indexing tests can run in CI.
- Set CI `DATABASE_URL`, `PGVECTOR_DIMENSION`, `LLM_PROVIDER=mock`, and `EMBEDDING_PROVIDER=mock` explicitly to match the test environment assumptions.
- Important files: `.github/workflows/ci.yml`, `AI_CHANGELOG.md`.
- Verification: `.\\.venv\\Scripts\\python.exe -m compileall src tests` passed; `.\\.venv\\Scripts\\python.exe -m pytest -q` passed with 78 tests.

### RAG and Project Chat rationale documentation

- Added feature guide rationale for why Project Chat uses verified current `source_file` chunks and standard terminology expansion instead of answering from stale chunks or commit diffs.
- Important files: `docs/feature-guide.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Incremental source indexing and embedding cost control

- Added manual incremental source indexing for `source_file` chunks so RAG and Project Chat can refresh only Git Sync changed files instead of scanning the whole repository during normal work.
- Added changed-file handling for added, modified, copied, deleted, and renamed files. Deleted and replaced source chunks now remove related vectors so stale file evidence does not remain searchable.
- Kept embedding generation explicit: incremental indexing and Project Chat source refresh leave new chunks as `embedding_status=pending`; users generate missing vectors from `RAG 검색 > Embedding` with a bounded limit.
- Added current embedding-model missing vector count to source index status and surfaced it in RAG and Project Chat.
- Added RAG and Project Chat buttons for `최근 Git sync 변경 파일만 인덱싱`, while keeping full `현재 소스 다시 인덱싱` as the recovery/initial-build action.
- Expanded Korean operations and AI technical documentation so teammates can distinguish Git Sync, incremental indexing, full re-indexing, and embedding generation from documentation alone.
- Important files: `src/rag/source_index_service.py`, `src/rag/chunker.py`, `src/ui/rag_page.py`, `src/ui/project_chat_page.py`, `tests/test_incremental_source_index_service.py`, `docs/setup-and-operations.md`, `docs/ai-technical-overview.md`, `docs/source-indexing-and-embedding-plan.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.\.venv\Scripts\python.exe -m compileall src tests` passed; `.\.venv\Scripts\python.exe -m pytest -q` passed with 78 tests; Browser verification against `http://localhost:8511` confirmed the new incremental indexing controls render on RAG and Project Chat.

### Agent documentation rationale guidance

- Added AGENTS guidance that feature, architecture, workflow, and AI behavior documentation should capture the user problem, operational gap, design rationale, tradeoffs, and remaining limitations, not only implementation details.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Korean-first user documentation cleanup

- Reworked user-facing Markdown documentation so explanatory prose is Korean-first, while preserving natural English headings, code identifiers, commands, environment variables, API names, and product/menu names where appropriate.
- Translated English-heavy documentation for source indexing, sample target repo design, rich sample demo walkthrough, DB migrations, and AI technical overview.
- Aligned README documentation links, screenshot gallery labels, and architecture/menu wording with the current Korean sidebar structure.
- Added an agent instruction that user-facing documentation should use Korean for explanatory prose by default without forcing familiar English documentation labels into Korean.
- Kept internal agent/task-management documents such as `AGENTS.md`, `ROADMAP.md`, and historical `AI_CHANGELOG.md` entries out of the translation scope except for the new roadmap/changelog bookkeeping.
- Important files: `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`, `docs/db-migrations.md`, `docs/feature-guide.md`, `docs/rich-sample-demo-walkthrough.md`, `docs/sample-target-repo-demo-design.md`, `docs/application-preview.md`, `docs/setup-and-operations.md`, `docs/source-indexing-and-embedding-plan.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed; project Markdown link sanity check passed.

### Artifact management sidebar grouping

- Added a `산출물 관리` sidebar group for developer list, program list, development plan, and standard terminology management screens.
- Renamed the Git-author developer page menu label to `개발자 현황` and shortened artifact page labels so upload/direct-management screens are easier to find.
- Updated the feature guide and screenshot gallery labels to match the new sidebar grouping.
- Refreshed the README and screenshot gallery Home images so the sidebar shows the new artifact management grouping.
- Important files: `app.py`, `docs/feature-guide.md`, `docs/application-preview.md`, `docs/images/ai-commit-advisor-home.png`, `docs/images/features/home.png`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `.venv\Scripts\python.exe -m py_compile app.py`, `.venv\Scripts\python.exe scripts\verify_home_ui.py --url http://localhost:8510 --screenshot docs\images\features\home.png`, `git diff --check`, and in-app Browser verification against `http://localhost:8510` passed.

### Project Chat history roadmap status correction

- Corrected the `Project Chat Answer Quality And History Persistence` roadmap detail status from `Done` to `In Progress` because database chat persistence, project-level history, and citation export remain incomplete.
- Important files: `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Source indexing and embedding plan

- Added a handoff design document for incremental source indexing, embedding cost control, cloud embedding operation, and Project Chat evidence scope.
- Added a roadmap task for incremental source indexing and embedding cost control so future implementation has a tracked plan.
- Linked the new design document from the README documentation hub for teammate handoff.
- Important files: `docs/source-indexing-and-embedding-plan.md`, `README.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Project Chat reset button alignment

- Adjusted the Project Chat section header column ratio so the reset action sits farther to the right as a section-level action.
- Important files: `src/ui/project_chat_page.py`, `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: `py_compile src/ui/project_chat_page.py` and `git diff --check` passed.

### Project Chat reset button placement

- Moved the Project Chat reset action from the search setting controls to the chat section header.
- Kept the reset button available in the chat header so the first answered turn does not render with a disabled-looking action.
- Important files: `src/ui/project_chat_page.py`, `AI_CHANGELOG.md`.
- Verification: `py_compile src/ui/project_chat_page.py` and `git diff --check` passed.

### Project Chat screenshot top-state refresh

- Refreshed the Project Chat screenshot so it shows the selected sample project, source index status, chat controls, Korean question, answer, and source citations in one view.
- Important files: `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected the refreshed screenshot; `git diff --check` passed.

### Standard terminology documentation and screenshots

- Updated README, Feature Guide, and AI technical overview to explain standard terminology upload and deterministic Korean query expansion.
- Added the standard terminology page to the screenshot gallery.
- Important files: `README.md`, `docs/feature-guide.md`, `docs/ai-technical-overview.md`, `docs/application-preview.md`, `docs/images/features/standard-terms.png`, `docs/images/features/project-chat.png`, `AI_CHANGELOG.md`.
- Verification: refreshed screenshots through the local Streamlit app; `git diff --check` passed.

### Project Chat answer formatting and evidence context

- Strengthened the Project Chat prompt so normal answers should be Korean Markdown, not JSON/code-block wrappers, and line ranges must be copied from retrieved metadata.
- Added local LLM response cleanup for common JSON wrapper responses such as fenced `{"response": "..."}` payloads.
- Added citation post-processing so answers that omit file line ranges append verified source metadata citations.
- Added Project Chat evidence context for matched standard terms and expanded queries so Korean query expansion is explainable during verification.
- Important files: `src/rag/chat_service.py`, `src/ui/project_chat_page.py`, `tests/test_project_chat_answer_format.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `pytest tests/test_project_chat_answer_format.py tests/test_project_chat_service.py -q` and `git diff --check` passed.

### Glossary-based Korean query expansion

- Added deterministic Project Chat query expansion using uploaded project standard terms and standard words.
- Added multi-query retrieval that merges results by chunk id and prefers verified source files under `src/main` or `src/test` for Project Chat evidence.
- Added focused query expansion tests for Korean payment amount questions expanding toward payment/code identifiers and `amount <= 0` search hints.
- Important files: `src/rag/query_expander.py`, `src/rag/retriever.py`, `src/rag/chat_service.py`, `tests/test_query_expander.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `pytest tests/test_query_expander.py tests/test_project_chat_service.py -q` and `git diff --check` passed.

### Standard terminology upload UI

- Added a Streamlit `표준용어/표준단어` page under data collection for project-level glossary upload and lookup.
- Added Excel template download, column guide, upload preview, validation summary, save action, and current glossary search/table display.
- Important files: `app.py`, `src/ui/standard_terms_page.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `py_compile app.py src/ui/standard_terms_page.py` and `git diff --check` passed.

### Standard terminology schema and service

- Added the `standard_terms` database model and Alembic migration for project-level SI standard terminology and standard words.
- Added a standard term service for Excel template generation, upload parsing, validation, save/update behavior, search, and derived keyword generation from English terms and abbreviations.
- Added focused tests for derived camelCase/PascalCase/snake_case/upper-snake keywords, required columns, duplicate detection, and row normalization.
- Important files: `src/db/models.py`, `migrations/versions/20260609_0003_add_standard_terms.py`, `src/services/standard_term_service.py`, `tests/test_standard_term_service.py`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `pytest tests/test_standard_term_service.py -q` and `git diff --check` passed.

### Sample standard terminology artifact plan

- Added sample target repository terminology rows for SI-style standard terms and standard words, including Korean term, English term, abbreviation, and description.
- Updated the sample target generator to create `advisor_uploads/sample_standard_terms.xlsx` alongside the existing developer, program, and development-plan upload files.
- Documented the standard terminology demo dataset and expected Korean Project Chat expansion scenario in the sample target repository design.
- Important files: `scripts/create_sample_target_repo.py`, `tests/test_sample_data_generation.py`, `docs/sample-target-repo-demo-design.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Project Chat glossary and Korean query expansion roadmap

- Added roadmap tasks for project standard terminology/standard word Excel upload, deterministic Korean query expansion, and Project Chat answer formatting/citation accuracy.
- Captured the agreed first-pass scope: teams enter Korean term, English term, and abbreviation while the app derives camelCase, PascalCase, snake_case, upper snake, token, and compact search variants.
- Documented that the initial query expansion should use uploaded terminology deterministically before adding any optional LLM query rewrite.
- Important files: `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### local LLM env 예시와 Project Chat 재현 절차

- Added `.env.local-llm.example` so teammates can start from a ready local_openai configuration for LM Studio chat and embedding models.
- Kept `.env.example` as the lightweight mock default, and updated README Quick Start to explain when to copy each env file.
- Documented that mock vectors are not reused by local_openai embedding search, so RAG Search and Project Chat require regenerating embeddings after provider/model changes.
- Important files: `.env.local-llm.example`, `README.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: markdown/link sanity checks and `git diff --check` passed.

### README 문서 허브 개편

- README를 짧은 진입 문서로 재구성하고, 상세 스크린샷/기능 설명/설치 운영 가이드를 별도 문서로 분리했습니다.
- GitHub에서 동작하는 상대 링크로 README의 Documentation 섹션을 구성해 필요한 문서를 바로 찾을 수 있게 했습니다.
- 기능별 화면 캡처는 `docs/application-preview.md`, 기능 흐름 설명은 `docs/feature-guide.md`, 설치/LLM/RAG 운영 기준은 `docs/setup-and-operations.md`로 이동했습니다.
- Important files: `README.md`, `docs/application-preview.md`, `docs/feature-guide.md`, `docs/setup-and-operations.md`, `ROADMAP.md`, `AI_CHANGELOG.md`.
- Verification: markdown/link sanity checks and `git diff --check` passed.

### README feature screenshot coverage refresh

- Refreshed README feature screenshots for Project, Git Sync, Sample Data, and RAG Search so they show realistic sample project state, execution results, generated data previews, and RAG retrieval results.
- Added sequential validation screenshots for Developer Upload and Development Plan Upload, and added a Project Chat screenshot showing a question, answer, and verified source evidence summary.
- Important files: `README.md`, `docs/images/features/project.png`, `docs/images/features/git-sync.png`, `docs/images/features/sample-data.png`, `docs/images/features/rag-search.png`, `docs/images/features/project-chat.png`, `docs/images/features/developer-upload-validation.png`, `docs/images/features/development-plan-upload-validation.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected refreshed screenshots; captured RAG and Project Chat in mock mode to match the stored sample vectors; `git diff --check` passed.

### Project Chat source evidence expander fix

- Fixed Project Chat source evidence rendering so evidence details no longer create nested Streamlit expanders, which caused `StreamlitAPIException` when an answer had verified sources.
- Kept the evidence summary expander and rendered individual source chunks as labeled detail blocks inside it.
- Important files: `src/ui/project_chat_page.py`, `AI_CHANGELOG.md`.
- Verification: `.venv\Scripts\python.exe -m py_compile src\ui\project_chat_page.py` passed; `git diff --check` passed.

### README screenshot guidance

- Added `AGENTS.md` guidance for README screenshots to prioritize meaningful workflow states and feature value over empty/default/pre-execution screens.
- Documented that multi-step workflows can be split into sequential screenshots with short labels when one image cannot clearly explain the flow.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### Program upload and code review walkthrough screenshots

- Re-captured the README Program Upload screenshots so the example shows the sample project's current program table and the Excel upload validation result instead of an empty/default project state.
- Split the README AI Code Review example into target selection, review result summary, and review detail screenshots so the actual review output, bug finding, refactoring suggestion, and review history are visible.
- Important files: `README.md`, `docs/images/features/program-upload.png`, `docs/images/features/program-upload-validation.png`, `docs/images/features/ai-code-review.png`, `docs/images/features/ai-code-review-result.png`, `docs/images/features/ai-code-review-detail.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected the refreshed screenshots and confirmed README references the new assets; `git diff --check` passed.

### Commit Impact walkthrough screenshots

- Split the README Commit Impact example into three sequential screenshots so the flow shows commit selection, impact summary, and detailed affected program/developer analysis.
- Re-captured the selected high-impact sample commit screen and added `commit-impact-summary.png` and `commit-impact-detail.png`.
- Important files: `README.md`, `docs/images/features/commit-impact.png`, `docs/images/features/commit-impact-summary.png`, `docs/images/features/commit-impact-detail.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected all three screenshots and confirmed the README references the new assets; `git diff --check` passed.

### Commit Impact README screenshot refresh

- Refreshed the README Commit Impact screenshot so it shows the selected high-impact sample commit, impact metrics, affected program analysis, and affected developer analysis instead of only the commit selection area.
- Kept README text unchanged; only the screenshot asset was updated.
- Important files: `docs/images/features/commit-impact.png`, `AI_CHANGELOG.md`.
- Verification: visually inspected the refreshed screenshot and confirmed it shows `HIGH` impact with affected program/developer analysis; `git diff --check` passed.

### Agent commit boundary guidance

- Added `AGENTS.md` guidance to keep materially different work types in separate commits when practical.
- Clarified that real code bugs found during verification or documentation work should be committed separately from screenshots, docs, or bookkeeping refreshes when practical.
- Important files: `AGENTS.md`, `AI_CHANGELOG.md`.
- Verification: `git diff --check` passed.

### 샘플 프로젝트 검증과 화면 캡처 갱신

- 앱 DB에 검증 전용 프로젝트 `AAA Sample Shop Rich Demo`를 구성하고 `C:\dev\ai-advisor-sample-shop`의 8개 프로그램/30개 커밋 샘플 repo와 `advisor_uploads` Excel 3종을 반영했습니다.
- mock LLM/embedding 기반으로 Git Sync, 프로그램/개발계획 적재, Mapping fallback, Risk Analysis, AI Progress, Commit Impact, RAG source indexing, Project Chat, AI Code Review 흐름을 검증했습니다.
- 검증 중 Spring MVC 샘플의 현재 소스 근거가 Project Chat에 잡히도록 RAG source_file 인덱싱 대상에 `.java`, `.jsp`를 추가하고 focused test를 보강했습니다.
- `docs/ai-technical-overview.md`에 current source indexing이 Java/JSP 등 샘플 프로젝트의 주요 텍스트/코드 파일을 포함한다는 설명을 추가했습니다.
- `docs/rich-sample-demo-walkthrough.md`와 `README.md`에 검증 전용 프로젝트명, mock 모드 Mapping 검증 주의점, Java/JSP source indexing 확인 기준을 보강했습니다.
- README 대표 이미지와 기능별 화면 캡처 전체를 새 샘플 데이터 기준으로 갱신했습니다.
- 검증 결과: 프로그램 8건, 커밋 30건, 관련 매핑 25건, unresolved risk 13건, source_file chunk/vector 70건, Project Chat verified source 8건, Code Review 1건 저장 확인.
- 검증: `.venv\Scripts\python.exe -m pytest tests\test_source_file_rag.py -q` 통과(`4 passed`), `.venv\Scripts\python.exe -m py_compile src\rag\chunker.py` 통과, Playwright로 README 기능별 화면 캡처 18종 갱신, `git diff --check` 통과.

### 샘플 프로젝트 검증 가이드 추가

- 8개 프로그램/30개 커밋 샘플 repo를 검증할 때 LLM/embedding 작업이 과도하게 늘어나지 않도록 `docs/rich-sample-demo-walkthrough.md`를 추가했습니다.
- 가이드에는 commit-based Mapping 우선 사용, 선택 커밋 1개 선검증, 후보 수 제한, RAG/Project Chat embedding 소량 실행, 추천 Code Review 대상 커밋, 예상 Risk Analysis 신호를 정리했습니다.
- `README.md`의 샘플 데이터 생성 섹션에서 전체 데모 검증이나 화면 캡처 갱신 전 해당 가이드를 먼저 확인하도록 안내했습니다.
- `ROADMAP.md`의 `Rich sample demo walkthrough and screenshots` 체크리스트에 권장 실행 흐름 문서화 항목을 추가했습니다.
- 검증: 문서 변경 범위 확인 및 `git diff --check` 통과.

### 샘플 프로젝트 검증과 스크린샷 작업 로드맵 등록

- 확장된 8개 프로그램/30개 커밋 샘플 데이터가 실제 앱 화면에서 잘 동작하는지 검증하고 README walkthrough 및 기능별 스크린샷을 맞추는 작업을 `ROADMAP.md`에 추가했습니다.
- Docker/deployment 작업보다 샘플 프로젝트 검증과 문서/스크린샷 정합성 작업을 먼저 볼 수 있도록 `P2 | Docs | Rich sample demo walkthrough and screenshots`를 `Planned`로 등록했습니다.
- 검증: 문서 변경 범위 확인 및 `git diff --check` 통과.

### README Home 화면 캡처 갱신

- README 대표 Home 이미지와 기능별 Home 캡처를 현재 Home 화면 문구 기준으로 갱신했습니다.
- 갱신한 이미지: `docs/images/ai-commit-advisor-home.png`, `docs/images/features/home.png`.
- 검증: 실행 중인 Streamlit 앱(`http://localhost:8501`) 기준으로 `.venv\Scripts\python.exe scripts\verify_home_ui.py --screenshot docs\images\features\home.png` 통과, 대표 이미지는 동일 캡처로 동기화, 이미지 육안 확인 통과.

### 확장 샘플 대상 repo 구현

- `scripts/create_sample_target_repo.py`의 샘플 대상 repo 생성 흐름을 확장해 8개 프로그램, 30개 Git commit, 6명의 가상 개발자 author를 생성하도록 했습니다.
- 주문, 재고, 결제, 매출, 대시보드, 쿠폰, 정산 계획 프로그램을 포함하고, 기능 추가/버그 유발/버그 수정/테스트 보강/리팩터링/문서 변경/교차 모듈 영향/미완료 기능 시나리오를 커밋 히스토리에 반영했습니다.
- Risk Analysis 데모를 위해 쿠폰 프로그램은 지연 80% 진행, 정산 내보내기 프로그램은 담당자 없음/지연/관련 커밋 없음 상태가 되도록 개발계획 override를 추가했습니다.
- AI Code Review 데모용 결제 0원 승인 위험 커밋과 대시보드 집계 over-count 위험 커밋, RAG/Project Chat용 업무 규칙 문서와 데모 가이드를 추가했습니다.
- `sample_data` Excel 3종을 새 샘플 repo 출력 기준으로 갱신했습니다.
- `README.md`와 `docs/sample-target-repo-demo-design.md`를 8개 프로그램/30개 커밋 기준으로 업데이트하고, 전체 데모에는 `advisor_uploads` Excel을 사용해야 리스크 계획 override가 포함된다는 안내를 추가했습니다.
- focused tests를 추가해 샘플 커밋 수, 리스크 데모 프로그램, 계획 override를 검증하도록 했습니다.
- 검증: `.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\generate_sample_development_data.py scripts\create_sample_target_repo.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`64 passed`), `git diff --check` 통과.

### 샘플 대상 repo 데모 시나리오 설계 문서 추가

- AI Commit Advisor의 전체 기능을 소개할 수 있도록 샘플 대상 repo의 목표 규모, 커밋 시나리오, 기능별 데모 신호를 정리한 `docs/sample-target-repo-demo-design.md`를 추가했습니다.
- 현재 샘플 repo의 장점과 한계를 정리하고, 권장 커밋 수를 25~40개, 우선 목표를 약 30개로 정의했습니다.
- Git Sync, Mapping, Program Detail, Commit Impact, Risk Analysis, RAG, Project Chat, AI Code Review, AI Progress별로 샘플 데이터가 보여줘야 할 조건을 문서화했습니다.
- `AGENTS.md`에 샘플 대상 repo, 샘플 커밋 히스토리, 샘플 데이터 생성, 데모 시나리오를 바꿀 때 설계 문서를 먼저 확인하라는 규칙을 추가했습니다.
- `AGENTS.md`에 커밋/푸시 전 변경 성격별로 관련 Markdown 문서 갱신 필요성을 확인하는 pre-commit documentation check를 추가했습니다.
- `ROADMAP.md`에 `Rich demo target repository scenario design` 작업을 등록했습니다.
- `README.md`의 샘플 데이터 생성 섹션에 현재 샘플 repo가 기본 기능 확인용 최소 데이터셋이며, 확장 시 설계 문서를 기준으로 한다는 안내를 추가했습니다.
- 검증: 문서 변경 범위 확인 및 `git diff --check` 통과.

### 가상 샘플 대상 프로젝트 생성 스크립트 추가

- AI Commit Advisor 앱 repo와 분리된 sibling Git repo `C:\dev\ai-advisor-sample-shop`를 생성하는 `scripts/create_sample_target_repo.py`를 추가했습니다.
- 생성 repo에는 Spring MVC Controller, Service, MyBatis Mapper interface/XML, JSP 화면으로 구성한 주문, 재고, 결제, 매출, 대시보드 예제 소스와 9개 Git commit, 6명의 한국인 가상 개발자 author, `샘플_프로그램목록.csv`, 업로드용 Excel 3종이 포함됩니다.
- 개발자 산출물의 role/skills는 업무 단위 개발 방식에 맞게 `PM`, `PL`, `개발자`, `QA`로 고정 프로필을 적용합니다.
- 샘플 데이터 생성기가 Spring/MyBatis 경로와 Python식 `controllers/services/repositories` 경로를 모두 더 자연스럽게 분류하도록 보완하고 focused tests를 추가했습니다.
- `샘플 데이터 생성` 화면의 기본 Git 경로를 `C:\dev\ai-advisor-sample-shop`로 바꾸고, README에 샘플 repo 생성/재생성/업로드 사용법을 추가했습니다.
- 검증: `.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\generate_sample_development_data.py scripts\create_sample_target_repo.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`61 passed`).

### Sidebar 메뉴 위치 흔들림 보정

- Sidebar 메뉴에서 선택 항목과 일반 버튼의 높이, margin, box sizing, 왼쪽 border 폭을 동일하게 맞춰 페이지 전환 시 메뉴 위치가 흔들리지 않도록 했습니다.
- 일반 메뉴 버튼에도 투명한 왼쪽 border를 적용해 선택 상태의 파란 border와 같은 공간을 항상 확보하도록 했습니다.
- `scripts/verify_home_ui.py`에 메뉴 클릭 전후 `Mapping` 항목의 위치와 폭이 안정적인지 확인하는 Playwright 검증을 추가했습니다.
- 검증: `.venv\Scripts\python.exe scripts\verify_home_ui.py` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\verify_home_ui.py` 통과.

### Home UI 검증 스크립트 추가

- Node Playwright가 없는 환경에서도 Home 화면을 검증할 수 있도록 Python Playwright 기반 `scripts/verify_home_ui.py`를 추가했습니다.
- 검증 스크립트는 Home의 짧아진 핵심 문구가 표시되는지, 제거한 설명투 문구가 남아 있지 않은지 확인하고 `.tmp/home-ui-check.png` 캡처를 생성합니다.
- `requirements.txt`에 `playwright==1.60.0`을 명시하고, `.tmp/`를 git 추적에서 제외했습니다.
- `README.md`의 로컬 검증 명령에 Home UI 검증 절차를 추가했습니다.
- 검증: `.venv\Scripts\python.exe scripts\verify_home_ui.py` 통과, `.venv\Scripts\python.exe -m compileall src app.py scripts\verify_home_ui.py` 통과.

### Home 문구 톤 정리

- Home 상단 설명을 짧은 상태 요약 문구로 줄였습니다.
- 분석 파이프라인 표의 긴 설명 컬럼을 간결한 `메모` 컬럼으로 바꾸고, 항목명을 짧게 정리했습니다.
- 다음 권장 작업 문장을 실행 항목 중심의 짧은 문구로 바꿨습니다.
- `src/ui/home_page.py`, `ROADMAP.md`를 수정했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과.

### README 화면 캡처 갱신

- `README.md`의 기능별 화면 캡처 안내 문구를 현재 그룹형 사이드바 메뉴 기준으로 정리했습니다.
- Home 대표 이미지와 기능별 화면 캡처 전체를 현재 UI 기준으로 갱신했습니다.
- 갱신한 이미지: `docs/images/ai-commit-advisor-home.png`, `docs/images/features/*.png`.
- 검증: Streamlit 앱을 `http://localhost:8501`에서 실행해 응답 `200`을 확인하고, Playwright Chromium으로 README 참조 화면 전체를 캡처했습니다. 문서와 이미지 변경만 수행해 pytest는 생략했습니다.

## 2026-06-08

### Sidebar 메뉴 UX 개선

- 사이드바의 2단 `radio` 메뉴를 제거하고, 업무 영역별 그룹 제목과 메뉴 버튼을 사용하는 내비게이션으로 변경했습니다.
- 현재 선택된 화면은 좌측 강조선과 배경으로 표시하고, 현재 위치를 사이드바 상단에 별도로 노출했습니다.
- 기존 페이지 그룹과 화면 렌더러는 유지해 메뉴 구조와 분석 기능 동작은 바꾸지 않았습니다.
- `README.md`와 `ROADMAP.md`에 사이드바 메뉴 UX 개선 내용을 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`53 passed`).

### LLM/Embedding 배치 안전장치와 예상시간 표시

- RAG embedding 실행 전에 남은 chunk 수, 이번 실행 최대 처리 수, 예상 소요 시간을 표시하도록 했습니다.
- source_file 재인덱싱 후 embedding을 함께 생성하는 경우에도 예상 소요 시간을 표시하도록 했습니다.
- 로컬 LM Studio/embedding 서버 과부하를 줄이기 위해 RAG embedding 기본 배치 수를 500건에서 50건으로 낮췄습니다.
- 예상시간 계산 helper와 focused tests를 추가했습니다.
- `README.md`, `docs/ai-technical-overview.md`, `ROADMAP.md`에 로컬 LLM/embedding 제한 실행 운영 방식을 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`53 passed`).

### Home 분석 관제 화면 개선

- Home 상단 설명을 개발계획, Git 변경 이력, AI 매핑 결과, 리스크를 통합해 보는 업무용 분석 콘솔 관점으로 정리했습니다.
- 프로젝트 등록, 프로그램 수, 개발자 수, Git 커밋 수집, 매핑 분석 완료 커밋, 구현상태 분석 결과, 미해결 리스크를 보여주는 분석 파이프라인 상태 섹션을 추가했습니다.
- 현재 데이터 상태에 따라 프로젝트 등록, 프로그램 등록, Git 동기화, Mapping 실행, 구현상태 분석, Risk Analysis 실행 같은 다음 권장 작업을 안내하도록 했습니다.
- 기존 전체 KPI, 상태별 프로그램 수, 계획 vs AI 진척도, 상위 리스크 프로그램 차트는 유지했습니다.
- `README.md`와 `ROADMAP.md`에 Home 분석 관제 화면 설명을 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`50 passed`).

### CI 테스트 워크플로우 추가

- GitHub Actions `CI` workflow를 추가해 push와 pull_request에서 Python 3.11 환경으로 기본 검증을 실행하도록 했습니다.
- CI 단계는 checkout, setup-python, `pip install -r requirements.txt`, `python -m compileall src app.py`, `python -m pytest -q` 순서로 구성했습니다.
- `README.md`에 CI와 동일한 로컬 검증 명령을 정리했습니다.
- `ROADMAP.md`의 P2 CI Test Workflow 상태와 체크리스트를 갱신했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`50 passed`).

### Project Chat 답변 품질과 근거 부족 처리 개선

- Project Chat에서 검증된 `source_file` 근거가 없으면 "현재 검증된 소스 근거만으로는 답변하기 어렵습니다", "추가 인덱싱 또는 검색어 조정이 필요합니다"를 반환하고 추측성 LLM 답변을 생성하지 않도록 했습니다.
- LLM 프롬프트를 보수적으로 정리해 검증된 현재 소스 근거에 없는 내용을 현재 코드 사실처럼 말하지 않고, commit/commit_file 근거는 과거 변경 이력으로만 다루도록 했습니다.
- 답변별 근거 표시를 현재 소스 근거와 이력/참고 근거로 분리하고, 파일 경로, line range, verification status, source type, 사용 근거 수를 확인할 수 있게 했습니다.
- stale/invalid `source_file` 제외, 근거 부족 응답, verified citation metadata 유지 focused tests를 추가했습니다.
- `ROADMAP.md`에서 Project Chat 품질 개선 완료 항목만 체크하고 chat history persistence는 미완료로 유지했습니다.
- `README.md`에 Project Chat의 근거 부족 안내 동작을 반영했습니다.
- `docs/ai-technical-overview.md`에 근거 부족 처리와 현재 소스/이력 근거 분리 설명을 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`50 passed`).

### source_file 인덱스 상태 표시 세부 보완

- RAG와 Project Chat의 source_file 인덱스 상태에 현재 HEAD와 다른 indexed HEAD chunk 수를 별도 표시했습니다.
- RAG 화면에서 source_file chunk에 저장된 indexed HEAD 종류를 확인할 수 있게 했습니다.
- 경고 문구를 "현재 Git HEAD와 인덱싱 시점이 다를 수 있습니다", "최신 코드 기준 답변을 위해 source_file 재인덱싱을 권장합니다"처럼 업무 사용자가 이해하기 쉬운 문장으로 정리했습니다.
- indexed HEAD mismatch count와 metadata 부족 invalid 처리 focused tests를 추가했습니다.
- `docs/ai-technical-overview.md`에 source index status 표시 항목을 최신 UI 기준으로 보강했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`46 passed`).

### Mapping 피드백 리뷰 큐 문서 정리

- `docs/architecture.md`에 `mapping_feedback_service.py` 역할, Mapping 피드백 리뷰 큐 흐름, 주요 서비스 목록을 최신 구현에 맞게 추가했습니다.
- `docs/ai-technical-overview.md`의 traceability 설명에 매핑 리뷰 큐가 피드백 미완료, 판단불가, 낮은 관련도, 비관련 판정, 근거 부족 후보를 우선 검토하도록 돕는다는 내용을 추가했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### Mapping 피드백 리뷰 큐와 품질 지표 추가

- Mapping 화면의 `매핑 피드백` 모드에 전체/피드백 완료/미완료/리뷰 필요/판단불가/낮은 관련도 KPI를 추가했습니다.
- 피드백 미완료, 판단불가, 낮은 관련도, 비관련 판정, 근거 부족 등 검토가 필요한 매핑을 찾는 리뷰 큐를 추가했습니다.
- 리뷰 큐 필터와 프로그램명, program_id, commit message, commit hash 기반 검색을 추가했습니다.
- 리뷰 큐에서 선택한 매핑을 기존 피드백 보정 form으로 바로 수정할 수 있게 했습니다.
- `mapping_feedback_service.py`에 리뷰 큐 조회와 품질 집계 helper를 추가하고 focused tests를 보강했습니다.
- `README.md`의 Mapping 설명에 매핑 피드백 리뷰 큐를 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`43 passed`).

### AI Progress 문서 설명 정리

- `README.md` 주요 기능 목록에 AI Progress가 계획 진척도, 매핑 기반 AI 진척도, 저장된 프로그램 단위 구현상태 분석 요약을 함께 비교한다는 설명을 추가했습니다.
- `docs/architecture.md`의 AI Progress 화면 역할, 처리 흐름, AI 진척도 계산 규칙, 주요 UI/서비스 설명을 최신 구현에 맞게 정리했습니다.
- 저장된 `program_implementation_status` 결과는 업무 검토용 요약 근거이며 AI 진척도/진척도 차이/리스크 조건 계산을 대체하지 않는다는 점을 문서에 명시했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### AI Progress 구현상태 분석 결과 표시

- AI Progress summary row에 저장된 프로그램 단위 구현상태 분석 상태, 업무용 라벨, 요약, 분석 일시, 근거 커밋 수를 포함했습니다.
- 프로그램별 비교 테이블에 `구현상태 분석`, `구현상태 요약`, `분석 일시`, `근거 커밋 수` 컬럼을 추가했습니다.
- 선택한 프로그램 상세 영역에 구현상태 분석 요약을 표시하고, 저장 결과가 없으면 `구현상태 분석 결과 없음`으로 안내하도록 했습니다.
- AI 진척도는 매핑 결과의 구현상태를 수치화한 값이고, 구현상태 분석은 프로그램 단위 요약 결과라는 안내 문구를 추가했습니다.
- 기존 AI 진척도, progress gap, risk reason 계산 방식은 변경하지 않았습니다.
- `README.md`, `docs/ai-technical-overview.md`에 AI Progress의 두 지표 구분 설명을 최소 반영했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`39 passed`).

### README 구현상태 분석 보수화 설명 정리

- `README.md`의 프로그램 단위 구현상태 분석 섹션에 커밋 수만으로 완료 판단을 하지 않는다는 원칙을 추가했습니다.
- `COMPLETED` 선택 기준, 테스트/예외처리/화면 연결/배포/검증의 한계, `incomplete_features`에 검증 필요 사항을 남기는 방식을 정리했습니다.
- LLM 응답 실패 또는 JSON 파싱 실패 시 fallback이 완료 단정보다 담당자 검증이 필요한 추정 결과를 우선한다는 설명을 보강했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### 구현상태 분석 프롬프트와 fallback 보수화

- `ProgramImplementationAnalyzer`의 LLM 프롬프트를 한국어 중심으로 정리하고, 프로그램 계획/설명/관련 커밋/변경 파일/기존 매핑 근거를 사용하되 커밋 수만으로 판단하지 않도록 명시했습니다.
- 커밋만으로 테스트 완료, 예외처리, 화면 연결, 배포/검증 완료를 확정할 수 없으며 불확실성은 `incomplete_features`에 남기도록 프롬프트를 보강했습니다.
- fallback 결과 문구를 한국어로 바꾸고, 완료 신호가 있어도 fallback에서는 담당자 검증이 필요한 `IN_PROGRESS`로 보수적으로 처리하도록 조정했습니다.
- 잘못된 status 값, 입력에 없는 evidence commit hash, mapping 없는 경우, 한국어 fallback 문구를 확인하는 focused tests를 추가했습니다.
- `docs/ai-technical-overview.md`에 구현상태 분석이 보수적 추정이며 업무 검증이 필요하다는 설명을 추가했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`36 passed`).

### README Program Detail 설명 정리

- `README.md`의 Program Detail 설명에서 저장된 분석 결과 조회와 `구현상태 재분석` 버튼의 동작을 구분해 정리했습니다.
- 프로그램 단위 구현상태 분석의 내부 상태값과 화면 표시 라벨을 표로 정리했습니다.
- 구현상태 결과 카드에서 확인할 수 있는 항목과 담당자 확인 필요 안내를 README에 더 명확히 반영했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### Program Detail 구현상태 분석 결과 표시 개선

- Program Detail의 저장된 프로그램 단위 구현상태 분석 결과를 업무 담당자가 이해하기 쉬운 한글 추정 라벨로 표시했습니다.
- 분석 결과 영역에 AI 분석 근거와 담당자 확인 필요성을 안내하는 문구를 추가했습니다.
- 구현상태, 분석 일시, 근거 커밋 수, 상태 요약, 완료/미완료 추정 기능, 주요 근거 커밋을 카드 형태로 정리했습니다.
- evidence_commits가 없거나 예상하지 못한 형태여도 화면이 깨지지 않도록 표시 전용 정규화 helper를 추가했습니다.
- 구현상태 재분석 실패 시 Program Detail 전체 화면이 죽지 않고 오류를 표시한 뒤 기존 저장 결과를 계속 보여주도록 예외 처리를 보강했습니다.
- `README.md`의 Program Detail/구현상태 분석 설명을 실제 화면 표현에 맞게 최소 수정했습니다.
- 검증: `.venv\Scripts\python.exe -m compileall src app.py` 통과, `.venv\Scripts\python.exe -m pytest -q` 통과(`31 passed`).

### source_file 재인덱싱 운영 기록 README 보강

- `README.md`에 source_file 재인덱싱과 embedding 생성을 분리해서 운영해야 하는 이유를 정리했습니다.
- LM Studio/local embedding 서버가 대량 chunk 처리 중 PC 자원을 오래 점유할 수 있으므로, embedding은 제한 수량으로 나눠 실행하도록 안내했습니다.
- 재인덱싱 또는 embedding 중 강제 종료되었을 때 PostgreSQL transaction rollback, 부분 완료 상태(`pending`, `failed`)의 의미, `orphan_vectors` 확인 방법을 문서화했습니다.
- 실제 점검에 사용한 `pg_isready`, source_file chunk/vector count, embedding_status 확인 SQL 예시를 README에 추가했습니다.
- 검증: 문서 변경만 수행해 테스트는 생략했습니다.

### source_file 재인덱싱 안전장치 보완

- `현재 소스 다시 인덱싱`이 기본으로 LM Studio/local embedding 서버를 대량 호출하지 않도록 변경했습니다.
- Project Chat의 재인덱싱은 chunk만 갱신하고, embedding 생성은 RAG 화면의 별도 선택 또는 Embedding 탭에서 제한 수량으로 실행하도록 분리했습니다.
- source_file refresh가 기존 chunk/vector를 먼저 전체 삭제하지 않고, 현재 HEAD 기준 chunk 생성 후 검증 불가 chunk/vector만 정리하도록 바꿨습니다.
- 갑작스러운 종료 시 기존 인덱스가 먼저 비워지는 위험을 줄이고, 삭제된 파일 근거는 성공적인 chunk 갱신 이후 제거하도록 했습니다.
- `README.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`의 재인덱싱 설명을 안전한 동작 기준으로 수정했습니다.
- 검증: `.venv\Scripts\python.exe -m pytest -q` 통과(`31 passed`), `.venv\Scripts\python.exe -m compileall app.py src` 통과.

### source_file 인덱스 상태 확인과 원클릭 재인덱싱

- RAG와 Project Chat 화면에 Current HEAD, Indexed HEAD, source_file chunk/vector 수, 현재 코드와 불일치/검증 불가 chunk 수를 표시했습니다.
- `src/rag/source_index_service.py`를 추가해 source_file 인덱스 상태 계산과 현재 HEAD 기준 재인덱싱을 공통 서비스로 분리했습니다.
- `현재 소스 다시 인덱싱` 버튼은 현재 Git HEAD 기준 source_file chunk를 갱신하고 검증되지 않는 오래된 chunk/vector를 정리합니다. embedding 자동 생성은 이후 안전장치 보완에서 기본 비활성화했습니다.
- 삭제된 파일이나 수정된 라인의 오래된 근거가 Project Chat 답변에 남지 않도록 재인덱싱 경로를 추가했습니다.
- `README.md`, `docs/architecture.md`, `docs/ai-technical-overview.md`에 소스 인덱스 상태 확인과 재인덱싱 흐름을 반영했습니다.
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
- `docs/architecture.md`의 아키텍처 다이어그램, RAG 흐름, 기능 목록, 제한사항, 주요 UI/서비스 목록을 최신 구현에 맞게 수정했습니다.

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

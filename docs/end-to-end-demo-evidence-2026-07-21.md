# Sample Shop 전체 시연 E2E 검증 증적

검증일: 2026-07-21

결과: PASS

검증 범위: 프로젝트 등록, Git 수집, 산출물 등록, Mapping, 구현상태, Risk, RAG/embedding, Knowledge Graph, Project Chat, AI Code Review, Dashboard, Docker 8501과 외부 접속 경로

## 1. 검증 목적

저장된 결과만 다시 여는 방식이 아니라 `C:\dev\ai-advisor-sample-shop`을 새 프로젝트에 연결해 수집부터 분석까지 전 과정을 다시 실행했습니다. 최종 결과는 기본 PostgreSQL DB `ai_commit_advisor`에 저장했고, 로컬 Python 8502에서 만든 결과가 Docker 8501과 Cloudflare quick tunnel에서도 동일하게 보이는지 확인했습니다.

이 문서는 화면별 확인 항목과 DB 수치를 함께 남긴 실행 증적입니다. 실제 시연에서는 저장된 결과를 기본으로 열고, 시간이 오래 걸리는 Mapping·embedding·새 LLM 호출은 질문을 받은 경우에만 선택적으로 실행합니다.

## 2. 최종 기준 환경

| 항목 | 검증 값 |
|---|---|
| 기준 PostgreSQL DB | `ai_commit_advisor` |
| 최종 실행 surface | Docker Streamlit `http://127.0.0.1:8501/?project_id=2716` |
| 외부 접속 검증 | Cloudflare quick tunnel, 동일 `project_id=2716` 확인 |
| 검증 프로젝트 | `Sample Shop 전체 시연 검증 2026-07-21` (`project_id=2716`) |
| Git 저장소 | `C:\dev\ai-advisor-sample-shop` |
| Git branch / HEAD | `main` / `221eb9ac9c83364f4450bdf4970196b51cb1f9e1` |
| LLM | `local_openai` / `qwen2.5-coder-7b-instruct`, context length 8192 |
| Embedding | `local_openai` / `text-embedding-nomic-embed-text-v1.5`, 768 dimensions |
| Host endpoint | `http://127.0.0.1:12345/v1` |
| Docker endpoint | `http://host.docker.internal:12345/v1` |
| Neo4j | enabled, connected, database `neo4j` |

Docker 8501은 `docker-compose.yml`의 실제 local provider 기본값을 사용합니다. 컨테이너 내부에서 `/v1/chat/completions` 응답과 768차원 `/v1/embeddings` 응답을 각각 확인했습니다. 검증용으로 열었던 로컬 8502는 종료했으며, 최종 상태에서는 8501만 수신합니다.

## 3. 최종 결과 요약

| 단계 | 결과 |
|---|---|
| 프로젝트 / 저장소 | 새 프로젝트 1개, 동일 Sample Shop 저장소 연결, working tree clean |
| Git 전체 수집 | commit 48건, 변경 파일/diff 106건, DB Sync HEAD 일치 |
| 개발자 / 산출물 | 프로젝트 개발자 6명, 프로그램 8건, 개발계획 8건, 표준용어 14건 |
| Mapping | commit 48/48 완료, 실패 0, 프로그램-commit 관계 39건 |
| Program Implementation Status | 8/8 생성, `IN_PROGRESS` 8건 |
| Risk Analysis | 32건: HIGH 8, MEDIUM 15, LOW 9 |
| RAG / embedding | 현재 소스 chunk 79건, vector 79건, 누락 0 |
| Knowledge Graph | node 213개, edge 591개, repo/graph HEAD 일치 |
| Project Chat | session 1개, 현재 source 6건, graph evidence 4건, `deterministic_repair` |
| AI Code Review | 최신 commit 검증 1건과 `2325182` 검증 1건, 후자는 bug finding 1건 |
| PL Briefing | 실제 local LLM 생성 1건 |
| AI 호출 | 52건, failed 0, fallback 1 |
| 운영 준비 | 11개 항목 모두 통과, 주의 0, 실패 0 |

Mapping 관계 39건은 분석한 commit 수가 아닙니다. 한 commit에 관계가 없거나 여러 프로그램 관계가 생길 수 있으므로 완료 여부는 commit 48건의 `mapping_analysis_status=completed`로 확인했습니다.

Project Chat의 fallback 1건은 모델 호출 실패나 mock 전환이 아닙니다. 실제 local LLM 응답이 검증된 직접 호출 순서를 정확히 지키지 않아, 현재 저장소의 메서드 단위 근거로 안전한 답변을 재구성한 `deterministic_repair`입니다. 화면에는 이 상태를 숨기지 않고 `fallback=True`, `repair=True`로 표시합니다.

## 4. 단계별 화면 증적

### 4.1 프로젝트 등록과 Git 수집

#### 01. 새 프로젝트 등록 전

![새 프로젝트 등록 전](images/usage-verification/end-to-end-demo-2026-07-21/01-project-registration-empty.png)

프로젝트명과 저장소 경로를 입력하기 전 상태입니다. 새 프로젝트에서 처음부터 시작했음을 보여줍니다.

#### 02. 프로젝트 등록 완료

![프로젝트 등록 완료](images/usage-verification/end-to-end-demo-2026-07-21/02-project-registered.png)

`Sample Shop 전체 시연 검증 2026-07-21`, 동일 샘플 저장소, `main` branch를 저장하고 project ID `2716`을 확인했습니다.

#### 03. Git 전체 수집 전

![Git 전체 수집 전](images/usage-verification/end-to-end-demo-2026-07-21/03-git-before-full-sync.png)

Repo HEAD는 존재하지만 DB Sync HEAD가 비어 있어 전체 수집이 필요한 상태입니다.

#### 04. Git 전체 수집 완료

![Git 전체 수집 완료](images/usage-verification/end-to-end-demo-2026-07-21/04-git-full-sync-complete.png)

commit 48건과 변경 파일 106건을 저장했습니다. Repo HEAD와 DB Sync HEAD가 `221eb9ac9c83`으로 일치하고 working tree가 깨끗합니다.

### 4.2 산출물 등록

#### 05. 개발자 Excel 검증

![개발자 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/05-developers-upload-validation.png)

업로드 파일에서 저장 가능한 개발자 6명과 오류 0건을 확인했습니다.

#### 06. 개발자 저장 완료

![개발자 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/06-developers-saved.png)

프로젝트 개발자 연결 6건이 저장됐습니다.

#### 07. 프로그램 Excel 검증

![프로그램 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/07-programs-upload-validation.png)

필수 컬럼을 매핑하고 프로그램 8건, 오류 0건을 확인했습니다.

#### 08. 프로그램 저장 완료

![프로그램 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/08-programs-saved.png)

Mapping, AI Progress, Risk Analysis가 사용할 업무 단위 8건을 저장했습니다.

#### 09. 개발계획 Excel 검증

![개발계획 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/09-development-plan-upload-validation.png)

프로그램과 개발자 ID를 모두 찾아 수정 대상 8건, 오류 0건으로 검증했습니다.

#### 10. 개발계획 저장 완료

![개발계획 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/10-development-plan-saved.png)

담당자, 계획일, 상태, 계획 진척도를 8개 프로그램에 반영했습니다.

#### 11. 표준용어 Excel 검증

![표준용어 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/11-standard-terms-upload-validation.png)

한글 업무 표현을 소스 식별자로 확장할 표준용어 14건, 오류 0건을 확인했습니다.

#### 12. 표준용어 저장 완료

![표준용어 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/12-standard-terms-saved.png)

표준용어 14건을 현재 프로젝트에 저장했습니다.

### 4.3 Mapping, 구현상태, Risk

#### 13. Mapping 실행 전

![Mapping 실행 전](images/usage-verification/end-to-end-demo-2026-07-21/13-mapping-before-analysis.png)

프로그램 8건, commit 48건, 미완료 48건인 시작 상태입니다.

#### 14. Mapping 완료

![Mapping 완료](images/usage-verification/end-to-end-demo-2026-07-21/14-mapping-complete.png)

실제 local LLM으로 commit 48/48을 분석했고 실패 0, 관계 39건을 저장했습니다.

#### 15. 프로그램 구현상태 분석

![프로그램 구현상태 분석](images/usage-verification/end-to-end-demo-2026-07-21/15-program-implementation-status.png)

8개 프로그램 모두 최신 관련 commit 묶음으로 구현상태가 생성됐습니다. 결과는 완료를 단정하지 않는 `IN_PROGRESS`입니다.

#### 16. Risk Analysis 실행 전

![Risk Analysis 실행 전](images/usage-verification/end-to-end-demo-2026-07-21/16-risk-before-analysis.png)

Risk Finding이 없는 초기 상태에서 규칙 기반 분석을 시작했습니다.

#### 17. Risk Analysis 완료

![Risk Analysis 완료](images/usage-verification/end-to-end-demo-2026-07-21/17-risk-analysis-complete.png)

HIGH 8, MEDIUM 15, LOW 9로 총 32건을 찾았습니다. 유형은 계획 종료 후 AI 진척 미완료 8, 계획 대비 차이 7, 최근 활동 없음 8, 담당자 없음 1, 예상 지연 8건입니다.

### 4.4 RAG와 현재 소스 검색

#### 18. RAG 인덱싱 전

![RAG 인덱싱 전](images/usage-verification/end-to-end-demo-2026-07-21/18-rag-before-indexing.png)

현재 소스 chunk와 vector가 비어 있는 시작 상태입니다.

#### 19. RAG 인덱싱 완료

![RAG 인덱싱 완료](images/usage-verification/end-to-end-demo-2026-07-21/19-rag-indexing-complete.png)

현재 source chunk 79건과 실제 embedding vector 79건을 만들었습니다. 누락은 0건입니다.

#### 20. RAG 검색 결과

![RAG 검색 결과](images/usage-verification/end-to-end-demo-2026-07-21/20-rag-search-results.png)

`PaymentService` 결제 금액 검증 검색에서 현재 파일의 관련 행이 verified source로 반환됐습니다.

### 4.5 Knowledge Graph

#### 21. Knowledge Graph 동기화 전

![Knowledge Graph 동기화 전](images/usage-verification/end-to-end-demo-2026-07-21/21-knowledge-graph-before-sync.png)

Neo4j 연결은 정상이지만 Graph HEAD가 비어 있어 전체 동기화가 필요한 상태입니다.

#### 22. Knowledge Graph 동기화 완료

![Knowledge Graph 동기화 완료](images/usage-verification/end-to-end-demo-2026-07-21/22-knowledge-graph-sync-complete.png)

node 213개와 edge 591개를 저장했고 Graph HEAD와 Repo HEAD가 일치합니다.

#### 23. Neo4j 노드와 엣지 분포

![Neo4j 노드와 엣지 분포](images/usage-verification/end-to-end-demo-2026-07-21/23-knowledge-graph-nodes-edges.png)

project, program, commit, file, class, domain 노드와 Mapping·파일 변경·class import 관계가 생성됐습니다.

### 4.6 Project Chat과 GraphRAG

#### 24. Project Chat 준비 완료

![Project Chat 준비 완료](images/usage-verification/end-to-end-demo-2026-07-21/24-project-chat-ready.png)

소스 79, 검색 준비 79/79, 코드 반영 최신, Knowledge Graph 최신을 확인했습니다.

#### 25. 검증된 Project Chat 답변

![검증된 Project Chat 답변](images/usage-verification/end-to-end-demo-2026-07-21/25-project-chat-answer.png)

`PaymentController.java`, `PaymentService.java`, `OrderStatusService.java`, `OrderStatusMapper.java`를 지정해 금액 조건과 `PAID` 전환 흐름을 질문했습니다. 답변은 직접 호출 다섯 단계를 합치지 않고 표시하며 `amount <= 0`, `amount > MAX_AUTHORIZATION_AMOUNT`의 `REJECTED` 결과와 정확한 파일·행을 함께 제시합니다. 한글은 `???`로 깨지지 않습니다.

#### 26. Project Chat GraphRAG 근거

![Project Chat GraphRAG 근거](images/usage-verification/end-to-end-demo-2026-07-21/26-project-chat-graph-evidence.png)

답변에 실제로 전달된 현재 source 6건과 graph evidence 4건을 확인했습니다. `deterministic_repair`와 `fallback=True`도 화면에 공개됩니다.

### 4.7 AI Code Review

#### 27. 리뷰 대상 commit 지정

![리뷰 대상 commit 지정](images/usage-verification/end-to-end-demo-2026-07-21/27-code-review-target.png)

설명 가능한 경계값 변경이 있는 `2325182`를 특정 commit으로 지정했습니다.

#### 28. AI Code Review 완료

![AI Code Review 완료](images/usage-verification/end-to-end-demo-2026-07-21/28-code-review-complete.png)

실제 local LLM이 `2325182`를 검토해 `PaymentService.java`의 0원 결제 허용 가능성을 보통 위험 bug finding 1건으로 저장했습니다. 최신 HEAD의 테스트 전용 commit도 별도로 검토했으며, 근거 없는 bug나 refactoring을 만들지 않았습니다.

### 4.8 종합 결과 화면

#### 29. Home 최종 상태

![Home 최종 상태](images/usage-verification/end-to-end-demo-2026-07-21/29-home-final-status.png)

프로그램 8, 완료 6, 진행중 2, 리스크 프로그램 8, commit 48을 한 화면에서 확인했습니다.

#### 30. AI Progress

![AI Progress](images/usage-verification/end-to-end-demo-2026-07-21/30-ai-progress.png)

계획 진척도 90.6%와 구현상태 기반 AI Progress 50.0%의 차이를 프로그램별 근거로 확인합니다.

#### 31. Dashboard 개요

![Dashboard 개요](images/usage-verification/end-to-end-demo-2026-07-21/31-dashboard-overview.png)

프로그램, commit, 계획/AI Progress, risk, 개발자 활동을 현재 프로젝트 기준으로 모아 보여줍니다.

#### 32. AI Resource Radar

![AI Resource Radar](images/usage-verification/end-to-end-demo-2026-07-21/32-dashboard-resource-radar.png)

먼저 확인할 프로그램과 점수 근거를 보여줍니다. 시간·공수 값은 확정 성과가 아니라 검토 우선순위용 추정치입니다.

#### 33. PL Briefing

![PL Briefing](images/usage-verification/end-to-end-demo-2026-07-21/33-dashboard-pl-briefing.png)

실제 local LLM이 Radar와 risk 근거로 요약, 확인 항목, 질문, 다음 action을 생성하고 저장했습니다.

#### 34. Git History 상세

![Git History 상세](images/usage-verification/end-to-end-demo-2026-07-21/34-git-history-detail.png)

commit 48건, 변경 파일 106건, 작성자별 이력과 저장 diff를 확인했습니다.

#### 35. Commit Impact

![Commit Impact](images/usage-verification/end-to-end-demo-2026-07-21/35-commit-impact.png)

선택 commit의 프로그램, 개발자, 파일 영향 범위를 Mapping과 Git 데이터로 추적합니다.

#### 36. AI 운영 현황

![AI 운영 현황](images/usage-verification/end-to-end-demo-2026-07-21/36-ai-operations-evidence.png)

LLM, embedding 768d, 최근 AI 호출, 검색 준비, Neo4j, Knowledge Graph 213/591, GraphRAG가 모두 통과합니다. 호출 요약은 total 52, failed 0, fallback 1입니다.

#### 37. 개발계획 대시보드

![개발계획 대시보드](images/usage-verification/end-to-end-demo-2026-07-21/37-development-plan-dashboard.png)

프로그램 8건 중 완료 6건, 전체 계획 대비 완료율 75.0%, 평균 계획 진척도 90.6%를 확인했습니다.

### 4.9 최종 실행 경로

#### 38. Docker 8501 Project Chat

![Docker 8501 Project Chat](images/usage-verification/end-to-end-demo-2026-07-21/38-docker-8501-project-chat.png)

Docker 8501에서 project ID `2716`, 저장 대화 `#429`, 검증된 한글 답변과 source/graph 수가 로컬 검증 결과와 같음을 확인했습니다.

#### 39. Cloudflare Home

![Cloudflare Home](images/usage-verification/end-to-end-demo-2026-07-21/39-cloudflare-home.png)

외부 quick tunnel에서 같은 project ID, 프로그램 8건, commit 48건, 준비 완료 상태를 확인했습니다.

#### 40. Cloudflare Project Chat

![Cloudflare Project Chat](images/usage-verification/end-to-end-demo-2026-07-21/40-cloudflare-project-chat.png)

외부 접속에서도 저장된 질문과 직접 호출 답변, provider, 검증 상태, 근거 수가 동일하게 표시됩니다. quick tunnel URL은 컨테이너를 다시 시작하면 바뀌므로 당일에는 새 URL을 다시 확인해야 합니다.

## 5. 데이터 보호와 정리

변경 전에 두 DB를 각각 PostgreSQL custom dump로 백업하고 임시 DB에 복원해 프로젝트 수를 조회했습니다.

| 백업 | 위치 | SHA-256 | 복구 확인 |
|---|---|---|---|
| 기준 DB | `C:\Users\chch\OneDrive\AI Commit Advisor Backups\database\20260721_183459\ai_commit_advisor_20260721_183459.dump` | `731FD3C7C016FF4F1DFFA3BB8F0076DDF4B0988C59315D294BEB34E58AED858C` | 프로젝트 7건 조회 |
| 격리 E2E DB | `C:\Users\chch\OneDrive\AI Commit Advisor Backups\database\20260721_183459\ai_commit_advisor_e2e_20260721_140322_20260721_183459.dump` | `DDB2D817F4DF9B5632382D50EF9E391E89005356B992EDAF60BBCD2B06632B94` | 프로젝트 1건 조회 |

기준 DB에서 중복 Sample Shop 프로젝트 ID `4`, `97`, `197`만 제거한 뒤 project `2716`을 새로 만들었습니다. 다른 프로젝트 ID `1`, `2`, `3`, `2461`은 유지했습니다. 최종 Docker·Cloudflare 검증 뒤 격리 DB `ai_commit_advisor_e2e_20260721_140322`를 삭제했으며, 위 dump로 복구할 수 있습니다.

샘플 Git 저장소는 commit 48건, HEAD `221eb9ac9c83364f4450bdf4970196b51cb1f9e1`, working tree clean 상태를 유지했습니다.

## 6. 관찰 사항과 남은 한계

- 현재 `git_commits.commit_hash`에는 전역 unique 제약이 남아 있어 같은 저장소를 같은 DB의 여러 프로젝트에 동시에 수집하면 commit 소유권이 이동할 수 있습니다. 그래서 같은 저장소의 중복 프로젝트를 유지하지 않고 project `2716` 하나만 기준으로 사용합니다.
- 과거 Project Chat의 `???`는 브라우저 글꼴 문제가 아니라 DB에 이미 깨진 문자열이 저장된 사례였습니다. 새 질문은 UTF-8로 정상 저장됐고, 호출 관계 검증을 통과하지 못한 모델 문장은 저장소 근거로 보정합니다.
- Project Chat의 메서드 근거 추출은 현재 Java 소스와 verified chunk 행 범위를 함께 확인하는 보수적 경로입니다. Java compiler 수준의 type resolution을 제공하지는 않습니다.
- local LLM 문장과 응답 시간은 재실행마다 달라질 수 있습니다. 직접 호출 순서, 조건식, 인용 범위는 후처리 검증 대상이며 답변 문체는 고정하지 않습니다.
- AI Progress, Risk, Resource Radar는 확인 순서를 정하는 보조 신호입니다. 실제 완료율, 일정 확정, 개인 성과 평가에 사용하지 않습니다.

## 7. 주요 검증 명령과 결과

```powershell
docker compose config --format json
docker compose up -d --build app
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8501/_stcore/health
docker exec ai_commit_advisor_app python -c "import requests; print(requests.get('http://host.docker.internal:12345/v1/models').status_code)"
.\.venv\Scripts\python.exe -m compileall -q src app.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_project_chat_service.py tests\test_neo4j_graph_service.py tests\test_project_chat_history_service.py tests\test_project_chat_page.py
```

확인 결과:

- Docker app: healthy, 8501 수신, 8502 미수신.
- Docker 실제 AI 연결: chat completion 성공, embedding dimension 768.
- 대상 테스트: `37 passed`.
- DB: Git 48/106, Mapping 48/48, 구현상태 8, Risk 32, source/vector 79/79, graph 213/591, AI 호출 52건.
- 화면 증적: PNG 40개, 보고서 link와 실제 파일 일치.

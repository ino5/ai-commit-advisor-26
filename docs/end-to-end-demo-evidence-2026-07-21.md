# Sample Shop 전체 시연 E2E 검증 증적

검증일: 2026-07-21
결과: PASS
검증 범위: 프로젝트 등록부터 Git 수집, 산출물 등록, Mapping, 구현상태, Risk, RAG/embedding, Knowledge Graph, Project Chat, AI Code Review, Dashboard와 운영 상태 확인까지

## 1. 검증 목적

저장된 결과를 다시 여는 수준이 아니라, 동일한 Sample Shop Git 저장소를 새 프로젝트에 연결해 처음부터 전체 흐름을 재현했습니다. 각 단계의 입력, 저장 결과, 다음 단계로 넘어갈 수 있는 조건을 화면과 DB 수치로 함께 확인했습니다.

기존 시연 프로젝트 197은 예비본으로 유지했습니다. 현재 데이터 모델은 commit_hash를 전역 유일값으로 관리하므로 같은 운영 DB에 새 프로젝트를 만들면 기존 프로젝트의 GitCommit 소유가 이동할 수 있습니다. 이를 막기 위해 Git 저장소는 그대로 사용하고 PostgreSQL DB와 Streamlit 인스턴스만 검증용으로 분리했습니다.

## 2. 검증 환경

| 항목 | 검증 값 |
|---|---|
| Runtime surface | Windows local .venv |
| Streamlit | 증적용 http://127.0.0.1:8502 |
| 검증용 PostgreSQL DB | ai_commit_advisor_e2e_20260721_140322 |
| 검증 프로젝트 | Sample Shop 전체 시연 검증 2026-07-21 |
| 검증 project ID | 202607210 |
| Git 저장소 | C:\dev\ai-advisor-sample-shop |
| Git branch / HEAD | main / 221eb9ac9c83364f4450bdf4970196b51cb1f9e1 |
| Git commit 수 | 48 |
| LLM provider / model | local_openai / qwen2.5-coder-7b-instruct |
| Embedding provider / model | local_openai / text-embedding-nomic-embed-text-v1.5 |
| Vector dimension | 768 |
| LLM/embedding endpoint | http://127.0.0.1:12345/v1 |
| Neo4j | enabled, connected, default database |

## 3. 최종 결과 요약

| 단계 | 결과 |
|---|---|
| 프로젝트 등록 | 1개, 동일 샘플 Git 저장소 연결 |
| Git 전체 수집 | commit 48건, 변경 파일/diff 106건, DB Sync HEAD 일치 |
| 개발자 | 프로젝트 연결 6명 |
| 프로그램 / 개발계획 | 프로그램 8건, 개발계획 반영 8건 |
| 표준용어/표준단어 | 14건 |
| Mapping | commit 48/48 완료, 실패 0, 관계 38건 |
| Program Implementation Status | 8/8 생성, 모두 IN_PROGRESS 추정 |
| Risk Analysis | 32건: HIGH 8, MEDIUM 15, LOW 9 |
| RAG / embedding | 현재 소스 chunk 79건, vector 79건, 누락 0 |
| Knowledge Graph | node 213개, edge 590개, repo/graph HEAD 일치 |
| Project Chat | session 1개, user/assistant 2개 메시지, source 11건, graph evidence 8건, fallback=False |
| AI Code Review | commit 2325182, 완료 1건, bug finding 1건, fallback=False |
| PL Briefing | 실제 local LLM 생성 1건, fallback=False |
| AI 호출 | 51건, 실패 0, fallback 0 |

Mapping 관계 38건은 분석한 commit 수가 아닙니다. 한 commit이 어떤 프로그램과도 관련 없으면 관계 행이 생기지 않고, 여러 프로그램과 관련되면 여러 행이 생깁니다. 완료 여부는 관계 수가 아니라 commit 48건의 mapping_analysis_status로 확인했습니다.

## 4. 단계별 화면 증적

### 4.1 프로젝트와 Git 수집

#### 01. 새 프로젝트 등록 전

![새 프로젝트 등록 전](images/usage-verification/end-to-end-demo-2026-07-21/01-project-registration-empty.png)

프로젝트명과 앱 서버 Git 저장소 경로를 입력하기 전의 빈 등록 화면입니다. 검증 DB에 기존 프로젝트가 없으므로 처음 사용하는 흐름과 같은 상태에서 시작했습니다.

#### 02. 프로젝트 등록 완료

![프로젝트 등록 완료](images/usage-verification/end-to-end-demo-2026-07-21/02-project-registered.png)

프로젝트명, 동일 샘플 저장소 경로, main branch, 검증 목적 설명을 저장했습니다. 저장 성공 메시지와 project ID 202607210을 확인했습니다.

#### 03. Git 전체 수집 전

![Git 전체 수집 전](images/usage-verification/end-to-end-demo-2026-07-21/03-git-before-full-sync.png)

Repo HEAD는 221eb9ac9c83이지만 DB Sync HEAD는 비어 있어 전체 수집이 필요한 상태입니다. branch main, working tree 깨끗함, 변경 파일 0건도 함께 확인했습니다.

#### 04. Git 전체 수집 완료

![Git 전체 수집 완료](images/usage-verification/end-to-end-demo-2026-07-21/04-git-full-sync-complete.png)

신규 commit 48건과 변경 파일 106건이 저장됐습니다. Repo HEAD, DB Sync HEAD, 최근 sync 대상이 모두 221eb9ac9c83으로 일치합니다.

### 4.2 산출물 등록

#### 05. 개발자 Excel 검증

![개발자 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/05-developers-upload-validation.png)

sample_developers.xlsx를 올린 뒤 신규 6명, 오류 0건, 저장 가능 6명으로 검증됐습니다. 저장 전 미리보기에서 개발자 ID, 이름, email, role, skills를 확인할 수 있습니다.

#### 06. 개발자 저장 완료

![개발자 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/06-developers-saved.png)

검증 통과 행 저장 결과를 확인했습니다. DB의 project_developers도 project ID 202607210 기준 6건입니다.

#### 07. 프로그램 Excel 검증

![프로그램 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/07-programs-upload-validation.png)

sample_programs.xlsx의 필수 컬럼을 자동 매핑했고 신규 8건, 오류 0건, 저장 가능 8건으로 확인했습니다.

#### 08. 프로그램 저장 완료

![프로그램 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/08-programs-saved.png)

프로그램 8건을 현재 프로젝트에 저장했습니다. 이 데이터가 이후 Mapping, AI Progress, Risk Analysis의 업무 단위가 됩니다.

#### 09. 개발계획 Excel 검증

![개발계획 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/09-development-plan-upload-validation.png)

sample_development_plan.xlsx가 기존 프로그램 8건과 개발자 ID를 모두 찾았고 수정 8건, 오류 0건으로 검증됐습니다.

#### 10. 개발계획 저장 완료

![개발계획 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/10-development-plan-saved.png)

8개 프로그램의 담당자, 계획일, 상태, 진행률을 반영했습니다. DB에서도 계획 시작일과 종료일이 있는 프로그램 8건을 확인했습니다.

#### 11. 표준용어 Excel 검증

![표준용어 Excel 검증](images/usage-verification/end-to-end-demo-2026-07-21/11-standard-terms-upload-validation.png)

sample_standard_terms.xlsx는 신규 14건, 오류 0건, 저장 가능 14건으로 검증됐습니다. 이 용어는 한글 질문을 코드 식별자와 연결하는 검색 확장에 사용됩니다.

#### 12. 표준용어 저장 완료

![표준용어 저장 완료](images/usage-verification/end-to-end-demo-2026-07-21/12-standard-terms-saved.png)

표준용어/표준단어 14건을 저장했습니다. 이후 RAG 검색과 Project Chat이 결제, 주문, 재고 같은 업무 표현을 소스 용어와 함께 검색할 수 있습니다.

### 4.3 Mapping, 구현상태, Risk

#### 13. Mapping 실행 전

![Mapping 실행 전](images/usage-verification/end-to-end-demo-2026-07-21/13-mapping-before-analysis.png)

프로그램 8건, Git commit 48건, 미완료 commit 48건인 초기 상태입니다. 기본 추천 방식인 commit 기준 분석과 local LLM 호출 조건을 확인했습니다.

#### 14. Mapping 완료

![Mapping 완료](images/usage-verification/end-to-end-demo-2026-07-21/14-mapping-complete.png)

48개 commit이 모두 완료됐고 미완료 0, 실패 0입니다. 실제 local LLM 호출 48건에서 fallback은 한 번도 사용되지 않았고 프로그램-commit 관계 38건이 저장됐습니다.

#### 15. 프로그램 구현상태 분석

![프로그램 구현상태 분석](images/usage-verification/end-to-end-demo-2026-07-21/15-program-implementation-status.png)

Program Detail에서 결제 승인 프로그램의 기본 정보, 관련 commit 5건, Mapping 참고 진척도 50%, 최신 구현상태 분석을 함께 확인했습니다. 구현상태는 완료를 단정하지 않고 진행중 추정과 근거를 보여줍니다.

#### 16. Risk Analysis 실행 전

![Risk Analysis 실행 전](images/usage-verification/end-to-end-demo-2026-07-21/16-risk-before-analysis.png)

저장된 risk finding이 없는 초기 상태입니다. 리스크 분석은 프로그램, 계획, Git 활동, 최신 구현상태를 규칙으로 비교하며 별도 LLM 호출 없이 계산됩니다.

#### 17. Risk Analysis 완료

![Risk Analysis 완료](images/usage-verification/end-to-end-demo-2026-07-21/17-risk-analysis-complete.png)

리스크 32건을 찾았습니다. 수준별로 HIGH 8, MEDIUM 15, LOW 9이며 유형은 계획 종료 후 AI 진척 미완료 8, 계획 대비 진척 차이 7, 최근 활동 없음 8, 담당자 없음 1, 예상 지연 8건입니다.

### 4.4 RAG와 현재 소스 검색

#### 18. RAG 인덱싱 전

![RAG 인덱싱 전](images/usage-verification/end-to-end-demo-2026-07-21/18-rag-before-indexing.png)

근거 chunk와 vector가 모두 0이고 코드 반영 상태를 확인해야 하는 초기 화면입니다. 처음 준비할 때는 전체 소스를 다시 읽고 embedding까지 이어서 실행합니다.

#### 19. RAG 인덱싱 완료

![RAG 인덱싱 완료](images/usage-verification/end-to-end-demo-2026-07-21/19-rag-indexing-complete.png)

현재 source_file chunk 79건과 vector 79건을 만들었습니다. 검색 준비는 79/79, 추가 준비 필요 0, 코드 반영 상태 최신입니다.

#### 20. RAG 검색 결과

![RAG 검색 결과](images/usage-verification/end-to-end-demo-2026-07-21/20-rag-search-results.png)

payment amount validation PaymentService 검색에서 PaymentService.java 29-37행이 1순위 verified source로 반환됐습니다. 검색 모델은 local_openai:text-embedding-nomic-embed-text-v1.5입니다.

### 4.5 Knowledge Graph

#### 21. Knowledge Graph 동기화 전

![Knowledge Graph 동기화 전](images/usage-verification/end-to-end-demo-2026-07-21/21-knowledge-graph-before-sync.png)

Neo4j 연결과 사용 설정은 정상이고 Graph HEAD가 비어 있어 전체 재동기화가 필요한 상태입니다. 예상 대상은 node 213개, edge 590개, class 58개, domain 21개입니다.

#### 22. Knowledge Graph 동기화 완료

![Knowledge Graph 동기화 완료](images/usage-verification/end-to-end-demo-2026-07-21/22-knowledge-graph-sync-complete.png)

node 213개와 edge 590개를 저장했고 Neo4j readback에서도 같은 수를 조회했습니다. 검증 DB의 graph state는 completed, mode full, Graph HEAD 221eb9ac9c83입니다.

#### 23. Neo4j 노드와 엣지 분포

![Neo4j 노드와 엣지 분포](images/usage-verification/end-to-end-demo-2026-07-21/23-knowledge-graph-nodes-edges.png)

노드는 project 1, program 8, commit 48, file 77, class 58, domain 21개입니다. 관계는 MAPPED_TO_COMMIT 38, TOUCHES_FILE 106, TOUCHES_DOMAIN 73, IMPORTS_CLASS 18건 등을 포함해 총 590건입니다.

### 4.6 Project Chat과 GraphRAG

#### 24. Project Chat 답변 준비 완료

![Project Chat 답변 준비 완료](images/usage-verification/end-to-end-demo-2026-07-21/24-project-chat-ready.png)

소스 근거 79개, 검색 준비 79/79, 코드 반영 상태 최신, 추가 준비 0입니다. Knowledge Graph도 최신이어서 관계 질문에 source와 graph 근거를 함께 사용할 수 있습니다.

#### 25. Project Chat 실제 답변

![Project Chat 실제 답변](images/usage-verification/end-to-end-demo-2026-07-21/25-project-chat-answer.png)

결제 승인 후 주문 상태 이동을 질문했습니다. 답변은 PaymentController, PaymentService, OrderStatusService의 역할과 파일 경로를 설명하고 Provider local_openai, model qwen2.5-coder-7b-instruct, fallback=False를 표시합니다.

#### 26. Project Chat GraphRAG 근거

![Project Chat GraphRAG 근거](images/usage-verification/end-to-end-demo-2026-07-21/26-project-chat-graph-evidence.png)

답변에는 현재 소스 11건과 graph evidence 8건이 사용됐습니다. class_import와 program → commit → file → class 영향 경로를 펼쳐 답변의 관계 근거를 추적할 수 있습니다.

### 4.7 AI Code Review

#### 27. 리뷰 대상 commit 선택

![리뷰 대상 commit 선택](images/usage-verification/end-to-end-demo-2026-07-21/27-code-review-target.png)

의도적으로 결제 경계값 위험을 포함한 2325182 Relax partner payment validation for pilot channel commit을 선택했습니다. 특정 commit을 고르면 시연 중 diff와 finding의 연결을 설명하기 쉽습니다.

#### 28. AI Code Review 완료

![AI Code Review 완료](images/usage-verification/end-to-end-demo-2026-07-21/28-code-review-complete.png)

local_openai / qwen2.5-coder-7b-instruct 결과가 완료 상태로 저장됐습니다. PaymentService.java에서 amount == 0, 즉 0원 결제가 새로 허용되는 경계 문제를 높은 위험 bug finding 1건으로 찾았고 fallback은 사용하지 않았습니다.

### 4.8 종합 결과 화면

#### 29. Home 최종 상태

![Home 최종 상태](images/usage-verification/end-to-end-demo-2026-07-21/29-home-final-status.png)

프로그램 8, commit 48, 개발자 6, 계획 진척도 90.6%, 추정 진척도 50.0%, 차이 40.6%를 한 화면에서 확인했습니다. 필수 준비 완료 상태이며 이후에는 경고와 근거 품질을 점검하면 됩니다.

#### 30. AI Progress

![AI Progress](images/usage-verification/end-to-end-demo-2026-07-21/30-ai-progress.png)

계획 진척도 90.6%와 프로그램 구현상태 기반 AI 진척도 50.0%의 차이를 보여줍니다. unresolved risk 32건과 HIGH risk 8건을 프로그램별 비교로 이어서 확인할 수 있습니다.

#### 31. Dashboard 개요

![Dashboard 개요](images/usage-verification/end-to-end-demo-2026-07-21/31-dashboard-overview.png)

프로그램, commit, 계획/AI 진척도, risk, 개발자 Git 활동을 한 화면에 모았습니다. 화면 하단에서 AI Resource Radar와 자원관리 지표로 이어집니다.

#### 32. AI Resource Radar

![AI Resource Radar](images/usage-verification/end-to-end-demo-2026-07-21/32-dashboard-resource-radar.png)

주문 상태 변경, 주문 접수, 재고 예약, 결제 승인 등 우선 검토 프로그램과 점수 근거를 보여줍니다. 미해결 risk 32건, HIGH 8건, 리뷰 시간 절감 가능성 0.5h, 추가 투입 예방 가능성 3.2MM은 의사결정 보조값으로 해석합니다.

#### 33. PL Briefing

![PL Briefing](images/usage-verification/end-to-end-demo-2026-07-21/33-dashboard-pl-briefing.png)

AI Resource Radar와 risk 근거를 바탕으로 실제 local LLM이 요약, 우선 확인 항목, 회의 질문, 다음 action을 생성했습니다. provider local_openai, mode LLM 생성, fallback=False인 저장 결과입니다.

#### 34. Git History 상세

![Git History 상세](images/usage-verification/end-to-end-demo-2026-07-21/34-git-history-detail.png)

commit 48건, 변경 파일 106건, 작성자 6명을 확인하고 최신 commit의 메시지, 작성자, 변경 파일, 저장 diff preview를 열었습니다.

#### 35. Commit Impact

![Commit Impact](images/usage-verification/end-to-end-demo-2026-07-21/35-commit-impact.png)

선택 commit의 프로그램, 개발자, 파일 영향 범위를 Mapping 결과와 Git 활동으로 설명합니다. 선택한 최신 probe commit은 프로그램 연결 0건이어도 개발자와 파일 영향 정보는 별도로 확인됩니다.

#### 36. AI 운영 현황

![AI 운영 현황](images/usage-verification/end-to-end-demo-2026-07-21/36-ai-operations-evidence.png)

LLM, Embedding, 최근 AI 호출, 검색 준비, 호출 요약, Neo4j, Knowledge Graph, Graph Readback, Project Chat GraphRAG가 모두 통과입니다. 호출 요약은 total 51, failed 0, fallback 0입니다.

#### 37. 개발계획 대시보드

![개발계획 대시보드](images/usage-verification/end-to-end-demo-2026-07-21/37-development-plan-dashboard.png)

프로그램 8건 중 완료 6건, 전체 계획 대비 완료율 75.0%, 평균 진행률 90.6%를 확인했습니다. 상태별 프로그램 수와 담당자별 배정 현황도 함께 표시됩니다.

## 5. 데이터 보호 확인

검증 종료 후 원본 Sample Shop 저장소는 commit 48건, HEAD 221eb9ac9c83, working tree clean 상태를 유지했습니다. 운영 DB의 기존 project 197도 commit 48건, 프로그램 8건, Mapping 관계 47건이 그대로 남아 있습니다.

검증용 DB는 삭제하지 않았습니다. 다시 확인해야 할 때 project ID 202607210과 Streamlit 8502를 사용하면 이번 결과를 그대로 열 수 있습니다. 일반 시연은 기존 8501과 project 197을 예비 동선으로 사용할 수 있습니다.

## 6. 관찰 사항과 한계

- 같은 운영 DB에서 동일 저장소를 새 프로젝트에 다시 수집하면 현재 GitCommit의 전역 commit_hash 제약과 sync 로직 때문에 기존 프로젝트 소유가 이동할 수 있습니다. 코드 수정 전까지는 기존 프로젝트 초기화 또는 격리 DB를 사용해야 합니다.
- Playwright CLI 세션에서 AI Code Review 버튼 click 이벤트가 저장 작업을 시작하지 않은 자동화 현상이 1회 있었습니다. DB에 review와 invocation이 모두 0건임을 확인한 뒤 UI와 동일한 CodeReviewService를 .venv에서 직접 실행했고, 저장 결과를 AI Code Review 화면으로 다시 열어 검증했습니다. 실제 서비스 호출은 완료, bug 1건, fallback 0건입니다.
- local LLM 문장은 재실행할 때 조금 달라질 수 있습니다. 시연에서는 이번에 저장한 Project Chat, Code Review, PL Briefing 결과를 기본으로 열고 live 호출은 질문을 받은 경우에만 실행하는 편이 안전합니다.
- AI Progress, Risk, Resource Radar 값은 Git과 계획 데이터를 바탕으로 한 검토 신호입니다. 실제 완료율이나 개인 성과를 확정하는 값으로 사용하지 않습니다.

## 7. 검증 명령과 결과

주요 확인 명령:

~~~powershell
git -C C:\dev\ai-advisor-sample-shop rev-list --count HEAD
git -C C:\dev\ai-advisor-sample-shop rev-parse HEAD
git -C C:\dev\ai-advisor-sample-shop status --short
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url http://127.0.0.1:8502 --project-name "Sample Shop 전체 시연 검증 2026-07-21" --feature <scenario>
~~~

검증 결과:

- 샘플 저장소: commit 48, HEAD 221eb9ac9c83364f4450bdf4970196b51cb1f9e1, working tree clean.
- 증적 PNG: 37개, 모두 열기 성공, 최소 1440×1000, 최소 파일 크기 76,810 bytes.
- 검증 DB: Git 48/106, Mapping 48/48, 구현상태 8, risk 32, source/vector 79/79, graph 213/590.
- 실제 AI 호출: 51건, failed 0, fallback 0.
- 원본 project 197: commit 48, 프로그램 8, Mapping 관계 47 유지.

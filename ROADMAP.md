# Roadmap

## Management Rules

- Check this file before starting meaningful feature, UX, schema, test, or documentation work.
- Move a task to `In Progress` when implementation starts.
- Move a task to `Done` when implementation, verification, `AI_CHANGELOG.md`, and documentation updates are complete.
- Record the related `AI_CHANGELOG.md` heading in the roadmap after completion when a task is roadmap-tracked. Do not maintain commit hashes in the roadmap; use Git history for commit-level traceability.
- Keep tasks small enough to complete and verify in one focused change set when practical.
- Use `Candidate Tasks` for known product/UX/engineering concerns that are worth preserving but not yet approved for implementation.
- When starting a candidate task, promote it into the priority overview and add a detailed task section before implementation.

## Priority Overview

| Priority | Area | Task | Status | Related AI Change Log |
|---|---|---|---|---|
| P2 | Navigation UX / Sample Data | Remove sample data UI and retain CLI workflow | Done | 샘플 데이터 생성 메뉴 제거와 CLI 유지 |
| P1 | Navigation UX | Tablet sidebar sticky header theme and touch fix | Done | 태블릿 sidebar 상단 고정 영역 보정 |
| P2 | Navigation UX | Mobile sidebar auto-collapse and sticky close control | Done | 모바일 sidebar 자동 닫기와 닫기 버튼 상단 고정 |
| P1 | Navigation UX | Mobile sidebar repeated auto-collapse reliability | Done | 모바일 sidebar 연속 자동 닫힘 안정화 |
| P1 | UX / State | Remove current-project URL synchronization | Done | 현재 프로젝트 URL 연동 제거 |
| P0 | Project Chat / Demo Data | Restore UTF-8 sample Project Chat evidence | Done | 샘플 Project Chat 한글 대화 복구 |
| P0 | Project Chat / Performance | Project Chat initial render latency reduction | Done | Project Chat 초기 화면 지연 개선 |
| P0 | Data UX | Program management UX improvement | Done | 프로그램 관리 UX 2차 개선 |
| P0 | Data UX | Developer management UX improvement | Done | 개발자 관리 UX 개선 |
| P0 | Data UX | Development plan management UX improvement | Done | 개발계획 관리 UX 개선 |
| P2 | Data UX / Sample Data | Artifact sample Excel downloads | Done | 산출물 관리 샘플 Excel 다운로드 |
| P1 | RAG | Project Chat answer quality and history persistence | Done | Project Chat database history and citation export |
| P1 | RAG | Standard terminology glossary upload and Korean query expansion | Done | Standard terminology documentation and screenshots |
| P1 | RAG | Incremental source indexing and embedding cost control | Done | Incremental source indexing and embedding cost control |
| P1 | RAG | Project Chat answer formatting and citation accuracy | Done | Standard terminology documentation and screenshots |
| P1 | RAG | Source file re-index warning and one-click refresh | Done | source_file 인덱스 상태 표시 세부 보완 |
| P1 | Program Detail | Implementation status result display improvement | Done | Program Detail 구현상태 분석 결과 표시 개선 |
| P1 | AI Analysis | Conservative implementation status prompt and fallback | Done | 구현상태 분석 프롬프트와 fallback 보수화 |
| P1 | AI Progress | Show implementation status analysis results | Done | AI Progress 구현상태 분석 결과 표시 |
| P1 | AI Progress / Semantics | Program-level AI Progress basis | Done | AI Progress 프로그램 단위 구현상태 기준 적용 |
| P1 | Mapping | Mapping feedback analytics and review queue | Done | Mapping 피드백 리뷰 큐와 품질 지표 추가 |
| P1 | Mapping / Ops | Commit-based mapping fallback and verified screenshots | Done | Commit-based mapping fallback and verified screenshots |
| P1 | CI | Git default branch deterministic tests | Done | CI Git default branch test fix |
| P1 | DB | Alembic migration stabilization | Done | Alembic DB 마이그레이션 도입 |
| P1 | Ops | LLM/Embedding batch safety and estimated runtime | Done | LLM/Embedding 배치 안전장치와 예상시간 표시 |
| P1 | AX / Resource Planning | AX resource management metrics foundation | Done | AX 자원관리 metric foundation |
| P1 | Forecast / Risk | Forecasted completion and proactive delay risk | Done | 예상 종료일과 자원관리 Dashboard |
| P1 | Resource UX | Developer workload and difficulty dashboard | Done | 예상 종료일과 자원관리 Dashboard |
| P2 | Docs / Business Value | AX customer value KPI documentation | Done | 예상 종료일과 자원관리 Dashboard |
| P1 | AX / AI Resource Planning | AI Resource Radar and PL Briefing | Done | AI Resource Radar와 PL Briefing 추가 |
| P2 | Validation / AI 검증 | PL Briefing live LLM verification evidence | Done | PL Briefing 실제 LLM 검증 증거 보강 |
| P2 | Docs / AI Positioning | AI technology application summary | Done | AI 기술 적용 요약 문서화 |
| P2 | UX | Sidebar navigation UX improvement | Done | Sidebar 메뉴 UX 개선 |
| P2 | UX | Artifact management menu grouping | Done | Artifact management sidebar grouping |
| P2 | Ops | CI test workflow | Done | CI 테스트 워크플로우 추가 |
| P2 | UX | Home analysis command center | Done | Home 분석 관제 화면 개선 |
| P2 | UX | Home copy tone cleanup | Done | Home 문구 톤 정리 |
| P2 | Ops | Home UI visual verification script | Done | Home UI 검증 스크립트 추가 |
| P2 | UX | Sidebar menu layout stabilization | Done | Sidebar 메뉴 위치 흔들림 보정 |
| P2 | Sample Data | Synthetic target project repository | Done | 가상 샘플 대상 프로젝트 생성 스크립트 추가 |
| P2 | Sample Data | Rich demo target repository scenario design | Done | 샘플 대상 repo 데모 시나리오 설계 문서 추가 |
| P2 | Sample Data | Rich demo target repository implementation | Done | 확장 샘플 대상 repo 구현 |
| P2 | Sample Data | Sample project commit history expansion | Done | Sample project commit history expansion |
| P2 | Docs | Rich sample demo walkthrough and screenshots | Done | 샘플 프로젝트 검증과 화면 캡처 갱신 |
| P2 | Docs | README documentation hub restructure | Done | README 문서 허브 개편 |
| P2 | Docs | Local LLM env onboarding guide | Done | local LLM env 예시와 Project Chat 재현 절차 |
| P2 | Docs | Korean-first user documentation cleanup | Done | Korean-first user documentation cleanup |
| P2 | Docs / Agent Policy | Mandatory AI-sounding wording review | Done | AI스러운 문구 필수 점검 agent policy 추가 |
| P2 | Docs / Agent Policy | Session-scoped Q&A documentation mode | Done | Session-scoped 시연 Q&A mode 추가 |
| P2 | Docs / Presentation | Text-brief-based final report rewrite | Done | 텍스트 계획서 기준 결과서 PPT 재작성 |
| P2 | Docs / Presentation | AI Use Case technical master deck rewrite | Done | AI Use Case 기술 상세 마스터덱 전면 재작성 |
| P2 | Docs / Presentation | AI Use Case internal share deck | Done | AI Use Case 내부 공유용 PPT 작성 |
| P2 | Docs / Presentation | AI Use Case internal share deck quality rewrite | Done | AI Use Case 내부 공유용 PPT 전면 보완 |
| P2 | Docs / Presentation | AI Use Case internal share deck aspect and polish pass | Done | AI Use Case 내부 공유용 PPT 이미지 비율과 품질 보정 |
| P2 | Ops | Application Dockerfile and deployment guide | Done | Application Dockerfile and deployment guide |
| P2 | Demo Ops | Quick Tunnel demo runbook and script | Done | Cloudflare Quick Tunnel 하루 시연 절차 자동화 |
| P1 | Demo Ops | Quick Tunnel restart persistence and active URL detection | Done | Quick Tunnel 자동 복구와 현재 URL 판별 |
| P2 | Docs | Engineering decisions log | Done | Engineering decisions documentation log |
| P2 | Ops | Feature screenshot capture automation | Done | Feature screenshot capture automation |
| P2 | Docs | Architecture document path cleanup | Done | Architecture document path cleanup |
| P2 | Docs | Application Preview rename | Done | Application Preview rename |
| P2 | Docs | Sample project wording cleanup | Done | Sample project wording cleanup |
| P2 | Docs | Natural wording policy generalization | Done | Natural wording policy generalization |
| P2 | Docs | Reader-facing wording policy simplification | Done | Reader-facing wording policy simplification |
| P2 | UX | Sidebar menu hierarchy sizing | Done | Sidebar 메뉴 계층 크기 조정 |
| P2 | Docs | Documentation impact gate policy | Done | Documentation impact gate policy |
| P2 | UX | Sidebar navigation structure stabilization | Done | Sidebar navigation structure stabilization |
| P2 | Docs | AI Agent onboarding guide | Done | AI Agent onboarding guide |
| P2 | UX | Global project context | Done | Global project context |
| P2 | UX | Home current project focus | Done | Home current project focus |
| P1 | Ops / Architecture | App-server Git repository operating model | Done | App-server Git repository operating model |
| P2 | Git Ops | Server repository update runbook/script | Done | Server repository update runbook and script |
| P2 | Git UX | Git History viewer | Done | Git History viewer |
| P2 | Docs | Git History Application Preview screenshot | Done | Git History Application Preview screenshot |
| P2 | Git Ops | Server repository status display | Done | Server repository status display |
| P2 | Docs | Demo user guide | Done | Demo user guide |
| P2 | Docs / Onboarding | Sample project first-run button guide | Done | 샘플 프로젝트 처음 시작 버튼 가이드 |
| P2 | Docs / Verification | Sample project usage guide verification evidence | Done | 샘플 프로젝트 사용 가이드 실제 검증 결과 추가 |
| P2 | Data UX | Project delete and reset safety | Done | Project delete and reset safety |
| P2 | UX / Data Model | Project developer membership model | Done | 프로젝트 개발자 연결 모델 |
| P2 | Code Review UX | AI Code Review server repository target wording | Done | AI Code Review 서버 저장소 대상 설명 정리 |
| P2 | Code Review UX | Remove server-local AI Code Review targets | Done | AI Code Review 서버 local 대상 제거 |
| P1 | Resource Analytics | Resource metric snapshot and trend dashboard | Done | 자원관리 지표 시계열 snapshot과 추세 분석 |
| P2 | Project Chat UX | Project Chat conversation controls cleanup | Done | Project Chat 대화 관리 UX 정리 |
| P2 | Project Chat UX | Project Chat source refresh wording cleanup | Done | Project Chat 근거 갱신 안내 UX 정리 |
| P2 | UX Help | Contextual help tooltips for Project/RAG controls | Done | Project/RAG 컨텍스트 도움말 툴팁 추가 |
| P2 | Resource UX | Resource value metric wording cleanup | Done | 자원관리 가치 지표 문구 정리 |
| P2 | UX / State | Current project selection persistence | Done | 현재 프로젝트 선택 유지 |
| P2 | UX / Analysis Views | User-facing analysis display cleanup | Done | 분석 화면 표시 정리 |
| P2 | UX / Action State | Completed-state action priority cleanup | Done | 완료 상태 액션 우선순위 정리 |
| P2 | UX / Data Flow | Program management project flow cleanup | Done | 프로그램 관리 현재 프로젝트 저장 흐름 정리 |
| P2 | Home UX | Home summary priority cleanup | Done | Home 요약 우선순위 정리 |
| P2 | Navigation UX | Sidebar group collapse cleanup | Done | Sidebar 접이식 그룹 정리 |
| P2 | Sample Data UX | Sample commit date normalization | Done | 샘플 프로젝트 commit 날짜 정규화 |
| P2 | Docs UX | Application Preview Dashboard wording cleanup | Done | Application Preview Dashboard 설명 문구 정리 |
| P2 | Dashboard UX | Dashboard value terminology cleanup | Done | Dashboard 가치 지표 용어 정리 |
| P2 | Docs / Screenshot UX | Application Preview current sidebar screenshots | Done | Application Preview 현재 메뉴 screenshot 갱신 |
| P2 | Docs UX | Sidebar menu map documentation | Done | Sidebar 메뉴 구조 문서화 |
| P2 | Docs / Screenshot UX | Application Preview lower-section coverage | Done | Application Preview 하단 기능 screenshot 보강 |
| P2 | Docs / Screenshot UX | Application Preview scroll coverage refresh | Done | Application Preview 스크롤 영역 screenshot 보강 |
| P1 | AX / AI 검증 | Structured PL Briefing history and validation hardening | Done | 구조화 PL Briefing 이력과 검증 안정화 |
| P2 | Docs / Screenshot UX | README representative screenshot source cleanup | Done | README 대표 screenshot source 통합 |
| P2 | Docs UX | README preview-first section ordering | Done | README preview-first section ordering |
| P2 | Docs / Onboarding | Local setup prerequisites guide | Done | Local setup prerequisites guide |
| P2 | Docs UX | Application Preview expanded sections | Done | Application Preview expanded sections |
| P2 | Docs / Screenshot UX | Project Chat GraphRAG preview screenshot | Done | Project Chat GraphRAG preview screenshot |
| P2 | Project Chat UX | Interactive GraphRAG evidence visualization | Done | Project Chat GraphRAG interactive visualization |
| P2 | Code Review / Demo UX | AI Code Review demo evidence and preview screenshot | Done | AI Code Review demo evidence and preview screenshot |
| P2 | AI Verification / Demo Quality | Real local LLM demo evidence correction | Done | Real local LLM demo evidence correction |
| P2 | Sample Data / Demo Quality | Scenario-designed sample evidence for rich AI outputs across features | Done | Scenario-designed sample evidence for rich AI outputs |
| P2 | AI Verification / Demo Quality | Project Chat real local LLM screenshot evidence | Done | Project Chat real local LLM screenshot evidence |
| P2 | GraphRAG / Demo Quality | Korean Project Chat class relationship evidence screenshot | Done | Korean Project Chat class relationship evidence screenshot |
| P1 | Project Chat / Demo Quality | Project Chat preview question replay stability | Done | Project Chat preview 질문 재현 안정화 |
| P1 | GraphRAG / Sample Quality | Service-layer Project Chat graph cleanup | Done | GraphRAG 관계도와 샘플 결제 흐름 정리 |
| P1 | GraphRAG / Demo Quality | Rich GraphRAG evidence without weak domain nodes | Done | GraphRAG 기본 근거 그래프 풍부도 복원 |
| P1 | GraphRAG / Demo Quality | Natural mixed GraphRAG layout | Done | GraphRAG 혼합 근거 그래프 배치 자연화 |
| P1 | GraphRAG / Demo Quality | Fold duplicate file and class graph nodes | Done | GraphRAG 파일/class 중복 노드 접기 |
| P2 | Docs / Application Preview | GraphRAG preview question caption | Done | Application Preview GraphRAG 질문 문구 보강 |
| P2 | Docs / Application Preview | AI Code Review recommended commits | Done | Application Preview AI Code Review 추천 커밋 보강 |
| P1 | Code Review / Demo Quality | AI Code Review selected sample commit execution | Done | AI Code Review 선별 커밋 실제 실행과 preview 갱신 |
| P1 | Code Review UX | Korean AI Code Review output and status labels | Done | AI Code Review 한국어 출력과 상태 표시 개선 |
| P1 | Code Review Quality | Grounded Korean AI Code Review suggestions | Done | AI Code Review grounded suggestion 보정 |
| P2 | Code Review UX | Compact AI Code Review metadata display | Done | AI Code Review 메타데이터 표시 compact화 |
| P1 | Code Review UX | AI Code Review commit list selection | Done | AI Code Review 커밋 목록 선택 |
| P1 | Code Review Reliability | AI Code Review Korean response repair with visible fallback | Done | AI Code Review 한국어 보정과 영어 원문 fallback |
| P2 | Sample Data / Demo Quality | Source-first sample project and demo verification guide | Done | Source-first sample project and demo verification guide |
| P2 | Docs / Policy | Roadmap commit hash tracking cleanup | Done | Roadmap commit hash tracking cleanup |
| P2 | UX / State | Project-scoped UI state namespacing | Done | Project-scoped UI state namespacing |
| P2 | Data UX | Project reset action after delete flow | Done | Project reset action after delete flow |
| P3 | Git Ops | Server-managed clone/fetch workflow | Done | Server-managed clone/fetch workflow |
| P2 | Git UX / Ops | Managed Git URL project onboarding | Done | 관리형 Git URL 프로젝트 등록 |
| P2 | Sample Data / Git UX | Public sample repository and managed onboarding verification | Done | 공개 샘플 GitHub 저장소와 관리형 등록 검증 |
| P1 | Data Model / Git Sync | Project-scoped Git commit identity across RAG and graph | Done | 프로젝트 범위 Git commit identity와 전체 저장소 격리 |
| P1 | AX / AI 검증 | AI evidence trace view | Done | AX AI 검증과 telemetry 구현 |
| P1 | Readiness | AI readiness cockpit | Done | AX AI 검증과 telemetry 구현 |
| P1 | AI Quality | Sample project AI evaluation scorecard | Done | AX AI 검증과 telemetry 구현 |
| P1 | AI Reliability | Strict structured-output validation and retry | Done | AX AI 검증과 telemetry 구현 |
| P2 | PL Workflow | Exportable weekly AI report | Done | AX AI 검증과 telemetry 구현 |
| P2 | AI Ops | AI invocation telemetry | Done | AX AI 검증과 telemetry 구현 |
| P1 | AX / AI 검증 | AI validation action cockpit | Done | AI 검증 실행 cockpit 개선 |
| P2 | Docs / Product Wording | Product wording cleanup | Done | 제품 용어 정리 |
| P2 | UX / Product Wording | AI validation menu purpose cleanup | Done | AI 검증 메뉴 목적과 제품 용어 정리 |
| P2 | UX / AI Ops | AI operations status menu | Done | AI 운영 현황 메뉴와 연결 상태 요약 |
| P1 | Graph / AI | Neo4j knowledge graph foundation | Done | Neo4j Knowledge Graph 기반 추가 |
| P1 | Graph / AI | Project Chat GraphRAG context injection | Done | Project Chat GraphRAG context injection |
| P1 | Graph Ops | Knowledge Graph freshness and incremental Neo4j sync | Done | Knowledge Graph freshness and incremental Neo4j sync |
| P1 | AI Ops | AI operations graph status | Done | AI operations graph status |
| P2 | Graph UX | Knowledge Graph exploration UI | Done | Knowledge Graph exploration UI |
| P2 | AI Quality | Project-level AI quality scorecard | Done | Project-level AI quality scorecard |
| P2 | AI Verification | Local LLM verification routine | Done | Local LLM verification routine |
| P1 | AI Ops / RAG | Local AI model and multilingual RAG optimization | Done | Local AI 모델 및 다국어 RAG 최적화 |
| P2 | Workflow | Git Sync follow-up action orchestrator | Done | Git Sync follow-up action orchestrator |
| P2 | Graph Ops | Neo4j production hardening | Done | Neo4j production hardening |
| P3 | Source Analysis | Source parser accuracy expansion | Done | Source parser accuracy expansion |
| P3 | Project Chat UX | Graph-aware question templates | Done | Graph-aware Project Chat question templates |
| P3 | Reporting | Graph-aware weekly report | Done | Graph-aware weekly report |
| P3 | Product UX | First-run and empty-state polish | Done | First-run and empty-state preparation guide |
| P1 | Demo Readiness | Internal demo rehearsal and preflight hardening | Done | 내부 시연 리허설과 사전 점검 안정화 |
| P1 | Demo Verification | Fresh end-to-end demo project rebuild and evidence | Done | 새 프로젝트 전체 시연 재현과 단계별 증적 |
| P0 | Demo Operations | Canonical demo database and Docker 8501 recovery | Done | 기본 DB와 Docker 8501 시연 환경 통합 |
| P0 | Demo Operations | Canonical demo startup contract and legacy Tunnel reuse | Done | 시연 서버 상태 우선 재기동과 legacy Tunnel 재사용 |

## P2 - Remove Sample Data UI And Retain CLI Workflow

Status: Done

Goal:
사용자용 sidebar에서 개발·검증 목적의 `샘플 데이터 생성` 화면과 관련 preview 산출물을 제거하되, Git 저장소에서 개발자·프로그램·개발계획 Excel을 생성하는 CLI 프로그램과 실행 가이드는 유지한다.

Rationale:
산출물 관리 화면에서 Sample Shop Excel을 직접 내려받을 수 있게 된 뒤에도 별도의 `샘플 데이터 생성` 메뉴가 남아 있어 두 경로의 목적이 겹쳐 보인다. 전용 화면은 앱 서버의 로컬 Git 경로를 요구하는 개발 도구 성격이 강하므로 일반 navigation에서는 제외하고, 임의 저장소로 가상 Excel을 만들어야 하는 개발·검증 작업은 명시적인 CLI로 계속 수행할 수 있게 한다.

Checklist:

- [x] sidebar 메뉴 연결과 전용 Streamlit page를 제거한다.
- [x] Application Preview section, screenshot asset, capture scenario를 제거한다.
- [x] `scripts/generate_sample_development_data.py`와 생성 로직 test를 유지한다.
- [x] README와 기능 가이드에 CLI 실행 방법, 출력 파일, 사용 경계를 남긴다.
- [x] architecture와 engineering decision에 UI/CLI 경계를 반영한다.
- [x] `AI_CHANGELOG.md`를 갱신한다.
- [x] 참조 검색, CLI smoke test, focused/전체 test, 문서 문구와 whitespace를 검증한다.

Related AI Change Log: `샘플 데이터 생성 메뉴 제거와 CLI 유지`

## P1 - Tablet Sidebar Sticky Header Theme And Touch Fix

Status: Done

Goal:
태블릿의 다크·라이트 테마에서 sidebar 상단 고정 영역이 주변 배경과 자연스럽게 이어지고, 과도한 높이 없이 터치로 닫기 버튼을 항상 사용할 수 있게 한다.

Rationale:
기존 sticky header는 존재하지 않는 CSS theme variable의 fallback을 흰색으로 지정하고 Streamlit 기본 header padding을 그대로 고정했다. 다크 테마 태블릿에서는 약 70px 높이의 흰 영역이 생겼고, hover가 없는 터치 화면에서는 그 안의 닫기 버튼도 보이지 않았다. sidebar의 실제 계산 배경색을 상속하고 compact toolbar 크기를 명시하며 touch capability에서 기본 닫기 버튼을 표시해야 원래 목적을 충족할 수 있다.

Checklist:

- [x] 흰색 fallback을 제거하고 sidebar 실제 배경색을 sticky header까지 상속한다.
- [x] sticky header 높이와 padding을 compact하게 줄이고 기존 메뉴 content와 겹치지 않게 한다.
- [x] hover가 없는 coarse pointer에서 Streamlit 기본 닫기 버튼을 항상 표시한다.
- [x] CSS 회귀 test와 태블릿 다크·라이트, 모바일·데스크톱 browser 검증을 수행한다.
- [x] engineering decision, failure history, `AI_CHANGELOG.md`를 갱신하고 Docker app을 재빌드한다.

Related AI Change Log: `태블릿 sidebar 상단 고정 영역 보정`

## P2 - Mobile Sidebar Auto-Collapse And Sticky Close Control

Status: Done

Goal:
모바일 화면에서 사이드바 메뉴로 다른 화면을 선택하면 본문을 바로 확인할 수 있도록 사이드바를 자동으로 닫고, 화면 크기와 관계없이 사이드바를 스크롤해도 닫기 버튼을 상단에 유지한다.

Rationale:
현재 custom `st.button` 내비게이션은 모바일에서 화면을 전환한 뒤에도 sidebar overlay가 열린 상태로 남아 본문을 가린다. 또한 메뉴가 길어 sidebar를 아래로 스크롤하면 Streamlit 기본 닫기 버튼이 함께 사라져 사용자가 다시 상단까지 이동해야 한다. 모바일 overlay에서만 실제 메뉴 이동 뒤 자동으로 닫고, 기본 닫기 버튼은 sticky header로 유지하면 데스크톱의 연속 탐색 흐름과 사용자의 수동 제어를 보존하면서 두 불편을 함께 줄일 수 있다.

Checklist:

- [x] 실제 sidebar 메뉴 이동에만 모바일 자동 닫기를 요청하고, 데스크톱·현재 메뉴 재클릭·프로젝트 변경에는 적용하지 않는다.
- [x] Streamlit 기본 sidebar header를 sticky 처리해 스크롤 뒤에도 닫기 버튼을 유지한다.
- [x] Python 상태 처리와 모바일/데스크톱 browser 회귀 test를 추가한다.
- [x] 기능 가이드, engineering decision, `AI_CHANGELOG.md`를 갱신하고 사용자-facing 문구를 점검한다.
- [x] focused/full test, compileall, 실제 viewport UI, Docker build를 검증한다.

Related AI Change Log: `모바일 sidebar 자동 닫기와 닫기 버튼 상단 고정`

## P1 - Mobile Sidebar Repeated Auto-Collapse Reliability

Status: Done

Goal:
모바일에서 sidebar를 다시 열어 연속으로 다른 메뉴를 선택해도 매번 자동으로 닫히도록 1회성 browser component 실행을 안정화한다.

Rationale:
현재 구현은 메뉴 이동 요청마다 같은 `components.html` payload를 렌더링한다. 첫 이동 뒤 iframe이 DOM에 남아 있으면 다음 이동에서 같은 `srcdoc`가 재사용되어 닫기 script가 다시 실행되지 않을 수 있고, Python 요청은 browser 성공 여부와 관계없이 이미 소비된다. 요청마다 고유한 payload를 만들고 sidebar DOM 준비 시점을 제한적으로 재시도하면 기존 모바일 전용 동작과 Streamlit 기본 닫기 버튼 재사용 원칙을 유지하면서 연속 이동 실패를 제거할 수 있다.

Checklist:

- [x] 모바일 닫기 요청마다 고유한 component payload를 만들고 sidebar DOM 준비를 제한적으로 재시도한다.
- [x] 요청 ID 소비와 연속 component 렌더링을 검증하는 회귀 test를 추가한다.
- [x] focused/full test와 compileall을 통과한다.
- [x] 390px 실제 browser에서 중간 rerun 없이 연속 메뉴 이동이 모두 닫히고 desktop은 열린 상태를 유지하는지 확인한다.
- [x] engineering decision, failure history, `AI_CHANGELOG.md`를 갱신한다.

Related AI Change Log: `모바일 sidebar 연속 자동 닫힘 안정화`

## P1 - Remove Current-Project URL Synchronization

Status: Done

Goal:
사이드바의 현재 프로젝트 선택을 Streamlit session state만으로 관리해 첫 선택이 이전 URL `project_id`에 덮이는 상태 충돌을 제거한다.

Rationale:
URL query parameter와 widget/session state를 동시에 현재값의 기준으로 사용하면 Streamlit rerun 시점에 서로 다른 값이 경쟁할 수 있다. 현재 프로젝트는 앱 안에서 사용자가 직접 바꾸는 작업 컨텍스트이므로 URL 공유·복원보다 한 번의 선택이 즉시 반영되는 동작을 우선한다.

Checklist:

- [x] `project_id` query parameter 읽기·쓰기와 관련 복원 정책을 제거한다.
- [x] 현재 프로젝트 selector에 고정 widget key와 session-state callback을 적용한다.
- [x] 첫 선택, 잘못된 선택 복구, URL 무시 동작의 회귀 test를 추가한다.
- [x] 사용자 문서, architecture, engineering decision, failure history를 새 상태 정책에 맞춘다.
- [x] `AI_CHANGELOG.md`를 갱신하고 focused/full test와 실제 UI 전환을 검증한다.

Related AI Change Log: `현재 프로젝트 URL 연동 제거`

## P1 - AI Code Review Commit List Selection

Status: Done

Goal: AI Code Review에서 특정 commit hash를 외부 화면에서 찾아 직접 입력하지 않고, 실제 앱 서버 Git 저장소의 최근 commit 목록을 확인해 리뷰 대상을 선택할 수 있게 한다.

Rationale: 현재 `특정 커밋` 흐름은 hash 또는 rev를 알고 있어야 하므로 Git History와 AI Code Review 사이를 오가야 한다. 리뷰 대상 저장소에서 직접 읽은 commit hash, 시각, 작성자, 메시지를 한 목록에 보여주면 사용자는 대상을 확인한 뒤 바로 리뷰할 수 있고, Git 수집 DB가 저장소 HEAD보다 늦은 경우에도 실제 리뷰 가능한 이력과 선택지가 일치한다.

- [x] 실제 리뷰 대상 Git 저장소에서 제한된 최근 commit 목록을 안전하게 조회한다.
- [x] AI Code Review 화면에서 commit 정보가 보이는 선택 목록과 직접 rev 입력 fallback을 제공한다.
- [x] 목록 조회와 표시 형식의 회귀 test를 추가한다.
- [x] 사용자 가이드와 `AI_CHANGELOG.md`를 갱신하고 사용자 문구를 점검한다.
- [x] focused test, compileall, 전체 test를 실행한다.

## P1 - AI Code Review Korean Response Repair With Visible Fallback

Status: Done

Goal: AI Code Review의 사용자 설명 필드가 영어 위주로 생성되면 한국어 보정을 한 번 시도하고, 보정에 실패해도 유효한 원문 리뷰는 화면과 저장 결과에 그대로 제공하면서 언어 검증 실패는 운영 log와 telemetry에만 남긴다.

Rationale: 현재 Structured Output은 JSON shape만 보장하며 설명 언어를 검증하지 않는다. 영어 응답은 사용성 문제지만 리뷰 내용 자체가 틀렸다는 뜻은 아니므로 사용자 결과를 실패 처리하거나 버리지 않는다. 대신 한국어 보정을 우선 시도하고, 끝까지 영어여도 완료 결과로 제공하되 운영자가 반복 빈도와 provider/model 품질을 추적할 수 있어야 한다.

- [x] 코드 식별자와 enum을 제외한 사용자 설명 필드의 한국어 여부를 검증한다.
- [x] 한국어 검증 실패 시 설명 필드만 보정하는 LLM 호출을 한 번 수행한다.
- [x] 보정 성공 결과를 저장하고, 보정 실패 시 최초 원문을 완료 결과로 저장·표시한다.
- [x] `language_repaired`와 `language_invalid`를 raw metadata, telemetry, application log에 기록한다.
- [x] 회귀 test와 AI/user-facing 문서, engineering decision, failure history, `AI_CHANGELOG.md`를 갱신한다.
- [x] focused test, compileall, 전체 test를 실행한다.

## P0 - Restore UTF-8 Sample Project Chat Evidence

Status: Done

Goal: 손상된 Project Chat 세션 `#1`만 제거하고 실제 브라우저 UI에서 기준 한글 질문을 다시 입력해, 질문·답변·근거가 UTF-8로 정상 저장되는지 검증한다.

Rationale: 새로 만든 샘플 프로젝트의 첫 대화가 저장소 문제가 아니라 실행 경계에서 이미 `?`로 변환된 입력을 받았다. 기존 매핑·임베딩·그래프 데이터는 유지하면서 잘못된 대화 증거만 교체하고, 답변 검증뿐 아니라 사용자 입력의 저장 왕복도 확인할 필요가 있다.

- [x] 손상 범위와 DB UTF-8 설정 확인
- [x] 삭제 전 복구용 백업 생성 및 대상 세션 재확인
- [x] DB에서 프로젝트 `1`의 세션 `#1`만 조건부 삭제
- [x] 브라우저 UI에서 기준 한글 질문으로 새 대화 생성
- [x] UI·DB 질문 원문과 답변 근거 검증
- [x] 프로젝트·매핑·임베딩·그래프 데이터 불변 확인
- [x] 운영 문서, 실패 이력, `AI_CHANGELOG.md` 갱신

## P1 - Quick Tunnel Restart Persistence And Active URL Detection

Status: Done

Goal:
명시적인 종료 명령이 없는 한 Quick Tunnel이 Docker daemon 재시작 뒤 자동 복구되고, 이전 실행 로그의 만료된 URL이 아니라 현재 실행에서 발급된 URL을 상태 확인에 사용하게 한다.

Rationale:
기존 legacy Tunnel은 restart policy가 `no`여서 Docker daemon이 재시작된 뒤 앱과 DB만 복구되고 외부 접속은 중단됐다. 같은 container를 다시 시작하면 과거와 현재 Quick Tunnel URL이 로그에 함께 남아 상태 확인이 이전 URL을 선택할 수도 있다. 사용자가 Tunnel 종료를 명시하지 않은 정상 재기동에서는 외부 경로도 함께 복구되어야 한다.

Checklist:

- [x] 종료 시각, exit code, OOM 여부와 다른 container 시작 시각으로 중단 원인을 확인한다.
- [x] 새 Quick Tunnel container에 `restart: unless-stopped`와 같은 Docker restart policy를 적용한다.
- [x] 현재 container 실행 이후 로그에서만 Quick Tunnel URL을 선택한다.
- [x] 기존 legacy Tunnel의 restart policy를 갱신하고 실제 외부 health를 확인한다.
- [x] focused/full test, 문서, engineering decision, failure history와 `AI_CHANGELOG.md`를 갱신한다.

Related changelog: `Quick Tunnel 자동 복구와 현재 URL 판별`

## P0 - Project Chat Initial Render Latency Reduction

Status: Done

Goal:
Project Chat 메뉴 진입과 질문 전송을 분리하고, 초기 화면에서는 저장소 전체 파일 검증이나 AI 호출 없이 현재 근거 상태와 입력창을 빠르게 표시한다.

Rationale:
현재 Docker 8501 환경에서 Project Chat 첫 화면이 표시되기 전에 source index 상태 확인과 현재 파일 검증이 실행되어 수십 초가 걸린다는 관측이 있다. 단계별 시간과 호출 횟수로 병목을 확정하고, stale source를 숨기지 않으면서 고비용 검증은 사용자가 요청하거나 질문에 필요한 시점으로 늦춰야 한다.

Checklist:

- [x] 초기 진입 call path와 DB, repository scan/hash, source freshness, embedding, Neo4j, session/history 시간을 계측한다.
- [x] localhost와 기존 Quick Tunnel의 메뉴 진입 시간을 비교하고 질문 응답 대기 시간과 분리한다.
- [x] 초기 render에서 repository 전체 검증, embedding, LLM, 전체 재색인, graph sync가 실행되지 않게 한다.
- [x] 마지막 확인 시각, repo HEAD 일치 여부, 새로고침 필요 상태를 표시하고 명시적 새로고침에서만 실제 파일 검증을 실행한다.
- [x] project ID, repo HEAD, embedding provider/model/dimension에 따른 cache 격리와 무효화를 검증한다.
- [x] 기존 citation, 직접 호출 검증, deterministic repair, session 격리 회귀를 검증한다.
- [x] 전체 pytest, Docker browser timing, 기존 Quick Tunnel timing, 실제 한국어 질문을 검증한다.
- [x] 관련 사용자/기술 문서, engineering decision, failure history와 `AI_CHANGELOG.md`를 갱신한다.

Related changelog: `Project Chat 초기 화면 지연 개선`

## P0 - Canonical Demo Startup Contract And Legacy Tunnel Reuse

Status: Done

Goal:
새 Agent 세션이나 운영자가 대화 맥락을 다시 설명하지 않아도 저장소의 한 가지 기동 절차만으로 LM Studio, Docker 8501, 기본 DB, 기존 Quick Tunnel과 현재 기준 project `1`을 안전하게 확인하고 필요한 서비스만 시작할 수 있게 한다.

Rationale:
README, setup 가이드, 시연 Runbook의 LM Studio port와 기동 순서가 달랐고, 현재 실행 중인 legacy Tunnel container와 저장소 스크립트가 관리하는 container 이름도 달랐다. 상태를 먼저 확인하지 않고 문서의 명령을 그대로 실행하면 불필요한 image rebuild, 잘못된 port 사용, 두 번째 Quick Tunnel 생성과 URL 변경이 생길 수 있다.

Checklist:

- [x] 정상 재기동, image rebuild, 외부 Tunnel 신규 생성 조건을 분리한다.
- [x] LM Studio port `12345`, Chat context length `8192`, embedding 768차원 기준을 환경 예시와 문서에서 통일한다.
- [x] 기존 `ai_commit_advisor_quick_tunnel`을 read-only로 감지하고 외부 URL을 재사용한다.
- [x] 한 명령으로 상태 확인·필요 서비스 기동·health·preflight를 수행하는 안전한 startup script를 추가한다.
- [x] 새 Agent 세션이 같은 startup contract를 자동으로 적용하도록 `AGENTS.md`에 운영 원칙을 기록한다.
- [x] Docker/LM Studio/Cloudflare를 호출하지 않는 focused test와 실제 환경의 비파괴 check-only 검증을 수행한다.
- [x] README, setup, Runbook, engineering decision, failure history와 `AI_CHANGELOG.md`를 갱신한다.

Related changelog: `시연 서버 상태 우선 재기동과 legacy Tunnel 재사용`

## P1 - Local AI Model And Multilingual RAG Optimization

Status: Done

Goal:
현재 PC의 RTX 3060 Ti 8GB와 32GB RAM 범위에서 local chat model의 안정성을 유지하면서, 한국어 질문이 영문·Java 소스 근거를 제대로 찾도록 embedding과 structured output 경로를 개선한다.

Rationale:
실제 Mapping 호출은 `qwen2.5-coder-7b-instruct`에서 빠르고 안정적이었지만, 현재 `nomic-embed-text-v1.5`는 한국어 질문으로 샘플 Java 소스를 찾는 소규모 진단에서 정답 파일을 상위 근거로 올리지 못했다. 문서와 질문을 같은 방식으로 embedding하고 Nomic이 요구하는 task prefix를 전달하지 않는 구현도 확인됐다. chat model을 무조건 키우기보다 LM Studio runtime, context, multilingual embedding, JSON schema 강제를 실제 프로젝트 지표로 나눠 검증해야 한다.

Checklist:

- [x] 현재 hardware, LM Studio, loaded model, context, VRAM, 실제 AI invocation 지표를 확인한다.
- [x] LM Studio를 최신 안정판으로 업그레이드하고 OpenAI-compatible endpoint와 기존 model load를 확인한다.
- [x] `qwen2.5-coder-7b-instruct`를 8192 context로 유지하고 GPU memory와 실제 호출을 검증한다.
- [x] 768 dimension을 유지하는 multilingual embedding model을 설치하고 query/document task prefix를 구현한다.
- [x] Mapping, 구현상태, Code Review, PL Briefing처럼 JSON을 요구하는 경로에 Structured Output을 적용한다.
- [x] 현재 프로젝트의 기존 embedding을 새 model로 재생성하고 한국어 검색 품질을 다시 측정한다.
- [x] 기존 Qwen2.5 기준과 후보 chat model을 같은 실제 프로젝트 평가 기준으로 비교할 수 있는 A/B 검증 경로를 준비한다.
- [x] 관련 사용자 문서, AI 기술 설명, engineering decision, failure history, `AI_CHANGELOG.md`를 갱신한다.
- [x] compile, focused/full tests, live LM Studio 연결, RAG 검색, LLM JSON 결과, diff hygiene을 검증한다.

Related AI Change Log: `Local AI 모델 및 다국어 RAG 최적화`

## P0 - Canonical Demo Database And Docker 8501 Recovery

Status: Done

Goal:
기본 PostgreSQL DB `ai_commit_advisor` 하나를 실제 시연 데이터의 기준으로 사용하고, Docker 8501과 Cloudflare 경로가 같은 DB와 실제 local LLM/embedding provider를 보도록 복구한다.

Rationale:
동일 저장소의 기존 commit 소유권 이동을 피하려고 별도 E2E DB를 만든 결과, local 8502와 Docker 8501이 서로 다른 프로젝트 목록과 provider 설정을 보여줬다. Docker 8501은 기본 DB와 mock provider를 사용해 과거의 깨진 Chat 메시지까지 다시 노출했다. 사용자가 포트나 실행 명령에 따라 다른 데이터를 보지 않도록 기준 DB와 실행 경로를 하나로 고정해야 한다.

Checklist:

- [x] 기본 DB와 격리 E2E DB를 OneDrive에 각각 백업하고 복구 가능한 dump인지 확인한다.
- [x] 잘못 열린 Docker 8501 앱과 quick tunnel을 중지한다.
- [x] 기본 DB의 기존 Sample Shop 프로젝트 4, 97, 197만 제거한다.
- [x] 기본 DB에 새 Sample Shop 프로젝트를 등록하고 Git, 산출물, Mapping, 구현상태, Risk, RAG, Knowledge Graph, Project Chat, Code Review, Dashboard 분석을 다시 실행한다.
- [x] Docker 8501이 기본 DB와 실제 local LLM/embedding provider, 768 dimension을 사용하도록 설정한다.
- [x] 한글 질문 저장, Project Chat 사실·호출 관계·인용 범위, 화면 프로젝트 ID를 검증한다.
- [x] Cloudflare 경로에서 새 프로젝트와 저장 결과를 확인한 뒤 격리 E2E DB를 제거한다.
- [x] 운영 문서, failure history, engineering decision, `AI_CHANGELOG.md`, 테스트와 화면 증적을 갱신한다.

Related AI Change Log: `기본 DB와 Docker 8501 시연 환경 통합`

## P1 - Fresh End-To-End Demo Project Rebuild And Evidence

Status: Done

Goal:
기존 시연 데이터를 안전한 예비본으로 유지하면서, 동일한 샘플 Git 저장소를 새 프로젝트에 연결해 수집부터 AI 분석까지 전 과정을 다시 실행하고 단계별 화면 증적과 설명을 별도 문서로 남긴다.

Rationale:
저장된 결과만 확인하면 신규 프로젝트에서 실제 수집·분석 흐름이 끝까지 이어지는지 증명하기 어렵다. 시연 전에 현재 로컬 실행 환경과 실제 local LLM/embedding을 사용해 전체 경로를 재현하고, 각 단계의 입력·결과·한계를 함께 기록하면 당일 진행 순서와 장애 지점을 빠르게 확인할 수 있다.

Checklist:

- [x] 기존 프로젝트와 샘플 Git 저장소를 변경하지 않고 새 프로젝트를 등록한다.
- [x] Git 전체 수집과 개발자·프로그램·개발계획·표준용어 자료 등록을 완료한다.
- [x] Mapping, 구현상태, Risk, RAG/embedding, Knowledge Graph 분석을 완료한다.
- [x] Project Chat과 AI Code Review 대표 결과를 실제 local LLM으로 생성한다.
- [x] 단계별 화면을 전용 폴더에 캡처하고 별도 한국어 증적 문서에 설명을 작성한다.
- [x] 문서 표현 점검, `AI_CHANGELOG.md` 갱신, 최종 검증을 완료한다.

Related AI Change Log: `새 프로젝트 전체 시연 재현과 단계별 증적`

## P1 - Internal Demo Rehearsal And Preflight Hardening

Status: Done

Goal:
목요일 팀 내부 시연 전에 샘플 프로젝트의 핵심 화면과 local LLM/embedding 연결을 실제로 리허설하고, 준비 상태 오판과 로컬 실행 환경 문제를 발표 전에 확인할 수 있는 실행 기준을 정리한다.

Rationale:
검증 데이터와 발표자료가 이미 있어도, Windows 예약 포트 때문에 LM Studio API가 시작되지 않거나 Mapping 결과 행 수를 분석 완료 commit 수로 잘못 비교하면 시연 직전 Home이 불완전 상태처럼 보일 수 있다. 시연에서는 데이터를 다시 만드는 것보다 저장된 결과를 안정적으로 보여주고, 필요한 경우에만 대표 AI 호출을 실행하는 편이 안전하다.

Checklist:

- [x] PostgreSQL, Neo4j, local LLM, embedding, Streamlit 기동과 핵심 연결을 확인한다.
- [x] Mapping 준비 상태가 분석 완료 commit 기준으로 계산되도록 수정하고 회귀 테스트를 추가한다.
- [x] 샘플 프로젝트의 Home, Risk, AI Progress, Project Chat, GraphRAG, AI Code Review 핵심 흐름을 리허설한다.
- [x] 내부 시연용 대본, 예상 질문, 장애 대응, 당일 체크리스트를 문서화한다.
- [x] 실패 이력, engineering decision, `AI_CHANGELOG.md`를 갱신하고 전체 검증을 완료한다.

Related AI Change Log: `내부 시연 리허설과 사전 점검 안정화`

## P2 - Mandatory AI-Sounding Wording Review

Status: Done

Goal:
사용자-facing 문서, UI 문구, 결과서, 발표자료를 마무리하기 전에 AI가 쓴 것처럼 보이는 추상적·번역체 문구가 남아 있는지 반드시 확인하도록 `AGENTS.md` agent policy를 강화한다.

Checklist:

- [x] `AGENTS.md`에 AI스러운 문구 최종 점검 규칙을 추가한다.
- [x] 반복 가능한 agent-policy 결정으로 `docs/engineering-decisions.md`에 배경과 tradeoff를 기록한다.
- [x] `AI_CHANGELOG.md`에 변경과 검증 결과를 남긴다.
- [x] `rg`와 `git diff --check`로 정책 반영과 diff hygiene을 확인한다.

## P2 - Text-Brief-Based Final Report Rewrite

Status: Done

Goal:
회사 제출용 AI Use Case 결과서를 기존 PPT 구조가 아니라 텍스트 계획서와 현재 앱 근거 기준으로 다시 작성한다.

Rationale:
이전 결과서는 새 화면과 내부 발표용 역할명을 앞세워 사용자가 보여주려던 "AI Use Case"와 "실제 SI 프로젝트에서 개발 리더가 관리 판단에 참고하는 지표" 관점을 흐렸습니다. 결과서는 기능을 더 만들기보다, 이미 구현된 산출물·Git 수집, Mapping, Risk Analysis, AI Progress, 자원관리 지표, AI Code Review, RAG/Project Chat/Knowledge Graph 근거를 제출 맥락에 맞게 설명해야 합니다.

Checklist:

- [x] 기존 8장 PPT를 자료원으로 쓰지 않고 텍스트 계획서와 현재 앱 evidence만 사용한다.
- [x] 초기 요약본으로 고객 Pain Point, Use Case 목표, 운영 흐름, 핵심 기능, PoC 결과, 적용 기준과 한계를 정리했고, 이후 기술 상세 마스터덱으로 대체한다.
- [x] `PL`, `Cockpit`, `action queue`, `개발자 집중관리`, `프로그램 액션 큐` 같은 전면 문구가 PPT에 남지 않도록 inspect로 확인한다.
- [x] 자원관리 가치는 개인 평가가 아니라 운영 참고 신호라는 경계를 포함한다.
- [x] `AI_CHANGELOG.md`와 `docs/failure-history.md`를 갱신한다.
- [x] PPT preview, inspect, 슬라이드 수, 문구 검색, documentation image test, diff hygiene을 검증한다.

## P2 - AI Use Case Technical Master Deck Rewrite

Status: Done

Goal:
AI Use Case성과 실제 기술 적용 구조가 충분히 드러나도록 결과서 PPT를 기술 상세 마스터덱으로 전면 재작성한다.

Rationale:
13장 요약본은 제출용 요약에는 가깝지만, 이 프로젝트가 가진 LLM Mapping, RAG/pgvector, source verification, Neo4j GraphRAG, AI telemetry, Resource Metrics 같은 AI 적용 구조를 충분히 보여주지 못했습니다. 사용자가 나중에 제출본을 골라낼 수 있도록 먼저 넓은 기술 상세덱을 만들고, 화면 근거와 아키텍처를 함께 보여주는 편이 더 안전합니다.

Checklist:

- [x] 13장 요약본을 전면 대체하고 47장 기술 상세 마스터덱으로 재작성한다.
- [x] Use Case 정의, 고객 Pain Point, end-to-end architecture, 데이터 흐름, 저장소/AI provider 구조를 포함한다.
- [x] LLM Mapping, 구현상태 분석, AI Progress, Risk Analysis, Resource Metrics, AI Code Review, RAG, Project Chat, GraphRAG, Knowledge Graph, AI telemetry를 각각 설명한다.
- [x] 자원관리 지표는 실제 Dashboard 하단 screenshot crop을 사용한다.
- [x] `PL`, `Cockpit`, `action queue`, `개발자 집중관리`, `프로그램 액션 큐` 같은 전면 문구가 PPT에 남지 않도록 inspect/layout으로 확인한다.
- [x] `AI_CHANGELOG.md`와 `docs/failure-history.md`를 갱신한다.
- [x] PPT preview, 슬라이드 수, AI 기술 키워드 coverage, 문구 검색, QA 검색, documentation image test, diff hygiene을 검증한다.

## P2 - AI Use Case Internal Share Deck

Status: Done

Goal:
팀 내부 공유용으로 `AI 커밋 분석 기반 프로젝트 자원 관리 서비스`를 짧게 설명하는 PPT를 만든다. 상위 폴더의 Use Case 텍스트를 기준으로 하되, 실제 앱 화면과 Application Preview의 좋은 screenshot을 함께 사용한다.

Rationale:
기존 47장 기술 상세덱은 제출·설명용으로는 충분하지만, 팀 내부에서 "이번에 어떤 AI Use Case를 만들었는지" 빠르게 공유하기에는 무겁다. 내부 공유용 덱은 Pain Point, 아키텍처, 실제 화면, 적용 AI 범위, 기대효과와 한계를 짧게 보여주는 쪽이 적합하다.

Checklist:

- [x] 상위 폴더 Use Case 텍스트와 Application Preview screenshot을 확인한다.
- [x] 내부 공유용 슬라이드 구조를 9장+부록 1장으로 정리한다.
- [x] PPTX를 생성하고 모든 슬라이드 preview를 렌더링한다.
- [x] 겹침, 잘림, 문구 톤, AI-sounding wording을 점검한다.
- [x] `AI_CHANGELOG.md`에 산출물과 검증 결과를 기록한다.

## P2 - AI Use Case Internal Share Deck Quality Rewrite

Status: Done

Goal:
`AX Use Case` 내부 공유용 PPT를 전면 보완한다. 새 덱은 실제 운영 전환 제안서가 아니라 "AI를 이용한 프로젝트 과제를 수행했고, 이런 화면과 결과가 나왔다"는 보고용 산출물로 구성한다.

Rationale:
초기 내부 공유용 덱은 짧게 요약하는 데 치우쳐 `AX Use Case` 과제를 수행했다는 인상이 약했다. 보완판은 고객 Pain Point, AI 적용 지점, 실제 화면 결과를 일반적인 Use Case PPT 흐름으로 보여주되, Project Chat 질문/답변, GraphRAG 근거, AI Code Review 결과 같은 화면 캡처를 발표 근거로 사용해야 한다. 한계 설명이나 세부 산식은 본문 중심이 아니다.

Checklist:

- [x] 기존 `outputs/ai-use-case-team-share.pptx`를 `outputs/backups/`에 백업한다.
- [x] 상위 폴더 Use Case 텍스트를 `docs/ai-use-case-brief-reference.md` 참고문서로 고정한다.
- [x] 발표 성격을 내부 `AX Use Case` 과제 결과 공유로 명확히 기록한다.
- [x] 기존 Application Preview, 47장 기술 상세덱, Use Case 참고문서에서 재사용할 근거를 고른다.
- [x] Project Chat 질문/답변과 GraphRAG 근거가 한 장 이상에서 명확히 보이게 구성한다.
- [x] AI Progress는 고객 Pain Point인 진척도 관리 불확실성을 줄이는 화면 근거로 설명하고, 세부 산식은 필요할 때만 보조 설명으로 둔다.
- [x] AI Code Review와 Risk/Resource 관점이 단순 스크린샷이 아니라 use case 흐름으로 이어지게 재배치한다.
- [x] PPTX를 다시 생성하고 PowerPoint preview/export로 전체 슬라이드를 검증한다.
- [x] `AI_CHANGELOG.md`, `docs/failure-history.md`, 필요 시 `CONTEXT.md`를 갱신한다.
- [x] AI-sounding wording과 diff hygiene을 점검한다.

## P2 - AI Use Case Internal Share Deck Aspect And Polish Pass

Status: Done

Goal:
`AX Use Case` 내부 공유용 PPT의 screenshot 비율과 발표자료 완성도를 보완한다. 특히 6페이지와 7페이지의 화면 캡처가 강제 배치로 납작해 보이는 문제를 수정하고, 추가로 어색한 슬라이드 문구·배치·이미지 crop을 점검한다.

Rationale:
전면 보완판은 흐름과 내용은 맞아졌지만, 일부 screenshot crop이 원본 비율과 다른 PPT frame에 강제로 맞춰지며 화면이 가로로 늘어나 보였다. 내부 공유용 과제 결과물은 기능 내용뿐 아니라 화면 품질도 "만든 티"를 좌우하므로, screenshot은 원본 비율을 보존하거나 target frame과 같은 비율로 crop한 뒤 삽입해야 한다.

Checklist:

- [x] 현재 `outputs/ai-use-case-team-share.pptx`를 `outputs/backups/`에 백업한다.
- [x] 6페이지와 7페이지 screenshot의 원본 crop 비율과 PPT 배치 비율을 맞춘다.
- [x] 전체 slide preview를 다시 보고 추가 개선점을 반영한다.
- [x] PowerPoint 열기와 전체 slide PNG export로 렌더링을 검증한다.
- [x] `AI_CHANGELOG.md`, `docs/failure-history.md`, `ROADMAP.md`를 갱신한다.
- [x] AI-sounding wording과 diff hygiene을 점검한다.

## P1 - Program-Level AI Progress Basis

Status: Done

Goal:
`AI Progress` 숫자를 커밋별 매핑 상태의 최고값이 아니라 프로그램 단위 `Program Implementation Status` 기준으로 표시한다. 분석 결과가 없거나 현재 관련 커밋 묶음과 맞지 않으면 확정 숫자 대신 `분석 필요` 또는 `재분석 필요`로 표시하고, 기존 Mapping 기반 0/50/100 값은 임시 참고값으로만 보여준다.

Rationale:
작은 커밋 여러 개가 합쳐져 프로그램이 완료되는 흐름에서는 커밋별 최고 상태 방식이 계속 50%에 머물 수 있다. 반대로 단일 커밋이 `구현완료`로 잘못 판단되면 전체 프로그램이 100%처럼 보일 수 있다. 관련 커밋 전체를 보는 구현상태 분석을 기준으로 삼아 AI Progress의 의미를 요구사항 단위 구현상태 신호에 맞춘다.

Checklist:

- [x] `ROADMAP.md` candidate를 active task로 승격한다.
- [x] `Program Implementation Status` 최신 여부와 AI Progress 산식을 공통 helper로 정리한다.
- [x] AI Progress/Home/Dashboard 표시에서 분석 필요 상태와 Mapping 참고값을 분리한다.
- [x] Risk/Resource Metrics가 오래된 mapping 숫자를 확정 AI 진척도로 쓰지 않도록 조정한다.
- [x] focused tests를 추가하거나 갱신한다.
- [x] `docs/ai-technical-overview.md`, `docs/engineering-decisions.md`, `AI_CHANGELOG.md`를 갱신한다.
- [x] compile/test와 문구 점검을 실행한다.

## P1 - Project Chat GraphRAG Context Injection

Status: Done

Goal:
Project Chat이 vector/RAG 근거뿐 아니라 Neo4j graph path를 답변 context와 저장 근거로 사용하게 한다.

Checklist:

- [x] 질문, 확장 쿼리, 검색된 source_file/commit 근거에서 graph seed 후보를 추출한다.
- [x] Neo4j에서 program-commit-file-class 영향 경로, class import 관계, domain summary를 조회한다.
- [x] Project Chat prompt에 graph context를 별도 섹션으로 넣고 current source 검증 정책을 유지한다.
- [x] Project Chat UI와 citation export에서 소스 근거와 그래프 관계 근거를 분리 표시한다.
- [x] Project Chat 저장 message와 AI 운영 현황 근거 추적에서 graph evidence를 확인하게 한다.
- [x] Focused tests를 추가한다.
- [x] 관련 AI/사용자-facing/architecture/decision documentation을 갱신한다.
- [x] Compile/test verification을 실행한다.
- [x] `AI_CHANGELOG.md`를 갱신한다.

## P1 - Knowledge Graph Freshness And Incremental Neo4j Sync

Status: Done

Goal:
Neo4j graph read model이 어떤 Git HEAD와 분석 데이터 기준으로 만들어졌는지 표시하고, Git 변경 이후 바뀐 파일/매핑만 반영하는 증분 동기화를 제공한다.

Rationale:
현재 `Neo4j 동기화`는 정확하지만 프로젝트 단위 전체 graph를 다시 만들기 때문에 대형 저장소에서는 비용이 커질 수 있다. 또한 Git Sync 이후 graph가 최신인지 사용자가 바로 알기 어렵다. 이 작업은 "한 번 만든 그림"이 아니라 실제 Git 변경 흐름을 따라가는 graph read model로 발전시키는 범위다.

Design split:

- `current source graph`: 현재 checkout 기준 파일, class, import, domain 관계. 소스가 바뀌면 관계를 끊고 다시 만든다.
- `historical git graph`: 과거 commit, commit file, diff 이력. 현재 파일이 삭제되어도 Git 이력 근거로 보존한다.
- `analysis graph`: program mapping처럼 PostgreSQL 분석 결과에서 온 관계. DB 상태에 맞춰 upsert/delete한다.

Checklist:

- [x] PostgreSQL graph sync state metadata를 Alembic migration으로 추가한다.
- [x] Knowledge Graph 화면에 Repo HEAD, DB sync HEAD, Graph sync HEAD, stale 여부를 표시한다.
- [x] 전체 Neo4j sync 성공/실패 metadata를 저장한다.
- [x] 최신 변경분만 반영하는 incremental Neo4j sync를 추가한다.
- [x] 변경 파일 current source 관계와 program mapping edge removal 규칙을 구현한다.
- [x] Knowledge Graph UI action을 `최신 변경분만 Neo4j 반영`과 `전체 재동기화`로 구분한다.
- [x] metadata, stale detection, modified/deleted/renamed/non-source, mapping edge refresh 중심 테스트를 추가한다.
- [x] architecture, AI technical overview, setup/operations, feature guide, engineering decision documentation을 갱신한다.
- [x] Compile/test/diff verification을 실행한다.
- [x] `AI_CHANGELOG.md`를 갱신한다.

## P1 - AI Operations Graph Status

Status: Done

Goal:
`AI 운영 현황`에서 LLM, embedding, source/vector 상태뿐 아니라 Neo4j graph와 Project Chat GraphRAG 준비 상태를 함께 확인하게 한다.

Rationale:
Project Chat이 GraphRAG 보조 근거를 사용할 수 있게 되었고, Knowledge Graph가 Repo HEAD/DB Sync HEAD/Graph HEAD 최신성을 갖게 되었지만, 운영자는 아직 AI 운영 현황 첫 화면에서 graph 계층이 준비되어 있는지 한눈에 보기 어렵다. 이 작업은 GraphRAG가 왜 사용 가능하거나 준비 필요 상태인지 AI 운영 상태판에서 설명하는 범위다.

Checklist:

- [x] AI 운영 상태 row에 Neo4j enabled/connected/database 상태를 추가한다.
- [x] Knowledge Graph node/edge count, 마지막 sync, stale 여부를 표시한다.
- [x] Neo4j 저장 graph readback 성공/실패와 오류 메시지를 표시한다.
- [x] Project Chat GraphRAG 최근 사용 상태와 evidence count를 표시한다.
- [x] Knowledge Graph 화면으로 이동하는 shortcut action을 추가한다.
- [x] 관련 tests를 추가/갱신한다.
- [x] 사용자-facing/AI/architecture documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/diff verification을 실행한다.

## P2 - Knowledge Graph Exploration UI

Status: Done

Goal:
사용자가 프로그램, class, domain, commit을 기준으로 Neo4j 관계를 탐색할 수 있게 한다.

Rationale:
Knowledge Graph는 저장 graph 기준 클래스 관계도와 영향 경로를 보여주지만, 사용자가 특정 프로그램, class, domain, commit을 선택해 그 주변 관계만 좁혀 보는 흐름은 아직 약하다. 대형 graph 전체를 그리는 대신 제한된 관계 path와 node detail을 표 중심으로 제공해 Neo4j 적용 가치를 더 직접 확인하게 한다.

Checklist:

- [x] 프로그램 기준 관련 commit/file/class/domain path 조회를 추가한다.
- [x] class 기준 import 관계, 포함 file, 연결 program 조회를 추가한다.
- [x] domain 기준 관련 program/file/class/commit 묶음 조회를 추가한다.
- [x] commit 기준 mapping program, touched file, impacted class 조회를 추가한다.
- [x] node detail panel에 node type, label, properties, related count를 표시한다.
- [x] path depth 또는 relationship type filter를 제공한다.
- [x] Neo4j read query tests를 추가한다.
- [x] Knowledge Graph UI와 documentation, `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/diff verification을 실행한다.

## P2 - Project-Level AI Quality Scorecard

Status: Done

Goal:
sample project 전용 점검을 실제 프로젝트에서도 쓸 수 있는 AI 품질 상태판으로 확장한다.

Rationale:
기존 `품질 점검`은 현재 프로젝트 ID를 받지만 "결과가 존재하는지"와 sample project 중심 조치 문구에 가깝다. 실제 AX Use Case에서는 프로젝트별 Mapping 품질, Project Chat 근거 사용률, PL Briefing fallback/validation, Code Review 결과 분포, Knowledge Graph 신선도를 한 화면에서 설명할 수 있어야 한다.

Checklist:

- [x] Mapping 판단불가 비율, low relevance 비율, 짧은 reason, feedback pending count를 계산한다.
- [x] Project Chat verified source 사용률, insufficient-evidence 비율, stale/invalid excluded count를 계산한다.
- [x] PL Briefing fallback/repair 발생률, 최근 provider/model, validation status를 표시한다.
- [x] Code Review 최근 대상 commit, risk level 분포, 저장 결과 count를 표시한다.
- [x] Knowledge Graph class/import 추출 수, impact path 수, graph stale 여부를 표시한다.
- [x] pass/warn/fail 상태와 다음 조치 이동 버튼을 제공한다.
- [x] 관련 tests를 추가/갱신한다.
- [x] 사용자-facing/AI/architecture documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/diff verification을 실행한다.

## P2 - Local LLM Verification Routine

Status: Done

Goal:
mock이 아닌 local LLM/embedding provider로 주요 AI 기능을 실제 실행했다는 증거를 반복 가능하게 만든다.

Rationale:
`AI 운영 현황`은 provider/model/fallback/telemetry를 보여주지만, 팀원이 어떤 명령으로 local OpenAI-compatible LLM을 켜고 주요 기능을 실제 실행했는지 반복 가능한 루틴은 아직 약하다. AX Use Case에서는 "AI를 실제로 썼다"는 설명이 화면 상태와 실행 기록으로 이어져야 하므로, mock 검증과 live local provider 검증을 명확히 분리한다.

Checklist:

- [x] LM Studio 또는 OpenAI-compatible local endpoint 기준 점검 절차를 문서화한다.
- [x] Mapping, Project Chat, PL Briefing, Code Review 중 선택한 2~4개 기능을 실행하는 CLI 루틴을 추가한다.
- [x] provider/model/base URL, invocation telemetry, fallback 여부를 결과로 기록한다.
- [x] `AI 운영 현황`에서 최근 local provider live verification 결과를 요약한다.
- [x] local LLM이 없으면 mock/fallback 검증과 live 검증을 분리해서 표시한다.
- [x] 외부 유료 API를 CI에서 호출하지 않도록 테스트는 mock DB/telemetry 기준으로 작성한다.
- [x] 사용자-facing/AI/architecture documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/diff verification을 실행한다.

## P2 - Git Sync Follow-Up Action Orchestrator

Status: Done

Goal:
Git Sync 이후 사용자가 실행해야 할 RAG, embedding, Mapping, Risk Analysis, Neo4j 갱신 작업을 한 흐름으로 안내한다.

Rationale:
Git Sync는 commit/diff metadata를 DB에 수집하지만, 그 뒤에 현재 소스 인덱싱, embedding, Mapping, Risk Analysis, Knowledge Graph 갱신을 따로 실행해야 AI 화면이 최신 근거를 사용한다. 기능이 늘어나면서 사용자가 다음 단계를 기억해야 하는 부담이 커졌으므로, Git Sync 화면에서 현재 상태 기준 권장 순서와 재시작 가능한 action을 보여준다.

Checklist:

- [x] Git Sync 완료 후 changed commit/file count와 현재 DB/HEAD 상태를 후속 작업 판단에 사용한다.
- [x] 다음 작업 후보를 source incremental indexing, embedding missing chunks, Mapping, Risk Analysis, Neo4j sync 기준으로 산출한다.
- [x] 각 작업의 준비 상태, 예상 소요, 비용/부하 주의 문구를 표시한다.
- [x] 권장 순서와 나중에 해도 되는 항목을 구분한다.
- [x] 실패/부분 완료 상태에서 재시작 가능한 화면 이동 또는 명시 실행 action을 제공한다.
- [x] 관련 tests를 추가/갱신한다.
- [x] 사용자-facing/architecture/operations documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/diff verification을 실행한다.

## P2 - Neo4j Production Hardening

Status: Done

Goal:
대형 프로젝트와 장시간 운영에서 Neo4j 동기화가 안정적으로 동작하도록 보강한다.

Rationale:
Knowledge Graph가 Project Chat GraphRAG와 AI 운영 상태의 근거가 되면서, Neo4j 동기화는 단순 preview 기능이 아니라 운영 근거 freshness를 유지하는 작업이 되었다. 대형 저장소에서는 단일 transaction에 모든 node/edge를 쓰면 transaction memory, timeout, 일시적 연결 실패에 취약하므로 batch write, retry, partial failure reporting, 복구 안내가 필요하다.

Checklist:

- [x] node/edge write batch size를 환경 설정으로 조절할 수 있게 한다.
- [x] full sync와 incremental sync write를 batch 단위 transaction으로 분할한다.
- [x] transient failure retry/backoff를 적용하고 retry metadata를 결과에 남긴다.
- [x] partial failure 시 성공/실패 batch, written node/edge count, 복구 안내를 표시한다.
- [x] Neo4j health/readiness 확인과 summary/readback 실패 메시지를 운영자가 이해할 수 있게 유지한다.
- [x] cleanup 실패 시 PostgreSQL 작업을 막지 않는 best-effort 정책을 유지하고 문서화한다.
- [x] backup/restore 또는 volume reset 운영 안내를 추가한다.
- [x] batch/retry/partial failure 중심 tests를 추가한다.
- [x] 사용자-facing/architecture/operations/decision/failure-history 검토와 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/diff verification을 실행한다.

## P3 - Source Parser Accuracy Expansion

Status: Done

Goal:
정규식 기반 Java class/import 추출의 한계를 줄이고 Knowledge Graph 품질을 높인다.

Rationale:
Knowledge Graph와 Project Chat GraphRAG는 Java class/import 관계를 근거로 사용한다. 현재 parser는 단순 정규식 기반이라 annotation type, static import, nested type, 주석/문자열 안의 가짜 선언, generated/build/test fixture 제외 같은 현실적인 SI Java project 패턴에서 graph 품질이 흔들릴 수 있다. compiler-level semantic analysis로 가기 전, 경량 parser의 누락과 오탐을 줄이고 skip/warning을 화면에 노출한다.

Checklist:

- [x] Java 주석/문자열을 제거한 뒤 package/import/type 선언을 추출해 오탐을 줄인다.
- [x] annotation type, static import, record/interface/enum/class, nested member type qualified name을 보강한다.
- [x] generated source, build output, test fixture Java 파일 제외 규칙과 skip count를 추가한다.
- [x] type 선언을 찾지 못한 Java 파일 수를 Knowledge Graph 준비 경고로 표시한다.
- [x] full/incremental graph payload와 GraphRAG seed 추출이 새 parser 결과를 사용하게 한다.
- [x] parser edge case와 graph payload warning tests를 추가한다.
- [x] 사용자-facing/AI/architecture documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/diff verification을 실행한다.

## P3 - Graph-Aware Project Chat Question Templates

Status: Done

Goal:
사용자가 RAG와 GraphRAG가 잘 답할 수 있는 질문을 쉽게 시작하도록 Project Chat 질문 템플릿을 제공한다.

Rationale:
Project Chat은 verified source evidence와 Neo4j graph evidence를 함께 사용할 수 있지만, 처음 사용하는 사용자는 어떤 질문이 graph 관계 근거를 잘 끌어내는지 알기 어렵다. Project Chat 화면에서 graph 준비 상태를 확인하고, 프로그램/커밋/class/domain 관계 질문을 바로 시작할 수 있게 해 GraphRAG 적용 가치를 더 드러낸다.

Checklist:

- [x] Project Chat 화면에 graph-aware 질문 템플릿 목록을 추가한다.
- [x] Knowledge Graph freshness가 `latest`일 때만 graph 템플릿 실행 버튼을 활성화한다.
- [x] graph가 stale/missing/skipped/failed이면 현재 상태와 보정 경로를 안내한다.
- [x] 템플릿 버튼을 누르면 해당 질문을 현재 chat session에 사용자 질문으로 실행한다.
- [x] 템플릿 문구가 프로그램/commit/file/class/domain 관계를 자연스럽게 유도하도록 정리한다.
- [x] 템플릿 상태 helper tests를 추가한다.
- [x] 사용자-facing/AI/architecture documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/UI verification을 실행한다.

## P3 - Graph-Aware Weekly Report

Status: Done

Goal:
주간 점검 보고서에 Neo4j impact path와 AI 근거 관계를 포함한다.

Rationale:
AI 운영 현황의 주간 보고서는 Radar, PL Briefing, Risk, AI Progress, telemetry를 한 파일로 묶지만, GraphRAG가 실제로 어떤 프로그램-커밋-파일-class 관계를 근거로 삼는지는 아직 별도 화면을 열어야 확인할 수 있다. 보고서에 graph freshness, 주요 impact path, 위험 프로그램별 graph 근거, Project Chat GraphRAG 사용 여부를 함께 넣어 AI와 Knowledge Graph 적용 가치를 한 문서에서 설명하게 한다.

Checklist:

- [x] 보고서에 Knowledge Graph freshness, node/edge summary, class/import/impact path 요약을 추가한다.
- [x] 주요 변경 commit -> program -> file -> class path를 Markdown table로 포함한다.
- [x] 미해결 risk와 AI Progress gap 프로그램별 graph path 근거를 연결한다.
- [x] provider/model/fallback/GraphRAG 사용 여부를 report metadata로 남긴다.
- [x] Neo4j가 비활성/실패/미저장 상태여도 보고서 생성이 실패하지 않게 한다.
- [x] focused tests를 추가/갱신한다.
- [x] 사용자-facing/AI/architecture documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/UI verification을 실행한다.

## P3 - First-Run And Empty-State Polish

Status: Done

Goal:
기능이 많아진 앱을 처음 보는 사람이 다음 행동을 잃지 않도록 빈 상태와 복구 안내를 정리한다.

Rationale:
Project, Git, 프로그램, Mapping, vector, Neo4j 중 하나라도 비어 있으면 여러 화면이 각각 다른 경고를 보여준다. 새 사용자는 어떤 순서로 조치해야 하는지 알기 어렵고, AI 운영 현황도 준비 상태는 보이지만 처음 실행 흐름을 한눈에 묶어주지는 않는다. Home과 AI 운영 현황에서 같은 기준의 다음 준비 작업을 보여줘 처음 등록부터 GraphRAG 준비까지 이어지는 경로를 더 분명하게 만든다.

Checklist:

- [x] 프로젝트 없음, Git 없음, 프로그램 없음, Mapping 없음, source/vector 없음, Neo4j 미연결 상태별 안내를 계산한다.
- [x] Home의 `다음 작업`을 상태/현재 값/이동 대상이 있는 준비 작업 목록으로 개선한다.
- [x] AI 운영 현황의 운영 준비 탭에 같은 준비 작업 목록과 화면 이동 action을 추가한다.
- [x] 설정 문제 발생 시 관련 setup 문서나 화면으로 이어지는 설명을 제공한다.
- [x] focused tests를 추가한다.
- [x] 사용자-facing/architecture/engineering decision documentation과 `AI_CHANGELOG.md`를 갱신한다.
- [x] Compile/test/UI verification을 실행한다.

## P2 - Sample Project First-Run Button Guide

Status: Done

Goal:
기능과 옵션을 처음 접하는 사용자가 샘플 프로젝트 준비부터 Project Chat 실행까지 필요한 메뉴와 버튼만 순서대로 따라갈 수 있는 짧은 가이드를 제공한다.

Rationale:
기존 사용 가이드는 각 기능의 의미와 전체 제품 흐름을 설명하지만, 설정과 분석 옵션이 늘어나면서 처음 사용하는 사람은 지금 눌러야 할 버튼과 건너뛰어도 되는 옵션을 구분하기 어렵다. 현재 준비된 샘플을 바로 사용하는 경로와 빈 DB에서 다시 만드는 경로를 분리하고, 각 단계의 완료 숫자를 함께 제시해야 시행착오를 줄일 수 있다.

Checklist:

- [x] 현재 준비된 `Sample Shop Demo`에서 Project Chat을 바로 사용하는 최소 경로를 적는다.
- [x] 빈 DB에서 프로젝트 등록, Git 수집, 산출물 업로드, Mapping, Risk, RAG, Knowledge Graph를 준비하는 메뉴와 버튼명을 확인한다.
- [x] 각 단계의 기대 건수와 필수/선택 옵션을 구분한다.
- [x] README와 기존 사용 가이드에서 새 문서로 연결한다.
- [x] `AI_CHANGELOG.md`를 갱신한다.
- [x] 링크, 현재 상태 수치, 사용자-facing 문구와 whitespace를 검증한다.

## P2 - Artifact Sample Excel Downloads

Status: Done

Goal:
산출물 관리의 개발자 목록, 프로그램 목록, 개발계획, 표준용어/표준단어 화면에서 Sample Shop 기준 Excel을 바로 내려받아 기존 업로드 검증 흐름을 실행할 수 있게 한다.

Rationale:
현재 샘플 Excel은 별도 샘플 프로젝트의 `advisor_uploads` 경로에만 있어 사용자가 파일 위치와 업로드 순서를 먼저 알아야 한다. 각 `Excel 업로드` 탭에서 해당 샘플 파일을 제공하면 로컬 경로를 모르는 사용자도 실제 파일 업로드, 미리보기, 검증, 저장 절차를 같은 화면에서 확인할 수 있다. 샘플 데이터는 자동 저장하지 않고 사용자가 내려받은 뒤 기존 검증 절차를 거치게 해 현재 프로젝트 데이터가 의도치 않게 바뀌는 것을 막는다.

Checklist:

- [x] Sample Shop 개발자, 프로그램, 개발계획, 표준용어 dataset을 앱에서 Excel로 생성한다.
- [x] 각 산출물 `Excel 업로드` 탭에 용도가 분명한 샘플 Excel 다운로드 버튼을 추가한다.
- [x] 개발계획 샘플의 선행 업로드 순서를 안내한다.
- [x] 생성 파일의 column, row, 핵심 시나리오를 회귀 test로 검증한다.
- [x] 사용자 가이드, engineering decision, `AI_CHANGELOG.md`를 갱신한다.
- [x] focused test, compileall, 전체 test를 실행한다.

Related AI Change Log: `산출물 관리 샘플 Excel 다운로드`

## P2 - Session-Scoped Q&A Documentation Mode

Status: Done

Goal:
새 Codex 세션에서도 사용자가 `qna ON`과 `qna OFF`만으로 시연 Q&A 기록 모드를 명시적으로 켜고 끌 수 있게 하고, 활성화 중에는 `docs/qna.md`를 중복 없이 주제별로 정리한다.

Rationale:
시연 준비 중에는 질문에 답하는 것과 답변을 문서에 남기는 작업이 반복된다. 이 동작을 매 세션마다 긴 prompt로 다시 설명하면 저장 위치, 다른 파일의 read-only 범위, 유사 질문 통합 여부가 달라질 수 있다. 저장소 지침에 session-scoped toggle과 문서 정리 기준을 두면 사용자는 짧은 명령으로 같은 workflow를 재현할 수 있고, 일반 개발 작업에는 Q&A 전용 제한이 자동 적용되지 않는다.

Checklist:

- [x] `AGENTS.md`에 기본 `OFF`, `qna ON`, `qna OFF`의 session-scoped 동작을 정의한다.
- [x] Q&A 모드에서 `docs/qna.md` 외 파일을 read-only로 다루고, 예외 변경은 명시적 허용을 요구하게 한다.
- [x] 유사 질문 검색, 기존 답변 통합·수정·보완, 주제별 배치 원칙을 정의한다.
- [x] 실제 동작과 한계를 `docs/qna.md`에 설명한다.
- [x] agent policy 결정과 관련 RAG 조사 교훈을 durable 문서에 기록한다.
- [x] 사용자-facing 문구, UTF-8, Markdown whitespace와 변경 범위를 검증한다.
- [x] `AI_CHANGELOG.md`를 갱신한다.

Related AI Change Log: `Session-scoped 시연 Q&A mode 추가`

## Candidate Tasks

These items are known follow-up concerns, not approved implementation tasks. Keep them here when the team wants to preserve the reasoning without committing to scope yet. When a candidate becomes active work, move it into the priority overview, add a dedicated roadmap section with checklist, and set it to `In Progress`.

아래 항목은 아직 승인된 구현 작업이 아니라, 다음 세션에서 바로 범위를 고를 수 있도록 보관하는 후보입니다. 작업을 시작할 때는 해당 후보를 `Priority Overview`로 승격하고, 별도 `P* - ...` 작업 섹션을 만든 뒤 `In Progress`로 바꿉니다.

| Priority | Area | Candidate | Why It Matters |
|---|---|---|---|
| P1 | Data Model / RAG | Enforce vector uniqueness per embedding profile | 현재 `vector_items`에는 `(chunk_id, embedding_model)` unique constraint가 없어 같은 profile의 re-embedding worker가 겹치면 중복 검색 row가 생길 수 있다. Alembic migration, 기존 duplicate 정리, conflict-safe insert, concurrent 회귀 test를 함께 설계해야 한다. |
| P1 | RAG / Reliability | Align unchanged source chunks with incremental indexed HEAD | 현재 source verification은 `indexed_head_hash`가 현재 `Repo HEAD`와 다르면 content hash 비교 전에 stale로 판정하지만, 증분 갱신은 변경된 path의 chunk만 새 HEAD로 기록한다. 변경되지 않은 파일의 기존 chunk를 content 검증 후 새 HEAD로 승격할지, file-level snapshot identity로 바꿀지 결정하고 회귀 test를 추가해야 한다. |
| P2 | AI Verification | Add non-mutating local AI verification mode | 현재 `run_local_ai_verification.py`의 PL Briefing, Project Chat, Code Review, Mapping은 정상 결과를 저장하므로 연결/schema만 점검해도 최신 시연 결과가 바뀔 수 있다. rollback 가능한 probe와 저장형 검증을 명시적으로 분리해야 한다. |
| P2 | Sample Data / Demo Quality | Additional multi-release evidence scenarios | 앞으로 샘플을 더 키울 때는 release rehearsal, incident postmortem, operator handoff처럼 실제 PL 검토에서 묻는 증거를 단계적으로 추가한다. 단순 commit 수 증량은 지양한다. |
| P2 | Test / Runtime Reliability | pgvector dimension preflight and failure-safe DB test cleanup | 기존 DB column 차원과 현재 `PGVECTOR_DIMENSION`이 다르면 DB-backed test와 RAG 실행이 늦게 실패한다. 구현을 시작할 때 read-only preflight 범위와 transaction 실패 후에도 임시 행을 정리하는 test fixture를 함께 설계한다. |

## P2 - Source-First Sample Project And Demo Verification Guide

Status: Done

Goal:
샘플 프로젝트 내부의 AI 판단 근거를 Markdown 설명 파일이 아니라 Java source, MyBatis XML, test/probe class, Excel upload 데이터, Git diff만으로 읽히게 재설계한다. 기존 `Application Preview` screenshot은 실제 local LLM/Neo4j 조건으로 재검증되기 전까지 덮어쓰지 않는다.

Rationale:
샘플 보강의 목적은 mock output이나 정답 문서로 결과를 꾸미는 것이 아니라, 제품 기능이 실제 local LLM과 graph/RAG 근거를 읽었을 때 설득력 있는 판단을 만들 수 있게 하는 것이다. 기존 preview screenshot은 이미 실제 결과 증거로 쓰이고 있으므로, 새 샘플 검증이 준비되지 않은 상태에서 훼손되면 안 된다.

Checklist:

- [x] 기존 `Application Preview` screenshot capture 조건과 실제 local LLM 검증 기준을 확인한다.
- [x] 샘플 프로젝트 내부 `docs/...` evidence 의존을 source/test/XML evidence로 전환한다.
- [x] 표준용어 Excel dataset을 새 source identifiers와 맞춘다.
- [x] 앱 저장소에 기능 테스트용 질문/리뷰 대상 가이드를 추가한다.
- [x] sample generation tests와 설계 문서를 source-first 기준으로 갱신한다.
- [x] 기본 샘플 경로를 덮어쓰기 전에 별도 target path에서 생성과 Git history shape를 검증한다.
- [x] 실제 local LLM/embedding/Neo4j 검증과 screenshot 갱신 여부를 분리해 기록한다.
- [x] `AI_CHANGELOG.md`를 갱신하고 commit/push한다.

## P2 - Korean Project Chat Class Relationship Evidence Screenshot

Status: Done

Goal:
Project Chat GraphRAG screenshot이 영어 질문이나 impact path 중심 화면이 아니라, 한국어 질문과 `PaymentService -> OrderMapper` class import 관계를 더 자연스럽게 보여주도록 한다.

Rationale:
GraphRAG의 demo 가치는 커밋 경로만 많이 보이는 화면보다 class import, program impact, domain summary가 함께 보여질 때 더 잘 전달된다. 실제 local LLM 결과 원칙은 유지하되, 질문과 evidence 선택이 화면에서 관계를 읽기 쉽게 해야 한다.

Checklist:

- [x] GraphRAG evidence 선택에서 `class_import`, `impact_path`, `domain_summary`가 균형 있게 남도록 조정한다.
- [x] Project Chat 질문을 한국어로 다시 실행하고 실제 `local_openai` 응답을 저장한다.
- [x] Project Chat answer/GraphRAG screenshot capture 조건을 한국어 질문과 `class_import` 근거 기준으로 갱신한다.
- [x] `docs/ai-technical-overview.md`, screenshot, tests, `AI_CHANGELOG.md`를 갱신한다.

## P2 - Project Chat Real Local LLM Screenshot Evidence

Status: Done

Goal:
Project Chat과 GraphRAG screenshot도 mock/fallback 결과가 아니라 실제 local LLM과 최신 Neo4j graph evidence로 만들어졌음을 화면과 캡처 조건에서 확인할 수 있게 한다.

Rationale:
AI Code Review만 provider/fallback을 표시하면 Project Chat, GraphRAG, 다른 AI 화면의 스크린샷 신뢰성은 여전히 약하다. AI 결과가 보이는 화면은 모두 실제 provider, fallback 여부, 근거 최신성을 검증할 수 있어야 한다.

Checklist:

- [x] 최신 샘플 repo HEAD로 Git Sync, chunk, local embedding, Mapping, Risk/AI Progress를 다시 실행한다.
- [x] Neo4j graph sync를 `NEO4J_ENABLED=true`로 실행해 graph freshness가 latest인지 확인한다.
- [x] Project Chat 답변에 provider/model/fallback metadata를 저장하고 화면에 표시한다.
- [x] Project Chat answer와 GraphRAG screenshot capture 조건에 `local_openai`, `fallback=False`, mock/fallback 금지를 추가한다.
- [x] 실제 local LLM Project Chat과 GraphRAG screenshot을 캡처한다.
- [x] focused tests와 `AI_CHANGELOG.md`를 갱신한다.

## P2 - Scenario-Designed Sample Evidence For Rich AI Outputs Across Features

Status: Done

Goal:
샘플 프로젝트를 단순 데이터량이 아니라 실제 local LLM이 Code Review, Project Chat, Risk/AI Progress, PL Briefing에서 풍부한 판단을 낼 수 있는 source, diff, 업무 문서, 미완료 evidence 중심으로 보강한다.

Rationale:
목 결과를 그럴듯하게 만드는 것은 제품 검증이 아니다. AI 기능이 설득력 있게 보이려면 샘플 프로젝트의 commit, source, docs, plan gap 자체가 리뷰할 만한 사건과 근거를 제공해야 한다. 이 작업은 LLM output을 고정하지 않고, local LLM이 읽을 수 있는 판단 재료를 설계해 데모 품질을 높이는 범위다.

Checklist:

- [x] Candidate task를 active Roadmap task로 승격한다.
- [x] AI Code Review가 읽을 high-risk commit diff와 설명 문서를 더 명확하게 만든다.
- [x] Project Chat/RAG가 답할 수 있는 업무 규칙, demo question, evidence index를 보강한다.
- [x] Risk Analysis와 AI Progress가 plan/source gap을 구분할 수 있는 coupon/settlement evidence를 보강한다.
- [x] PL Briefing이 요약할 수 있는 release readiness, 운영 handoff, 남은 제한 문서를 보강한다.
- [x] sample generation tests를 업데이트한다.
- [x] 샘플 저장소를 재생성해 commit count, 최신 날짜, 핵심 파일을 검증한다.
- [x] 관련 설계 문서와 `AI_CHANGELOG.md`를 갱신한다.

## P2 - Real Local LLM Demo Evidence Correction

Status: Done

Goal:
Application Preview와 검증 산출물이 mock provider 결과를 실제 AI 분석처럼 보이지 않게 바로잡고, AI Code Review를 포함한 데모 화면은 mock이 아닌 local LLM 실행 결과만 사용한다.

Rationale:
사용자는 샘플 프로젝트 데이터를 기능별 LLM 판단 재료로 풍부하게 설계하자는 의도를 밝혔는데, 이전 작업은 mock provider가 샘플 diff를 읽은 것처럼 deterministic 결과를 만들고 이를 Application Preview screenshot에 사용했다. 이는 실제 local LLM 분석 증거가 아니며, 제품 검증 신뢰를 떨어뜨린다. 데모용 데이터는 LLM이 판단할 사건을 제공해야 하지만, 결과 자체는 실제 local LLM invocation과 telemetry로 남아야 한다.

Checklist:

- [x] AI Code Review mock/default 결과 enrichment와 screenshot preseed를 제거한다.
- [x] 실제 local LLM으로 샘플 AI Code Review commit을 실행하고 telemetry/fallback 상태를 확인한다.
- [x] 실제 local LLM 결과로 Application Preview AI Code Review screenshot을 갱신한다.
- [x] Failure History에 mock 결과를 실제 분석처럼 보이게 만든 실수를 기록한다.
- [x] 샘플 프로젝트 확장은 별도 scenario-designed sample evidence 작업으로 남긴다.
- [x] Focused tests, screenshot verification, diff check를 실행한다.
- [x] `AI_CHANGELOG.md`를 갱신한다.

## P2 - AI Code Review Demo Evidence And Preview Screenshot

Status: Done

Goal:
Application Preview의 AI Code Review 화면이 대상 선택만 보여주는 상태를 벗어나, 샘플 프로젝트의 의도된 risky/refactoring commit을 기반으로 실제 review finding과 제안이 보이는 결과 화면을 보여준다.

Rationale:
AI Code Review는 단순 데이터량보다 리뷰할 만한 diff와 commit message가 중요하다. 샘플 프로젝트에는 bug-introducing payment commit과 dashboard cross-module commit이 이미 있지만, preview screenshot은 그 근거를 풍부한 결과로 드러내지 못했다. 이 작업은 처음에 mock provider 보강으로 잘못 구현되었고, `Real Local LLM Demo Evidence Correction`에서 실제 local LLM 결과만 데모 증거로 쓰도록 바로잡았다.

Checklist:

- [x] AI Code Review 결과 화면이 저장된 review result의 finding, 영향, 제안 수정을 보여주도록 보강한다.
- [x] 결과 화면을 캡처할 수 있도록 screenshot automation을 갱신한다.
- [x] Application Preview 문구와 screenshot을 결과 중심으로 갱신한다.
- [x] 샘플 설계 문서의 AI Code Review commit quality 기준과 preview 흐름을 맞춘다.
- [x] Focused tests와 screenshot verification을 실행한다.
- [x] `AI_CHANGELOG.md`를 갱신한다.

## P1 - AI 검증 Trace View

Status: Done

Goal:
Show how AI-facing results were produced: input summary, retrieved evidence, provider/model, fallback status, raw response metadata, and stored output.

Checklist:

- [x] Add a read-only evidence trace surface for PL Briefing, Mapping, Project Chat, and AI Code Review.
- [x] Mask or summarize raw payloads so the view is useful without exposing unnecessary prompt text.
- [x] Link trace data to stored model/provider/fallback metadata.
- [x] Document and verify the trace surface.

## P1 - AI Readiness Cockpit

Status: Done

Goal:
Give operators a single pass/warn/fail view for DB, Git, sample data, LLM, embedding, source index, vectors, and recent AI outputs.

Checklist:

- [x] Add readiness checks for project, Git sync, program/commit counts, local LLM/embedding configuration, source index, vectors, risk/progress, and saved PL Briefing.
- [x] Show concise remediation hints for warning/fail states.
- [x] Document and verify the readiness cockpit.

## P1 - Sample Project AI Evaluation Scorecard

Status: Done

Goal:
Evaluate stored sample project AI outputs against expected analysis signals so AI quality is visible as pass/partial/fail status.

Checklist:

- [x] Add scorecard checks for Mapping, AI Progress, Risk Analysis, RAG/Project Chat evidence, Code Review, PL Briefing, and AI Resource Radar.
- [x] Show expected signal, observed value, status, and follow-up action.
- [x] Document and verify the scorecard.

## P1 - Strict Structured-Output Validation And Retry

Status: Done

Goal:
Make PL Briefing structured output more reliable by validating required sections, retrying repair once when useful, and recording fallback reasons.

Checklist:

- [x] Validate PL Briefing JSON shape before rendering.
- [x] Add one repair retry for malformed non-mock LLM responses.
- [x] Store validation status, repair attempt, and fallback reason in telemetry/evidence.
- [x] Add tests for valid, repaired, and fallback paths.

## P2 - Exportable Weekly AI Report

Status: Done

Goal:
Create a reusable Markdown report that combines Dashboard Radar, latest PL Briefing, Risk Analysis, AI Progress gaps, and key citations for weekly PL review.

Checklist:

- [x] Add a report generation service for the current project.
- [x] Add a download action from the AI evidence surface.
- [x] Include assumptions and limitations in the generated report.
- [x] Document and verify report output.

## P2 - AI Invocation Telemetry

Status: Done

Goal:
Track AI invocation provider/model, latency, prompt/response length, status, error, and fallback use so local AI operation is observable.

Checklist:

- [x] Add `ai_invocation_logs` schema and service.
- [x] Record telemetry for PL Briefing and high-value AI calls where project context is available.
- [x] Include telemetry summary and recent call table in the AI evidence surface.
- [x] Include reset/delete lifecycle cleanup, docs, migration guidance, and tests.

## P1 - AI Validation Action Cockpit

Status: Done

Goal:
Make AI 검증 useful as an AI validation cockpit by highlighting the most urgent readiness/quality gaps first and letting the operator run core AI preparation actions from the same screen.

Rationale:
AI 검증 already proves that Mapping, RAG, PL Briefing, scorecard, and telemetry exist, but the first view still looks like a passive evidence table. For an AX Use Case review, the screen should show AI readiness at a glance and make the next AI action obvious when a warning or failure is visible.

Checklist:

- [x] Show pass/warn/fail summary metrics and warning/fail-first tables for readiness and scorecard rows.
- [x] Add shortcut actions for Mapping, Risk Analysis, PL Briefing, and source search readiness.
- [x] Update user-facing documentation and Application Preview screenshot.
- [x] Run focused tests and UI screenshot verification.

## P2 - Product Wording Cleanup

Status: Done

Goal:
Keep product-facing language focused on validation, operating readiness, and review workflows instead of event-oriented wording.

Rationale:
The application should read like an AX product/workflow tool, not a one-off presentation artifact. Product docs and screens should describe what users prepare, verify, and operate.

Checklist:

- [x] Replace event-oriented Korean wording in UI, services, docs, automation text, and recent change records.
- [x] Refresh affected Application Preview screenshot.
- [x] Verify no remaining Korean event-oriented wording is present in tracked text files.
- [x] Run focused tests and documentation checks.

## P2 - AI Validation Menu Purpose Cleanup

Status: Done

Goal:
Make the AI validation area explain why it exists: checking whether AI-generated analysis is grounded, traceable, and operationally ready.

Rationale:
The current English menu label can read like an internal artifact bucket. The product surface should make it clear that this area is the control point for AI analysis evidence, model/provider state, fallback behavior, scorecard status, reports, and telemetry.

Checklist:

- [x] Rename the user-facing menu and tab copy to product-facing AI validation wording.
- [x] Remove the remaining internal validation-stage abbreviation from tracked project text and code identifiers.
- [x] Update AI validation purpose in user-facing and technical documentation.
- [x] Refresh the Application Preview screenshot and verification text.
- [x] Run text search, focused tests, screenshot capture, and full test suite.

## P2 - AI Operations Status Menu

Status: Done

Goal:
Rename the AI validation surface into an operations-oriented status area and make connected LLM/embedding configuration visible before the detailed evidence tabs.

Rationale:
`AI 검증` explained the purpose more clearly than the old English label, but it can still read like an internal inspection task. For a PL or reviewer, the first question is whether AI is currently connected and what model/configuration is producing the results. The menu should therefore read as a status surface, not only as a validation artifact list.

Checklist:

- [x] Rename the user-facing menu/title to `AI 운영 현황`.
- [x] Add a top-level connected AI summary for LLM, embedding, recent invocation, and search readiness.
- [x] Update user-facing and technical documentation to explain the status surface.
- [x] Refresh the Application Preview screenshot and capture criteria.
- [x] Run focused tests, screenshot capture, text search, and diff checks.

## P1 - Neo4j Knowledge Graph Foundation

Status: Done

Goal:
Add Neo4j as a graph read model for project, program, commit, file, class, and domain relationships so code impact and AI evidence can be explored as connected paths.

Rationale:
The existing PostgreSQL/pgvector model already stores project artifacts, Git history, RAG chunks, AI analysis, and risk records, but class-level structure and relationship traversal are not first-class. Neo4j makes the AX Use Case more visible by showing how AI analysis connects plans, commits, files, classes, domains, and risk/evidence paths.

Checklist:

- [x] Add Neo4j driver dependency, environment settings, and Docker service.
- [x] Implement a Neo4j graph sync service that builds project/program/commit/file/class/domain nodes and relationships from existing data and source files.
- [x] Add a Knowledge Graph screen with connection status, sync action, domain summary, class relationship summary, and impact path preview.
- [x] Update setup, architecture, AI technical overview, feature guide, DB migration guidance, engineering decision, README, roadmap, and changelog.
- [x] Add focused tests for source graph extraction and graph payload generation.
- [x] Run compile, focused tests, full tests when practical, and documentation checks.

## P1 - Structured PL Briefing History And Validation Hardening

Status: Done

Goal:
Make `PL Briefing` more stable for AX validation reviews by generating structured briefing sections, storing generated briefing history, tightening UI smoke verification, and cleaning stale limitation wording.

Rationale:
The current live LLM briefing demonstrates real AI use, but the output is still rendered from free-form text and disappears after generation. For validation and review, PLs should see consistent sections, inspect the latest saved briefing, and trust that screenshots and documentation represent current behavior.

Checklist:

- [x] Generate `PL Briefing` from structured sections instead of relying on free-form Markdown.
- [x] Persist generated PL briefing history with provider/model/mode and evidence payload.
- [x] Show latest briefing history on Dashboard and keep generated output visible after reruns.
- [x] Add focused service/UI smoke verification for the briefing action and history display.
- [x] Refresh affected Application Preview images without unnecessary oversized captures.
- [x] Update AI technical overview, feature guide, architecture, DB migration guidance, engineering decision notes, and changelog.
- [x] Run migration, compile, tests, screenshot, and documentation checks.

## P2 - Application Preview Scroll Coverage Refresh

Status: Done

Goal:
Refresh Application Preview screenshots so screens with meaningful content below the fold include the lower scroll area.

Rationale:
Several preview screenshots intentionally focused on a viewport section, but the PL Briefing and some detail/list screens now need the lower content to be visible for demo review. Full-page captures reduce the chance that important generated output or evidence tables are hidden just below the screenshot edge.

Checklist:

- [x] Update screenshot scenarios that need lower scroll coverage.
- [x] Re-capture affected Application Preview and verification images.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run screenshot/documentation verification.

## P2 - PL Briefing Live LLM Verification Evidence

Status: Done

Goal:
Show that the AX-oriented `PL Briefing` verification path uses the configured local LLM and leaves visible screenshot/evidence for reviewers.

Rationale:
`AI Resource Radar` already ranks resource and schedule signals, but validation needs to show the AI-generated briefing result itself, not only the button that triggers it. Capturing the live local LLM result and recording a short rehearsal makes the AI use case easier to inspect before a review.

Checklist:

- [x] Verify `PL Briefing` generation with the configured local LLM.
- [x] Add or refresh an Application Preview screenshot that shows the generated briefing result.
- [x] Record a short end-to-end validation rehearsal result.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run focused tests and documentation verification.

## P1 - AI Resource Radar And PL Briefing

Status: Done

Goal:
Expose a clear AX-oriented AI decision-support surface on Dashboard by ranking resource/schedule risk signals and generating an evidence-based PL briefing.

Rationale:
The app already has LLM mapping, implementation analysis, RAG, Risk Analysis, Code Review, and resource metrics, but the AI value can look scattered across screens. A Dashboard-level AI Resource Radar should make the AI-derived project signals visible as prioritized PL actions, while PL Briefing uses an LLM to turn those evidence rows into a meeting-ready Korean summary.

Checklist:

- [x] Promote the two candidate ideas into one active roadmap task.
- [x] Add an AI Resource Radar service that ranks programs from AI-derived resource/risk signals with explainable evidence.
- [x] Add a PL Briefing generator that uses LLM when configured and has a deterministic fallback.
- [x] Add focused tests for ranking and briefing behavior.
- [x] Add Dashboard UI for radar items and briefing generation.
- [x] Update AI technical overview, feature guide, Application Preview or user-facing docs as needed.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and documentation verification.

## P2 - AI Technology Application Summary

Status: Done

Goal:
Make it clear which AI technologies are already applied in the AX Use Case and how each one contributes to project resource management, risk detection, source-grounded answers, and traceable decision support.

Rationale:
The app already uses LLM, embedding/RAG, source verification, AI-derived mapping/progress evidence, and rule-based analytics. However, the value can look like a general project dashboard unless the documentation explains the AI stack and its AX resource-management role in one place.

Checklist:

- [x] Add an AX-oriented AI technology summary to `docs/ai-technical-overview.md`.
- [x] Distinguish real LLM/embedding/RAG usage from rule-based analytics that consume AI-derived evidence.
- [x] Update README document navigation so readers can find the summary.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run documentation verification.

## P3 - Server-Managed Clone/Fetch Workflow

Status: Done

Goal:
Allow the app server to clone or fetch/reset a configured Git remote into an approved server repository path without storing Git credentials in AI Commit Advisor.

Rationale:
The previous operating model required repositories to be pre-cloned before project registration. Some deployments need a lighter operator flow where project settings include the remote URL and branch, and the app server prepares or refreshes the local clone itself while still keeping credential handling outside the app.

Checklist:

- [x] Add project schema fields for Git remote URL and branch through Alembic.
- [x] Add a service that clones missing repositories and fetch/resets existing repositories under the configured repository path.
- [x] Add a sync lock and dirty working tree guard.
- [x] Add guarded Project/Git settings UI controls for remote clone/fetch.
- [x] Add focused local Git tests for clone, fetch/reset, dirty skip, and force reset.
- [x] Update operating model, runbook, setup, architecture, DB migration, and engineering decision docs.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and documentation diff verification.

## P2 - Managed Git URL Project Onboarding

Status: Done

Goal:
기존 앱 서버 Git 경로 등록 방식은 읽기 전용 분석 경로로 유지하면서, 외부 사용자가 공개 HTTPS Git URL과 branch만 입력하면 앱이 별도의 쓰기 가능한 관리형 저장소 경로를 자동 배정하고 clone/fetch할 수 있게 한다.

Rationale:
현재 프로젝트 등록 화면은 서버 경로와 remote URL을 모두 받지만, Docker는 `C:\dev`를 읽기 전용으로 mount하므로 외부 사용자가 새 저장소를 clone할 수 없다. 반대로 전체 `C:\dev`를 쓰기 가능하게 열면 분석 대상 저장소와 다른 개발 폴더까지 앱이 수정할 수 있다. 기존 경로 분석과 외부 URL 등록을 함께 제공하려면 읽기 전용 기존 경로와 쓰기 가능한 관리형 clone 영역을 분리해야 한다.

Checklist:

- [x] 기존 서버 경로와 관리형 Git URL 등록 방식을 프로젝트 설정 화면에서 구분한다.
- [x] 관리형 프로젝트 경로를 사용자 입력 없이 프로젝트별 전용 폴더로 생성한다.
- [x] Docker에 기존 `C:\dev` read-only mount와 별도 managed repository read-write mount를 구성한다.
- [x] 관리형 clone은 인증정보 없는 허용된 공개 HTTPS Git host로 제한한다.
- [x] 기존 경로 매핑과 관리형 경로 매핑을 함께 검증하는 테스트를 추가한다.
- [x] 사용자 가이드, 운영·아키텍처·engineering decision, `AI_CHANGELOG.md`를 갱신한다.
- [x] compile, focused/full tests, Docker config와 문서 diff를 검증한다.

Related AI Change Log: `관리형 Git URL 프로젝트 등록`

## P2 - Public Sample Repository And Managed Onboarding Verification

Status: Done

Goal:
현재 48개 commit Sample Shop 저장소를 공개 GitHub 저장소로 게시하고, Docker 시연 앱의 `Git URL에서 가져오기` 흐름이 공개 HTTPS URL에서 관리형 clone과 HEAD 확인까지 실제로 동작하는지 검증한다.

Rationale:
관리형 Git URL 등록은 공개 외부 저장소 clone을 지원하지만, 현재 샘플 저장소는 로컬 sibling 경로에만 존재한다. 공개 샘플 원격을 준비하고 실제 시연 앱에서 등록해야 외부 사용자가 서버 경로를 알지 못해도 같은 clone 흐름을 재현할 수 있으며, 같은 commit을 기본 DB에 다시 수집할 때 발생할 수 있는 전역 commit hash 제약도 검증 범위에서 분리해 보존할 수 있다.

Checklist:

- [x] 로컬 샘플 저장소의 작업트리, history, 공개 게시 안전성을 확인한다.
- [x] `ino5/ai-advisor-sample-shop` 공개 GitHub 저장소를 만들고 48개 commit `main` history를 push한다.
- [x] 시연 앱에 `Sample Shop Demo (github)` 프로젝트를 관리형 Git URL로 등록한다.
- [x] 관리형 clone 경로, remote URL, branch, Repo HEAD가 공개 원격과 일치하는지 확인한다.
- [x] 기본 프로젝트 commit 소유권을 보호하기 위해 같은 DB에서의 중복 Git 수집 제한을 검증 결과에 기록한다.
- [x] 샘플 설계, 사용/검증 문서, engineering decision, `AI_CHANGELOG.md`를 갱신한다.
- [x] 관련 테스트와 문서 검증을 완료한다.

Related AI Change Log: `공개 샘플 GitHub 저장소와 관리형 등록 검증`

## P1 - Project-Scoped Git Commit Identity Across RAG And Graph

Status: Done

Goal:
동일한 Git history를 여러 프로젝트가 독립적으로 수집해도 기존 프로젝트의 commit, 변경 파일, Mapping, RAG/vector, Knowledge Graph, 저장 AI 근거가 이동하거나 섞이지 않도록 commit identity와 후속 데이터 흐름을 프로젝트 범위로 통일한다.

Rationale:
작업 시작 당시 `git_commits`에는 `(project_id, commit_hash)` unique constraint와 별도로 `commit_hash` 전역 unique constraint가 남아 있었고, Git Sync는 같은 hash가 다른 프로젝트에 있으면 해당 row의 `project_id`를 새 프로젝트로 바꿨다. 이 동작은 오류를 내지 않는 대신 기존 프로젝트의 commit 소유권을 조용히 이동시키며, commit/file DB ID를 참조하는 Mapping과 RAG chunk, 프로젝트별 Neo4j read model, 저장된 AI 근거를 stale 상태로 만들 수 있었다.

Checklist:

- [x] `GitCommit`의 hash/id 조회, FK, Mapping, RAG/vector, Neo4j node key와 cleanup 경로를 전수 감사한다.
- [x] Alembic migration으로 전역 `commit_hash` unique constraint를 제거하고 `(project_id, commit_hash)` unique를 유지한다.
- [x] Git Sync가 현재 프로젝트 안에서만 중복을 판단하고 다른 프로젝트의 commit 소유권을 바꾸지 않게 수정한다.
- [x] 동일 저장소를 두 프로젝트에 수집해 commit/file/mapping/RAG/vector/graph identity가 분리되는 회귀 테스트를 추가한다.
- [x] 기존 DB upgrade와 영향 프로젝트의 재색인·graph 재동기화 복구 절차를 검증한다.
- [x] README, architecture, AI technical overview, DB migration, sample/user guide, engineering decision, failure history를 갱신한다.
- [x] focused/full tests, migration, Docker runtime, 문서와 사용자 문구 검증을 완료한다.

Related AI Change Log: `프로젝트 범위 Git commit identity와 전체 저장소 격리`

## P2 - Project Reset Action After Delete Flow

Status: Done

Goal:
Add a guarded project reset action that keeps the project and uploaded artifact data but clears collected analysis/runtime data for repeatable demo and verification runs.

Rationale:
Project deletion already provides a clean-slate path, but repeated demos often need to keep the same project name, Git path, programs, developers, plans, and standard terms while clearing Git sync and analysis outputs. A separate reset action avoids using full deletion for a less destructive workflow.

Checklist:

- [x] Define reset policy for preserved artifact data versus cleared analysis/runtime data.
- [x] Add service impact/count and reset execution helpers.
- [x] Add focused tests proving reset clears only resettable project-owned data and preserves project/artifact data.
- [x] Add guarded UI action to `프로젝트/Git 설정`.
- [x] Update user-facing, architecture, and engineering decision documentation.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and documentation diff verification.

## P2 - Project-Scoped UI State Namespacing

Status: Done

Goal:
Prevent project-specific Streamlit widget state from carrying stale selections across projects when the global current project changes.

Rationale:
The global project selector intentionally keeps the selected project across pages, but Streamlit widget keys can keep page-level selections such as selected program, selected commit, filters, or mapping rows after the project changes. Search text can sometimes be useful across projects, so the fix should namespace project-dependent choices instead of clearing all UI state.

Checklist:

- [x] Add a shared helper for project-scoped widget keys.
- [x] Apply project-scoped keys to RAG search, Mapping filters/selections, Program Detail filters/selections, Commit Impact filters/selections, Git History selections, Risk filters, and AI Progress selections where state belongs to one project.
- [x] Keep intentionally reusable text search behavior where cross-project reuse is useful and not misleading.
- [x] Add focused tests for the helper and project isolation behavior that can be verified without a browser.
- [x] Update user-facing or architecture documentation if visible behavior or UI state policy changes.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and documentation diff verification.

## P2 - Roadmap Commit Hash Tracking Cleanup

Status: Done

Goal:
Keep `ROADMAP.md` focused on planning state and related changelog headings, while leaving commit-level traceability to Git history.

Rationale:
The previous `Commit` column made each roadmap task need a second bookkeeping update after the real work commit was created. That added manual maintenance cost and created stale or empty cells without improving traceability enough to justify the extra step.

Checklist:

- [x] Remove the `Commit` column from the Roadmap priority overview.
- [x] Update Roadmap management rules to stop requiring commit hash tracking.
- [x] Update `AGENTS.md` so future agents do not create follow-up commits only for Roadmap hash bookkeeping.
- [x] Supersede the previous engineering decision that put commit hashes in `ROADMAP.md`.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run documentation diff and policy reference verification.

## P2 - Sample Commit Date Normalization

Status: Done

Goal:
Keep generated sample project commit dates from appearing later than the app verification date.

Rationale:
The 48-commit sample history should feel realistic when users inspect Git History and Commit Impact. If the latest generated sample commit appears in the future, users may distrust the analysis or think the app sorted/parsed dates incorrectly.

Checklist:

- [x] Adjust sample target repo generation start date so the 48-commit history ends on 2026-06-14.
- [x] Add a focused test that guards the latest generated commit date.
- [x] Update sample design documentation.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and sample generation verification.

## P2 - Application Preview Dashboard Wording Cleanup

Status: Done

Goal:
Make the Dashboard preview description easier to understand on first read.

Rationale:
The previous paragraph combined the screen purpose, resource metric caveat, 검증 value assumptions, and snapshot trend behavior in one dense sentence. Application Preview should help readers recognize the screen quickly before they dive into detailed feature documentation.

Checklist:

- [x] Rewrite the Dashboard preview text with shorter reader-facing sentences.
- [x] Preserve the boundary that resource metrics are planning signals, not personal evaluation or confirmed savings.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run documentation diff verification.

## P2 - Dashboard Value Terminology Cleanup

Status: Done

Goal:
Make Dashboard resource value metrics read like operational reference signals instead of internal 검증/KPI terminology.

Rationale:
The Dashboard values are useful because they help PLs spot workload concentration, schedule risk, review burden, and possible extra effort earlier. Labels such as `가정값`, `고객가치 KPI`, and `planning signal` explain internal caution but can make the screen feel experimental or like audited performance management. The UI should say what the value helps decide, while documentation keeps the calculation boundary clear.

Checklist:

- [x] Replace Dashboard-facing `가정값` and `KPI` wording with reference-estimate wording.
- [x] Update README, Application Preview, feature guide, demo user guide, architecture, AI technical overview, and DB migration wording where the old Dashboard value terms appeared.
- [x] Add an engineering decision for UI/reference-metric terminology.
- [x] Add a regression assertion that the Dashboard value assumption does not expose `검증`.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and diff verification.

## P2 - Application Preview Current Sidebar Screenshots

Status: Done

Goal:
Refresh Application Preview screenshots so the visible sidebar matches the current collapsible menu structure.

Rationale:
After the sidebar moved to grouped expanders, older Application Preview screenshots still showed the previous always-expanded menu. Mixed screenshots make the documentation feel stale and can mislead readers about where pages live in the current navigation.

Checklist:

- [x] Review Application Preview image references and existing feature screenshots for old sidebar states.
- [x] Extend screenshot capture automation for collapsible sidebar groups and system Chrome fallback.
- [x] Refresh current representative feature screenshots.
- [x] Remove old Application Preview references and obsolete image files for states that are not currently reproduced by automation.
- [x] Fix the Risk Analysis rendering bug discovered during screenshot verification.
- [x] Update `AI_CHANGELOG.md` and `docs/failure-history.md`.
- [x] Run compile, screenshot, reference, and diff verification.

## P2 - Sidebar Menu Map Documentation

Status: Done

Goal:
Document where each current sidebar menu item lives and when users should use it.

Rationale:
The collapsible sidebar keeps the app easier to scan, but users still need one stable written map of the menu groups. Screenshots show the UI shape, while the feature guide should explain the navigation structure without requiring readers to infer it from images.

Checklist:

- [x] Add a sidebar menu structure table to `docs/feature-guide.md`.
- [x] Include every current `app.py` sidebar group and page.
- [x] Link the menu map to Application Preview screenshots.
- [x] Update README document link wording.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run documentation diff verification.

## P2 - Application Preview Lower-Section Coverage

Status: Done

Goal:
Make Application Preview show important lower-page feature areas that can be missed in a single viewport screenshot.

Rationale:
Several Streamlit pages contain useful controls or results below the first visible area. A single screenshot can make those features look absent even though they are available after scrolling. Application Preview should split long workflows into representative sections instead of relying on one cropped image.

Checklist:

- [x] Review current Application Preview screenshots for long pages where key areas can be hidden below the fold.
- [x] Add screenshot scenarios for lower/result sections.
- [x] Capture additional images for Program Detail, Risk Analysis, RAG Search, Project Chat, Dashboard, and AI Progress.
- [x] Update Application Preview captions and image references.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run screenshot/reference/diff verification.

## P2 - README Representative Screenshot Source Cleanup

Status: Done

Goal:
Make the README top screenshot use the same current Home screenshot as Application Preview.

Rationale:
README is the first user-facing entry point. Keeping a separate top screenshot file from Application Preview made the first image stale even after the preview screenshots were refreshed. The representative screenshot needs one source of truth so future visual updates do not miss the README again.

Checklist:

- [x] Point the README top screenshot at `docs/images/features/home.png`.
- [x] Remove the duplicate README screenshot image lower in the document.
- [x] Delete legacy representative screenshot files that are no longer referenced.
- [x] Add a regression test preventing README from using `ai-commit-advisor-home*.png`.
- [x] Record the root cause in `docs/failure-history.md`.
- [x] Update screenshot convention in `docs/engineering-decisions.md`.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run documentation image reference and test verification.

## P2 - Sidebar Group Collapse Cleanup

Status: Done

Goal:
Reduce sidebar scrolling by rendering workflow menu groups as collapsible sections, with the current group expanded by default.

Rationale:
The sidebar now contains enough project, artifact, analysis, and management pages that listing every group and child page at once pushes lower navigation below ordinary desktop viewports. Collapsible groups keep the workflow structure while making the current task area easier to scan.

Checklist:

- [x] Render sidebar menu groups as expanders.
- [x] Expand the current group by default and keep page selection behavior unchanged.
- [x] Remove obsolete sidebar group CSS.
- [x] Update user-facing and architecture documentation.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and Browser rendering verification.

## P2 - Home Summary Priority Cleanup

Status: Done

Goal:
Make Home show the selected project's key numbers and next actions before the detailed pipeline status table.

Rationale:
Home is the command-center screen. Users landing there need the current project summary and recommended next action before reading a detailed readiness table. Showing the pipeline table first makes the page feel like a setup checklist even when real KPI data exists.

Checklist:

- [x] Move Home KPI metrics above pipeline status.
- [x] Keep next actions near the top so users can decide what to do next.
- [x] Keep pipeline status available below the summary.
- [x] Update preview/feature documentation text.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and Browser rendering verification.

## P2 - Program Management Project Flow Cleanup

Status: Done

Goal:
Make Program Management strictly operate on the sidebar current project and move new project creation responsibility to Project/Git settings.

Rationale:
Most project-scoped screens now use the global current project context. Program Management still exposes `새 프로젝트명으로 저장`, which can make users think program upload is also a project creation screen. This weakens the shared project context model and makes accidental writes to a similarly named project easier.

Checklist:

- [x] Remove the `새 프로젝트명으로 저장` path from Program Management.
- [x] Save direct-add and Excel-import programs to the current project ID, not by project name lookup/create.
- [x] Keep no-project guidance pointing users to Project/Git settings.
- [x] Add focused service tests for project-ID-based program saving.
- [x] Update user-facing and architecture documentation.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and Browser rendering verification.

## P2 - Completed-State Action Priority Cleanup

Status: Done

Goal:
Make already-complete or already-current workflows look complete instead of continuing to emphasize expensive or redundant execution buttons.

Rationale:
Screens such as Git Sync, Mapping, RAG Search, and Project Chat have enough status information to know when no immediate work is needed. If the main button remains primary in that state, users can read the page as unfinished and may rerun expensive analysis or indexing without a reason.

Checklist:

- [x] Prefer incremental Git sync as the primary action and make full collection visually secondary.
- [x] Show Mapping completion state before analysis controls when all commits are analyzed.
- [x] Make RAG and Project Chat refresh buttons primary only when code evidence needs refresh.
- [x] Disable or de-emphasize one-click RAG preparation when no search-preparation work remains.
- [x] Update relevant documentation and `AI_CHANGELOG.md`.
- [x] Run compile/tests and Browser rendering verification.

## P2 - User-Facing Analysis Display Cleanup

Status: Done

Goal:
Replace raw JSON-like dictionaries, internal field names, and code-first risk labels in analysis screens with readable business-oriented summaries while keeping technical details available where they are useful.

Rationale:
AI Progress, Program Detail, Commit Impact, Git History, Risk Analysis, and AI Code Review are review surfaces for project leads and operators. When these pages expose `st.write({ ... })`, `st.json`, `risk_type`, `planned_start_date`, or `Risk Level: HIGH` directly, the page feels like a debug console and makes users translate internal data shapes before making a decision.

Checklist:

- [x] Replace raw commit/project dictionaries with compact summary tables or metrics.
- [x] Rename visible table/filter labels for risk and program details to user-facing Korean labels where practical.
- [x] Keep technical identifiers such as commit hash, file path, and program ID visible when they are useful evidence.
- [x] Update feature/architecture documentation if the display policy changes.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and Browser rendering verification.

## P2 - Current Project Selection Persistence

Status: Done

Superseded: 2026-07-22 `Remove Current-Project URL Synchronization`에서 첫 선택 안정성을 우선해 URL `project_id` 연동을 제거했습니다. 아래 내용은 당시 구현 목표를 보존한 기록입니다.

Goal:
Keep the sidebar current project selection stable after browser reloads or shared URL navigation so users do not accidentally fall back to another project with a similar name.

Rationale:
The current project selector is the context for Home, Mapping, RAG, Project Chat, Git History, Code Review, and most project-scoped screens. When the selection only lives in Streamlit session state, a reload can return to the first project sorted by name. In environments with multiple sample or verification projects, that makes metrics and analysis results look inconsistent even though the app is simply looking at a different project.

Checklist:

- [x] Persist the selected project ID in the page URL query parameter.
- [x] Restore the current project from the query parameter before falling back to the first available project.
- [x] Keep invalid or deleted project IDs recoverable.
- [x] Add focused tests for query-parameter restore and cleanup behavior.
- [x] Update relevant user-facing and architecture documentation.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile/tests and Browser verification.

## P2 - Resource Value Metric Wording Cleanup

Status: Done

Goal:
Make Dashboard resource value KPI labels understandable as 검증 planning estimates instead of confirmed savings or cost avoidance.

Rationale:
Labels such as `AI 리뷰 절감 추정` and `추가 MM 회피 노출` expose internal formula intent but do not tell users what action or interpretation is expected. The AX resource dashboard should show these values as decision-support possibilities with visible assumptions, so PLs do not read them as audited financial results.

Checklist:

- [x] Rename Dashboard value KPI labels and trend columns to user-facing possibility wording.
- [x] Add contextual help that explains the 검증 assumptions and limits.
- [x] Update user-facing documentation and screenshot verification criteria.
- [x] Update `AI_CHANGELOG.md`.
- [x] Verify compile/tests, Browser rendering, and Dashboard screenshot capture.

## P2 - Project Chat Source Refresh Wording Cleanup

Status: Done

Goal:
Make the Project Chat source refresh/status area understandable to product users by replacing implementation-first wording such as chunk, embedding, and source_file with task-oriented guidance.

Rationale:
The existing copy explained the internal indexing pipeline before explaining what the user should do. In a chat workflow, users need to know whether answers use the latest code, which refresh action is safe, and where to go when search preparation is still missing.

Checklist:

- [x] Replace Project Chat source status labels and refresh button copy with user-facing wording.
- [x] Move chunk/embedding/HEAD details into an optional technical detail area.
- [x] Update user-facing documentation and screenshot verification text.
- [x] Update `AI_CHANGELOG.md`.
- [x] Verify with compile/test and browser/screenshot checks.

## P2 - Contextual Help Tooltips For Project/RAG Controls

Status: Done

Goal:
Add question-mark tooltip help to controls that use product or AI-search terms so users can understand actions such as project selection, TOP K, search preparation, source refresh, and saved conversations without adding permanent explanatory text to the page.

Rationale:
Some controls need just-in-time explanation, but always-visible descriptions make Project Chat and RAG Search noisy. Streamlit widget `help` text gives users a compact question-mark affordance while preserving the cleaned-up UI.

Checklist:

- [x] Add contextual `help` text to the global project selector.
- [x] Add contextual `help` text to Project Chat metrics, refresh buttons, session controls, TOP K, and history options.
- [x] Add contextual `help` text to RAG Search metrics, preparation controls, TOP K, and source filters.
- [x] Update user-facing docs and `AI_CHANGELOG.md`.
- [x] Verify compile/tests and Browser UI rendering.

## P2 - Project Chat Conversation Controls Cleanup

Status: Done

Goal:
Make Project Chat conversation controls feel intentional by removing duplicated "reset/new chat" actions and grouping session selection with the new conversation action.

Rationale:
`대화 초기화` and `새 대화` both created a new chat session, so users could read them as different destructive and non-destructive actions even though neither deleted history. A single conversation management area should make the saved-session model clearer.

Checklist:

- [x] Replace the separate reset button with one `새 대화 시작` action beside the session selector.
- [x] Clarify the session selector labels and empty-session wording.
- [x] Update user-facing docs and Application Preview wording/screenshot.
- [x] Update `AI_CHANGELOG.md`.
- [x] Verify with compile/test and browser/screenshot checks.

## P1 - Resource Metric Snapshot And Trend Dashboard

Status: Done

Goal:
Persist AX resource management KPI snapshots and show project trend analysis so PLs can compare risk, workload, difficulty, forecast delay, and AI review value over time.

Rationale:
The current resource metrics are calculated at read time, which is useful for the current state but cannot answer whether delay risk, workload concentration, or review productivity is improving. A lightweight manual snapshot flow gives the 검증 traceable trend evidence without introducing background scheduling or webhook operations.

Checklist:

- [x] Add an Alembic-managed `resource_metric_snapshots` table and SQLAlchemy model.
- [x] Add service functions to save the current resource metric summary and read recent project snapshots.
- [x] Add focused tests for snapshot persistence and trend ordering.
- [x] Add Dashboard controls for saving a snapshot and viewing trend charts/tables.
- [x] Update README, feature guide, architecture, AI technical overview, DB migration docs, engineering decisions, and user guide.
- [x] Update `AI_CHANGELOG.md`.

## P2 - AI Code Review Server Repository Target Wording

Status: Done

Goal:
Make the AI Code Review screen and documentation match the central app-server Git repository model, where commit history is the normal review target and working tree/staged review only applies to local changes inside the server clone.

Rationale:
The app does not read each developer's personal working tree. In the shared 검증/server model, developers usually push commits and the app reviews the server-accessible repository history. Presenting working tree and staged changes as equal primary targets can make users think the app can inspect local developer machines.

Checklist:

- [x] Reorder the AI Code Review target options so latest/specific commit review is the primary path.
- [x] Clarify in the UI that server working tree/staged review means local changes in the app-server clone.
- [x] Update README, user guide, feature guide, architecture, AI technical overview, and Application Preview wording.
- [x] Record the operating-model decision in `docs/engineering-decisions.md`.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Remove Server-Local AI Code Review Targets

Status: Done

Goal:
AI Code Review의 실행 대상을 앱 서버에서 안정적으로 재현할 수 있는 최신 commit과 선택 commit으로 한정하고, 서버 clone의 working tree/staged 변경을 일반 사용자와 운영 검증 경로에서 제거한다.

Rationale:
서버 작업트리와 서버 Staged 변경은 개발자 개인 PC의 미커밋 변경을 보여주지 못하고, 분석용 서버 clone에 local 변경을 남기지 않는 현재 관리형 clone/fetch 운영 원칙과도 맞지 않는다. 예외적인 서버 임시 변경 점검 기능을 기본 리뷰 대상으로 유지하면 사용자가 지원 범위를 오해하고 화면 선택지만 복잡해진다. 기존 저장 리뷰는 삭제하지 않고 과거 대상 label을 계속 표시한다.

Checklist:

- [x] UI에서 서버 작업트리와 서버 Staged 변경 선택지 및 관련 안내를 제거한다.
- [x] service와 local AI verification CLI에서 `working_tree`/`staged` 실행 경로를 제거한다.
- [x] 기존 저장 리뷰의 legacy target label 표시를 유지하고 회귀 test를 추가한다.
- [x] 사용자 가이드, feature/architecture/AI 문서와 engineering decision을 현재 commit-only 운영 모델에 맞춘다.
- [x] `AI_CHANGELOG.md`를 갱신하고 사용자 문구를 점검한다.
- [x] focused test, compileall, 전체 test와 diff hygiene을 검증한다.

Related AI Change Log: `AI Code Review 서버 local 대상 제거`

## P1 - AX Resource Management Metrics Foundation

Status: Done

Goal:
Define the shared metric model needed to align AI Commit Advisor with the AX use case for AI commit analysis based project resource management.

Rationale:
The current product already covers commit collection, program mapping, AI progress, risk analysis, developer activity, and AI code review. The main AX gaps are forecasted completion dates, developer workload/capacity indicators, developer-level difficulty indicators, and quantified business-value KPIs. This foundation task keeps the first implementation focused on reusable metric definitions before spreading calculations across dashboards.

Checklist:

- [x] Confirm `AGENTS.md` already requires documentation impact checks and user-facing documentation updates for feature/UX/behavior changes.
- [x] Record the AX use case gap analysis as roadmap-tracked work.
- [x] Define metric names, formulas, confidence labels, and interpretation boundaries for workload, difficulty, forecast, and value KPIs.
- [x] Decide whether the first implementation is computed-only or needs stored metric snapshots and Alembic migration.
- [x] Add or update the reusable service layer for project/program/developer resource metrics.
- [x] Add focused tests for formula boundaries and empty/partial data behavior.
- [x] Update `docs/engineering-decisions.md` if the metric formula policy becomes a repeatable product convention.
- [x] Update `docs/architecture.md`, `docs/feature-guide.md`, and `docs/ai-technical-overview.md` as implementation changes require.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Forecasted Completion And Proactive Delay Risk

Status: Done

Goal:
Estimate program-level completion outlook and surface likely schedule delay before the planned end date is missed.

Checklist:

- [x] Calculate `forecast_end_date`, expected delay days, confidence, and evidence from plan dates, AI progress, mapping evidence, and recent commit activity.
- [x] Add a proactive delay risk type to Risk Analysis without replacing the existing overdue/progress-gap rules.
- [x] Show forecast evidence in Dashboard and Risk Analysis summaries where useful.
- [x] Add tests for no-activity, partial-progress, completed, overdue, and low-confidence cases.
- [x] Update user-facing docs and screenshots when the UI is added.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Developer Workload And Difficulty Dashboard

Status: Done

Goal:
Give PLs a developer-level view of assigned workload, implementation progress, difficulty, and risk concentration.

Checklist:

- [x] Define workload score from assigned programs, unfinished programs, progress gap, unresolved risks, and recent Git activity.
- [x] Define difficulty score from changed files, diff size, touched module breadth, DB/API/UI impact, cross-program impact, and risk evidence.
- [x] Add a dashboard view or extend Dashboard with developer-level workload, progress, difficulty, and risk charts.
- [x] Keep metric labels clear that scores are planning indicators, not personnel evaluation truth.
- [x] Add tests for aggregation by assigned developer and Git author fallback behavior.
- [x] Update feature guide, architecture, Application Preview, and `AI_CHANGELOG.md`.

## P2 - AX Customer Value KPI Documentation

Status: Done

Goal:
Document how the 검증 expresses AX customer value such as risk reduction, workload visibility, review productivity, and estimated resource savings.

Checklist:

- [x] Define 검증용 formulas for early risk count, estimated review time saved, forecasted delay count, and estimated extra MM avoided.
- [x] Add user-facing explanation that these are decision-support estimates, not contractual financial measurements.
- [x] Link the value KPIs to the relevant screens and sample project evidence.
- [x] Update README or feature guide if the value KPI becomes visible in the app.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Demo User Guide

Status: Done

Goal:
Create a user-facing guide for demonstrating AI Commit Advisor with the sample project, focused on product workflow rather than internal verification details.

Checklist:

- [x] Add a 검증 사용 가이드 for the sample-project demo flow.
- [x] Explain project registration, Git sync, artifact upload, Mapping, Risk Analysis, AI Progress, Program Detail, Git History, Commit Impact, RAG, Project Chat, and AI Code Review in demo order.
- [x] Link the guide from README.
- [x] Fix the stale sample walkthrough commit-count wording.
- [x] Run documentation link and whitespace checks.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Sample Project Usage Guide Verification Evidence

Status: Done

Goal:
Run the sample project usage guide against the current application with real local LLM/embedding providers and keep separate verification evidence so the user-facing guide stays concise.

Checklist:

- [x] Add an agent policy for preserving usage-guide verification evidence outside the user-facing guide.
- [x] Execute the sample project flow with local LLM and local embedding settings, not mock providers.
- [x] Capture representative screenshots under `docs/images/usage-verification/`.
- [x] Add a verification result document with environment, execution results, screenshots, and limitations.
- [x] Link or reference the verification result from the appropriate documentation hub if useful.
- [x] Run screenshot/documentation verification checks.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Project Delete And Demo Reset Safety

Status: Done

Goal:
Let users remove a project and its project-owned analysis data so the sample-project demo can be repeated without wiping the whole database or affecting the global developer master.

Checklist:

- [x] Add a project deletion service with impact counts.
- [x] Add a guarded delete flow to `프로젝트/Git 설정`.
- [x] Keep global `developers` rows when a project is deleted.
- [x] Recover the current project selection after deletion.
- [x] Add focused tests for deletion impact, cascade cleanup, developer preservation, and project context recovery.
- [x] Update feature/demo/architecture/decision documentation.
- [x] Run compile and DB-independent focused tests.
- [x] Run DB-backed focused/full tests when PostgreSQL is available.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Project Developer Membership Model

Status: Done

Goal:
Keep `developers` as a global master while adding project-level developer membership so project-scoped screens and repeatable demos show the expected developer set without breaking existing program assignment behavior.

Checklist:

- [x] Add `project_developers` through Alembic migration and ORM model.
- [x] Add membership helpers and project-scoped developer queries.
- [x] Link Git author extraction, manual developer creation, and Excel upload to the current project.
- [x] Make developer management default to current-project developers while preserving global master access.
- [x] Keep `programs.developer_id` and global developer behavior backward-compatible.
- [x] Add migration/service/cascade tests.
- [x] Update architecture, feature, engineering decision, DB migration, roadmap, and changelog documentation.
- [x] Run migration, compile, focused tests, full tests, and diff checks.

## P2 - Server Repository Status Display

Status: Done

Goal:
Show app-server Git repository status beside DB sync state so operators can tell whether the server repo itself is reachable/current and whether app Git Sync needs to run.

Checklist:

- [x] Add a read-only Git repository status service.
- [x] Show branch, HEAD, upstream, dirty state, and DB sync mismatch on Git sync screen.
- [x] Show compact repository status on project/Git settings screen.
- [x] Add focused tests for clean, dirty, ahead/behind, and missing-path status handling.
- [x] Update feature/architecture/setup documentation as needed.
- [x] Run compile and tests.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Git History Application Preview Screenshot

Status: Done

Goal:
Show the new Git History screen in Application Preview with meaningful sample project state.

Checklist:

- [x] Add Git History screenshot scenario to the capture automation.
- [x] Capture the Git History commit list/activity graph state.
- [x] Capture the Git History commit detail/diff preview state.
- [x] Update `docs/application-preview.md`.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Commit-Based Mapping Fallback And Verified Screenshots

Status: Done

Goal:
Verify the 48-commit sample through the core analysis workflow before refreshing screenshots, and harden commit-based Mapping so one malformed LLM JSON response does not leave a demonstrably related commit in failed state.

Checklist:

- [x] Run commit-based Mapping on the 48-commit sample project.
- [x] Add commit-based token-similarity fallback when the LLM response is not valid mapping JSON.
- [x] Add focused Mapping fallback tests.
- [x] Run Risk Analysis and verify AI Progress after Mapping.
- [x] Run RAG indexing, embedding, retrieval, and Project Chat verification with local providers.
- [x] Prevent concurrent Streamlit sessions from rerunning Alembic migrations in the same process.
- [x] Extend screenshot automation for Mapping, Risk Analysis, AI Progress, and RAG Search.
- [x] Refresh Home, Mapping, Risk Analysis, AI Progress, RAG Search, Project Chat, and Git History screenshots after analysis state is meaningful.
- [x] Update `AI_CHANGELOG.md`, `docs/ai-technical-overview.md`, and `docs/failure-history.md`.

## P1 - Git Default Branch Deterministic Tests

Status: Done

Goal:
Keep Git-dependent tests portable across Windows local machines and Ubuntu CI runners by making temporary repository branch names explicit.

Checklist:

- [x] Reproduce the CI failure in a Linux container.
- [x] Make Git repository status tests independent of the host Git default branch.
- [x] Run focused and full test verification.
- [x] Update `AI_CHANGELOG.md` and `docs/failure-history.md`.

## P2 - Git History Viewer

Status: Done

Goal:
Let users inspect project commit history, changed files, saved diff snippets, and optional full server-repo diff from inside AI Commit Advisor.

Checklist:

- [x] Add a Git history service for commit/file listing and full `git show` retrieval.
- [x] Add a project-scoped Git History Streamlit page with message, author, file, and date filters.
- [x] Show selected commit summary, changed files, saved diff preview, and optional full diff.
- [x] Add navigation entry under analysis results.
- [x] Add focused tests for filtering and full-diff safety behavior.
- [x] Update README/feature/architecture documentation as needed.
- [x] Run compile and tests.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Server Repository Update Runbook/Script

Status: Done

Goal:
Make the current operating policy usable by giving internal server operators a repeatable way to update pre-cloned repositories under `REPO_STORAGE_ROOT` before running app Git Sync.

Checklist:

- [x] Add a repository update script with safe defaults for pre-cloned repositories.
- [x] Keep clone/fetch credentials outside the app and avoid storing secrets.
- [x] Document the recommended fetch/reset workflow and examples.
- [x] Link the runbook from setup/operations and Git repository operating model docs.
- [x] Add focused script verification.
- [x] Update `AI_CHANGELOG.md`.

## P1 - App-Server Git Repository Operating Model

Status: Done

Goal:
Make the product model explicit that AI Commit Advisor analyzes Git repositories accessible from the app server, not arbitrary browser-user PC paths, so internal-network server operation is understandable and safer.

Checklist:

- [x] Rename user-facing Git path wording from local-user wording to app-server-accessible repository wording.
- [x] Add optional `REPO_STORAGE_ROOT` validation so server deployments can restrict project repository paths to an approved root.
- [x] Document the Git repository operating model in a dedicated user-facing document and link it from README.
- [x] Update setup/operations, architecture, and feature guide documentation.
- [x] Record the operating model decision in `docs/engineering-decisions.md`.
- [x] Add focused tests for repository root validation.
- [x] Run compile and focused tests.
- [x] Update `AI_CHANGELOG.md`.

## P0 - Program Management UX Improvement

Status: Done

Goal:
Make program data manageable without knowing the Excel schema in advance.

Checklist:

- [x] Add program Excel template download.
- [x] Show required and optional column guide in the UI.
- [x] Add upload preview before save.
- [x] Add upload validation for required columns, duplicate program IDs, dates, and progress values.
- [x] Show import summary: new rows, updated rows, skipped/error rows.
- [x] Add existing program search and filters.
- [x] Add manual program creation form.
- [x] Add program edit flow.
- [x] Add program delete flow with impact warning.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.
- [x] Update related README sections.

## P0 - Developer Management UX Improvement

Status: Done

Goal:
Make developer data easy to create, correct, and remove from the UI.

Checklist:

- [x] Add developer Excel template download.
- [x] Show required and optional column guide in the UI.
- [x] Add upload preview and validation.
- [x] Add existing developer search and filters.
- [x] Add manual developer creation form.
- [x] Add developer edit flow.
- [x] Add delete flow with assigned program warning.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.
- [x] Update related README sections.

## P0 - Development Plan Management UX Improvement

Status: Done

Goal:
Make plan progress, dates, status, and assignments editable without re-uploading Excel.

Checklist:

- [x] Add development plan Excel template download.
- [x] Show required and optional column guide in the UI.
- [x] Add upload preview and validation.
- [x] Add current plan grid with filters.
- [x] Add manual plan update form.
- [x] Add bulk status/progress update where safe.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.
- [x] Update related README sections.

## P1 - Project Chat Answer Quality And History Persistence

Status: Done

Goal:
Improve Project Chat from session-only Q&A into a more reliable project assistant.

Checklist:

- [x] Persist chat sessions in the database.
- [x] Add project-level chat history list.
- [x] Add source citation export or copy-friendly format.
- [x] Add "insufficient evidence" answer classification.
- [x] Separate current source evidence from historical/reference evidence in the UI.
- [x] Add focused tests for insufficient, stale/invalid, and verified source evidence.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Standard Terminology Glossary Upload And Korean Query Expansion

Status: Done

Goal:
Improve Korean business-question retrieval by using project standard terminology and standard words to connect Korean terms with code, DB, and naming identifiers.

Scope:

- Add a project-level standard terminology/standard word management menu.
- Support Excel template download and Excel upload for SI-style terminology deliverables.
- Keep the Excel input lightweight: teams enter Korean term, English term, and abbreviation; the app derives search variants.
- Use uploaded terminology to expand Korean Project Chat and RAG queries into English/code/DB identifier candidates.
- Keep query expansion deterministic first, without adding an extra LLM call per chat question.

Suggested menu:

- `데이터 관리 > 표준용어/표준단어`

Excel columns:

- Required: `korean_term`, `english_term`
- Recommended: `abbreviation`
- Optional: `term_type`, `description`

Derived search variants:

- tokenized English words
- abbreviation tokens
- `camelCase`
- `PascalCase`
- `snake_case`
- `UPPER_SNAKE_CASE`
- compact lowercase form

Checklist:

- [x] Add schema for project-level glossary terms through Alembic migration.
- [x] Add glossary service for normalization, validation, and derived keyword generation.
- [x] Add Excel template generation for standard terminology upload.
- [x] Add Excel upload validation for required columns, duplicate Korean/English terms, and empty values.
- [x] Add current glossary list/search UI.
- [x] Add glossary query expansion for Project Chat and RAG retrieval.
- [x] Merge multi-query retrieval results by chunk id and prefer verified `source_file` evidence for Project Chat.
- [x] Add focused tests for Korean payment amount questions expanding to `payment`, `amount`, `PaymentService`, `payment_amount`, and abbreviation variants.
- [x] Update README, Feature Guide, and AI technical overview.
- [x] Update `AI_CHANGELOG.md`.

Out of scope for first pass:

- Manual row-level glossary edit/delete UI.
- LLM-based query rewrite.
- Full DB table/column lineage inference from source code.

## P1 - Incremental Source Indexing And Embedding Cost Control

Status: Done

Goal:
Make Project Chat source indexing practical for large SI repositories and cloud deployment by avoiding full source scans and repeated embedding calls during normal work.

Context:

- Git commit sync is already incremental through `last_synced_commit_hash`.
- Source file re-indexing is currently manual and content-aware, but it still scans the repository tree.
- Embedding generation already creates vectors only for missing `chunk_id + embedding_model` pairs.
- A complete commit-triggered incremental source indexing pipeline does not exist yet.

Design document:

- `docs/source-indexing-and-embedding-plan.md`

Checklist:

- [x] Document current behavior and limitations in user-facing operations guidance.
- [x] Add a changed-file source indexing service that accepts added, modified, deleted, and renamed file paths.
- [x] Rebuild chunks only for changed source files during incremental refresh.
- [x] Remove chunks and vectors for deleted source files.
- [x] Keep full source re-indexing as a separate recovery and large-change action.
- [x] Add UI status for missing embeddings, stale chunks, and when full re-index is recommended.
- [x] Keep embedding generation explicit or limited so cloud API usage is controlled.
- [x] Add focused tests for modified, deleted, renamed, unchanged/non-source, and explicit-embedding behavior.
- [x] Update README, setup/operations guidance, AI technical overview, and `AI_CHANGELOG.md` when implemented.

## P1 - Project Chat Answer Formatting And Citation Accuracy

Status: Done

Goal:
Make Project Chat answers presentation-ready and defensible by preventing JSON-shaped responses, reducing line-number hallucination, and showing source evidence clearly.

Observed issues:

- local LLM responses can return JSON code blocks even when the UI expects readable chat text.
- The LLM can infer incorrect line numbers instead of using the provided source metadata.
- README screenshots look weak when answers show `Mock answer`, hidden evidence, or only file lists.

Checklist:

- [x] Strengthen the Project Chat prompt to forbid JSON/code-block response wrappers unless the user explicitly asks for JSON.
- [x] Require Markdown prose/bullets in Korean for normal answers.
- [x] Require file paths and line ranges to be copied only from retrieved source metadata.
- [x] Add response post-processing for common JSON wrapper shapes from local LLMs.
- [x] Show the matched/expanded query information in debug or evidence context when useful.
- [x] Adjust source evidence rendering so screenshots can show answer plus key evidence without looking empty.
- [x] Add focused tests for JSON wrapper cleanup and citation line-range preservation.
- [x] Refresh the Project Chat README screenshot only after real local LLM/RAG verification succeeds.
- [x] Update README, Application Preview, Feature Guide, and AI technical overview as needed.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Source File Re-Index Warning And One-Click Refresh

Status: Done

Goal:
Reduce stale RAG results when the repository HEAD changes after indexing.

Checklist:

- [x] Show indexed HEAD vs current HEAD in RAG and Project Chat.
- [x] Show indexed HEAD variants and current HEAD mismatch chunk count.
- [x] Add stale source_file chunk count.
- [x] Add one-click source_file re-index action.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Implementation Status Result Display Improvement

Status: Done

Goal:
Make saved program implementation status analysis easier for business owners to understand and verify.

Checklist:

- [x] Show AI status values as business-friendly Korean labels.
- [x] Add explanatory guidance that the result is an AI estimate requiring owner confirmation.
- [x] Improve saved result layout for status, analyzed time, evidence count, summary, features, and evidence commits.
- [x] Make evidence commit rendering defensive for malformed payloads.
- [x] Keep reanalysis failures from breaking the whole Program Detail page.
- [x] Run compileall and pytest.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Conservative Implementation Status Prompt And Fallback

Status: Done

Goal:
Make program implementation status analysis more conservative and easier to verify in business review.

Checklist:

- [x] Rewrite the LLM prompt in Korean with conservative status rules.
- [x] Clarify that commits alone do not prove testing, deployment, or production verification.
- [x] Make fallback summaries and incomplete guidance Korean.
- [x] Avoid easy COMPLETED fallback results.
- [x] Add focused tests for fallback and payload normalization.
- [x] Update AI technical overview.
- [x] Run compileall and pytest.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Show Implementation Status Analysis Results In AI Progress

Status: Done

Goal:
Show saved program-level implementation analysis beside existing AI progress metrics without changing progress calculations.

Checklist:

- [x] Add implementation analysis fields to progress summary rows.
- [x] Map saved implementation analysis statuses to business-friendly labels.
- [x] Add implementation analysis columns to the AI Progress program table.
- [x] Show selected program implementation analysis summary in the detail area.
- [x] Add guidance explaining AI progress rate versus implementation analysis.
- [x] Keep AI progress, progress gap, and risk calculations unchanged.
- [x] Add focused tests.
- [x] Update README and AI technical overview where needed.
- [x] Run compileall and pytest.
- [x] Update `AI_CHANGELOG.md`.

## P1 - Mapping Feedback Analytics And Review Queue

Status: Done

Goal:
Turn manual mapping feedback into an analysis quality workflow.

Checklist:

- [x] Add feedback completed/pending/review-needed quality summary.
- [x] Add review queue candidates for no feedback, unknown status, low relevance, short reason, and unrelated mappings.
- [x] Add review queue filters and keyword search.
- [x] Reuse the existing mapping feedback correction form for selected queue rows.
- [x] Add focused tests.
- [x] Update `AI_CHANGELOG.md`.

## P1 - LLM/Embedding Batch Safety And Estimated Runtime

Status: Done

Goal:
Reduce local LLM and embedding overload by showing estimated runtime and keeping batch execution bounded.

Checklist:

- [x] Add a reusable estimated runtime helper.
- [x] Show estimated runtime before RAG embedding execution.
- [x] Show estimated runtime before source_file refresh with embedding.
- [x] Use safer default embedding batch sizes for local runs.
- [x] Add focused tests.
- [x] Update README and `AI_CHANGELOG.md`.

## P2 - Sidebar Navigation UX Improvement

Status: Done

Goal:
Make the sidebar feel like workflow navigation instead of radio-button settings.

Checklist:

- [x] Replace the two-level radio menu with grouped navigation controls.
- [x] Keep the existing page groups and page renderers.
- [x] Show the current menu path clearly.
- [x] Update README and `AI_CHANGELOG.md`.
- [x] Run compileall and pytest.

## P2 - Artifact Management Menu Grouping

Status: Done

Goal:
Group upload and direct-management screens for project artifacts so users can find SI deliverables in one sidebar section.

Checklist:

- [x] Add a sidebar group for artifact management screens.
- [x] Move developer list, program list, development plan, and standard terminology management pages into the artifact group.
- [x] Keep Git sync and sample data generation under data collection.
- [x] Update related workflow documentation.
- [x] Run compile and UI verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - CI Test Workflow

Status: Done

Goal:
Run tests consistently before merge or push.

Checklist:

- [x] Add GitHub Actions workflow.
- [x] Run py_compile or import smoke check.
- [x] Run pytest.
- [x] Document local verification commands.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Home Analysis Command Center

Status: Done

Goal:
Make Home a practical analysis command center that shows pipeline status and next work items.

Checklist:

- [x] Rewrite Home guidance in a business workflow tone.
- [x] Add analysis pipeline status for project, program, developer, Git, mapping, implementation status, and unresolved risk data.
- [x] Add data-driven next recommended actions.
- [x] Keep existing KPI and chart sections.
- [x] Update README and `AI_CHANGELOG.md`.

## P2 - Home Copy Tone Cleanup

Status: Done

Goal:
Make Home feel less like an explanatory AI demo and more like a compact work status screen.

Checklist:

- [x] Shorten Home header copy.
- [x] Replace long pipeline explanations with compact status notes.
- [x] Shorten next action messages.
- [x] Keep existing Home data collection and charts unchanged.
- [x] Run compileall.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Home UI Visual Verification Script

Status: Done

Goal:
Make Home copy and layout verification repeatable without relying on Node Playwright.

Checklist:

- [x] Add a Python Playwright verification script for Home.
- [x] Record Playwright as a local dependency.
- [x] Document the verification command.
- [x] Run the script against the local Streamlit server.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Sidebar Menu Layout Stabilization

Status: Done

Goal:
Keep sidebar menu item positions stable when switching pages.

Checklist:

- [x] Normalize active and inactive menu item box sizing.
- [x] Keep active and inactive menu item spacing consistent.
- [x] Run compileall and focused UI verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Sidebar Menu Hierarchy Sizing

Status: Done

Goal:
Make sidebar group labels read as section headers by sizing them slightly larger than their child menu items while preserving stable menu positions.

Checklist:

- [x] Adjust sidebar group and child menu text sizes.
- [x] Refresh the Home application preview screenshot.
- [x] Update user-facing Markdown documentation.
- [x] Run compileall and focused UI screenshot verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Synthetic Target Project Repository

Status: Done

Goal:
Create a separate fake Git project that can be used as a clean AI Commit Advisor analysis target.

Checklist:

- [x] Add a script that creates a sibling sample Git repository.
- [x] Include realistic developers, program list, source files, and commit history.
- [x] Generate sample Excel upload files from the fake repository.
- [x] Document how to create and use the sample target.
- [x] Run compileall and sample generation.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Rich Demo Target Repository Scenario Design

Status: Done

Goal:
Define how the synthetic sample target repository should demonstrate the full AI Commit Advisor feature set before expanding its source files and commit history.

Checklist:

- [x] Document the current sample target strengths and gaps.
- [x] Define target demo scale for programs, developers, and commits.
- [x] Map sample commit scenarios to Git Sync, Mapping, Program Detail, Commit Impact, Risk Analysis, RAG, Project Chat, AI Code Review, and AI Progress.
- [x] Define intentional risk and review scenarios.
- [x] Add agent guidance for checking the demo design before changing sample target repo behavior.
- [x] Add pre-commit documentation check guidance for related Markdown files.
- [x] Update README sample data guidance.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Rich Demo Target Repository Implementation

Status: Done

Goal:
Expand the synthetic sample target repository from a minimal verification dataset into a richer demo dataset that exercises the full AI Commit Advisor workflow.

Checklist:

- [x] Expand generated program rows for additional demo-risk scenarios.
- [x] Expand sample commit history to about 30 commits.
- [x] Add source and documentation scenarios for code review, RAG, Project Chat, commit impact, and AI Progress.
- [x] Add development-plan overrides for delayed, unassigned, and no-related-commit risk scenarios.
- [x] Update focused tests for the richer sample shape.
- [x] Regenerate the sibling sample target repository.
- [x] Update README and sample design documentation if needed.
- [x] Run compileall, pytest, and sample generation verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Sample Project Commit History Expansion

Status: Done

Goal:
Expand the 샘플 프로젝트 commit history from a compact 30-commit demo into a fuller 48-commit workflow history so Git History, Mapping, RAG, Project Chat, Risk Analysis, AI Code Review, and AI Progress have more realistic evidence without making local analysis unnecessarily slow.

Checklist:

- [x] Update the sample design target scale from about 30 commits to 35-50 commits.
- [x] Add meaningful follow-up commits for payment, inventory, dashboard, reports, coupon, settlement, QA, and Project Chat evidence.
- [x] Update focused tests for the expanded commit count and new scenario markers.
- [x] Regenerate the sibling sample project repository.
- [x] Run compileall, focused tests, and sample generation verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Rich Sample Demo Walkthrough And Screenshots

Status: Done

Goal:
Verify the expanded sample target repository through the actual app workflow and align the README walkthrough and feature screenshots with the richer 8-program, 30-commit demo data.

Checklist:

- [x] Document the recommended execution flow to avoid excessive LLM and embedding work.
- [x] Register or refresh the sample project in the app with `C:\dev\ai-advisor-sample-shop`.
- [x] Upload the `advisor_uploads` developer, program, and development-plan Excel files.
- [x] Run Git sync, Mapping, Risk Analysis, AI Progress, Commit Impact, RAG, Project Chat, and AI Code Review checks.
- [x] Document the recommended demo walkthrough, including expected risk scenarios and recommended code review commits.
- [x] Refresh README feature screenshots that changed because of the richer sample data.
- [x] Update `docs/sample-target-repo-demo-design.md` if verified behavior differs from the design.
- [x] Update `AI_CHANGELOG.md`.

## P2 - README Documentation Hub Restructure

Status: Done

Goal:
Make README easier for teammates to scan by turning it into a concise entry document and moving detailed screenshots, feature explanations, setup, and operations guidance into dedicated docs.

Checklist:

- [x] Keep README focused on overview, quick start, sample project entry points, representative screenshots, and documentation links.
- [x] Move feature screenshots into `docs/application-preview.md`.
- [x] Move feature workflow explanations into `docs/feature-guide.md`.
- [x] Move setup, LLM/embedding, RAG operations, and verification commands into `docs/setup-and-operations.md`.
- [x] Use GitHub-friendly relative links from README to each supporting document.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - README Preview-First Section Ordering

Status: Done

Goal:
Make the README easier to scan by moving Application Preview and first-run execution guidance before deeper architecture and operating-model details.

Checklist:

- [x] Move the Application Preview entry near the top of README.
- [x] Put Quick Start and sample project guidance before feature detail sections.
- [x] Keep architecture and Git repository operating model links available after the main workflow entry points.
- [x] Reorder document links so preview, user guide, feature guide, and setup guide are easier to find first.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Local Setup Prerequisites Guide

Status: Done

Goal:
Make the local setup guide explicit about what a teammate must install and prepare before running the project locally, including Python, Docker Desktop, Git, LM Studio, and local chat/embedding models.

Checklist:

- [x] Add a local prerequisites checklist to `docs/setup-and-operations.md`.
- [x] Document Python, Docker Desktop, Git, and optional LM Studio installation checks.
- [x] Explain mock mode versus local LLM mode before the first run commands.
- [x] Document recommended LM Studio chat and embedding model names and matching `PGVECTOR_DIMENSION`.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Application Preview Expanded Sections

Status: Done

Goal:
Make Application Preview behave like an immediately visible visual walkthrough by expanding the screenshot sections instead of hiding each screen behind collapsed details blocks.

Checklist:

- [x] Replace collapsed `details` sections with regular Markdown headings.
- [x] Keep existing screenshot descriptions and image order.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Project Chat GraphRAG Preview Screenshot

Status: Done

Goal:
Add an Application Preview screenshot that explicitly shows Project Chat's Neo4j graph relationship evidence without removing the existing Project Chat screenshots.

Checklist:

- [x] Capture a Project Chat answer with `그래프 관계 근거 보기` expanded.
- [x] Add the new screenshot to `docs/images/features/`.
- [x] Update `docs/application-preview.md` with a short explanation and image link.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run screenshot and markdown/link verification.

## P2 - Interactive GraphRAG Evidence Visualization

Status: Done

Goal:
Make Project Chat's Neo4j graph evidence readable as a compact interactive relationship graph while keeping table and raw metadata available for verification.

Checklist:

- [x] Add a maintained wrapper/helper that converts graph evidence into display nodes and edges.
- [x] Render an interactive `streamlit-agraph` relationship graph inside `그래프 관계 근거 보기`.
- [x] Keep the tabular evidence and move raw JSON under a secondary metadata control that does not nest Streamlit expanders.
- [x] Add focused tests for graph conversion and fallback behavior.
- [x] Update Application Preview screenshot and relevant user-facing docs.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile, focused tests, screenshot, and link verification.

## P2 - Local LLM Env Onboarding Guide

Status: Done

Goal:
Make it clear which environment file teammates should use for lightweight mock runs versus real local LLM/RAG/Project Chat verification.

Checklist:

- [x] Add a local LLM environment example for LM Studio based chat and embedding.
- [x] Keep `.env.example` as the lightweight mock default.
- [x] Explain the two env choices in README Quick Start.
- [x] Document that provider/model changes require regenerating embeddings for RAG Search and Project Chat.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Korean-First User Documentation Cleanup

Status: Done

Goal:
Make user-facing Markdown documentation Korean-first unless a technical identifier, command, file path, API name, or product name is clearer in English.

Checklist:

- [x] Translate English-heavy docs under `docs/` to Korean while preserving code identifiers and commands.
- [x] Keep internal agent/task-management documents out of scope unless they directly face users.
- [x] Align architecture and feature wording where user-facing menu names changed.
- [x] Run markdown/link sanity checks.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Application Dockerfile And Deployment Guide

Status: Done

Goal:
Make local and server deployment repeatable.

Checklist:

- [x] Add application Dockerfile.
- [x] Add compose service for Streamlit app.
- [x] Document environment variables.
- [x] Document migration startup behavior.
- [x] Add deployment smoke check.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Quick Tunnel Demo Runbook And Script

Status: Done

Goal:
Allow an operator to start, inspect, and stop a one-day Cloudflare Quick Tunnel demo without remembering Docker network details or relying on an agent session.

Checklist:

- [x] Add a repository-local start/status/stop script that preserves DB volumes and limits destructive actions to the dedicated Quick Tunnel container.
- [x] Verify local and public Streamlit health and print the generated `trycloudflare.com` URL.
- [x] Document prerequisites, security boundaries, troubleshooting, and shutdown steps in Korean.
- [x] Record the reusable operations decision and rationale.
- [x] Add focused automated tests and run static/runtime-safe verification.
- [x] Update `AI_CHANGELOG.md`.

Related changelog: `Cloudflare Quick Tunnel 하루 시연 절차 자동화`

## P2 - Engineering Decisions Log

Status: Done

Goal:
Separate non-failure engineering, operations, verification, automation, and documentation-structure decisions from failure history and the change log.

Checklist:

- [x] Add a dedicated engineering decisions document and reusable entry template.
- [x] Record the screenshot capture automation direction as the first decision.
- [x] Add agent policy for when to update the decision log.
- [x] Link the decision log from README.
- [x] Clarify the boundary between failure history and decision history.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Feature Screenshot Capture Automation

Status: Done

Goal:
Make README and Application Preview capture work more repeatable by using feature-based Playwright scenarios instead of one-off manual browser flows.

Checklist:

- [x] Add an extensible feature screenshot capture script.
- [x] Include Home and Project Chat starter scenarios.
- [x] Keep the existing Home verification command compatible.
- [x] Document capture commands and runtime-surface guidance.
- [x] Update engineering decision follow-up notes.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run focused script and documentation verification.

## P2 - Architecture Document Path Cleanup

Status: Done

Goal:
Move the architecture guide into the `docs/` documentation set so the README hub and agent documentation checklist use one consistent document location.

Checklist:

- [x] Move the root architecture guide to `docs/architecture.md`.
- [x] Update README document hub link.
- [x] Update agent documentation checklist and rationale guidance.
- [x] Replace stale architecture document path references in Markdown.
- [x] Record the documentation structure decision.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown path and whitespace checks.

## P2 - Application Preview Rename

Status: Done

Goal:
Rename the screenshot-focused documentation to Application Preview so the document reads like an app preview instead of a raw image collection.

Checklist:

- [x] Move the screenshot-focused document to `docs/application-preview.md`.
- [x] Update README and feature guide links.
- [x] Update `AGENTS.md` screenshot guidance naming.
- [x] Update setup/operations and engineering decision references.
- [x] Replace stale Markdown path references.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown path and whitespace checks.

## P2 - Sample Project Wording Cleanup

Status: Done

Goal:
Make sample/demo documentation read naturally in Korean by using reader-facing `샘플 프로젝트` wording instead of literal internal repository terminology.

Checklist:

- [x] Add agent guidance for natural Korean sample/demo wording.
- [x] Update README sample project wording.
- [x] Update sample project design and verification guide prose.
- [x] Update related engineering decision rationale.
- [x] Keep code identifiers and file names unchanged.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run targeted wording and whitespace checks.

## P2 - Natural Wording Policy Generalization

Status: Done

Goal:
Keep the natural Korean documentation policy useful without turning `AGENTS.md` into a literal banned-phrase list.

Checklist:

- [x] Remove the explicit awkward-phrase list from `AGENTS.md`.
- [x] Keep the preferred reader-facing sample project wording.
- [x] Generalize the policy around avoiding direct translations of internal repository roles and demo mechanics.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run targeted wording and whitespace checks.

## P2 - Reader-Facing Wording Policy Simplification

Status: Done

Goal:
Keep `AGENTS.md` natural wording guidance principle-based instead of listing preferred phrases.

Checklist:

- [x] Remove preferred phrase examples from the natural Korean documentation wording policy.
- [x] Keep the guidance about reader-facing product terms.
- [x] Keep the exception for stable technical file paths.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run targeted wording and whitespace checks.

## P2 - Documentation Impact Gate Policy

Status: Done

Goal:
Make agent documentation impact review explicit before meaningful work starts, especially when maintainability, verification policy, structural tradeoffs, or agent behavior are part of the request.

Checklist:

- [x] Add a `Documentation Impact Gate` to `AGENTS.md`.
- [x] Require `docs/engineering-decisions.md` as a review candidate for maintainability, future reuse, verification policy, structural tradeoff, operating policy, or agent behavior changes.
- [x] Record the policy decision in `docs/engineering-decisions.md`.
- [x] Record the missed engineering-decision review as reusable failure history.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run targeted documentation and whitespace checks.

## P2 - Sidebar Navigation Structure Stabilization

Status: Done

Goal:
Remove sidebar menu position jitter by rendering active and inactive navigation items with the same Streamlit button structure instead of mixing buttons with custom active `div` markup.

Checklist:

- [x] Render active and inactive sidebar menu items through the same `st.button` path.
- [x] Remove custom `.nav-active` markup and CSS from the sidebar menu.
- [x] Expand Playwright sidebar stability checks to compare active/inactive item boxes, text offsets, and adjacent spacing.
- [x] Record the maintainability decision in `docs/engineering-decisions.md`.
- [x] Record the previous CSS-only stabilization gap in `docs/failure-history.md`.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run compile and focused UI verification.

## P2 - AI Agent Onboarding Guide

Status: Done

Goal:
Help teammates who are new to AI Agent coding understand how to use this project with Codex without repeating durable project rules in every prompt.

Checklist:

- [x] Add a beginner-friendly onboarding guide for AI Agent coding in this project.
- [x] Explain what `AGENTS.md`, `ROADMAP.md`, and `AI_CHANGELOG.md` are for.
- [x] Clarify when Codex reads project instructions automatically and when prompts should mention documentation checks.
- [x] Link the onboarding guide from README.
- [x] Update `AI_CHANGELOG.md`.
- [x] Run markdown/link sanity checks.

## P2 - Global Project Context

Status: Done

Goal:
Move repeated page-level project selection into a shared app-level project context so project-based workflows stay consistent across menus.

Checklist:

- [x] Add a shared project context helper for loading, selecting, validating, and displaying the current project.
- [x] Render the current project selector once in the sidebar.
- [x] Convert analysis and project-scoped management pages to use the shared project context instead of local project selectors.
- [x] Keep project creation, sample data generation, and global settings outside forced project context where appropriate.
- [x] Record the maintainability decision in `docs/engineering-decisions.md`.
- [x] Update related user-facing and architecture documentation where the navigation/project-selection flow changes.
- [x] Run compile, tests, and focused UI verification.
- [x] Update `AI_CHANGELOG.md`.

## P2 - Home Current Project Focus

Status: Done

Goal:
Align Home with the global current project selector so the first screen reads as the selected project's command center instead of an all-project aggregate.

Checklist:

- [x] Make Home use the shared current project context.
- [x] Scope Home KPIs, pipeline status, next actions, and charts to the current project.
- [x] Keep app-level counts only as secondary context where useful.
- [x] Update user-facing and architecture documentation as needed.
- [x] Refresh the Home Application Preview screenshot.
- [x] Run compile, tests, and focused UI verification.
- [x] Update `AI_CHANGELOG.md`.

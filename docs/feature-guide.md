# 기능 가이드

이 문서는 AI Commit Advisor의 주요 기능을 화면 흐름 기준으로 설명합니다. 전체 화면 예시는 [Application Preview](application-preview.md)를 참고하세요.

## AI / LLM 활용 흐름

AI Commit Advisor는 개발계획, Git 변경 이력, 현재 소스 코드를 하나의 분석 흐름으로 연결합니다. LLM은 판단이 필요한 비교, 요약, 리뷰에 사용하고, RAG와 규칙 분석은 근거 검색과 일관된 리스크 탐지에 사용합니다.

| 단계 | 입력 데이터 | AI/LLM 활용 | 결과 |
|---|---|---|---|
| Git 수집 | commit message, author, changed files, diff | 분석 대상 변경 이력 구성 | `git_commits`, `commit_files` 저장 |
| RAG 검색 준비 | 현재 소스 파일, 프로그램 정보, 커밋 메시지, diff | 질문과 관련된 근거를 찾기 위한 검색 준비 | `document_chunks`, `vector_items` 저장 |
| 프로그램-커밋 매핑 | 프로그램 목록, 커밋, 변경 파일, RAG 후보 | LLM이 관련 프로그램과 구현상태를 판단 | 관련도, 구현상태, 판단 근거 저장 |
| 구현상태 분석 | 프로그램 계획, 관련 커밋, 매핑 결과 | LLM이 프로그램 단위 구현 상태를 요약 | NOT_STARTED / IN_PROGRESS / COMPLETED / UNKNOWN |
| Project Chat | 현재 소스 검색 결과, Neo4j graph evidence | LLM이 검증된 소스 근거와 보조 graph 관계 근거로 질문에 답변 | 저장된 대화, 파일 경로/라인 근거, 그래프 관계 근거가 포함된 답변 |
| AI Code Review | 앱 서버 Git 저장소의 commit diff 중심, 필요 시 서버 clone local diff | LLM이 변경 의도, 위험, 버그, 리팩토링 포인트 분석 | 리뷰 요약, 버그 후보, 개선 제안 |
| Knowledge Graph | 프로젝트, 프로그램, 커밋, 파일, Java class/import | Neo4j graph read model로 관계 경로와 도메인 묶음을 구성 | 도메인 요약, 저장 그래프 기준 클래스 관계도, 커밋-프로그램-클래스 영향 경로 |
| Risk Analysis | 일정, 진척도, 커밋 활동, AI 매핑 결과 | 규칙 기반 누락/지연/불확실성 탐지 | 위험 프로그램과 evidence 저장 |

Project Chat은 현재 파일 내용과 일치하는 소스 근거만 기본 답변 근거로 사용합니다. 커밋 diff는 변경 이력으로 취급하며 현재 코드 근거와 구분합니다. Neo4j graph가 준비되어 있으면 프로그램, 커밋, 파일, class, domain 관계를 보조 근거로 함께 보여줍니다. Knowledge Graph가 최신 상태이면 Project Chat의 `관계 질문` 영역에서 프로그램 구현 근거, 커밋 영향 범위, class/domain 연결 질문을 바로 시작할 수 있습니다. 대화는 프로젝트별 session과 message로 저장되어 이전 질문과 답변을 다시 열람할 수 있습니다.

## 권장 사용 순서

왼쪽 사이드바는 현재 작업할 프로젝트를 먼저 고른 뒤, 업무 영역을 나타내는 접이식 메뉴 그룹과 실제 화면으로 이동하는 하위 메뉴를 제공합니다. 현재 위치의 그룹은 기본으로 펼쳐지고, 다른 업무 영역은 필요할 때만 열어 사이드바 스크롤 부담을 줄입니다.

현재 프로젝트 선택은 URL의 `project_id` 값에도 함께 저장됩니다. 브라우저를 새로고침하거나 같은 URL을 다시 열어도 가능한 한 같은 프로젝트를 유지해, 이름이 비슷한 샘플·검증 프로젝트 사이에서 분석 대상이 갑자기 바뀌는 일을 줄입니다. URL의 프로젝트가 삭제되었거나 존재하지 않으면 앱은 남아 있는 첫 프로젝트로 복구합니다.

프로젝트를 바꾸면 Mapping, Program Detail, Commit Impact, Git History, Risk Analysis, AI Progress, RAG 검색 같은 화면의 프로그램·커밋·필터 선택은 프로젝트별로 따로 유지됩니다. 이전 프로젝트에서 고른 커밋이나 프로그램이 새 프로젝트 화면에 남아 보이지 않게 하기 위한 동작입니다.

Home은 사이드바에서 선택한 현재 프로젝트의 핵심 지표, 다음 작업, 분석 상태, 진척도, 리스크 프로그램을 보여주는 첫 화면입니다. 전체 프로젝트 수는 보조 지표로만 표시하고, 프로그램·커밋·매핑·리스크 판단은 현재 프로젝트 기준으로 계산합니다.

## 사이드바 메뉴 구조

사이드바 메뉴는 작업 흐름에 맞춰 아래 그룹으로 나뉩니다. 현재 위치의 그룹은 자동으로 펼쳐지고, 다른 그룹은 필요할 때 열어 이동합니다.

| 메뉴 그룹 | 화면 | 주로 사용하는 때 |
|---|---|---|
| 개요 | Home | 현재 프로젝트의 핵심 지표, 다음 작업, 분석 상태를 먼저 확인할 때 |
| 개요 | Dashboard | 프로젝트 현황, AI Resource Radar, 자원관리 참고 지표, 개발자별 부하, 예상 지연/난이도를 볼 때 |
| 개요 | AI Progress | 계획 진척도와 AI 진척도 차이, 리스크 프로그램, 구현상태 분석 결과를 비교할 때 |
| 개요 | AI 운영 현황 | 연결된 LLM/embedding/Neo4j, GraphRAG 준비 상태, AI 실행 근거, 품질 점검, 호출 기록을 확인할 때 |
| 프로젝트 설정 | 프로젝트/Git 설정 | 프로젝트 이름, 설명, 앱 서버 Git 저장소 경로를 등록하거나 삭제할 때 |
| 프로젝트 설정 | Git 동기화 | 앱 서버 Git 저장소 상태를 확인하고 commit/diff를 DB에 수집할 때 |
| 프로젝트 설정 | 샘플 데이터 생성 | 데모나 업로드 테스트용 Excel 산출물을 만들 때 |
| 산출물 관리 | 개발자 현황 | Git author 기반 개발자 자동 추출과 commit/file 활동 현황을 볼 때 |
| 산출물 관리 | 개발자 목록 | 현재 프로젝트 개발자 연결과 전역 개발자 마스터를 조회·추가·업로드할 때 |
| 산출물 관리 | 프로그램 목록 | 프로그램 데이터를 조회·수정·삭제하거나 Excel로 업로드할 때 |
| 산출물 관리 | 개발계획 | 계획 일정과 진행률을 조회·수정·일괄 업데이트하거나 Excel로 업로드할 때 |
| 산출물 관리 | 표준용어/표준단어 | 한글 업무 용어를 코드/DB 식별자 검색과 연결할 때 |
| 분석 실행 | Mapping | Git commit과 프로그램의 관련성, 구현상태를 분석할 때 |
| 분석 실행 | Risk Analysis | 일정, 매핑, commit 활동 기반 리스크를 탐지하고 resolved 처리할 때 |
| 분석 실행 | RAG 검색 | 현재 소스/프로그램/commit 근거를 만들고 검색 품질을 확인할 때 |
| 분석 실행 | Project Chat | 현재 소스 근거 기반으로 프로젝트 질문을 하고 저장된 대화를 관리할 때 |
| 분석 실행 | AI Code Review | 최신 commit 또는 특정 commit diff를 LLM으로 리뷰할 때 |
| 분석 결과 | Program Detail | 특정 프로그램의 계획, AI 진척도, 관련 commit, 리스크를 상세 확인할 때 |
| 분석 결과 | Git History | 프로젝트별 commit 목록, 변경 파일, diff preview를 탐색할 때 |
| 분석 결과 | Commit Impact | 특정 commit이 영향을 주는 프로그램, 개발자, 파일 범위를 볼 때 |
| 분석 결과 | Knowledge Graph | 프로젝트, 프로그램, 커밋, 파일, 클래스, 도메인 관계를 Neo4j 그래프로 동기화하고 저장된 관계를 확인할 때 |
| 분석 결과 | 개발계획 대시보드 | 개발계획 기준 프로그램 상태, 완료율, 담당자별 배정을 볼 때 |
| 관리 | 설정 | DB, LLM, embedding provider 설정 상태를 확인할 때 |

전체 화면 예시는 [Application Preview](application-preview.md)에서 현재 메뉴 구조가 보이는 screenshot으로 확인할 수 있습니다.

1. 프로젝트/Git 설정 화면에서 프로젝트와 앱 서버에서 접근 가능한 Git 저장소 경로를 등록합니다.
2. 사이드바의 현재 프로젝트에서 작업할 프로젝트를 선택합니다.
3. Git 동기화 화면에서 앱 서버 저장소 상태를 확인한 뒤 증분 동기화로 새 commit과 diff를 저장합니다. 처음 수집하거나 DB를 다시 맞춰야 할 때만 전체 수집을 사용합니다.
4. 개발자 현황 화면에서 Git author 기반 개발자 자동 추출을 수행합니다.
5. 산출물 관리 메뉴에서 개발자 목록, 프로그램 목록, 개발계획을 직접 관리하거나 Excel로 업로드합니다.
6. 산출물 관리 > 표준용어/표준단어 화면에서 SI 산출물 Excel을 업로드해 한글 업무 용어와 코드 식별자를 연결합니다.
7. 필요하면 프로젝트 설정 > 샘플 데이터 생성 화면에서 데모용 Excel 산출물을 생성합니다.
8. Mapping 화면에서 커밋 기준 분석을 먼저 실행합니다.
9. Risk Analysis에서 리스크를 탐지하고, Program Detail, Commit Impact, Knowledge Graph, AI Progress에서 분석 결과를 검토합니다.
10. RAG Search와 Project Chat에서 현재 소스 기반 근거 검색과 질의응답을 확인합니다.
11. AI Code Review에서 최신 commit 또는 특정 commit을 중심으로 리뷰합니다.

## 프로젝트 관리와 삭제

프로젝트/Git 설정 화면은 프로젝트 이름, 설명, 앱 서버 Git 저장소 경로를 관리합니다. 기존 프로젝트를 선택하면 마지막 Git 동기화 상태와 저장소 상태를 확인할 수 있고, 같은 화면에서 분석 데이터 초기화나 프로젝트 삭제를 실행할 수 있습니다.

분석 데이터 초기화는 같은 프로젝트의 분석 결과를 다시 만들거나 검증할 때 사용합니다. 프로젝트명, Git 저장소 경로, 프로그램/개발계획, 프로젝트 개발자 연결, 표준용어/표준단어는 유지하고, Git commit, 변경 파일, 매핑, 분석 실행 이력, 구현상태 분석, 리스크, 자원관리 snapshot, RAG 근거/검색 데이터, Project Chat, AI Code Review 결과만 삭제합니다. 초기화 전 화면은 유지/초기화 대상을 나누어 보여주고, 프로젝트명을 다시 입력해야 실행됩니다.

프로젝트 삭제는 더 이상 사용하지 않는 프로젝트를 정리할 때 사용합니다. 삭제 전 화면은 프로그램, Git commit, 변경 파일, 매핑, 분석 실행 이력, 리스크, 자원관리 snapshot, RAG 근거/검색 데이터, Project Chat, AI Code Review, 표준용어/표준단어 등 삭제될 프로젝트 소유 데이터 건수를 보여주고, 프로젝트명을 다시 입력해야 삭제가 실행됩니다.

개발자 정보는 두 층으로 관리합니다. `developers`는 여러 프로젝트에서 재사용될 수 있는 전역 개발자 마스터이고, `project_developers`는 특정 프로젝트에 그 개발자가 참여한다는 연결 정보입니다. 프로젝트 삭제는 해당 프로젝트의 분석 데이터와 개발자 연결을 삭제하지만, 다른 프로젝트에서 재사용될 수 있는 전역 `developers` row는 삭제하지 않습니다.

## 데이터 관리

산출물 관리 메뉴의 개발자 목록, 프로그램 목록, 개발계획 데이터는 Excel 업로드와 화면 기반 직접 관리를 모두 지원합니다.

- 개발자 관리: 현재 프로젝트 개발자 조회, 전역 개발자 마스터 조회, Git author 기반 자동 추출, 검색, 직접 추가/수정/삭제, Excel 양식 다운로드, 업로드 전 검증
- 프로그램 관리: 현재 프로젝트 기준 검색, 직접 추가/수정/삭제, Excel 양식 다운로드, 업로드 전 검증/미리보기, 신규/수정 요약
- 개발계획 관리: 현재 계획 조회, 직접 수정, 일괄 업데이트, Excel 양식 다운로드, 업로드 전 검증

개발자 목록 화면은 현재 프로젝트에 연결된 개발자를 기본으로 보여줍니다. 직접 추가와 Excel 업로드는 전역 개발자 마스터를 생성하거나 업데이트한 뒤, 현재 프로젝트가 선택되어 있으면 그 프로젝트의 개발자로도 연결합니다. 전체 개발자 마스터를 확인해야 할 때는 `전역 마스터` 탭을 사용합니다.

Git author 기반 자동 추출도 같은 정책을 따릅니다. 커밋 author에서 추정한 개발자는 전역 마스터에 저장하고, 해당 Git 동기화 프로젝트의 개발자 연결을 만듭니다. 같은 개발자가 다른 프로젝트에도 등장하면 전역 row는 재사용하고 프로젝트 연결만 추가합니다.

개발자 삭제는 v1에서 전역 개발자 마스터 삭제입니다. 현재 프로젝트에서만 연결을 제거하는 기능은 아직 제공하지 않으므로, 삭제 전에는 다른 프로젝트 연결과 담당 프로그램 영향을 확인해야 합니다.

업로드 저장 전에는 필수 컬럼, 중복 ID, 날짜 형식, 시작/종료일 순서, 진행률 범위를 검증합니다.

프로그램 목록 화면은 새 프로젝트를 만들지 않습니다. 새 프로젝트가 필요하면 먼저 `프로젝트/Git 설정`에서 프로젝트를 등록한 뒤, 사이드바의 현재 프로젝트로 선택하고 프로그램을 추가하거나 업로드합니다.

## 표준용어/표준단어

표준용어/표준단어 화면은 SI 프로젝트 산출물의 한글 업무 용어를 코드와 DB 식별자 검색에 연결합니다.

Excel 입력은 가볍게 유지합니다.

- 필수: `korean_term`, `english_term`
- 권장: `abbreviation`
- 선택: `term_type`, `description`

앱은 영문명과 약어에서 `camelCase`, `PascalCase`, `snake_case`, `UPPER_SNAKE_CASE`, compact lowercase, token words 같은 검색용 변형을 자동 파생합니다.

예를 들어 `결제금액 / payment amount / pay amt`를 업로드하면 Project Chat은 `결제 금액` 질문을 `payment amount`, `paymentAmount`, `payment_amount`, `pay_amt`, `amount` 같은 검색 후보로 확장합니다.

## Mapping

Mapping은 프로그램 목록과 Git 커밋 정보를 LLM으로 분석해 `program_commit_mappings`에 관련도, 구현상태, 판단 근거를 저장합니다.

기본 추천 방식은 커밋 기준 분석입니다. 커밋 하나를 기준으로 후보 프로그램 TOP N개를 먼저 추린 뒤 LLM에 전달하므로, 모든 프로그램과 모든 커밋 조합을 무작정 호출하지 않습니다. 모든 커밋 매핑이 완료된 상태에서는 재분석 옵션을 접어 두고, 필요한 경우에만 다시 열어 실행합니다.

주요 정책:

- 기본값은 커밋 1개당 후보 프로그램 TOP 10입니다.
- diff_text는 파일별 앞부분만 사용하고 입력 길이를 제한합니다.
- 이미 같은 `program_id + commit_id` 매핑이 있으면 새로 만들지 않고 업데이트합니다.
- 일괄 분석은 이미 `completed`인 커밋을 건너뛰므로 중단 후 재시작할 수 있습니다.
- 매핑 피드백 리뷰 큐에서 근거 부족, 판단불가, 낮은 관련도 매핑을 우선 검토할 수 있습니다.

## Program Detail과 AI Progress

Program Detail은 특정 프로그램의 계획, AI 진척도, 관련 커밋, 개발자 기여, 리스크, 구현상태 분석 결과를 한 화면에서 확인합니다.

AI Progress는 계획 진척도와 LLM 매핑 결과 기반 AI 진척도를 비교합니다. 저장된 프로그램 단위 구현상태 분석 결과는 수치를 대체하지 않고 업무 검토용 요약 근거로 함께 표시합니다.

분석 결과 화면은 업무 판단에 필요한 라벨을 우선 사용합니다. commit hash, program ID, file path처럼 근거 추적에 필요한 식별자는 그대로 보이지만, 날짜 객체나 내부 `risk_type` 같은 원본 데이터 구조는 기본 화면에 그대로 노출하지 않습니다.

구현상태 분석 화면 라벨은 단정이 아닌 추정입니다.

| 내부 상태 | 화면 라벨 | 의미 |
|---|---|---|
| `NOT_STARTED` | 구현전 추정 | 관련 구현 근거가 거의 없다고 추정 |
| `IN_PROGRESS` | 진행중 추정 | 구현 근거는 있으나 완료 여부가 불확실 |
| `COMPLETED` | 구현완료 추정 | 관련 커밋과 매핑 근거상 구현 완료 가능성이 높음 |
| `UNKNOWN` | 판단불가 | 근거가 부족하거나 상충됨 |

## Commit Impact

Commit Impact는 특정 Git commit이 어떤 프로그램, 개발자, 모듈, 파일에 영향을 주는지 분석합니다. 새로운 LLM 호출 없이 기존 `program_commit_mappings`, `git_commits`, `commit_files`, `programs` 데이터를 재사용합니다.

주요 기능:

- commit message, author, 날짜 필터
- 영향 프로그램 목록과 관련도 점수 확인
- 변경 파일 목록과 diff snippet 확인
- 영향 프로그램 수, 영향 개발자 수, 영향 파일 수 KPI
- 영향도 점수 `LOW`, `MEDIUM`, `HIGH` 계산

## Knowledge Graph

Knowledge Graph는 PostgreSQL에 저장된 프로젝트 분석 결과와 앱 서버 Git 저장소의 Java 소스 구조를 Neo4j에서 탐색할 수 있는 관계 그래프로 투영합니다. 원본 데이터는 계속 PostgreSQL과 앱 서버 Git 저장소이며, Neo4j는 클래스 관계, 도메인 묶음, 커밋 영향 경로를 빠르게 설명하기 위한 read model입니다. Java 구조 추출은 주석/문자열을 제외한 경량 parser로 `class`, `interface`, `enum`, `record`, annotation type, static import, nested member type을 읽습니다.

화면은 현재 프로젝트 기준 그래프 preview를 먼저 구성하고, `Graph 상태`에서 Repo HEAD, DB Git Sync HEAD, Neo4j에 마지막으로 반영된 Graph HEAD를 비교합니다. 이 상태가 `갱신 필요`이면 Git Sync나 mapping 이후 graph read model이 오래된 상태라는 뜻입니다. 처음 저장하거나 기준이 꼬였을 때는 `전체 재동기화`를 실행하고, Git Sync 이후 일반 변경분만 반영할 때는 `최신 변경분만 Neo4j 반영`을 사용합니다.

동기화 후에는 클래스 관계도, 영향 경로, node/edge 저장 상태를 Neo4j에 저장된 그래프에서 다시 조회해 보여줍니다. `관계 탐색` 탭에서는 프로그램, 클래스, 도메인, 커밋 중 하나를 선택해 주변 path를 깊이와 관계 종류로 좁혀 볼 수 있습니다. Neo4j 동기화 결과의 `Neo4j 동기화 실행 세부`에서는 batch 크기, 완료 batch 수, retry 수, 실패 operation을 확인할 수 있습니다. `동기화 준비 경고`에 generated source, build output, test fixture, type 선언 없음이 표시되면 해당 파일은 graph class/import 근거에서 제외됐다는 뜻입니다. Neo4j 없이 가볍게 실행해야 할 때만 `NEO4J_ENABLED=false`로 바꾸면 preview는 유지되고 저장 동기화와 저장 그래프 조회만 건너뜁니다.

주요 기능:

- 프로젝트, 프로그램, 커밋, 파일, 클래스, 도메인 node 구성
- `MAPPED_TO_COMMIT`, `TOUCHES_FILE`, `CONTAINS_CLASS`, `IMPORTS_CLASS`, `TOUCHES_DOMAIN` 같은 관계 구성
- 도메인별 프로그램/파일/클래스/커밋 묶음 확인
- 선택한 프로그램, 클래스, 도메인, 커밋 주변 path와 node properties 확인
- Neo4j에 저장된 Java package/import 기반 클래스 관계도 확인
- Neo4j에 저장된 커밋-프로그램-파일-클래스 영향 경로 확인
- Neo4j에 저장된 node/edge 종류와 수 확인
- Repo HEAD, DB Sync HEAD, Graph HEAD 기준 최신성 확인
- 변경된 Java 파일의 current source 관계와 program mapping edge 증분 반영
- 프로젝트 분석 데이터 초기화나 프로젝트 삭제 시 선택 프로젝트의 Neo4j graph 정리

Neo4j graph는 LLM을 대체하지 않습니다. 대신 RAG/Project Chat, Mapping, Commit Impact에서 쓰는 근거를 관계 구조로 재해석할 수 있는 기반을 제공합니다. `Knowledge Graph`에서 최신 graph를 유지해 두면 Project Chat은 질문과 검색된 소스 근거를 seed로 삼아 Neo4j의 영향 경로, class import, domain summary를 보조 근거로 사용할 수 있습니다.

## Git History

Git History는 현재 프로젝트의 커밋 이력을 탐색하는 화면입니다. Commit Impact가 선택한 커밋의 업무 영향도를 분석하는 화면이라면, Git History는 커밋 목록, 변경 파일, diff를 빠르게 확인하는 조회 화면입니다.

주요 기능:

- commit message, 작성자, 파일 경로, 날짜 필터
- 일자별 commit 수와 작성자별 commit 수 그래프
- 선택한 commit의 hash, message, author, commit time 확인
- DB에 저장된 변경 파일 목록과 diff preview 확인
- 앱 서버 Git 저장소에서 `git show` 기반 전체 diff 조회

전체 diff 조회는 브라우저 사용자 PC가 아니라 앱 서버에 등록된 Git 저장소 경로에서 실행됩니다. 따라서 사내 서버 운영에서는 서버에 clone된 저장소가 최신 상태인지 먼저 확인한 뒤 Git 동기화를 실행해야 합니다.

## Git 동기화와 저장소 상태

Git 동기화 화면은 앱 서버 Git 저장소 상태와 DB 동기화 상태를 함께 보여줍니다.

확인 항목:

- Repo HEAD와 DB sync commit
- 현재 branch
- upstream branch
- upstream 대비 ahead/behind 수
- working tree local 변경 여부와 변경 파일 수
- 등록 경로가 `REPO_STORAGE_ROOT` 하위인지 여부

Repo HEAD와 DB sync commit이 다르면 서버 저장소에는 새 commit이 있지만 앱 DB에는 아직 수집되지 않은 상태입니다. 이 경우 Git 동기화 화면에서 증분 동기화 또는 전체 수집을 실행합니다. working tree에 local 변경이 있으면 분석용 서버 clone에 임시 변경이 남아 있는 상태이므로, 운영자가 저장소 갱신 정책을 먼저 확인해야 합니다.

Repo HEAD와 DB sync commit이 같으면 DB는 최신 상태입니다. 이때는 Git 수집을 반복하기보다 다음 분석 화면으로 이동하고, 새 commit을 가져온 뒤 증분 동기화를 실행하는 흐름을 기본으로 봅니다.

Git 동기화 화면의 `동기화 후 다음 작업`은 Git Sync 이후 AI 근거를 최신화하는 순서를 보여줍니다. 권장 순서는 현재 소스 근거 갱신, 검색 준비, Mapping, Risk Analysis, Knowledge Graph 갱신으로 구성되며, 각 항목은 현재 값, 예상 소요, 비용/부하 주의, 이동할 화면을 함께 표시합니다. 이 패널은 모든 후속 작업을 자동 실행하지 않습니다. embedding이나 LLM 호출이 필요한 작업은 사용자가 해당 화면으로 이동해 명시적으로 실행해야 합니다.

## Risk Analysis

Risk Analysis는 프로그램 목록, 개발계획, Git 커밋, LLM 매핑 결과를 기반으로 누락 가능성이 있는 프로그램과 위험 프로그램을 자동 탐지합니다.

탐지 규칙 예시:

- 프로그램은 등록되어 있지만 관련 commit이 없음
- 계획 종료일이 지났지만 AI 진척도 < 100
- 계획 진척도와 AI 진척도 차이가 30 이상
- LLM 매핑 결과가 모두 판단불가
- 최근 14일 동안 관련 commit이 없음
- 담당자가 없거나 개발자 정보가 불명확함
- 예상 종료일이 계획 종료일보다 7일 이상 늦어질 것으로 계산됨

## RAG Search와 Project Chat

RAG Search는 현재 소스 파일, 프로그램 정보, commit 메시지, 변경 파일/diff를 검색 가능한 근거로 만들고 질문과 비슷한 근거를 찾습니다.

Project Chat은 현재 파일과 일치한다고 검증된 소스 근거만 기본 답변 근거로 사용합니다. 표준용어/표준단어가 등록되어 있으면 한글 업무 질문을 영문명, 약어, 코드 식별자 후보로 확장해 검색합니다. Neo4j graph가 준비된 프로젝트에서는 질문, 확장 쿼리, 검색된 파일/class 후보를 바탕으로 program-commit-file-class 영향 경로와 class import 관계를 보조 근거로 붙입니다. 검증된 현재 소스 근거가 없으면 graph 근거가 있더라도 추측성 답변을 만들지 않고 추가 준비 또는 검색어 조정이 필요하다고 안내합니다.

Project Chat 화면의 `대화 관리` 영역에서 프로젝트별 저장된 session을 선택할 수 있고, `새 대화 시작`은 기존 이력을 지우지 않고 새 session을 만듭니다. Assistant 답변에는 `답변 근거 보기`와 `그래프 관계 근거 보기`가 분리되어 있으며, `근거 복사용 Markdown` 영역은 답변, 현재 소스 근거, 이력/참고 근거, 그래프 관계 근거를 회의록이나 리뷰 문서에 붙여 넣기 쉬운 형식으로 제공합니다.

`관계 질문` 템플릿은 질문 품질을 보장하는 자동 분석이 아니라 시작 문장입니다. Graph 상태가 `갱신 필요`, `저장 필요`, `실패`, `미사용`이면 버튼은 비활성화되고, 먼저 `Knowledge Graph`에서 최신 변경분 반영 또는 전체 재동기화를 실행해야 합니다.

이 설계는 오래된 근거나 commit diff만으로 현재 코드처럼 답변하는 문제를 줄이기 위한 것입니다. 사용자가 한글 업무 용어로 질문하더라도 실제 소스에는 영문 변수명, 약어, DB 컬럼명, class/function 이름으로 남는 경우가 많아 검색어나 근거가 제대로 매핑되지 않을 수 있습니다. 표준용어/표준단어가 있으면 한글 질의와 함께 관련 영문명, 약어, 코드 식별자 표현까지 검색해 이 문제를 줄이고, 현재 파일 검증은 답변 근거가 실제 checkout 상태와 어긋나지 않도록 제한합니다. Graph evidence는 관계를 설명하는 보조 근거라서 현재 코드 사실을 단독으로 증명하지 않습니다.

현재 소스 파일을 수정하거나 브랜치/HEAD가 바뀐 뒤에는 Project Chat의 `답변 근거 상태`를 확인하고 필요 시 `최신 변경분 반영` 또는 `전체 소스 다시 읽기`를 실행하세요. 화면의 `검색 준비`가 전체 근거 수보다 적으면 `RAG 검색 > 검색 준비`에서 남은 작업을 제한 수량으로 실행합니다.

`현재 프로젝트`, `TOP K`, `검색 준비`, `최신 변경분 반영`, `전체 소스 다시 읽기`처럼 의미를 바로 알기 어려운 control에는 물음표 도움말이 붙어 있습니다. 화면 설명을 길게 늘리지 않기 위해 기본 화면에는 짧은 label만 두고, 필요한 경우 물음표에 마우스를 올려 기준과 사용 시점을 확인합니다.

## AI Code Review

AI Code Review는 앱 서버 Git 저장소의 commit 이력을 LLM으로 리뷰합니다. 중앙 앱 서버에서 실행하는 검증에서는 개발자 개인 PC의 작업트리나 staged 변경을 직접 볼 수 없으므로, 기본 흐름은 `최신 커밋` 또는 `특정 커밋` 리뷰입니다.

지원 대상:

- 최신 commit: `HEAD`
- 특정 commit: commit hash 또는 rev 입력
- 서버 작업트리 변경: 앱 서버 clone에 아직 stage하지 않은 local 변경이 남아 있을 때의 `git diff`
- 서버 Staged 변경: 앱 서버 clone에서 `git add`된 local 변경이 남아 있을 때의 `git diff --cached`

서버 작업트리와 서버 Staged 변경은 운영자가 분석용 clone 상태를 점검하거나 임시 변경을 리뷰할 때 쓰는 보조 옵션입니다. 일반 개발자가 각자 PC에서 작성한 미커밋 변경은 앱 서버가 직접 읽지 못하므로 Git push 이후 커밋 이력 기반으로 리뷰하는 흐름이 더 자연스럽습니다.

리뷰 결과는 `code_review_results` 테이블에 저장되며, 변경 의도, 영향 범위, 위험도, 버그 후보, 리팩토링 제안을 포함합니다.

## 대시보드

- 개발계획 대시보드: 프로그램 목록, 상태별 프로그램 수, 개발자별 배정 프로그램 수, 지연 프로그램, 계획 대비 완료율
- Dashboard: 프로젝트 계획/AI/Git 활동 요약, AI Resource Radar, 개발자별 업무량·난이도, 예상 지연 프로그램, 고객가치 참고 지표, 자원관리 snapshot 추세
- AI 운영 현황: LLM/embedding/Neo4j 연결 상태, Knowledge Graph/GraphRAG 준비 상태, AI 실행 바로가기, AI 근거 추적, 프로젝트 AI 품질 점검, 주간 점검 보고서, AI 호출 기록

## 자원관리 지표

Dashboard의 자원관리 지표는 AX Use Case의 개발자별 업무량, 진행도, 난이도, 일정 리스크, 고객가치 추정을 한 화면에서 확인하기 위한 영역입니다. 기본 지표는 `resource_metrics_service.py`에서 현재 DB 상태 기준으로 계산하고, PL이 `현재 지표 저장`을 누르면 `resource_metric_snapshots`에 기준 시점 snapshot을 저장합니다.

`AI Resource Radar`는 Dashboard에서 PL이 먼저 확인할 프로그램을 우선순위로 보여줍니다. Radar는 AI 매핑/진척도 근거, 미해결 리스크, 예상 지연, diff 규모, cross-program commit, 관련 commit 부재, 담당자 업무량 신호를 설명 가능한 점수로 합산합니다. `PL Briefing 생성`을 누르면 이 Radar 근거를 LLM이 구조화된 요약, 우선 확인 항목, 회의 질문, 다음 액션으로 정리하고 앱이 일관된 Markdown 브리핑으로 표시합니다. 생성된 브리핑은 `pl_briefing_history`에 저장되며 Dashboard에서 최근 브리핑과 이력 표를 다시 확인할 수 있습니다. LLM을 사용할 수 없는 mock 환경에서는 같은 근거로 만든 fallback briefing을 저장하고 보여줍니다.

현재 계산하는 지표:

- 프로그램별 난이도 점수: 관련 commit 수, 변경 파일 수, diff line 수, touched area 수, cross-program commit 수, unresolved risk 수를 조합합니다.
- 프로그램별 업무량 근거: 미완료 여부, 계획 대비 AI 진척도 차이, 리스크 수, 난이도 점수를 조합합니다.
- 프로그램별 예상 종료 상태: 계획 시작/종료일, AI 진척도, 관련 commit 활동을 기준으로 예상 종료일, 예상 지연일, 신뢰도를 계산합니다.
- 개발자별 업무량/난이도 집계: 담당 프로그램 수, 미완료 프로그램 수, 리스크 프로그램 수, 평균 계획/AI 진척도, 평균 난이도를 집계합니다.
- 고객가치 참고 지표: unresolved risk 수, HIGH risk 수, 예상 지연 프로그램 수, AI Code Review 실행 수, 리뷰 시간 절감 가능성, 추가 투입 예방 가능성을 계산합니다.
- AI Resource Radar: 우선 검토 프로그램, 주요 이유, 권장 액션, 관련 commit 근거, 저장형 PL Briefing을 제공합니다.
- 추세 분석: 저장된 snapshot의 예상 지연 프로그램, HIGH/미해결 리스크, 평균 업무량, 평균 난이도, 리뷰 시간 절감 가능성, 추가 투입 예방 가능성을 시간순으로 비교합니다.

이 지표는 PL의 의사결정을 돕는 참고 신호입니다. 커밋과 산출물에서 관측 가능한 신호를 조합한 값이므로 개인 성과를 확정 평가하는 지표로 사용하면 안 됩니다. Snapshot은 자동 감사 로그가 아니라 회의, 주간 점검, 리스크 리뷰 같은 기준 시점을 남기는 수동 기록입니다.
리뷰 시간 절감 가능성과 추가 투입 예방 가능성은 확정된 비용 절감액이 아니라 현재 계산 기준의 참고 추정값입니다. 현재 기준은 AI Code Review 1건을 0.5h의 리뷰 부담 완화 가능성으로 보고, 조기 대응 시 HIGH 미해결 리스크 1건은 0.25MM, 예상 지연 프로그램 1건은 0.15MM의 추가 투입 예방 가능성으로 봅니다.

## AI 운영 현황

`AI 운영 현황`은 AI 분석 결과를 그대로 믿기 전에 연결 상태와 실행 근거를 확인하는 화면입니다. 단순히 결과 화면을 하나 더 보여주는 것이 아니라, 현재 LLM/embedding/Neo4j 설정이 무엇인지, Knowledge Graph와 GraphRAG 근거가 준비됐는지, 결과가 어떤 provider/model/fallback 상태와 근거로 만들어졌는지, 주간 점검에 가져갈 수 있는 산출물이 있는지 한곳에서 확인합니다.

주요 탭:

- 운영 준비: DB, Git, 산출물, Mapping, AI Progress, Risk Analysis, LLM/embedding 설정, source index, PL Briefing, AI 호출 기록 상태를 `통과/주의/실패`로 보여줍니다. 상단의 `AI 실행 바로가기`에서 Mapping, Risk Analysis, PL Briefing, 검색 준비를 바로 실행할 수 있고, 준비 상태는 요약 지표와 `주의/실패 우선 확인` 영역으로 먼저 확인합니다.
- 근거 추적: 최근 PL Briefing, Mapping, Project Chat, AI Code Review 결과의 provider/model, fallback 여부, source evidence, graph evidence, raw response metadata를 읽기 전용으로 확인합니다.
- 품질 점검: 현재 프로젝트의 Mapping 판단불가/낮은 관련도/짧은 근거/피드백 미완료, Project Chat verified source 사용률과 insufficient evidence, PL Briefing provider/model/validation/fallback, AI Code Review 결과 분포, Knowledge Graph 최신성과 class/import/impact path를 `통과/주의/실패`로 점검합니다. 주의/실패 항목은 관련 화면으로 바로 이동해 조치할 수 있습니다.
- 실제 LLM 검증: `local_openai` 같은 live provider로 embedding 연결, PL Briefing, Project Chat, AI Code Review, Mapping을 실행한 telemetry를 확인합니다. Mock/fallback 결과와 live provider 성공 결과를 분리해 보여줍니다.
- 주간 보고서: Radar, PL Briefing, 미해결 리스크, AI Progress gap, Knowledge Graph impact path, Project Chat GraphRAG 사용 여부, telemetry 요약을 Markdown 보고서로 다운로드합니다.
- 호출 기록: AI 호출별 provider/model, latency, prompt/response length, validation/fallback/error 상태를 확인합니다.

상단의 `연결된 AI`는 LLM/embedding뿐 아니라 Neo4j 연결, Knowledge Graph 최신성, Neo4j 저장 graph readback, 최근 Project Chat GraphRAG evidence 상태를 함께 보여줍니다. Graph가 `갱신 필요`, `저장 필요`, `미연결`이면 `Knowledge Graph로 이동` 버튼으로 graph 동기화 화면에 바로 이동할 수 있습니다.

이 화면은 AI 결과를 확정 판단으로 만들기 위한 것이 아니라, PL이 연결된 모델과 근거, 호출 상태를 보고 결과를 신뢰할지 판단하도록 돕기 위한 장치입니다. 운영 점검 중에는 상단의 `연결된 AI`에서 LLM/embedding/Neo4j와 최근 호출 상태를 먼저 확인한 뒤, 경고 항목을 처리하고 `근거 추적`과 `호출 기록`에서 실제 provider/model/fallback 상태를 확인하는 흐름이 가장 자연스럽습니다.

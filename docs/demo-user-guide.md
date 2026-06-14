# AI Commit Advisor 사용 가이드

이 문서는 AI Commit Advisor의 주요 흐름을 따라 사용할 수 있도록 안내합니다. 설명은 기본 샘플 프로젝트를 기준으로 하지만, 같은 절차를 실제 분석 대상 프로젝트에도 적용할 수 있습니다. 설치 세부값이나 내부 검증 절차보다, 어떤 화면을 어떤 순서로 보고 어떤 질문에 답하는지에 집중합니다.

샘플 프로젝트는 실제 고객 코드 없이도 개발계획, Git 변경 이력, AI 매핑, 리스크, 소스 기반 질의응답, 코드 리뷰 흐름을 한 번에 확인할 수 있도록 준비된 예제 데이터입니다.

## 사용 목표

이 가이드는 다음 질문에 답하는 것을 목표로 합니다.

- 계획된 프로그램이 실제 Git 변경 이력과 연결되는가?
- 어떤 프로그램이 구현 완료, 진행 중, 근거 부족 상태로 보이는가?
- 일정이 지났거나 담당자/커밋 근거가 부족한 위험 항목은 어디인가?
- 특정 commit이 어떤 프로그램과 파일에 영향을 주는가?
- 현재 소스 기준으로 업무 질문에 답하고 근거 파일을 확인할 수 있는가?
- AI Code Review가 변경 의도와 위험 후보를 요약할 수 있는가?
- 개발자별 업무량, 난이도, 예상 지연 프로그램, 고객가치 참고 지표를 확인할 수 있는가?

## 준비 기준

로컬에서 사용할 때는 현재 PC가 앱 서버입니다. 프로젝트/Git 설정에 입력하는 Git 저장소 경로도 현재 PC에서 접근 가능한 경로를 사용합니다.

기본 샘플 경로:

```text
C:\dev\ai-advisor-sample-shop
```

샘플 프로젝트가 없거나 최신 상태로 다시 만들려면 앱 저장소 루트에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force
```

샘플 프로젝트에는 8개 프로그램, 48개 commit, Spring MVC + MyBatis 예제 소스, 업로드용 Excel 파일이 포함됩니다.

업로드 파일 위치:

```text
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_developers.xlsx
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_programs.xlsx
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_development_plan.xlsx
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_standard_terms.xlsx
```

앱 실행과 DB 준비가 필요하면 [설치와 운영](setup-and-operations.md)의 설치 및 실행 절차를 먼저 따릅니다.

이미 같은 샘플 프로젝트를 사용한 적이 있다면 `프로젝트 설정 > 프로젝트/Git 설정`에서 기존 샘플 프로젝트를 선택한 뒤 `분석 데이터 초기화`를 먼저 사용합니다. 이 기능은 프로젝트명, Git 저장소 경로, 업로드한 프로그램/개발계획, 프로젝트 개발자 연결, 표준용어는 유지하고 Git 수집 결과와 분석 결과만 지웁니다. 프로젝트 자체와 업로드 산출물까지 모두 지우고 다시 등록해야 할 때만 `프로젝트 삭제`를 사용합니다.

## 1. 프로젝트 등록

`프로젝트 설정 > 프로젝트/Git 설정`으로 이동합니다.

입력 예시:

| 항목 | 값 |
|---|---|
| 프로젝트명 | `AAA Sample Shop Demo` |
| 설명 | `AI Commit Advisor 샘플 프로젝트` |
| 앱 서버 Git 저장소 경로 | `C:\dev\ai-advisor-sample-shop` |

저장 후 왼쪽 사이드바의 현재 프로젝트 선택에서 방금 만든 프로젝트가 선택되어 있는지 확인합니다.

이 화면에서 강조할 점:

- 앱은 GitHub API를 직접 읽는 것이 아니라 앱 서버에서 접근 가능한 Git 저장소를 읽습니다.
- 로컬 실행에서는 내 PC의 샘플 프로젝트 경로가 앱 서버 Git 저장소 경로입니다.
- 사내 서버 실행에서는 서버에 clone된 저장소 경로를 등록해야 합니다.

## 2. Git 동기화

`프로젝트 설정 > Git 동기화`로 이동합니다.

먼저 저장소 상태 영역에서 Repo HEAD, DB sync commit, branch, working tree 상태를 확인합니다. 새 프로젝트라면 DB에 아직 commit이 없으므로 전체 수집을 실행합니다.

권장 순서:

1. 저장소 상태를 확인합니다.
2. `전체 수집`을 실행합니다.
3. 저장된 commit 수와 변경 파일 수를 확인합니다.

기대 상태:

- commit 수가 48개로 수집됩니다.
- 변경 파일과 diff 일부가 DB에 저장됩니다.

이 화면에서 강조할 점:

- Git 동기화는 앱 서버에 준비된 Git 저장소의 commit과 diff를 앱 DB로 수집하는 단계입니다.
- 원격 저장소를 앱 서버 경로에 먼저 준비해야 한다면 `프로젝트 설정 > 프로젝트/Git 설정`의 `서버 저장소 clone/fetch`를 사용합니다. 이미 로컬 샘플 경로가 준비된 walkthrough에서는 이 단계를 생략해도 됩니다.
- 이후 Mapping, Git History, Commit Impact, Risk Analysis는 이 수집 데이터를 근거로 동작합니다.

## 3. 산출물 업로드

샘플 프로젝트의 업무 기준 데이터를 앱에 넣습니다.

### 개발자 목록

`산출물 관리 > 개발자 목록`으로 이동해 아래 파일을 업로드합니다.

```text
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_developers.xlsx
```

업로드 전 미리보기와 검증 결과를 확인한 뒤 저장합니다.

### 프로그램 목록

`산출물 관리 > 프로그램 목록`으로 이동해 아래 파일을 업로드합니다.

```text
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_programs.xlsx
```

현재 프로젝트에 저장하는 흐름을 사용합니다. 저장 후 8개 프로그램이 보이는지 확인합니다.

### 개발계획

`산출물 관리 > 개발계획`으로 이동해 아래 파일을 업로드합니다.

```text
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_development_plan.xlsx
```

저장 후 계획 일정, 담당자, 진행률이 들어왔는지 확인합니다.

### 표준용어/표준단어

Project Chat에서 한글 업무 질문을 더 잘 검색하도록 `산출물 관리 > 표준용어/표준단어`에서 아래 파일을 업로드합니다.

```text
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_standard_terms.xlsx
```

이 화면에서 강조할 점:

- 프로그램 목록과 개발계획은 사용자가 생각하는 업무 단위입니다.
- Git commit은 개발 이력입니다.
- AI Commit Advisor의 핵심은 두 데이터를 연결해 계획 대비 구현 근거를 보여주는 것입니다.

## 4. Home에서 상태 확인

`개요 > Home`으로 이동합니다.

확인할 내용:

- 현재 프로젝트명이 맞는지 확인합니다.
- 프로그램, commit, 매핑, 리스크 등 분석 파이프라인 상태를 봅니다.
- 다음에 해야 할 작업 안내를 확인합니다.

Home은 현재 프로젝트의 관제 화면입니다. 데이터 수집이나 분석을 실행한 뒤 다시 돌아와 상태가 어떻게 바뀌는지 확인하기 좋습니다.

## 5. Mapping 실행

`분석 실행 > Mapping`으로 이동합니다.

권장 실행 순서:

1. 커밋 기준 분석 모드를 선택합니다.
2. 먼저 특정 commit 1개를 선택해 분석합니다.
3. 결과가 만들어지는 방식을 설명합니다.
4. 이후 미처리 commit 일괄 분석을 실행합니다.

이 화면에서 강조할 점:

- 앱은 commit message, 변경 파일, diff, 프로그램 정보를 함께 보고 관련 프로그램 후보를 찾습니다.
- LLM은 후보 프로그램 중 실제 관련성이 있는 항목과 구현 상태를 판단합니다.
- 결과는 `program_commit_mappings`에 저장되고, 이후 Risk Analysis와 AI Progress가 재사용합니다.
- 매핑 피드백 리뷰 큐에서 사람이 관련성 판단을 보정할 수 있습니다.

LLM 설정이 `mock`이면 실제 판단 품질보다 화면 흐름 확인에 가깝습니다. 실제 판단 품질을 확인하려면 local LLM 설정을 사용합니다.

## 6. Program Detail 확인

`분석 결과 > Program Detail`로 이동합니다.

프로그램을 하나 선택하고 다음을 확인합니다.

- 계획 정보와 담당자
- 관련 commit 목록
- commit별 관련도와 구현 상태
- 변경 파일과 diff preview
- 저장된 구현상태 분석 결과
- 리스크 요약

이 화면에서 강조할 점:

- 단순히 “진척률 몇 퍼센트”만 보여주는 화면이 아니라, 왜 그렇게 판단했는지 commit과 file 근거까지 내려가 볼 수 있습니다.
- 업무 프로그램 단위로 Git 근거를 모아 보는 화면입니다.

## 7. Risk Analysis 실행

`분석 실행 > Risk Analysis`로 이동해 리스크 분석을 실행합니다.

확인할 수 있는 리스크 예시:

- 계획 종료일이 지났지만 AI 진척도가 낮은 프로그램
- 관련 commit이 없거나 부족한 프로그램
- 담당자 정보가 비어 있는 프로그램
- 매핑 결과가 판단불가에 가까운 프로그램
- 최근 commit 활동이 부족한 프로그램

이 화면에서 강조할 점:

- 리스크는 LLM의 단정이 아니라 계획, commit 활동, 매핑 결과를 결합한 규칙 기반 탐지입니다.
- 사용자는 리스크를 검토하고 해결 처리할 수 있습니다.

## 8. AI Progress 확인

`개요 > AI Progress`로 이동합니다.

확인할 내용:

- 계획 진척도와 AI 진척도 차이
- 관련 commit 수
- 구현상태 분석 요약
- 리스크 프로그램

이 화면에서 강조할 점:

- 계획 진척도는 산출물 기준이고, AI 진척도는 Git commit과 매핑 근거 기준입니다.
- 두 수치의 차이가 크면 실제 구현 근거와 보고 진척 사이에 검토가 필요할 수 있습니다.
- 저장된 구현상태 분석은 업무 검토를 돕는 요약이며, 최종 판단은 사람이 근거와 함께 확인해야 합니다.

## 9. Dashboard 자원관리 지표 확인

`개요 > Dashboard`로 이동합니다.

기존 프로젝트 현황과 개발자 Git 활동 아래의 `자원관리 지표` 영역을 확인합니다.

확인할 내용:

- 미해결 리스크, HIGH 리스크, 예상 지연 프로그램 수
- 리뷰 시간 절감 가능성과 추가 투입 예방 가능성
- 개발자별 업무량 점수, 평균 난이도, 미완료 프로그램 수, 리스크 프로그램 수
- 예상 종료일 기준 지연 주의 프로그램과 신뢰도
- `현재 지표 저장`으로 남긴 자원관리 snapshot과 `추세 분석` 탭

이 화면에서 강조할 점:

- 자원관리 지표는 커밋, diff, 매핑, 계획, 리스크를 조합해 일정과 병목을 보는 참고 신호입니다.
- 개인 성과를 확정 평가하는 값이 아니라, PL이 병목과 일정 리스크를 먼저 볼 수 있도록 돕는 보조 지표입니다.
- 리뷰 시간 절감 가능성과 추가 투입 예방 가능성은 실제 절감 확정값이 아니라 현재 계산 기준으로 추정한 조기 대응 가능성입니다.
- 예상 지연 프로그램은 Risk Analysis의 `FORECAST_DELAY` 리스크와 함께 확인하면 좋습니다.
- Snapshot은 자동으로 쌓이는 로그가 아니라 주간 점검, 리스크 리뷰, 검증 기준점처럼 사용자가 명시적으로 저장한 비교 기준입니다.

## 10. Git History와 Commit Impact

### Git History

`분석 결과 > Git History`로 이동합니다.

확인할 내용:

- commit 목록
- 작성자, 날짜, 파일 경로 필터
- 선택한 commit의 변경 파일
- 저장된 diff preview
- 필요 시 전체 diff 조회

Git History는 개발 이력을 빠르게 탐색하는 화면입니다.

### Commit Impact

`분석 결과 > Commit Impact`로 이동합니다.

추천 commit 검색어:

```text
Change dashboard summary query across operations modules
Fix dashboard summary over-counting
Add payment authorization flow
```

확인할 내용:

- 해당 commit이 영향을 주는 프로그램
- 관련 파일과 개발자
- 영향도 점수
- 기존 Mapping 결과와 연결된 근거

이 화면에서 강조할 점:

- Git History가 commit 자체를 보는 화면이라면, Commit Impact는 commit이 업무 프로그램에 미치는 영향을 보는 화면입니다.

### Knowledge Graph

`분석 결과 > Knowledge Graph`로 이동합니다.

확인할 내용:

- 도메인별 프로그램, 파일, 클래스, 커밋 묶음
- Java class/import 기반 클래스 관계도
- 커밋에서 프로그램, 파일, 클래스, 도메인으로 이어지는 영향 경로
- Neo4j 연결 상태와 동기화 대상 node/edge 수

기본 Quick Start를 따르면 Neo4j가 함께 실행되므로 `Neo4j 동기화`로 graph 저장까지 확인할 수 있습니다. Neo4j를 끈 환경에서는 PostgreSQL과 앱 서버 Git 저장소 기준 preview만 볼 수 있습니다.

## 11. RAG Search와 Project Chat

소스 기반 질의응답은 실제 embedding과 LLM 설정이 있을 때 가장 잘 보입니다. mock 설정에서는 흐름 확인용으로 사용합니다.

### RAG Search 준비

`분석 실행 > RAG 검색`으로 이동합니다.

추천 순서:

1. 현재 소스 인덱스 상태를 확인합니다.
2. `전체 소스 다시 읽기` 또는 `최신 변경분 반영`을 실행합니다.
3. `검색 준비 연결 테스트`를 실행합니다.
4. `검색 준비` 탭에서 남은 작업을 작은 수량부터 실행합니다.
5. 검색어로 근거 파일이 나오는지 확인합니다.

검색 예시:

```text
결제금액 검증
재고 부족
dashboard summary query
```

### Project Chat

`분석 실행 > Project Chat`으로 이동합니다.

질문 예시:

- 결제금액 검증은 어디에서 수행되나요?
- 재고가 부족하면 어떤 일이 발생하나요?
- 결제승인 후 주문상태는 어떻게 이동하나요?
- dashboard summary를 만드는 query는 무엇인가요?
- 의도적으로 incomplete 또는 risky하게 만든 샘플 program은 무엇인가요?

답변에서 확인할 내용:

- 답변 본문
- 현재 소스 근거
- 파일 경로와 line range
- 이력/참고 근거
- 근거 복사용 Markdown

이 화면에서 강조할 점:

- Project Chat은 현재 소스와 일치한다고 검증된 `source_file` chunk를 우선 사용합니다.
- 검증된 근거가 부족하면 추측성 답변을 만들지 않고 근거 부족을 안내합니다.
- 표준용어/표준단어를 업로드하면 한글 질문이 코드 식별자 검색으로 확장됩니다.

## 12. AI Code Review

`분석 실행 > AI Code Review`로 이동합니다.

추천 리뷰 대상:

```text
Relax partner payment validation for pilot channel
Change dashboard summary query across operations modules
Extract shared order status constants
```

확인할 내용:

- 변경 의도 요약
- 위험도
- 버그 후보
- 리팩토링 제안
- 리뷰 대상 commit과 diff 근거

이 화면에서 강조할 점:

- 중앙 앱 서버 데모에서는 최신 commit 또는 특정 commit 리뷰가 기본 흐름입니다.
- 서버 작업트리/Staged 변경 옵션은 앱 서버의 분석용 clone에 local 변경이 남아 있을 때만 의미가 있습니다.
- 특정 commit을 선택하면 결과를 설명하기 쉽고, 개발자 개인 PC의 미커밋 변경과 서버 저장소 commit 이력을 혼동하지 않을 수 있습니다.

## 사용 흐름 요약

빠르게 확인할 때는 다음 순서로 진행합니다.

```text
프로젝트/Git 설정
-> Git 동기화
-> 개발자/프로그램/개발계획/표준용어 업로드
-> Home
-> Mapping
-> Risk Analysis
-> AI Progress
-> Dashboard
-> Program Detail
-> Git History
-> Commit Impact
-> Knowledge Graph
-> RAG Search
-> Project Chat
-> AI Code Review
```

시간이 짧으면 Dashboard의 자원관리 지표를 먼저 보고, RAG Search, Project Chat, AI Code Review는 대표 질문과 대표 commit 1개만 보여줍니다.

## 자주 나오는 질문

### GitHub와 직접 연결하나요?

앱은 GitHub API credential이나 Git password를 저장하지 않습니다. 운영자나 사용자가 앱 서버에서 접근 가능한 위치에 Git 저장소를 미리 clone해 둘 수 있고, 프로젝트/Git 설정의 `Git remote URL`과 branch를 저장해 앱 서버가 clone/fetch/reset을 실행하게 할 수도 있습니다. private repository는 서버 OS의 SSH key나 credential helper처럼 앱 밖의 인증 설정을 사용합니다.

### mock 모드와 실제 LLM 모드는 무엇이 다른가요?

mock 모드는 설치와 화면 흐름을 빠르게 확인하기 위한 기본값입니다. 실제 매핑 품질, 코드 리뷰 품질, Project Chat 답변 품질을 보여주려면 LM Studio 같은 OpenAI-compatible local LLM과 embedding 서버를 연결해야 합니다.

### AI 진척도가 실제 진척률인가요?

AI 진척도는 Git commit과 매핑 결과를 바탕으로 한 보조 지표입니다. 계획 진척도와 다를 수 있으며, 차이가 큰 항목은 Program Detail, 관련 commit, diff, 리스크 근거를 함께 보고 사람이 검토해야 합니다.

### Project Chat이 답하지 않는 경우는 실패인가요?

항상 실패는 아닙니다. 현재 소스 근거가 없거나 인덱스가 오래되었거나 embedding이 부족하면 답변을 보류합니다. 이 동작은 오래된 diff나 불확실한 근거를 현재 코드 사실처럼 말하지 않기 위한 안전장치입니다.

## 문제 해결

| 증상 | 확인할 것 |
|---|---|
| Git 저장소 경로가 유효하지 않다고 나옴 | 경로가 현재 앱 실행 환경에서 접근 가능한지 확인합니다. Docker라면 volume mount와 path mapping을 확인합니다. |
| Git 동기화 commit 수가 48개가 아님 | 샘플 프로젝트를 `--force`로 다시 생성했는지, 올바른 경로를 등록했는지 확인합니다. |
| 프로그램이나 개발계획이 비어 있음 | `advisor_uploads` 아래 샘플 Excel 파일을 업로드했는지 확인합니다. |
| Mapping 결과가 기대와 다름 | mock 모드인지 확인합니다. 실제 판단 품질을 보려면 local LLM 설정이 필요합니다. |
| Project Chat이 근거 부족이라고 답함 | source_file 인덱싱과 embedding 생성 여부, 현재 Git HEAD와 indexed HEAD가 맞는지 확인합니다. |
| Docker에서 샘플 경로를 못 읽음 | 기본 Compose는 `C:/dev`를 `/host-dev`로 mount합니다. 샘플이 다른 경로에 있으면 mount와 `REPO_PATH_*` 값을 함께 바꿔야 합니다. |
| 같은 샘플 프로젝트를 다시 처음부터 사용하고 싶음 | `프로젝트/Git 설정`에서 기존 샘플 프로젝트의 `분석 데이터 초기화`를 실행합니다. 프로젝트와 업로드 산출물까지 없애야 할 때만 `프로젝트 삭제`를 사용합니다. |

## 관련 문서

- [README](../README.md): 프로젝트 소개와 빠른 시작.
- [설치와 운영](setup-and-operations.md): 로컬 실행, Docker 실행, LLM/embedding 설정.
- [기능 가이드](feature-guide.md): 화면별 기능 설명.
- [사용 가이드 검증 결과](sample-project-usage-verification.md): local LLM/embedding 환경에서 이 가이드를 실제 실행한 결과와 화면 증거.
- [샘플 프로젝트 검증 가이드](rich-sample-demo-walkthrough.md): 검증자용 상세 실행 기준.
- [Application Preview](application-preview.md): 샘플 프로젝트 기준 주요 화면 미리보기.
- [Git 저장소 운영 모델](git-repository-operating-model.md): 앱 서버 기준 Git 저장소 접근 방식.

# 기능 가이드

이 문서는 AI Commit Advisor의 주요 기능을 화면 흐름 기준으로 설명합니다. 전체 화면 예시는 [Application Preview](application-preview.md)를 참고하세요.

## AI / LLM 활용 흐름

AI Commit Advisor는 개발계획, Git 변경 이력, 현재 소스 코드를 하나의 분석 흐름으로 연결합니다. LLM은 판단이 필요한 비교, 요약, 리뷰에 사용하고, RAG와 규칙 분석은 근거 검색과 일관된 리스크 탐지에 사용합니다.

| 단계 | 입력 데이터 | AI/LLM 활용 | 결과 |
|---|---|---|---|
| Git 수집 | commit message, author, changed files, diff | 분석 대상 변경 이력 구성 | `git_commits`, `commit_files` 저장 |
| RAG 인덱싱 | 현재 소스 파일, 프로그램 정보, 커밋 메시지, diff | embedding 생성 후 pgvector 검색 기반 구축 | `document_chunks`, `vector_items` 저장 |
| 프로그램-커밋 매핑 | 프로그램 목록, 커밋, 변경 파일, RAG 후보 | LLM이 관련 프로그램과 구현상태를 판단 | 관련도, 구현상태, 판단 근거 저장 |
| 구현상태 분석 | 프로그램 계획, 관련 커밋, 매핑 결과 | LLM이 프로그램 단위 구현 상태를 요약 | NOT_STARTED / IN_PROGRESS / COMPLETED / UNKNOWN |
| Project Chat | 현재 소스 검색 결과 | LLM이 검증된 소스 근거로 질문에 답변 | 저장된 대화, 파일 경로와 라인 근거가 포함된 답변 |
| AI Code Review | working tree, staged diff, commit diff | LLM이 변경 의도, 위험, 버그, 리팩토링 포인트 분석 | 리뷰 요약, 버그 후보, 개선 제안 |
| Risk Analysis | 일정, 진척도, 커밋 활동, AI 매핑 결과 | 규칙 기반 누락/지연/불확실성 탐지 | 위험 프로그램과 evidence 저장 |

Project Chat은 현재 파일 내용과 일치하는 소스 chunk만 기본 근거로 사용합니다. 커밋 diff는 변경 이력으로 취급하며 현재 코드 근거와 구분합니다. 대화는 프로젝트별 session과 message로 저장되어 이전 질문과 답변을 다시 열람할 수 있습니다.

## 권장 사용 순서

왼쪽 사이드바는 현재 작업할 프로젝트를 먼저 고른 뒤, 업무 영역을 나타내는 중메뉴와 실제 화면으로 이동하는 하위 메뉴를 제공합니다. 중메뉴는 하위 메뉴보다 살짝 크게 표시되어 `산출물 관리`, `분석 실행`, `분석 결과` 같은 작업 묶음을 먼저 훑고 필요한 화면으로 이동할 수 있습니다.

Home은 사이드바에서 선택한 현재 프로젝트의 분석 상태, 다음 작업, KPI, 진척도, 리스크 프로그램을 보여주는 첫 화면입니다. 전체 프로젝트 수는 보조 지표로만 표시하고, 프로그램·커밋·매핑·리스크 판단은 현재 프로젝트 기준으로 계산합니다.

1. 프로젝트/Git 설정 화면에서 프로젝트와 앱 서버에서 접근 가능한 Git 저장소 경로를 등록합니다.
2. 사이드바의 현재 프로젝트에서 작업할 프로젝트를 선택합니다.
3. Git 동기화 화면에서 전체 수집 또는 증분 동기화로 commit과 diff를 저장합니다.
4. 개발자 현황 화면에서 Git author 기반 개발자 자동 추출을 수행합니다.
5. 산출물 관리 메뉴에서 개발자 목록, 프로그램 목록, 개발계획을 직접 관리하거나 Excel로 업로드합니다.
6. 산출물 관리 > 표준용어/표준단어 화면에서 SI 산출물 Excel을 업로드해 한글 업무 용어와 코드 식별자를 연결합니다.
7. 필요하면 프로젝트 설정 > 샘플 데이터 생성 화면에서 데모용 Excel 산출물을 생성합니다.
8. Mapping 화면에서 커밋 기준 분석을 먼저 실행합니다.
9. Risk Analysis에서 리스크를 탐지하고, Program Detail, Commit Impact, AI Progress에서 분석 결과를 검토합니다.
10. RAG Search와 Project Chat에서 현재 소스 기반 근거 검색과 질의응답을 확인합니다.
11. AI Code Review에서 작업트리, staged 변경, 최신 commit, 특정 commit을 리뷰합니다.

## 데이터 관리

산출물 관리 메뉴의 개발자 목록, 프로그램 목록, 개발계획 데이터는 Excel 업로드와 화면 기반 직접 관리를 모두 지원합니다.

- 개발자 관리: Git author 기반 자동 추출, 검색, 직접 추가/수정/삭제, Excel 양식 다운로드, 업로드 전 검증
- 프로그램 관리: 검색, 직접 추가/수정/삭제, Excel 양식 다운로드, 업로드 전 검증/미리보기, 신규/수정 요약
- 개발계획 관리: 현재 계획 조회, 직접 수정, 일괄 업데이트, Excel 양식 다운로드, 업로드 전 검증

업로드 저장 전에는 필수 컬럼, 중복 ID, 날짜 형식, 시작/종료일 순서, 진행률 범위를 검증합니다.

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

기본 추천 방식은 커밋 기준 분석입니다. 커밋 하나를 기준으로 후보 프로그램 TOP N개를 먼저 추린 뒤 LLM에 전달하므로, 모든 프로그램과 모든 커밋 조합을 무작정 호출하지 않습니다.

주요 정책:

- 기본값은 커밋 1개당 후보 프로그램 TOP 10입니다.
- diff_text는 파일별 앞부분만 사용하고 입력 길이를 제한합니다.
- 이미 같은 `program_id + commit_id` 매핑이 있으면 새로 만들지 않고 업데이트합니다.
- 일괄 분석은 이미 `completed`인 커밋을 건너뛰므로 중단 후 재시작할 수 있습니다.
- 매핑 피드백 리뷰 큐에서 근거 부족, 판단불가, 낮은 관련도 매핑을 우선 검토할 수 있습니다.

## Program Detail과 AI Progress

Program Detail은 특정 프로그램의 계획, AI 진척도, 관련 커밋, 개발자 기여, 리스크, 구현상태 분석 결과를 한 화면에서 확인합니다.

AI Progress는 계획 진척도와 LLM 매핑 결과 기반 AI 진척도를 비교합니다. 저장된 프로그램 단위 구현상태 분석 결과는 수치를 대체하지 않고 업무 검토용 요약 근거로 함께 표시합니다.

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

## Risk Analysis

Risk Analysis는 프로그램 목록, 개발계획, Git 커밋, LLM 매핑 결과를 기반으로 누락 가능성이 있는 프로그램과 위험 프로그램을 자동 탐지합니다.

탐지 규칙 예시:

- 프로그램은 등록되어 있지만 관련 commit이 없음
- 계획 종료일이 지났지만 AI 진척도 < 100
- 계획 진척도와 AI 진척도 차이가 30 이상
- LLM 매핑 결과가 모두 판단불가
- 최근 14일 동안 관련 commit이 없음
- 담당자가 없거나 개발자 정보가 불명확함

## RAG Search와 Project Chat

RAG Search는 현재 소스 파일, 프로그램 정보, commit 메시지, 변경 파일/diff를 chunk로 만들고 embedding을 저장해 검색합니다.

Project Chat은 현재 파일과 일치한다고 검증된 `source_file` chunk만 기본 답변 근거로 사용합니다. 표준용어/표준단어가 등록되어 있으면 한글 업무 질문을 영문명, 약어, 코드 식별자 후보로 확장해 검색합니다. 검증된 현재 소스 근거가 없으면 추측성 답변을 만들지 않고 추가 인덱싱 또는 검색어 조정이 필요하다고 안내합니다.

Project Chat 화면의 `대화 이력`에서 프로젝트별 저장된 session을 선택할 수 있고, `새 대화` 또는 `대화 초기화`는 기존 이력을 지우지 않고 새 session을 만듭니다. Assistant 답변에는 `근거 복사용 Markdown` 영역이 있어 답변, 현재 소스 근거, 이력/참고 근거를 회의록이나 리뷰 문서에 붙여 넣기 쉬운 형식으로 제공합니다.

이 설계는 오래된 chunk나 commit diff만으로 현재 코드처럼 답변하는 문제를 줄이기 위한 것입니다. 사용자가 한글 업무 용어로 질문하더라도 실제 소스에는 영문 변수명, 약어, DB 컬럼명, class/function 이름으로 남는 경우가 많아 검색어나 근거 chunk가 제대로 매핑되지 않을 수 있습니다. 표준용어/표준단어가 있으면 한글 질의와 함께 관련 영문명, 약어, 코드 식별자 표현까지 검색해 이 문제를 줄이고, 현재 파일 검증은 답변 근거가 실제 checkout 상태와 어긋나지 않도록 제한합니다.

현재 소스 파일을 수정하거나 브랜치/HEAD가 바뀐 뒤에는 RAG 또는 Project Chat 화면에서 인덱스 상태를 확인하고 필요 시 현재 소스를 다시 인덱싱하세요.

## AI Code Review

AI Code Review는 앱 서버 Git 저장소의 변경 사항 또는 commit을 LLM으로 리뷰합니다.

지원 대상:

- 작업트리 변경: 아직 stage하지 않은 `git diff`
- Staged 변경: `git diff --cached`
- 최신 commit: `HEAD`
- 특정 commit: commit hash 또는 rev 입력

리뷰 결과는 `code_review_results` 테이블에 저장되며, 변경 의도, 영향 범위, 위험도, 버그 후보, 리팩토링 제안을 포함합니다.

## 대시보드

- 개발계획 대시보드: 프로그램 목록, 상태별 프로그램 수, 개발자별 배정 프로그램 수, 지연 프로그램, 계획 대비 완료율
- Dashboard: Git author 기반 개발자별 commit 수와 변경 파일 수

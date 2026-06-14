# Application Preview

이 문서는 README를 가볍게 유지하기 위해 주요 화면과 기능 상태를 미리 볼 수 있도록 정리한 Application Preview입니다. 캡처는 48개 commit 샘플 프로젝트 `AAA Sample Shop Rich Demo 48` 기준의 의미 있는 workflow 상태를 우선합니다.

## Preview Screens

<details>
<summary>Home</summary>

개발계획, Git 변경 이력, AI 매핑 결과, 리스크를 통합해 현재 프로젝트의 핵심 KPI와 다음 권장 작업을 먼저 확인하는 관제 화면입니다. 사이드바는 업무 영역 중메뉴와 하위 메뉴의 크기 차이로 현재 작업 흐름을 훑기 쉽게 보여주며, 본문에는 분석 파이프라인 상태도 함께 표시합니다.

![Home](images/features/home.png)

</details>

<details>
<summary>Project</summary>

![Project](images/features/project.png)

</details>

<details>
<summary>개발자 현황</summary>

![개발자 현황](images/features/developer.png)

</details>

<details>
<summary>Program Detail</summary>

![Program Detail](images/features/program-detail.png)

</details>

<details>
<summary>개발자 목록</summary>

현재 개발자 데이터

![개발자 목록](images/features/developer-upload.png)

업로드 검증 결과

![개발자 목록 업로드 검증](images/features/developer-upload-validation.png)

</details>

<details>
<summary>프로그램 목록</summary>

현재 프로그램 데이터

![프로그램 목록](images/features/program-upload.png)

업로드 검증 결과

![프로그램 목록 업로드 검증](images/features/program-upload-validation.png)

</details>

<details>
<summary>개발계획</summary>

현재 개발계획

![개발계획](images/features/development-plan-upload.png)

업로드 검증 결과

![개발계획 업로드 검증](images/features/development-plan-upload-validation.png)

</details>

<details>
<summary>Git 동기화</summary>

![Git Sync](images/features/git-sync.png)

</details>

<details>
<summary>Git History</summary>

현재 프로젝트의 커밋 목록, 작성자/날짜/파일 필터, 변경 파일, 저장된 diff preview를 한 화면에서 확인하는 Git History 상태입니다.

커밋 목록과 활동 그래프

![Git History](images/features/git-history.png)

커밋 상세와 diff preview

![Git History Detail](images/features/git-history-detail.png)

</details>

<details>
<summary>샘플 데이터 생성</summary>

![Sample Data](images/features/sample-data.png)

</details>

<details>
<summary>표준용어/표준단어</summary>

![Standard Terms](images/features/standard-terms.png)

</details>

<details>
<summary>Mapping</summary>

![Mapping](images/features/mapping.png)

</details>

<details>
<summary>Risk Analysis</summary>

![Risk Analysis](images/features/risk-analysis.png)

</details>

<details>
<summary>Commit Impact</summary>

커밋 선택

![Commit Impact](images/features/commit-impact.png)

영향도 요약

![Commit Impact Summary](images/features/commit-impact-summary.png)

상세 분석

![Commit Impact Detail](images/features/commit-impact-detail.png)

</details>

<details>
<summary>RAG 검색</summary>

근거 조각과 검색 데이터 준비 상태, 검색 품질 확인 결과, 조회된 근거 목록을 함께 보여주는 RAG 검색 상태입니다. `TOP K`, 근거 조각 크기, 검색 준비 수량처럼 판단이 필요한 control은 물음표 도움말로 의미와 사용 기준을 확인할 수 있습니다.

![RAG Search](images/features/rag-search.png)

</details>

<details>
<summary>Project Chat</summary>

답변 근거 상태에서 소스 근거, 검색 준비, 코드 반영 상태를 확인하고, 최신 변경분 반영과 전체 소스 다시 읽기 중 필요한 작업을 바로 선택할 수 있는 Project Chat 상태입니다. `TOP K`, 커밋 이력 참고, 저장된 대화, 새 대화 시작은 물음표 도움말로 동작을 확인할 수 있습니다.

![Project Chat](images/features/project-chat.png)

</details>

<details>
<summary>AI Code Review</summary>

커밋 이력 중심 리뷰 대상 선택

![AI Code Review](images/features/ai-code-review.png)

리뷰 결과 요약

![AI Code Review Result](images/features/ai-code-review-result.png)

리뷰 상세

![AI Code Review Detail](images/features/ai-code-review-detail.png)

</details>

<details>
<summary>Dashboard</summary>

프로젝트 계획/AI/Git 활동 요약과 함께 개발자별 업무량·난이도, 예상 지연 프로그램, PoC 고객가치 KPI를 확인하는 운영 대시보드입니다. 자원관리 지표는 개인 성과 확정값이 아니라 PL이 병목과 일정 리스크를 먼저 볼 수 있도록 돕는 planning signal이며, 리뷰 시간 절감 가능성과 추가 투입 예방 가능성도 확정 절감액이 아닌 PoC 가정값으로 표시합니다. 사용자가 저장한 snapshot으로 추세 분석을 확인할 수 있습니다.

![Dashboard](images/features/dashboard.png)

</details>

<details>
<summary>개발계획 대시보드</summary>

![개발계획 대시보드](images/features/planning-dashboard.png)

</details>

<details>
<summary>AI Progress</summary>

![AI Progress](images/features/ai-progress.png)

</details>

<details>
<summary>설정</summary>

![설정](images/features/settings.png)

</details>

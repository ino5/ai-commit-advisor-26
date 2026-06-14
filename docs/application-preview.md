# Application Preview

이 문서는 README를 가볍게 유지하기 위해 주요 화면과 기능 상태를 미리 볼 수 있도록 정리한 Application Preview입니다. 캡처는 샘플 프로젝트 기준의 의미 있는 workflow 상태를 우선합니다.

## Preview Screens

<details>
<summary>Home</summary>

개발계획, Git 변경 이력, AI 매핑 결과, 리스크를 통합해 현재 프로젝트의 핵심 지표와 다음 권장 작업을 먼저 확인하는 관제 화면입니다. 사이드바는 업무 영역을 접이식 그룹으로 묶어 현재 작업 흐름을 훑기 쉽게 보여주며, 본문에는 분석 파이프라인 상태도 함께 표시합니다.

![Home](images/features/home.png)

</details>

<details>
<summary>Dashboard</summary>

Dashboard는 프로젝트 진행 상황을 한눈에 보는 화면입니다. 계획, AI 분석, Git 활동을 모아 지연 가능성이 있는 프로그램과 개발자별 업무 부담 신호를 보여줍니다. `AI Resource Radar`는 PL이 먼저 확인할 프로그램, 주요 이유, 권장 action을 우선순위로 보여주고, 필요하면 LLM 기반 PL Briefing으로 회의용 요약을 생성합니다. 이 값은 개인 평가나 확정 절감액이 아니라 PL이 병목과 일정 리스크를 빨리 찾기 위한 참고 지표입니다. 필요하면 현재 상태를 snapshot으로 저장해 추세를 비교할 수 있습니다.

프로젝트 현황과 Git 활동

![Dashboard Overview](images/features/dashboard-overview.png)

AI Resource Radar 우선순위와 PL Briefing action

![Dashboard AI Resource Radar](images/features/dashboard-radar.png)

local LLM이 생성하고 저장한 PL Briefing 결과

![Dashboard PL Briefing](images/features/dashboard-pl-briefing.png)

PL Briefing 회의 질문, 다음 action, 이력 확인

![Dashboard PL Briefing Actions](images/features/dashboard-pl-briefing-actions.png)

자원관리 참고 지표

![Dashboard](images/features/dashboard.png)

</details>

<details>
<summary>AI Progress</summary>

진척도 요약과 리스크 프로그램

![AI Progress](images/features/ai-progress.png)

프로그램별 비교와 관련 커밋 상세

![AI Progress Detail](images/features/ai-progress-detail.png)

</details>

<details>
<summary>AI 운영 현황</summary>

연결된 LLM/embedding 설정, 최근 AI 호출, 검색 준비 상태를 먼저 확인하고 필요한 AI 실행을 바로 시작하는 화면입니다. 준비 상태와 품질 점검은 요약 지표와 `주의/실패 우선 확인` 영역으로 먼저 보여주며, 같은 화면에서 저장된 AI 결과가 어떤 근거와 provider/model/fallback 상태로 만들어졌는지 추적할 수 있습니다.

![AI 운영 현황](images/features/ai-evidence.png)

</details>

<details>
<summary>Project</summary>

프로젝트 기본 정보와 앱 서버 Git 저장소 경로를 저장하고, 같은 화면에서 서버 저장소 준비와 반복 검증용 분석 데이터 초기화를 이어서 실행할 수 있습니다.

![Project](images/features/project.png)

서버 저장소 상태, `서버 저장소 clone/fetch`, `분석 데이터 초기화`, `프로젝트 삭제`가 함께 보이는 운영 action 구간입니다.

![Project Operations](images/features/project-operations.png)

</details>

<details>
<summary>Git 동기화</summary>

![Git Sync](images/features/git-sync.png)

</details>

<details>
<summary>샘플 데이터 생성</summary>

![Sample Data](images/features/sample-data.png)

</details>

<details>
<summary>개발자 현황</summary>

![개발자 현황](images/features/developer.png)

</details>

<details>
<summary>개발자 목록</summary>

현재 개발자 데이터

![개발자 목록](images/features/developer-upload.png)

</details>

<details>
<summary>프로그램 목록</summary>

현재 프로그램 데이터

![프로그램 목록](images/features/program-upload.png)

</details>

<details>
<summary>개발계획</summary>

현재 개발계획

![개발계획](images/features/development-plan-upload.png)

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

리스크 요약과 유형별 현황

![Risk Analysis](images/features/risk-analysis.png)

리스크 목록과 resolved 처리

![Risk Analysis List](images/features/risk-analysis-list.png)

</details>

<details>
<summary>RAG 검색</summary>

근거 조각과 검색 데이터 준비 상태, 검색 품질 확인 결과, 조회된 근거 목록을 함께 보여주는 RAG 검색 상태입니다. `TOP K`, 근거 조각 크기, 검색 준비 수량처럼 판단이 필요한 control은 물음표 도움말로 의미와 사용 기준을 확인할 수 있습니다.

검색 준비와 품질 확인

![RAG Search](images/features/rag-search.png)

조회된 근거 목록

![RAG Search Results](images/features/rag-search-results.png)

</details>

<details>
<summary>Project Chat</summary>

답변 근거 상태에서 소스 근거, 검색 준비, 코드 반영 상태를 확인하고, 최신 변경분 반영과 전체 소스 다시 읽기 중 필요한 작업을 바로 선택할 수 있는 Project Chat 상태입니다. `TOP K`, 커밋 이력 참고, 저장된 대화, 새 대화 시작은 물음표 도움말로 동작을 확인할 수 있습니다.

답변 근거 상태와 대화 관리

![Project Chat](images/features/project-chat.png)

답변과 근거 파일

![Project Chat Answer](images/features/project-chat-answer.png)

</details>

<details>
<summary>AI Code Review</summary>

커밋 이력 중심 리뷰 대상 선택

![AI Code Review](images/features/ai-code-review.png)

</details>

<details>
<summary>Program Detail</summary>

기본 정보와 관련 커밋 요약

![Program Detail](images/features/program-detail.png)

저장된 리스크와 구현상태 분석 상세

![Program Detail Analysis](images/features/program-detail-analysis.png)

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
<summary>Commit Impact</summary>

커밋 선택과 영향도 요약

![Commit Impact](images/features/commit-impact.png)

</details>

<details>
<summary>Knowledge Graph</summary>

프로젝트, 프로그램, 커밋, 파일, 클래스, 도메인을 Neo4j 관계 그래프로 동기화한 상태입니다. 화면 상단에서 Neo4j 연결과 사용 설정을 확인하고, `Neo4j 동기화` 실행 결과와 Neo4j에서 다시 조회한 저장 node/edge 수를 확인합니다. 아래 탭에서는 Neo4j에 저장된 그래프를 기준으로 클래스 관계도, 커밋-프로그램-클래스 영향 경로, node/edge 저장 상태를 이어서 볼 수 있습니다.

Neo4j 연결, 동기화, 저장 확인

![Knowledge Graph](images/features/knowledge-graph.png)

클래스 관계도

![Knowledge Graph Class](images/features/knowledge-graph-class.png)

커밋 영향 경로

![Knowledge Graph Impact](images/features/knowledge-graph-impact.png)

노드/엣지 저장 상태

![Knowledge Graph Nodes And Edges](images/features/knowledge-graph-nodes-edges.png)

</details>

<details>
<summary>개발계획 대시보드</summary>

![개발계획 대시보드](images/features/planning-dashboard.png)

</details>

<details>
<summary>설정</summary>

![설정](images/features/settings.png)

</details>

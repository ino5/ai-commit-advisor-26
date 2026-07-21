# AI Commit Advisor

AI Commit Advisor는 개발계획과 Git 실행 근거를 연결해 프로젝트 리더가 프로그램별 구현상태와 리스크를 검토하는 맥락입니다.

## Language

**AX Use Case**:
AI 활용 과제나 숙제의 결과로 팀 내부에 보여주는 업무 적용 사례입니다. 실제 운영 전환 제안이나 상용 도입 계획이 아니라, 어떤 문제에 AI를 적용했고 어떤 화면과 결과를 만들었는지 설명하는 발표 맥락입니다.
_Avoid_: 운영 전환 계획, 실제 서비스 론칭 제안, 한계 중심 검토서

**Program**:
개발계획에 등록된 업무 또는 요구사항 단위입니다. 일정, 담당자, 계획 진척도, 관련 Git 근거를 한곳에 묶어 판단합니다.
_Avoid_: 단순 화면, 단순 소스 파일

**Plan Progress**:
계획 문서나 운영자가 입력한 프로그램의 관리상 진척도입니다. Git 근거에서 계산한 구현상태와 별도로 취급합니다.
_Avoid_: AI 진척도, 실제 구현률

**AI Progress**:
관련 커밋 근거를 프로그램 단위로 함께 검토해 산출하는 보수적 구현상태 신호입니다. 작은 커밋 하나의 상태나 커밋 수를 그대로 누적한 완료율이 아닙니다.
_Avoid_: 커밋별 활동 점수, 커밋 수 기반 완료율

**Related Commit**:
특정 Program의 구현상태 판단에 근거로 쓸 수 있다고 매핑된 Git commit입니다. Related Commit은 구현 근거이지, 그 자체가 Program 완료를 의미하지 않습니다.
_Avoid_: 완료 커밋, 정답 커밋

**Implementation Evidence**:
Program의 구현상태를 판단할 때 검토하는 Related Commit, 변경 파일, diff, 설명, 매핑 사유 같은 근거 묶음입니다.
_Avoid_: 단순 커밋 개수, 단일 점수

**Program Implementation Status**:
Program 범위와 Implementation Evidence를 함께 보고 판단한 구현상태입니다. 단일 Related Commit의 상태보다 Program 전체 완료 여부를 보수적으로 표현합니다.
_Avoid_: 커밋별 구현상태, 배포 완료 여부

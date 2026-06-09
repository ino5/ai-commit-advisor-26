# Engineering Decisions

이 문서는 실패 이력은 아니지만, 이후 구현·검증·운영·문서화 방향에 영향을 주는 주요 결정을 기록합니다.

`AI_CHANGELOG.md`가 "무엇을 바꿨는지"를 기록하고, `docs/failure-history.md`가 "무엇이 실패했고 어떻게 재발을 막을지"를 기록한다면, 이 문서는 "왜 이 방향을 선택했는지"를 남깁니다. 나중에 같은 선택지를 다시 검토할 때 결정 배경, 대안, tradeoff를 빠르게 확인하는 것이 목적입니다.

## 기록 기준

다음 중 하나에 해당하면 이 문서에 항목을 추가합니다.

- 기능, UX, architecture, 운영, 검증, 자동화, 문서 구조의 방향을 선택했습니다.
- 실패는 아니지만 앞으로 반복될 작업 방식이나 판단 기준이 바뀌었습니다.
- 여러 대안 중 하나를 고르면서 비용, 신뢰도, 유지보수성, 확장성 tradeoff가 생겼습니다.
- 특정 기능에 한정되지 않는 공통 정책이나 workflow를 만들었습니다.
- 나중에 "왜 이렇게 했지?"라는 질문이 다시 나올 가능성이 큽니다.

다음 항목은 보통 기록하지 않습니다.

- 단순한 명령 실행 순서나 일회성 local 작업 선택
- 기존 정책을 그대로 따른 기계적 문서 수정
- `AI_CHANGELOG.md`만으로 충분히 설명되는 작은 변경
- 실패나 사고에 해당해서 `docs/failure-history.md`에 기록하는 편이 더 적절한 사례

## 작성 형식

새 항목은 가능하면 아래 구조를 따릅니다.

```markdown
## YYYY-MM-DD - 결정 제목

### 배경

### 결정

### 이유

### 검토한 대안

### 영향과 tradeoff

### 후속 확인

### 관련 문서
```

모든 항목을 길게 쓸 필요는 없습니다. 다만 결정 배경, 선택한 방향, 포기한 대안, 남은 한계는 다음 사람이 판단을 이어받을 수 있을 정도로 남깁니다.

## 2026-06-10 - 기능 스크린샷 캡처 자동화 방향

### 배경

README와 Screenshot Gallery의 화면 캡처는 단순한 장식이 아니라, 기능이 실제 sample project에서 어떤 상태로 동작하는지 보여주는 검증 자료입니다. 특히 Project Chat처럼 RAG, source indexing, 현재 Git HEAD 검증, 근거 표시가 얽힌 기능은 빈 화면이나 실패 상태 캡처만으로는 기능 가치를 설명하기 어렵습니다.

최근 Project Chat 캡처를 갱신하는 과정에서 Docker 실행 환경이 Windows host repository path를 읽지 못해, 원래 답변 가능해야 하는 `결제금액 검증은 어디에서 수행되나요?` 질문이 근거 부족 상태로 보이는 문제가 있었습니다. 이 문제 자체는 failure history에 기록했지만, 이후 큰 기능 변경 때마다 어떤 방식으로 캡처를 재현할지에 대한 운영 기준은 별도 결정으로 남길 필요가 있습니다.

### 결정

기능 화면 캡처 자동화를 추가할 때는 특정 기능 하나에만 묶인 임시 스크립트보다, 기능별 시나리오를 확장할 수 있는 공통 캡처 흐름을 우선합니다.

초기 구현은 작게 시작합니다. 예를 들어 Project Chat, Home, Risk Analysis처럼 자주 갱신되는 화면부터 `feature` 단위 시나리오를 추가하되, 공통 준비 단계, 실행 surface 선택, screenshot 저장 위치, 핵심 텍스트 검증은 재사용 가능한 구조로 둡니다.

### 이유

- 큰 기능 변경 때마다 수동으로 같은 sample project 준비, 질문 입력, evidence 확인, screenshot 저장을 반복하면 누락 가능성이 큽니다.
- 캡처 자동화는 예쁜 화면만 찍는 도구가 아니라, README에 올라갈 화면이 실제 기능 상태를 보여주는지 확인하는 검증 surface 역할도 해야 합니다.
- 모든 화면을 한 번에 자동화하면 초기 비용이 커지고 유지보수 부담이 생깁니다. 반대로 Project Chat 전용 스크립트만 만들면 다음 기능으로 확장할 때 같은 판단을 다시 반복하게 됩니다.
- local Python 실행과 Docker 실행은 repository path mapping, mounted file 접근, service URL 때문에 결과가 달라질 수 있으므로, 캡처 결과에는 어떤 실행 surface를 썼는지 드러나야 합니다.

### 검토한 대안

- 완전 수동 캡처 유지: 당장 비용은 가장 낮지만, 기능 상태 검증과 재현성이 약합니다.
- 모든 화면의 캡처를 한 번에 자동화: 방향은 좋지만 현재 필요한 범위보다 크고, 기능별 fixture와 데이터 준비 비용이 큽니다.
- Project Chat 전용 스크립트만 작성: 빠르게 문제를 줄일 수 있지만, 이후 Home, Risk Analysis, Code Review 등으로 확장할 때 중복이 생깁니다.

### 영향과 tradeoff

- 초기 자동화는 모든 기능을 커버하지 않습니다. 사용자가 큰 기능 변경 후 캡처를 요청하는 화면부터 점진적으로 추가합니다.
- 각 시나리오는 단순 screenshot 저장 전에 핵심 UI text, sample data, evidence 또는 결과 table이 보이는지 확인해야 합니다.
- Docker에서 캡처하면 container runtime 문제를 함께 검증할 수 있지만, ordinary source/UI 변경까지 매번 Docker image rebuild로 검증하지는 않습니다.
- local Python에서 캡처하면 빠르고 가볍지만, Docker mount나 host path mapping 문제는 별도로 검증해야 합니다.

### 후속 확인

- 캡처 자동화가 실제로 추가될 때 `docs/setup-and-operations.md`에 실행 명령과 권장 사용 시점을 기록합니다.
- README Screenshot Guidance와 같은 원칙을 유지해 빈 화면보다 기능 가치가 드러나는 상태를 캡처합니다.
- 새 기능의 캡처 시나리오를 추가할 때는 해당 기능의 sample data 전제와 검증 text를 함께 남깁니다.

### 관련 문서

- [README Screenshot Guidance](../AGENTS.md#readme-screenshot-guidance)
- [Verification Surface Selection](../AGENTS.md#verification-surface-selection)
- [Screenshot Gallery](screenshot-gallery.md)
- [Failure History](failure-history.md)

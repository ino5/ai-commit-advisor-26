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

## 2026-06-10 - Roadmap candidate tasks preserve unresolved product concerns

### 배경

전역 프로젝트 컨텍스트와 Home 현재 프로젝트 중심 개선 이후, 바로 구현하지는 않지만 잊으면 안 되는 UX 고민이 남았습니다. 예를 들어 프로젝트별 UI 상태 key 정리, 프로그램 관리의 새 프로젝트 저장 예외, 개발자 목록의 전역/프로젝트별 범위 결정은 모두 제품 방향과 유지보수성에 영향을 줄 수 있습니다.

이런 내용을 별도 `ideas.md` 같은 문서로 만들면 로드맵과 분리되어 실제 작업으로 승격할 때 누락될 수 있습니다. 반대로 바로 `In Progress` 작업으로 만들면 아직 승인되지 않은 범위가 진행 중처럼 보입니다.

### 결정

`ROADMAP.md`에 `Candidate Tasks` 섹션을 둡니다. 이 섹션은 알려진 고민거리와 후속 개선 후보를 보관하되, 승인된 구현 작업과 구분합니다.

후보 작업을 실제로 시작할 때는 priority overview에 정식 작업으로 올리고, 별도 task section과 checklist를 만든 뒤 `In Progress`로 전환합니다.

### 이유

- 후보와 진행 중 작업을 분리해 현재 작업 상태를 더 정확히 보여줍니다.
- 제품/UX 고민을 로드맵 안에 보관하므로 이후 구현 작업으로 승격하기 쉽습니다.
- 별도 문서를 늘리지 않고 기존 roadmap 관리 흐름을 유지합니다.
- 에이전트가 사용자의 "기록만 해줘"와 "구현해줘"를 구분하기 쉬워집니다.

### 검토한 대안

- 별도 고민거리 문서 생성: 자유롭게 쓸 수 있지만 로드맵과 분리되어 구현 전환 시 누락될 가능성이 있습니다.
- 모든 후보를 priority overview에 `Backlog`로 추가: 표가 길어지고 완료된/승인된 작업과 미승인 후보가 섞입니다.
- `docs/engineering-decisions.md`에 후보를 기록: 아직 결정되지 않은 항목을 결정 로그에 넣는 것은 문서 역할과 맞지 않습니다.

### 영향과 tradeoff

- `ROADMAP.md` 상단이 조금 길어집니다.
- 대신 후속 개선 후보의 배경, 가능한 방향, 주의점을 한곳에서 관리할 수 있습니다.
- Candidate는 구현 약속이 아니므로, 실제 작업 전에는 다시 범위와 문서 영향을 검토해야 합니다.

### 관련 문서

- [Roadmap](../ROADMAP.md)
- [Agent Instructions](../AGENTS.md)
- [AI Change Log](../AI_CHANGELOG.md)

## 2026-06-10 - Global project context through a shared UI helper

### 배경

프로젝트 단위 화면마다 `프로젝트 선택` selectbox와 프로젝트 목록 조회 코드가 반복되어 있었습니다. 사용자는 메뉴를 이동할 때마다 같은 프로젝트를 다시 고르는 느낌을 받았고, 유지보수자는 selector label, 정렬, 선택 복구, 프로젝트 삭제 시 fallback 같은 규칙을 여러 화면에서 맞춰야 했습니다.

AI Commit Advisor의 주요 업무는 하나의 프로젝트를 기준으로 Git, 산출물, Mapping, Risk, RAG, Project Chat 결과를 연결하는 흐름입니다. 따라서 현재 작업 프로젝트를 앱 공통 컨텍스트로 두는 편이 사용자 흐름과 데이터 모델 모두에 더 잘 맞습니다.

### 결정

`src/ui/project_context.py`를 현재 프로젝트 컨텍스트의 공식 진입점으로 둡니다.

- 사이드바에서 현재 프로젝트를 한 번 선택합니다.
- 프로젝트 단위 화면은 `st.session_state`를 직접 읽지 않고 `require_project_context()` 또는 `get_current_project_context()`를 통해 프로젝트를 받습니다.
- helper는 프로젝트 목록 로드, 현재 선택 저장/조회, 삭제되었거나 잘못된 선택 복구, 프로젝트가 없을 때 안내를 담당합니다.
- Mapping, Risk, RAG, Project Chat, AI Progress, Program Detail, Commit Impact, Git, Developer, 개발계획, 표준용어 같은 프로젝트 단위 화면의 local 프로젝트 selector를 제거합니다.
- `프로젝트/Git 설정`은 프로젝트 생성/수정 화면이므로 자체 선택 UI를 유지하되, 저장한 프로젝트를 현재 프로젝트로 동기화합니다.
- `프로그램 목록`은 전역 프로젝트를 기본으로 쓰고, 기존처럼 새 프로젝트명으로 저장해야 하는 경우를 별도 옵션으로 분리합니다.

### 이유

- 전역 프로젝트 선택은 사용자가 페이지를 이동할 때 같은 분석 대상을 유지하게 해 줍니다.
- 페이지가 `st.session_state` key를 직접 읽으면 선택 복구 정책이 흩어지므로, helper를 통해 접근하는 규칙이 유지보수에 유리합니다.
- 현재 `PAGE_GROUPS`는 인자 없는 render 함수를 사용합니다. 모든 page renderer를 `render_page(project_context)` 형태로 한 번에 바꾸면 변경 범위가 커져 회귀 위험이 큽니다.
- 얇은 helper 방식은 중복 selector를 제거하면서도 기존 Streamlit 페이지 구조를 크게 흔들지 않습니다.

### 검토한 대안

- 각 페이지의 selector를 그대로 두고 기본값만 전역 선택으로 맞춤: 사용자 혼란은 조금 줄지만 선택 UI와 fallback 규칙 중복은 남습니다.
- 모든 render 함수가 `ProjectContext`를 인자로 받도록 즉시 변경: 의존성이 명확해지는 장점은 있지만 `app.py`, 모든 페이지, 테스트를 동시에 크게 바꿔야 해서 이번 범위에는 과합니다.
- `app.py`에서 직접 `st.session_state["current_project_id"]`를 관리하고 페이지들이 같은 key를 읽게 함: 구현은 빠르지만 삭제 복구, 안내 문구, DB 조회 정책이 페이지별로 퍼질 가능성이 큽니다.

### 영향과 tradeoff

- 프로젝트 단위 화면의 상단에는 현재 프로젝트 caption만 표시되고, 프로젝트 전환은 사이드바에서 수행합니다.
- helper가 비대해지지 않도록 Mapping, Risk, RAG, 업로드 검증, Project Chat 세션 같은 페이지별 비즈니스 로직은 helper에 넣지 않습니다.
- 전역 선택이 없는 상태에서도 프로그램 목록은 새 프로젝트명으로 저장할 수 있지만, 일반적인 작업 흐름은 프로젝트/Git 설정에서 프로젝트를 만든 뒤 사이드바에서 선택하는 방식입니다.
- 나중에 앱 구조가 커지면 `render_page(project_context)` 방식으로 명시적 의존성 주입을 다시 검토할 수 있습니다.

### 후속 확인

- 새 프로젝트 저장, 프로젝트 삭제 또는 이름 변경 흐름이 추가되면 `project_context.py`의 선택 복구와 동기화 규칙을 먼저 확인합니다.
- 프로젝트 단위 새 화면을 추가할 때는 페이지 내부 `프로젝트 선택`을 만들기 전에 `require_project_context()` 사용을 우선 검토합니다.

### 관련 문서

- [Feature Guide](feature-guide.md)
- [Architecture](architecture.md)
- [AI Change Log](../AI_CHANGELOG.md)
- [Roadmap](../ROADMAP.md)

## 2026-06-10 - Sidebar navigation uses one Streamlit rendering structure

### 배경

사이드바 메뉴는 이전에 활성 항목을 custom `div.nav-active`로 렌더링하고, 비활성 항목은 `st.button`으로 렌더링했습니다. CSS로 높이, padding, 왼쪽 border, font size를 맞췄지만 실제 DOM 구조와 wrapper margin이 달라 클릭 후 항목 위치가 미묘하게 달라질 수 있었습니다.

사용자 관점에서는 버튼 색만 바뀌어야 할 것처럼 보이는데 실제로는 메뉴 슬롯이 흔들리는 느낌을 줬고, 유지보수자 관점에서는 Streamlit button 구조와 custom HTML 구조를 계속 맞춰야 하는 부담이 남았습니다.

### 결정

사이드바 내비게이션 항목은 활성/비활성 상태와 관계없이 모두 `st.button`으로 렌더링합니다. 선택된 항목을 다시 클릭하면 상태 변경과 `st.rerun()` 없이 no-op로 처리합니다.

현재 위치 표시는 사이드바 상단의 `현재 위치` 경로에 맡기고, 메뉴 행 자체는 같은 box model과 같은 Streamlit DOM 구조를 유지합니다.

### 이유

- 같은 역할의 메뉴 항목이 상태에 따라 다른 DOM 구조를 쓰면 CSS 보정이 누적되고 회귀 가능성이 커집니다.
- Streamlit 앱에서는 기본 컴포넌트 구조를 유지하는 편이 custom HTML/JS 내비게이션보다 다음 유지보수자가 이해하기 쉽습니다.
- 활성 항목의 시각 강조보다 클릭 전후 위치 안정성이 더 중요한 UX 문제였습니다.
- 기존 `현재 위치` 표시가 선택 상태를 이미 알려주므로 메뉴 행에서 별도 active markup을 유지할 필요가 낮습니다.

### 검토한 대안

- `div.nav-active` 구조를 유지하고 margin/padding을 더 정밀하게 보정: 당장 차이는 줄일 수 있지만 Streamlit 내부 button wrapper와 custom div를 계속 동기화해야 합니다.
- 전체 사이드바를 custom HTML/JS navigation으로 재작성: 시각 제어는 가장 강하지만 Streamlit 상태 처리, 접근성, URL/query 동작을 직접 책임져야 해서 현재 앱 규모에는 과합니다.
- 선택된 버튼 label에 prefix를 붙여 active 상태를 표시: DOM 구조는 통일되지만 label text가 바뀌어 테스트, 문서, 사용자의 메뉴 인식에 불필요한 차이를 만듭니다.

### 영향과 tradeoff

- 메뉴 행의 active highlight는 제거되고, 선택 상태는 상단 `현재 위치` 표시로 확인합니다.
- Playwright 검증은 custom `.nav-active`가 남아 있으면 실패하고, 클릭 전후 메뉴 항목 box, text offset, 인접 간격이 바뀌면 실패하도록 보강했습니다.
- 향후 active highlight를 다시 추가해야 한다면 같은 `st.button` 구조 위에서 구현하거나, 동일한 wrapper 구조를 유지하는 별도 설계를 먼저 검증해야 합니다.

### 후속 확인

- Home feature screenshot capture는 사이드바 안정성 검증을 포함합니다.
- 사이드바에 새 메뉴 상태를 추가할 때는 활성/비활성 렌더링 구조가 갈라지지 않는지 확인합니다.

### 관련 문서

- [Failure History](failure-history.md)
- [Documentation Impact Gate](../AGENTS.md#documentation-impact-gate)
- [AI Change Log](../AI_CHANGELOG.md)
- [Roadmap](../ROADMAP.md)

## 2026-06-10 - Documentation impact gate for agent work

### 배경

사이드바 메뉴 위치 흔들림을 read-only로 조사한 뒤 유지보수성 관점의 처리 계획을 세우는 과정에서, 변경이 `docs/engineering-decisions.md` 검토 대상이라는 판단이 늦었습니다. `AGENTS.md`에는 이미 Engineering Decisions 기준이 있었지만, 계획 단계에서 변경 유형을 단순 UX 버그로 좁게 분류하면서 유지보수성·검증 정책·반복 가능한 agent policy 관점이 바로 연결되지 않았습니다.

이번 사례는 개별 문서 하나를 더 기억하는 문제가 아니라, 의미 있는 작업을 시작하기 전에 문서 영향도를 명시적으로 분류하는 게이트가 필요하다는 신호입니다.

### 결정

`AGENTS.md`에 `Documentation Impact Gate`를 추가합니다. 에이전트는 의미 있는 code, UX, test, behavior, automation, operations, documentation 작업을 제안하거나 시작하기 전에 최소한 다음 문서 영향도를 분류해야 합니다.

- `AI_CHANGELOG.md`
- `ROADMAP.md`
- `docs/engineering-decisions.md`
- `docs/failure-history.md`
- user-facing docs
- `docs/architecture.md`
- `docs/ai-technical-overview.md`
- `docs/db-migrations.md`
- `docs/sample-target-repo-demo-design.md`

특히 사용자가 유지보수성, future reuse, verification policy, structural tradeoff, operating policy, agent behavior 관점으로 변경을 설명하면 `docs/engineering-decisions.md`를 필수 검토 후보로 취급합니다.

### 이유

- 기존 지침은 각 문서의 역할을 설명했지만, 작업 계획 시점에 문서 영향도 분류를 하나의 명시적 게이트로 강제하지는 않았습니다.
- 유지보수성이나 검증 정책을 다루는 변경은 코드 diff가 작아도 앞으로 반복될 판단 기준을 바꿀 수 있습니다.
- 문서 업데이트를 빠뜨렸는지 사후에 확인하는 방식보다, 계획 단계에서 업데이트 대상과 제외 사유를 분리하는 편이 누락을 줄입니다.
- 새 문서를 만들기보다 기존 `AI_CHANGELOG.md`, `ROADMAP.md`, `engineering-decisions`, `failure-history`의 역할을 더 명확히 연결하는 편이 유지보수 부담이 낮습니다.

### 검토한 대안

- 별도 문서 영향도 체크리스트 파일 추가: 확인 대상이 늘어나고, 기존 `AGENTS.md` 정책과 중복될 수 있어 선택하지 않았습니다.
- `Pre-Commit Documentation Check`만 보강: commit 직전에는 이미 구현 방향이 굳어진 뒤라, 계획 단계 누락을 막기에는 늦습니다.
- 에이전트 응답 관행에만 맡기기: 이번 누락처럼 변경 분류가 좁아질 때 같은 문제가 반복될 수 있습니다.

### 영향과 tradeoff

- 의미 있는 작업 계획이 조금 길어질 수 있습니다.
- 반대로 agent policy, 검증 정책, 유지보수성 판단이 들어간 변경에서 문서 누락 가능성이 줄어듭니다.
- 모든 문서를 매번 수정하라는 뜻은 아닙니다. 영향도를 검토하고, 업데이트하지 않는 문서는 계획·최종 응답·commit note 중 한 곳에 이유를 남기는 것이 핵심입니다.

### 후속 확인

- 이번 변경은 `docs/failure-history.md`에도 연결해, 기존 정책이 있었는데도 `engineering-decisions` 검토가 늦어진 원인과 예방 규칙을 남깁니다.
- 향후 사이드바 구조 안정화처럼 유지보수성 중심의 UX 변경을 구현할 때는 이 게이트에 따라 `docs/engineering-decisions.md`를 먼저 검토해야 합니다.

### 관련 문서

- [Documentation Impact Gate](../AGENTS.md#documentation-impact-gate)
- [Failure History](failure-history.md)
- [AI Change Log](../AI_CHANGELOG.md)
- [Roadmap](../ROADMAP.md)

## 2026-06-10 - 기능 스크린샷 캡처 자동화 방향

### 배경

README와 Application Preview의 화면 캡처는 단순한 장식이 아니라, 기능이 실제 sample project에서 어떤 상태로 동작하는지 보여주는 검증 자료입니다. 특히 Project Chat처럼 RAG, source indexing, 현재 Git HEAD 검증, 근거 표시가 얽힌 기능은 빈 화면이나 실패 상태 캡처만으로는 기능 가치를 설명하기 어렵습니다.

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

- 캡처 자동화는 `scripts/capture_feature_screenshot.py`로 시작했습니다. 초기 시나리오는 `home`과 `project-chat`이며, 기존 Home 검증 명령은 `scripts/verify_home_ui.py` wrapper로 유지합니다.
- `docs/setup-and-operations.md`에 실행 명령, `--expect-text`/`--forbid-text` 검증 옵션, `--surface local|docker` 기록 방식을 남겼습니다.
- Application Preview Screenshot Guidance와 같은 원칙을 유지해 빈 화면보다 기능 가치가 드러나는 상태를 캡처합니다.
- 새 기능의 캡처 시나리오를 추가할 때는 해당 기능의 sample data 전제와 검증 text를 함께 남깁니다.

### 관련 문서

- [Application Preview Screenshot Guidance](../AGENTS.md#application-preview-screenshot-guidance)
- [Verification Surface Selection](../AGENTS.md#verification-surface-selection)
- [Application Preview](application-preview.md)
- [Failure History](failure-history.md)

## 2026-06-10 - 아키텍처 문서 경로 정리

### 배경

README는 프로젝트 진입점이고, 상세 문서는 대부분 `docs/` 아래에 모여 있습니다. 그런데 아키텍처 문서만 루트에 별도 파일로 남아 있어 문서 허브 구조에서 튀고, 새 문서를 찾을 때 일관성이 떨어졌습니다.

### 결정

아키텍처 문서를 `docs/architecture.md`로 이동하고, README 문서 허브와 `AGENTS.md`의 문서 체크리스트도 새 경로를 기준으로 정리합니다.

### 이유

- 루트에는 README와 프로젝트 설정 파일을 중심으로 두고, 세부 가이드는 `docs/`에 모으는 편이 탐색하기 쉽습니다.
- `docs/feature-guide.md`, `docs/setup-and-operations.md`, `docs/ai-technical-overview.md`와 같은 문서 구조와 맞습니다.
- 이후 architecture, data flow, service responsibility를 수정할 때 어느 파일을 업데이트해야 하는지 더 명확합니다.

### 검토한 대안

- 루트의 아키텍처 문서 유지: 기존 링크를 바꾸지 않아도 되지만 문서 구조의 어색함이 계속 남습니다.
- 파일명을 `ARCHITECTURE.md`로만 축약: 루트 파일명은 나아지지만 상세 문서를 `docs/`에 모은다는 방향과는 맞지 않습니다.

### 영향과 tradeoff

- 기존 루트 경로를 직접 열던 사람은 새 경로를 사용해야 합니다.
- README와 agent policy가 새 경로를 안내하므로 문서 허브를 통해 접근하는 흐름은 더 단순해집니다.

### 관련 문서

- [Architecture](architecture.md)
- [README 문서 허브](../README.md#문서)

## 2026-06-10 - Application Preview 문서명 선택

### 배경

기능별 화면 캡처 문서는 단순 이미지 모음처럼 보이기보다, 앱의 주요 화면과 실제 기능 상태를 미리 확인하는 문서로 읽히는 편이 더 적절합니다. 기존 이름은 문서의 용도를 너무 좁게 보이게 했고, README 문서 허브에서도 다소 투박하게 읽혔습니다.

### 결정

화면 캡처 중심 문서의 이름을 `Application Preview`로 정하고, 파일 경로는 `docs/application-preview.md`를 사용합니다. `AGENTS.md`의 관련 정책명도 `Application Preview Screenshot Guidance`로 맞춥니다.

### 이유

- `Application Preview`는 화면 캡처 중심 문서라는 의미를 유지하면서도 앱의 실제 사용 상태를 미리 본다는 느낌이 분명합니다.
- `Feature Overview`는 `docs/feature-guide.md`와 역할이 겹쳐 기능 설명 문서인지 화면 미리보기 문서인지 모호해질 수 있습니다.
- README 문서 허브에서 영어 문서명으로 유지해도 자연스럽고, 한국어 설명문과 함께 읽을 때 어색하지 않습니다.

### 영향과 tradeoff

- 기존 경로를 직접 열던 사람은 새 경로를 사용해야 합니다.
- 화면 자체는 그대로 두고 문서 이름과 링크만 바꾸므로 앱 동작이나 캡처 스크립트의 저장 경로는 바뀌지 않습니다.

### 관련 문서

- [Application Preview](application-preview.md)
- [Application Preview Screenshot Guidance](../AGENTS.md#application-preview-screenshot-guidance)

## 2026-06-10 - 샘플 프로젝트 문서 표현 기준

### 배경

샘플 데이터와 데모용 Git 저장소를 설명하는 문서에 내부 식별자를 직역한 표현이 남아 있었습니다. 의미는 전달되지만 한국어 제품 문서로는 어색하고, AI가 만든 문장처럼 읽힐 수 있었습니다.

### 결정

사용자가 읽는 Markdown 설명에서는 `샘플 프로젝트`를 기본 표현으로 사용합니다. 실제 고객 코드가 아니라는 점을 강조해야 할 때는 `데모용 샘플 프로젝트`라고 쓰고, Git 저장소라는 기술적 구분이 필요한 문장에서는 `샘플 프로젝트 Git 저장소`라고 씁니다.

파일명이나 코드 식별자는 안정성을 위해 그대로 둘 수 있지만, 링크 라벨과 주변 설명문은 자연스러운 한국어로 작성합니다.

### 이유

- README와 가이드 문서는 내부 구현 용어보다 사용자가 이해할 흐름을 먼저 보여줘야 합니다.
- 내부 구현 기준의 직역 표현은 정확하더라도 문서 문장에서는 기계 번역처럼 읽힙니다.
- 파일명까지 즉시 바꾸면 링크, 이력, 스크립트 참조가 불필요하게 흔들릴 수 있습니다.

### 관련 문서

- [샘플 프로젝트 설계](sample-target-repo-demo-design.md)
- [샘플 프로젝트 검증 가이드](rich-sample-demo-walkthrough.md)
- [Natural Korean Documentation Wording](../AGENTS.md#natural-korean-documentation-wording)

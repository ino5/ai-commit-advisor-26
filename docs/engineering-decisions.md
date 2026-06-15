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

## 2026-06-15 - Knowledge Graph Java 구조 추출은 경량 parser와 coverage warning으로 확장한다

### 배경

Knowledge Graph와 Project Chat GraphRAG는 Java class/import 관계를 보조 근거로 사용합니다. 단순 정규식은 빠르지만 annotation type, static import, nested member type, 주석/문자열 안의 가짜 선언, generated/build/test fixture 파일에서 graph 품질을 흔들 수 있습니다. 반대로 compiler-level semantic analysis를 바로 도입하면 설정, classpath, build tool 의존성이 커집니다.

### 결정

현재 단계에서는 Java source를 compiler로 빌드하지 않고, 주석/문자열 제거, static import 정규화, brace depth 기반 nested member type 추출, generated/build/test fixture 제외 규칙을 가진 경량 parser를 유지합니다. 제외 파일과 type 선언을 찾지 못한 파일은 `GraphPayload.warnings`와 `Neo4jSyncResult.warnings`로 분리해 `Knowledge Graph` 화면의 `동기화 준비 경고`에 표시합니다.

### 이유

- AX Use Case에서 필요한 것은 완전한 Java semantic graph보다 commit-program-file-class 관계를 설명할 수 있는 안정적인 read model입니다.
- 경량 parser는 앱 서버 저장소만 있으면 동작하므로 Maven/Gradle 설정, JDK, classpath 차이에 덜 민감합니다.
- warning을 error와 분리하면 graph coverage 문제를 운영자가 확인하면서도 증분 동기화를 불필요하게 실패시키지 않습니다.
- generated/build/test fixture를 제외하면 실제 업무 class/import 관계가 noise에 묻히는 일을 줄일 수 있습니다.

### 검토한 대안

- Java compiler 또는 language server 기반 AST/semantic 분석: 정확도는 높지만 환경 의존성과 실행 비용이 커서 별도 대형 작업으로 둡니다.
- 모든 `.java` 파일을 계속 포함: 구현은 단순하지만 generated/build/test fixture가 graph node와 import 관계를 오염시킬 수 있습니다.
- parser warning을 기존 `errors`에 섞기: UI 노출은 쉽지만 증분 동기화 실패 조건과 섞여 운영 흐름이 불안정해질 수 있습니다.

### 영향과 tradeoff

Nested member type과 static import 관계는 개선되지만, local class, anonymous class, generic type resolution, annotation processing 결과물은 여전히 완전하게 해석하지 않습니다. parser rule이 바뀐 뒤 기존 Neo4j graph와 preview가 다르게 보이면 `전체 재동기화`가 기준 복구 절차입니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `Source parser accuracy expansion`
- `ROADMAP.md`의 `P3 - Source Parser Accuracy Expansion`
- `docs/ai-technical-overview.md`
- `docs/setup-and-operations.md`

## 2026-06-15 - Neo4j graph write는 batch/retry 기반으로 처리하고 전체 재동기화를 복구 기준으로 둔다

### 배경

Knowledge Graph가 Project Chat GraphRAG와 AI 운영 상태의 보조 근거가 되면서 Neo4j 동기화는 단순한 화면 preview가 아니라 운영 근거 최신성에 영향을 주게 되었습니다. 대형 저장소에서 모든 node/edge를 하나의 transaction으로 쓰면 transaction memory, timeout, 일시적인 Bolt 연결 오류에 취약합니다.

### 결정

Neo4j full sync와 incremental sync의 write를 `NEO4J_WRITE_BATCH_SIZE` 단위로 나누고, 각 batch는 `NEO4J_RETRY_ATTEMPTS`, `NEO4J_RETRY_BACKOFF_SECONDS` 기준으로 retry합니다. 결과 metadata에는 요청 node/edge 수, batch 수, 완료 batch 수, written count, retry count, failed operation을 남깁니다. partial failure가 발생하면 `Knowledge Graph` 화면과 sync state metadata에서 실패 원인을 확인하고, `전체 재동기화`를 복구 기준으로 사용합니다.

### 이유

- batch write는 Neo4j transaction memory와 timeout 위험을 줄입니다.
- retry는 일시적인 연결 끊김이나 container 기동 직후 불안정한 상태를 흡수합니다.
- partial failure metadata가 있으면 운영자가 어디까지 반영됐는지 판단하고 복구 action을 선택할 수 있습니다.
- PostgreSQL은 여전히 source of truth이고 Neo4j는 read model이므로, graph가 의심될 때 전체 재동기화로 재생성하는 정책이 단순하고 안전합니다.

### 검토한 대안

- 모든 node/edge를 단일 transaction으로 계속 처리: atomicity는 좋지만 대형 graph에서 실패 가능성이 커집니다.
- 복잡한 resume cursor를 두어 실패 batch부터 이어쓰기: 효율적이지만 삭제/rename/current source 관계 정리와 결합하면 상태 관리가 복잡해집니다.
- Neo4j write 실패 시 PostgreSQL 작업까지 실패 처리: graph는 read model이므로 프로젝트 삭제/초기화 같은 PostgreSQL 작업을 막지 않는 기존 best-effort 정책과 맞지 않습니다.

### 영향과 tradeoff

Batch 단위로 쓰기 때문에 실패 시 일부 node/edge만 반영된 상태가 될 수 있습니다. 그래서 실패 메시지는 partial 가능성을 명시하고, 운영 복구는 전체 재동기화를 기본으로 합니다. `NEO4J_WRITE_BATCH_SIZE`를 너무 낮추면 안정성은 올라가지만 전체 sync 시간이 늘어날 수 있습니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `Neo4j production hardening`
- `ROADMAP.md`의 `P2 - Neo4j Production Hardening`
- `docs/setup-and-operations.md`
- `docs/architecture.md`

## 2026-06-15 - Git Sync 이후 AI 후속 작업은 상태 기반 안내와 명시 실행으로 분리한다

### 배경

Git Sync는 commit과 diff를 PostgreSQL에 수집하지만, RAG/Project Chat의 현재 소스 근거, embedding, Mapping, Risk Analysis, Neo4j Knowledge Graph는 별도 갱신이 필요합니다. 기능이 늘어나면서 사용자가 Git Sync 후 어떤 화면을 어떤 순서로 확인해야 하는지 기억해야 했고, 이 흐름이 끊기면 AI 분석 화면이 오래된 근거를 사용할 수 있었습니다.

### 결정

`Git 동기화` 화면에 `동기화 후 다음 작업` 패널을 두고, `git_followup_service.py`가 현재 DB/HEAD/source index/embedding/Mapping/Risk/Knowledge Graph 상태를 읽어 권장 순서를 계산합니다. 패널은 관련 화면으로 이동하는 재시작 가능한 action을 제공하지만, embedding이나 LLM 호출이 필요한 작업을 자동 실행하지 않습니다.

### 이유

- Git Sync 직후 사용자가 최신 근거 갱신 순서를 한 화면에서 볼 수 있습니다.
- embedding/LLM/Neo4j 작업은 비용과 local model 부하가 있으므로 사용자가 명시적으로 실행해야 합니다.
- 후속 작업 상태 계산을 Streamlit UI 밖 service에 두면 테스트와 재사용이 쉽습니다.
- Git Sync 결과가 없어도 현재 상태를 다시 계산하므로 나중에 화면을 열었을 때도 같은 점검 흐름을 사용할 수 있습니다.

### 검토한 대안

- Git Sync 성공 직후 모든 후속 작업 자동 실행: 편하지만 LLM/embedding 비용과 실행 시간이 커지고, 실패 시 원인 분리가 어렵습니다.
- 문서에 순서만 기록: 안전하지만 사용자가 매번 문서를 찾아야 하고 현재 프로젝트 상태를 반영하지 못합니다.
- 각 화면에만 개별 경고 표시: 기존 흐름과 비슷해 Git Sync 직후의 다음 행동을 한눈에 잡기 어렵습니다.

### 영향과 tradeoff

후속 작업 패널은 안내와 이동을 담당하며, 실제 실행은 RAG 검색, Project Chat, Mapping, Risk Analysis, Knowledge Graph 각 화면의 기존 action을 사용합니다. 따라서 한 번에 끝나는 자동 pipeline은 아니지만, 비용이 큰 작업을 사용자가 통제할 수 있고 실패/부분 완료 상태에서 필요한 화면으로 다시 들어가기 쉽습니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `Git Sync follow-up action orchestrator`
- `ROADMAP.md`의 `P2 - Git Sync Follow-Up Action Orchestrator`
- `docs/feature-guide.md`
- `docs/setup-and-operations.md`
- `docs/architecture.md`

## 2026-06-15 - Local LLM 검증은 명시 실행 script와 AI invocation telemetry로 남긴다

### 배경

AX Use Case에서 AI 적용 여부를 설명하려면 mock/fallback 화면 확인과 실제 local LLM 실행 증거를 분리해야 합니다. 이미 `ai_invocation_logs`는 provider/model/fallback/latency를 저장하지만, 팀원이 같은 방식으로 live provider 검증을 반복하는 명령과 화면 요약이 부족했습니다.

### 결정

`scripts/run_local_ai_verification.py`를 local OpenAI-compatible provider 검증 entrypoint로 둡니다. 이 script는 embedding 연결 확인, PL Briefing, Project Chat, AI Code Review, 선택적 Mapping을 실행하고 기존 `ai_invocation_logs`에 provider/model/status/fallback/validation을 남깁니다. `AI 운영 현황 > 실제 LLM 검증`은 이 telemetry를 읽어 mock이 아닌 provider의 fallback 없는 성공 범위와 최근 실행 증거를 보여줍니다.

### 이유

- 새 검증 전용 table을 만들지 않아도 기존 AI 호출 telemetry와 연결됩니다.
- CI나 기본 mock 환경에서 외부 LLM을 호출하지 않고, 사용자가 local model server를 켠 환경에서만 명시적으로 실행합니다.
- PL Briefing, Project Chat, AI Code Review, Mapping처럼 서로 다른 AI surface의 실행 증거를 같은 기준으로 비교할 수 있습니다.
- `--allow-mock`을 명시한 경우만 mock smoke check를 허용해 live 검증과 화면 흐름 확인을 섞지 않습니다.

### 검토한 대안

- 앱 화면에서 버튼 하나로 live 검증 전체 실행: 편하지만 LLM/embedding 서버 부하가 크고 의도치 않은 비용/시간 사용이 생길 수 있습니다.
- 별도 verification result table 추가: query는 편해지지만 telemetry와 중복되고 schema 관리가 늘어납니다.
- 문서에 수동 절차만 기록: 안전하지만 실행 결과가 일관된 telemetry로 남지 않아 다음 세션에서 확인하기 어렵습니다.

### 영향과 tradeoff

검증 script는 실제 프로젝트 데이터를 수정할 수 있습니다. PL Briefing과 Code Review는 이력을 추가하고, Mapping을 선택하면 지정 commit의 mapping 결과를 갱신할 수 있습니다. 그래서 기본 기능 목록에는 Mapping을 넣지 않고, 필요한 경우 `--features mapping --mapping-commit-limit 1`처럼 명시 실행하게 했습니다.

### 후속 확인

- local model server가 없으면 `AI 운영 현황 > 실제 LLM 검증`은 경고 상태를 보여주는 것이 정상입니다.
- 결과 품질 benchmark가 아니라 운영 증거이므로, 답변 품질은 각 기능의 source evidence, raw response, fallback 여부와 함께 검토해야 합니다.

### 관련 문서

- `docs/local-llm-verification.md`
- `docs/setup-and-operations.md`
- `AI_CHANGELOG.md`의 `Local LLM verification routine`

## 2026-06-15 - Knowledge Graph 최신성은 PostgreSQL metadata와 증분 read model 갱신으로 관리한다

### 배경

Neo4j Knowledge Graph와 Project Chat GraphRAG가 추가되면서 graph가 언제 만들어졌는지가 답변 근거 품질에 직접 영향을 주게 되었습니다. 기존 전체 동기화는 정확하지만 대형 저장소에서는 비용이 커지고, Git Sync나 mapping 변경 이후 Neo4j graph가 오래되었는지 화면에서 알기 어려웠습니다.

### 결정

PostgreSQL에 `project_graph_sync_state`를 추가해 Repo HEAD, DB Sync HEAD, Graph HEAD, sync mode, node/edge count, 마지막 commit row와 mapping update 기준을 저장합니다. Neo4j는 계속 재생성 가능한 read model로 유지하고, `Knowledge Graph` 화면에서 `최신 변경분만 Neo4j 반영`과 `전체 재동기화`를 구분합니다.

증분 반영은 graph를 `current_source`, `historical_git`, `analysis` 성격으로 나눠 다룹니다. 변경/삭제/rename된 Java 파일은 해당 path의 class node를 제거해 current source 관계를 끊고 다시 만들며, commit-file 이력 관계는 보존합니다. Program mapping edge는 현재 DB 기준으로 전체 refresh해 `is_related=false`나 삭제된 mapping이 graph에 남지 않게 합니다.

### 이유

- PostgreSQL이 계속 source of truth라서 graph sync metadata도 같은 transaction/backup 경계에서 관리할 수 있습니다.
- Neo4j를 source of truth로 만들지 않아도 GraphRAG가 사용할 관계 근거의 최신성을 사용자에게 설명할 수 있습니다.
- 변경 파일 단위로 current source 관계를 갈아끼우면 일반 Git Sync 이후에는 전체 graph 삭제/재생성을 피할 수 있습니다.
- Historical commit/file edge를 보존하면 삭제된 파일도 과거 diff 근거로 계속 설명할 수 있습니다.

### 검토한 대안

- 매번 전체 Neo4j 재동기화만 사용: 구현은 단순하지만 대형 프로젝트에서 비용이 커지고 "최신인지"를 별도로 설명하지 못합니다.
- Neo4j에 sync metadata를 저장: graph DB만 보면 편하지만 앱의 원본 상태와 migration/backup 경계가 갈라져 운영 복잡도가 커집니다.
- 변경 파일마다 개별 mapping edge만 추적 삭제: edge별 삭제 조건이 복잡해지고 mapping이 삭제되거나 `is_related=false`로 바뀐 경우 놓치기 쉽습니다.
- Neo4j를 업무/분석 source of truth로 승격: graph query는 강해지지만 기존 PostgreSQL/RAG/AI data lifecycle과 충돌합니다.

### 영향과 tradeoff

증분 sync는 Java source class/import 관계와 program mapping edge를 중심으로 다룹니다. Java parser가 정규식 기반인 한계, XML/SQL/다른 언어 관계 누락, 큰 branch 전환 같은 경우에는 `전체 재동기화`가 필요할 수 있습니다. Relationship type은 기존처럼 `RELATED`를 유지하고 `edge_type`, `graph_scope` property로 성격을 구분하므로 Neo4j Browser에서 native relationship type 다양성은 제한됩니다.

### 후속 확인

- 대형 프로젝트에서는 batch write, transaction timeout, retry/backoff가 별도 hardening 대상입니다.
- AI 운영 현황에도 graph freshness와 GraphRAG 준비 상태를 함께 보여주는 후속 작업이 남아 있습니다.
- parser 정확도 확장 시 current source 관계 삭제/재생성 테스트 fixture를 함께 보강해야 합니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `Knowledge Graph freshness and incremental Neo4j sync`
- `ROADMAP.md`의 `P1 - Knowledge Graph Freshness And Incremental Neo4j Sync`
- `docs/architecture.md`
- `docs/ai-technical-overview.md`
- `docs/feature-guide.md`
- `docs/setup-and-operations.md`

## 2026-06-15 - Project Chat GraphRAG는 verified source를 대체하지 않는 보조 근거로 적용한다

### 배경

Neo4j Knowledge Graph가 추가되면서 Project Chat이 vector/RAG 근거뿐 아니라 프로그램, 커밋, 파일, class, domain 관계도 답변에 사용할 수 있게 되었습니다. 다만 graph path는 관계를 잘 설명하지만 현재 checkout의 실제 코드 내용을 직접 검증하지는 않습니다. GraphRAG를 무조건 답변 근거로 승격하면 오래된 graph나 Java parser 누락이 현재 코드 사실처럼 보일 위험이 있습니다.

### 결정

Project Chat은 먼저 기존처럼 verified `source_file` evidence를 확보합니다. 검증된 현재 소스 근거가 있을 때만 질문, 확장 쿼리, 검색된 source/commit 근거에서 seed를 추출해 Neo4j의 `program -> commit -> file -> class`, `class -> imports -> class`, domain summary를 보조 context로 조회합니다. Graph evidence는 답변, UI, Markdown export, AI 운영 현황에서 source evidence와 분리해 저장/표시합니다.

### 이유

- Source verification은 현재 코드 사실을 말하기 위한 핵심 안전장치입니다.
- Graph path는 프로그램과 코드 구조 사이의 관계 설명에는 강하지만, 현재 파일 line/hash 검증을 대신하지 못합니다.
- Source evidence와 graph evidence를 분리하면 PL이 "현재 코드 근거"와 "관계 경로 근거"를 따로 검토할 수 있습니다.
- Neo4j가 꺼져 있거나 graph가 아직 동기화되지 않은 프로젝트도 기존 RAG-only 흐름으로 계속 사용할 수 있습니다.

### 검토한 대안

- Graph evidence만으로도 답변 허용: GraphRAG 가치는 커지지만 stale graph나 parser 한계가 현재 코드 사실처럼 보일 수 있어 채택하지 않았습니다.
- Project Chat이 매번 graph full preview를 재구성: Neo4j 동기화 없이도 동작하지만 질문마다 Git/DB/소스 scan 비용이 커지고, 저장 graph read model을 검증 표면으로 쓰는 설계와 어긋납니다.
- 별도 Graph Chat 화면 신설: scope가 커지고 사용자가 source RAG와 graph 질문을 구분해야 해서 현재 작업의 목표인 Project Chat 답변 품질 개선에는 과합니다.

### 영향과 tradeoff

Graph evidence는 `project_chat_messages.raw_metadata`에 저장해 PostgreSQL schema migration 없이 확장했습니다. 대신 graph evidence를 강하게 query/filter하는 기능은 아직 제한적입니다. Graph seed 추출은 질문, 확장 쿼리, 검색된 파일/class 이름 기반의 deterministic 방식이라 LLM 추가 호출 비용은 없지만, 질문이 너무 추상적이고 source retrieval도 부족하면 graph evidence를 찾지 못할 수 있습니다.

### 후속 확인

Knowledge Graph freshness와 incremental Neo4j sync가 구현되기 전까지는 사용자가 `Knowledge Graph` 화면에서 graph를 다시 동기화해야 최신 관계 근거가 반영됩니다. Java 외 언어, XML mapper, SQL 관계까지 graph 범위를 넓히는 작업은 별도 parser 정확도 개선과 함께 다룹니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `Project Chat GraphRAG context injection`
- `ROADMAP.md`의 `P1 - Project Chat GraphRAG Context Injection`
- `docs/ai-technical-overview.md`
- `docs/feature-guide.md`
- `docs/architecture.md`

## 2026-06-15 - Neo4j는 프로젝트 관계 그래프 read model로 적용한다

### 배경

AX Use Case에서 AI Commit Advisor는 LLM 호출 자체뿐 아니라 개발계획, Git 실행 이력, 코드 구조, 도메인 영향 범위를 연결해서 설명해야 합니다. 기존 PostgreSQL + pgvector 구조는 원본 데이터 저장, vector 검색, 규칙 기반 분석에는 적합하지만, 커밋-프로그램-파일-클래스-도메인으로 이어지는 관계 경로를 시각적으로 탐색하거나 이후 GraphRAG 근거로 확장하기에는 표현력이 부족했습니다.

### 결정

Neo4j를 선택적 graph read model로 추가합니다. PostgreSQL은 계속 source of truth로 유지하고, `Knowledge Graph` 화면에서 현재 프로젝트의 프로그램, 커밋, 파일, Java class, domain 관계를 Neo4j에 동기화합니다. Neo4j가 꺼져 있어도 화면은 PostgreSQL과 앱 서버 Git 저장소 기준 preview를 보여주며, 실제 graph 저장만 건너뜁니다.

### 이유

- Neo4j는 node/edge/path 탐색과 graph visualization 도구가 성숙해 AX 설명에서 관계형 AI 기반을 드러내기 좋습니다.
- PostgreSQL 원본 schema를 크게 흔들지 않고도 graph 기능을 바로 실험할 수 있습니다.
- `program_commit_mappings`, `commit_files`, Java class/import 관계를 graph로 투영하면 Commit Impact보다 넓은 프로젝트 전체 관계망을 보여줄 수 있습니다.
- 이후 Project Chat이 vector retrieval뿐 아니라 graph path를 근거로 사용하는 GraphRAG 확장으로 이어질 수 있습니다.

### 검토한 대안

- PostgreSQL 재귀 CTE와 JSONB만 사용: 추가 인프라는 줄지만 graph path 탐색, class/domain 관계 시각화, Neo4j Browser 기반 검토 장점이 약합니다.
- Apache AGE 같은 PostgreSQL graph 확장: 단일 DB 운영에는 유리하지만 Docker/Windows 개발 환경과 Python ecosystem 검증 범위가 커지고, Neo4j만큼 익숙한 graph 운영/시각화 경험을 바로 얻기 어렵습니다.
- Neo4j를 source of truth로 사용: graph 질의는 강하지만 기존 업무/AI/RAG 데이터 모델을 이중 원본으로 나누게 되어 동기화 충돌과 운영 복잡도가 커집니다.
- GraphRAG까지 즉시 구현: AI 활용감은 강하지만 retrieval 품질, prompt safety, 테스트 범위가 커져 첫 Neo4j 적용의 안정성을 떨어뜨립니다.

### 영향과 tradeoff

Neo4j Docker service, Python driver, 환경 변수가 추가되어 실행 구성은 조금 무거워집니다. 로컬 Quick Start는 Neo4j를 기본으로 켜지만, `NEO4J_ENABLED=false`에서는 기존 앱 기능이 그대로 동작합니다. 현재 Java 구조 추출은 정규식 기반 경량 parser라 compiler 수준의 완전성을 보장하지 않습니다. graph edge는 `RELATED` relationship에 `edge_type` property를 두는 방식으로 저장해 동적 relationship type 관리 복잡도를 줄였지만, Neo4j Browser에서 관계 type이 모두 `RELATED`로 보이는 tradeoff가 있습니다.

### 후속 확인

- GraphRAG로 확장할 때는 Project Chat prompt에 graph path를 어떻게 넣을지, vector 근거와 graph 근거의 우선순위를 어떻게 표시할지 별도 결정이 필요합니다.
- Java 외 언어 또는 MyBatis XML, SQL mapper 관계까지 확장할 때는 parser 전략과 테스트 fixture를 보강해야 합니다.
- 운영 환경에서는 Neo4j 비밀번호와 volume backup 정책을 기본값에서 분리해야 합니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `Neo4j Knowledge Graph foundation`
- `ROADMAP.md`의 `P1 - Neo4j Knowledge Graph Foundation`
- `docs/architecture.md`
- `docs/ai-technical-overview.md`
- `docs/feature-guide.md`
- `docs/setup-and-operations.md`
- `docs/db-migrations.md`
- `docs/failure-history.md`의 `Neo4j schema 변경과 graph write를 같은 transaction에서 실행했다`

## 2026-06-15 - AI 근거 화면은 운영 현황으로 보이게 한다

### 배경

AI 분석 근거와 호출 telemetry를 한곳에 모으는 화면은 AX Use Case에서 AI가 실제로 어떻게 동작했는지 설명하는 데 필요합니다. 다만 메뉴명이 검증 행위에만 초점을 맞추면 PL이나 리뷰어가 "무엇을 보러 들어가는 화면인지" 바로 이해하기 어렵고, 연결된 LLM/embedding 모델이 무엇인지도 첫 화면에서 드러나지 않습니다.

### 결정

사용자-facing 메뉴와 화면 제목은 `AI 운영 현황`으로 둡니다. 화면 상단에는 `연결된 AI` 요약을 배치해 LLM provider/model/base URL, embedding provider/model/dimension, 최근 AI 호출, 검색 준비, 호출 요약을 먼저 보여줍니다. 기존 근거 추적, 품질 점검, 주간 보고서, 호출 기록은 같은 화면 안의 세부 탭으로 유지합니다.

### 이유

- `AI 운영 현황`은 단순 검증표보다 현재 AI 연결 상태와 실행 결과를 함께 보는 화면이라는 의미가 자연스럽습니다.
- AX Use Case에서는 "어떤 모델이 붙어 있고, 실제 호출과 fallback이 남았는가"가 AI 적용 설명의 첫 질문입니다.
- Dashboard와 PL Briefing은 업무 화면으로 유지하고, 이 화면은 AI 상태와 근거를 확인하는 보조 관제 역할에 집중하는 편이 메뉴 구조가 덜 혼란스럽습니다.

### 검토한 대안

- `AI 상태`: 짧고 쉽지만 근거 추적, 보고서, 호출 기록까지 담기에는 범위가 좁게 읽힙니다.
- `AI 운영 상태`: 의미는 맞지만 메뉴명으로는 다소 딱딱하고 현재/최근 실행 기록을 포괄하는 느낌이 약합니다.
- 화면 삭제: 일반 업무 흐름은 단순해지지만 AI provider/model, fallback, evidence, telemetry를 한곳에서 설명할 수 있는 AX 검토 표면을 잃습니다.

### 영향과 tradeoff

내부 파일명과 service 이름은 기존 `ai_evidence` 계열을 유지합니다. 사용자-facing 이름은 자연스러워지지만, 내부 구현 이름과 화면명이 완전히 일치하지 않는 절충이 생깁니다. 파일명 변경은 import, screenshot scenario, 과거 문서 링크 churn이 크므로 별도 필요가 생길 때 다룹니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `AI 운영 현황 메뉴와 연결 상태 요약`
- `ROADMAP.md`의 `AI operations status menu`
- `docs/ai-technical-overview.md`
- `docs/feature-guide.md`
- `docs/application-preview.md`

## 2026-06-15 - 검증 설명은 검증과 운영 준비 표현을 우선한다

### 배경

AX Use Case 프로젝트는 단발성 발표 자료가 아니라 실제 운영 판단을 돕는 제품형 도구로 보여야 합니다. 화면과 문서가 행사 중심 표현에 기대면 AI 운영 현황, Project reset, 샘플 프로젝트 같은 기능이 실제 PL 점검 흐름보다 일회성 발표 맥락으로 읽힐 수 있습니다.

### 결정

사용자-facing UI, README, 기능 가이드, Application Preview, 샘플 프로젝트 문서, 자동 캡처 기준에서는 검증, 운영 준비, 분석 재실행, 근거 확인 같은 표현을 우선 사용합니다. 내부 파일명이나 기존 영문 convention은 과도하게 바꾸지 않되, 화면에 직접 보이는 한국어 문구는 제품 사용 맥락에 맞춥니다.

### 이유

- AX 검증의 가치는 단순 발표보다 AI 근거, 운영 상태, 리스크 판단 흐름을 설명하는 데 있습니다.
- 같은 기능을 고객사나 팀원이 반복 사용한다고 가정하면 검증/운영 표현이 더 자연스럽습니다.
- 문서와 화면의 톤을 맞추면 AI 운영 현황이 일회성 자료가 아니라 품질 확인 cockpit으로 읽힙니다.

### 검토한 대안

- 기존 표현 유지: 내부 의도는 분명하지만 제품 화면에서는 일회성 행사처럼 보일 수 있습니다.
- 모든 `demo` 파일명까지 변경: 톤은 더 일관되지만 파일명, 링크, 이력까지 큰 churn이 생겨 현재 범위에는 맞지 않습니다.

### 영향과 tradeoff

기존 문서의 일부 historical wording도 현재 제품 톤에 맞춰 바뀝니다. 다만 파일명과 익숙한 영문 label은 유지하므로, 과거 맥락을 완전히 지우기보다 사용자-facing 한국어 표현을 정돈하는 절충입니다.

### 후속 확인

새 화면이나 문서를 추가할 때 검증, 운영 준비, 근거 확인, 분석 재실행 같은 표현을 먼저 검토합니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `검증 용어 정리`
- `ROADMAP.md`의 `검증 wording cleanup`

## 2026-06-15 - AX 검증 AI 신뢰성은 AI 검증 화면과 telemetry로 설명한다

### 배경

AX 검증에서 AI 기능이 많아질수록 "AI를 실제로 썼는가", "어떤 근거로 판단했는가", "검증 전에 환경이 준비됐는가"를 한 화면에서 설명할 필요가 커졌습니다. Dashboard, Mapping, Project Chat, AI Code Review, PL Briefing은 각각 결과를 보여주지만, 검증자는 provider/model, fallback, validation, source evidence, latency를 흩어진 화면에서 찾아야 했습니다.

### 결정

`AI 검증` 화면을 추가해 검증 준비 상태, evidence trace, 프로젝트 AI 품질 점검, 주간 보고서 export, AI invocation telemetry를 한 곳에 묶습니다. AI 호출 관측값은 `ai_invocation_logs`에 저장하고, PL Briefing은 구조화 validation 실패 시 1회 repair retry를 시도한 뒤 fallback reason을 남깁니다.

### 이유

- 검증에서는 기능 개수보다 AI 판단의 근거와 운영 상태를 즉시 설명하는 것이 설득력에 더 직접적입니다.
- 별도 화면으로 묶으면 Dashboard의 PL 업무 흐름을 복잡하게 만들지 않으면서도 검증 담당자가 필요한 근거를 빠르게 찾을 수 있습니다.
- telemetry를 DB에 남기면 local LLM 품질 차이, fallback 발생, latency 문제를 감각이 아니라 기록으로 설명할 수 있습니다.
- 주간 보고서 export는 화면 검증을 실제 PL 점검 산출물로 연결합니다.

### 대안

- 각 기능 화면에만 trace expander 추가: 화면별 맥락은 좋지만 검증 준비와 품질 점검이 흩어져 전체 AI 적용 설명이 약해집니다.
- 외부 observability 도구 연동: 운영적으로는 강하지만 현재 검증 범위와 배포 복잡도에 비해 무겁습니다.
- 평가 scorecard를 별도 CLI만으로 제공: 자동화에는 좋지만 검증자가 화면에서 바로 설명하기 어렵습니다.

### 영향과 한계

- `ai_invocation_logs` schema와 reset/delete lifecycle 관리가 추가됩니다.
- scorecard는 현재 프로젝트에 저장된 AI 결과와 evidence 충분성을 보는 운영 점검이며, 통계적 benchmark가 아닙니다.
- raw metadata는 debugging/evidence 목적이므로 민감정보를 직접 표시하지 않도록 화면에서는 요약과 접이식 JSON 중심으로 다룹니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `AX AI 검증과 telemetry 구현`
- `docs/ai-technical-overview.md`
- `docs/architecture.md`
- `docs/db-migrations.md`

## 2026-06-15 - PL Briefing은 구조화 응답과 저장 이력으로 관리한다

### 배경

`PL Briefing`은 AX 검증에서 실제 LLM 활용을 보여주는 핵심 장면입니다. 하지만 free-form Markdown을 그대로 표시하면 모델마다 제목, 섹션, 문장 톤이 흔들릴 수 있고, 생성 결과가 화면 rerun 뒤 사라져 회의 기록이나 검증 증거로 재사용하기 어렵습니다.

### 결정

LLM에는 `summary`, `priority_items`, `meeting_questions`, `next_actions` JSON schema를 요청하고, 앱이 이 구조를 일관된 Markdown으로 조립합니다. 생성 결과는 `pl_briefing_history`에 provider/model/mode, 구조화 섹션, rendered text, Radar evidence payload, raw response와 함께 저장합니다. 구조화 파싱에 실패하거나 mock provider를 사용할 때는 같은 schema의 deterministic fallback을 저장합니다.

### 이유

- 브리핑 화면의 제목과 섹션을 앱이 통제하면 검증 중 출력 흔들림이 줄어듭니다.
- 저장 이력이 있으면 PL이 최근 브리핑을 다시 확인하고, 같은 프로젝트의 점검 기록을 비교할 수 있습니다.
- Radar score는 여전히 설명 가능한 계산으로 유지하고, LLM은 evidence를 회의용 언어로 정리하는 역할에 머물러야 합니다.
- raw response와 evidence payload를 함께 저장하면 LLM 출력 품질이나 근거 불일치를 나중에 검토할 수 있습니다.

### 검토한 대안

- free-form Markdown 유지: 구현은 단순하지만 모델별 문장/섹션 흔들림이 커서 검증 안정성이 떨어집니다.
- generated Markdown만 저장: 화면 재표시는 쉽지만 구조화된 이력 분석이나 섹션별 표시 개선이 어렵습니다.
- briefing을 저장하지 않음: schema 변경은 피하지만 회의 기록과 검증 증거가 남지 않습니다.

### 영향과 tradeoff

- `pl_briefing_history` schema가 추가되어 migration과 reset/delete lifecycle 관리가 필요합니다.
- LLM 응답이 schema를 지키지 않으면 fallback으로 전환하므로, 사용자는 항상 브리핑을 볼 수 있지만 provider별 생성 품질 차이는 남습니다.
- 저장 이력은 회의 보조 기록이며 확정 일정 판단이나 개인 평가 근거가 아닙니다.

### 관련 문서

- `ROADMAP.md`의 `Structured PL Briefing History And Validation Hardening`
- `docs/ai-technical-overview.md`
- `docs/feature-guide.md`
- `docs/architecture.md`
- `docs/db-migrations.md`
- `AI_CHANGELOG.md`의 `구조화 PL Briefing 이력과 검증 안정화`

## 2026-06-14 - AI Resource Radar는 설명 가능한 점수와 LLM briefing을 분리한다

### 배경

AX Use Case에서는 AI가 프로젝트 자원관리 판단을 어떻게 돕는지가 검증에서 분명해야 합니다. 기존 Dashboard는 자원관리 지표와 리스크를 보여주지만, LLM/RAG/AI Progress 결과가 여러 화면에 흩어져 있어 "AI가 무엇을 먼저 보라고 추천하는지"가 한눈에 드러나지 않았습니다.

### 결정

Dashboard에 `AI Resource Radar`를 추가하되, 우선순위 점수는 HIGH risk, 예상 지연, 계획 대비 AI 진척도 차이, 난이도, cross-program commit, 관련 commit 부재, workload point 같은 설명 가능한 신호로 계산합니다. LLM은 점수를 직접 결정하지 않고, 사용자가 `PL Briefing 생성`을 누를 때 Radar evidence를 주간 점검 브리핑으로 요약하는 역할만 맡깁니다. LLM provider가 `mock`이거나 호출 실패 시 deterministic fallback briefing을 보여줍니다.

### 이유

- PL이 먼저 볼 항목은 근거와 산식이 보여야 하므로 LLM 단독 판정보다 설명 가능한 점수가 안전합니다.
- LLM은 회의용 요약과 확인 질문 생성에 강점이 있어, evidence 기반 briefing 생성자로 쓰는 편이 AX 검증 가치가 큽니다.
- mock/local 환경 모두에서 Dashboard가 깨지지 않아야 하므로 fallback이 필요합니다.
- 기존 `resource_metrics_service.py`를 재사용하면 자원관리 산식이 UI에 흩어지지 않습니다.

### 검토한 대안

- LLM이 전체 우선순위를 직접 산출: AI 활용감은 강하지만 재현성, 테스트, 근거 추적이 약합니다.
- 규칙 기반 Radar만 제공: 안정적이지만 사용자가 기대하는 생성형 AI 활용이 덜 드러납니다.
- 별도 DB 테이블에 briefing 저장: 감사/이력에는 좋지만 첫 구현에서는 schema와 lifecycle이 커진다고 판단해 보류했습니다. 이후 `2026-06-15 - PL Briefing은 구조화 응답과 저장 이력으로 관리한다` 결정에서 채택했습니다.

### 영향과 tradeoff

- Radar score는 의사결정 보조 신호이며 확정 일정 판단이나 개인 평가 지표가 아닙니다.
- PL Briefing은 LLM 출력이므로 문장 품질은 provider/model에 따라 달라질 수 있습니다. 화면에는 provider, model, LLM/fallback mode를 함께 보여줍니다.
- briefing 이력 저장은 2026-06-15에 `pl_briefing_history`로 추가되어, 최근 브리핑과 이력 표를 Dashboard에서 다시 확인할 수 있습니다.

### 관련 문서

- `ROADMAP.md`의 `AI Resource Radar And PL Briefing`
- `docs/ai-technical-overview.md`
- `docs/feature-guide.md`
- `docs/architecture.md`
- `AI_CHANGELOG.md`의 `AI Resource Radar와 PL Briefing 추가`

## 2026-06-14 - 서버 저장소 clone/fetch는 인증정보 저장 없이 지원한다

### 배경

기존 운영 모델은 운영자가 앱 서버에 Git 저장소를 미리 clone하고, AI Commit Advisor는 그 경로만 읽는 방식이었습니다. 이 모델은 안전하지만 프로젝트를 자주 만들거나 반복 검증하는 환경에서는 remote URL과 branch를 앱에 저장한 뒤 서버 clone을 준비하는 흐름이 더 편합니다.

### 결정

프로젝트에 `git_remote_url`, `git_branch`를 저장하고, 프로젝트/Git 설정에서 `서버 저장소 clone/fetch` action을 제공합니다. 대상 경로가 없으면 clone하고, 이미 Git 저장소면 `origin`을 fetch한 뒤 branch를 `origin/<branch>`로 reset합니다. 동시 실행은 repository별 lock 파일로 막고, working tree에 local 변경이 있으면 기본적으로 reset을 건너뜁니다. 앱은 access token, SSH key, password를 저장하지 않습니다. HTTPS remote URL에 userinfo가 포함되거나 URL에 password가 포함되면 저장/실행을 거부하고, clone 성공 메시지에도 remote URL 원문을 표시하지 않습니다.

### 이유

- 운영자가 매번 서버 shell에서 clone/fetch를 실행하지 않아도 앱 안에서 저장소 준비를 시작할 수 있습니다.
- 인증정보를 앱 DB에 넣지 않으면 보안 검토 범위와 유출 위험을 줄일 수 있습니다.
- `REPO_STORAGE_ROOT` 경로 제한을 그대로 사용해 앱이 준비할 수 있는 저장소 위치를 제한합니다.
- dirty working tree guard와 lock 파일은 분석용 clone을 무심코 덮어쓰는 위험을 낮춥니다.

### 검토한 대안

- 기존 pre-cloned 방식만 유지: 안전하지만 반복 등록과 운영 자동화가 불편합니다.
- 앱이 token/SSH key를 저장: 편하지만 credential encryption, rotation, 접근권한, 감사 로그 설계가 필요해 현재 범위보다 큽니다.
- 별도 운영 스크립트만 확장: 서버 운영에는 좋지만 앱 사용자에게 현재 프로젝트의 remote/branch 상태를 보여주기 어렵습니다.

### 영향과 tradeoff

- private repository는 서버 OS의 SSH agent, credential helper, 배포 계정 권한을 먼저 준비해야 합니다.
- 앱은 저장소 용량 정리, credential rotation, 사용자별 Git 권한을 관리하지 않습니다.
- URL userinfo 차단은 앱 DB와 화면 메시지의 우발적 credential 노출을 줄이지만, 서버 OS credential helper나 SSH agent 자체의 권한 관리는 여전히 운영 책임입니다.
- reset은 `origin/<branch>` 기준으로 working tree를 맞추므로 분석용 clone에 local 변경을 남기는 운영과는 맞지 않습니다.

### 관련 문서

- `ROADMAP.md`의 `Server-Managed Clone/Fetch Workflow`
- `docs/git-repository-operating-model.md`
- `docs/server-repository-update-runbook.md`
- `docs/setup-and-operations.md`
- `AI_CHANGELOG.md`의 `Server-managed clone/fetch workflow`

## 2026-06-14 - 프로젝트 초기화는 산출물을 보존하고 분석 데이터만 지운다

### 배경

프로젝트 삭제는 잘못 등록했거나 더 이상 쓰지 않는 프로젝트를 완전히 정리하는 기능입니다. 하지만 반복 실행이나 검증에서는 같은 프로젝트명, Git 경로, 프로그램 목록, 개발계획, 개발자 연결, 표준용어를 유지한 채 Git 수집과 분석 결과만 다시 만들고 싶을 때가 많습니다. 이때 삭제를 사용하면 산출물 업로드와 프로젝트 등록부터 다시 해야 해서 반복 비용이 큽니다.

### 결정

`프로젝트/Git 설정`에 별도 `분석 데이터 초기화` action을 둡니다. 초기화는 프로젝트 record, Git 저장소 경로, 프로그램/개발계획, 표준용어/표준단어, 프로젝트 개발자 연결을 보존합니다. 대신 Git commit, 변경 파일/diff, 프로그램-커밋 매핑, 분석 실행 이력, 구현상태 분석, 리스크, 자원관리 snapshot, RAG chunk/vector, Project Chat session/message, AI Code Review 결과, 마지막 Git 동기화 상태를 삭제합니다.

### 이유

- 반복 검증은 산출물보다 분석 결과를 다시 만드는 작업이 핵심입니다.
- 프로젝트 삭제보다 덜 파괴적인 action을 분리하면 잘못된 clean-slate 작업을 줄일 수 있습니다.
- 프로그램/개발계획/표준용어를 보존하면 Mapping, Risk, RAG, Project Chat 재실행 흐름을 빠르게 반복할 수 있습니다.
- 마지막 Git 동기화 상태를 비워야 Git Sync가 초기 수집처럼 다시 실행될 수 있습니다.

### 검토한 대안

- 프로젝트 삭제만 사용: 가장 단순하지만 산출물 재등록 비용이 크고 반복 데모에 불편합니다.
- 프로그램/개발계획까지 모두 초기화: 깨끗하지만 “같은 프로젝트 shell로 재분석”이라는 목적과 맞지 않습니다.
- 초기화 옵션을 세분화: 유연하지만 어떤 데이터 조합이 안전한지 사용자가 판단해야 하므로 첫 버전에는 과합니다.

### 영향과 tradeoff

- 초기화 후에도 프로그램과 표준용어는 남으므로 완전한 빈 프로젝트가 필요하면 프로젝트 삭제를 사용해야 합니다.
- Git commit과 RAG/Project Chat 데이터는 제거되므로 초기화 후에는 Git 동기화, Mapping, RAG 검색 준비, Project Chat 근거 준비를 다시 실행해야 합니다.
- 전역 `developers`는 삭제하지 않으며, 프로젝트 개발자 연결도 보존합니다. 개발자 목록 자체를 정리하려면 별도 관리 화면을 사용합니다.

### 관련 문서

- `ROADMAP.md`의 `Project Reset Action After Delete Flow`
- `docs/feature-guide.md`
- `docs/architecture.md`
- `AI_CHANGELOG.md`의 `Project reset action after delete flow`

## 2026-06-14 - Dashboard 가치 지표는 사용자-facing 참고 지표로 표현한다

### 배경

Dashboard의 자원관리 영역은 리뷰 시간 절감 가능성, 추가 투입 예방 가능성, 예상 지연 프로그램처럼 PL이 조기 대응에 참고할 값을 보여줍니다. 이전 표현은 `계산 가정`, `KPI`, `planning signal` 같은 내부 설계 용어를 화면과 사용자 문서에 직접 노출했습니다. 이 표현은 계산값이 확정 성과가 아니라는 경계는 분명하지만, 사용자가 기능을 운영 화면이 아니라 실험용 화면처럼 받아들일 수 있습니다.

### 결정

앱 화면과 사용자-facing 문서에서는 `고객가치 KPI`, `가정값`, `planning signal` 대신 `고객가치 참고 지표`, `현재 계산 기준의 참고 추정값`, `일정과 병목을 보는 참고 신호`처럼 해석 중심 표현을 사용합니다. 기술 문서와 engineering decision에서는 계산 가정, 검증 범위, 운영 한계를 설명할 때만 내부 단계 표현을 제한적으로 남길 수 있습니다.

### 이유

- Dashboard 사용자는 먼저 "어떤 결정을 돕는 값인가"를 이해해야 합니다.
- `KPI`는 확정 성과관리 지표처럼 읽힐 수 있어 현재의 추정형 지표와 어긋납니다.
- `계산 가정`은 내부 단계 표현이라 화면 신뢰도를 낮출 수 있습니다.
- 개인 평가나 확정 절감액이 아니라는 안전장치는 표현을 낮추더라도 계속 필요합니다.

### 검토한 대안

- 화면에도 `검증`와 `KPI`를 유지: 한계는 분명하지만 첫 독자에게 딱딱하고 내부자 용어처럼 보입니다.
- 모든 문서에서 `검증`를 제거: 실제 계산 가정과 운영 범위를 설명해야 하는 기술 문서에서는 오히려 맥락이 사라집니다.
- `비즈니스 KPI`로 대체: 성과관리나 회계 지표처럼 오해될 수 있어 현재의 참고 추정값 성격과 맞지 않습니다.

### 영향과 tradeoff

사용자 화면은 더 자연스럽게 읽히지만, 계산식과 한계를 설명하는 문서와의 용어 차이가 생깁니다. 따라서 사용자 문서에는 짧은 해석 경계를 남기고, 기술 문서에는 계산 기준과 검증 범위를 계속 기록합니다.

### 후속 확인

Dashboard에 새 가치 지표를 추가할 때는 먼저 사용자-facing label을 정하고, tooltip에는 계산 기준과 한계를 짧게 적습니다. 확정 성과나 개인 평가로 읽히는 표현은 피합니다.

### 관련 문서

- `AI_CHANGELOG.md`의 `Dashboard 가치 지표 용어 정리`
- `docs/feature-guide.md`
- `docs/ai-technical-overview.md`
- `docs/application-preview.md`

## 2026-06-14 - 분석 화면 기본 표시는 업무 라벨을 우선한다

### 배경

Program Detail, AI Progress, Git History, Commit Impact, Risk Analysis, AI Code Review는 프로젝트 리더와 운영자가 판단을 내리는 화면입니다. 이 화면에 Python dictionary, JSON, `risk_type`, `planned_start_date`, `target_type` 같은 내부 필드명이 그대로 나오면 사용자는 원본 데이터 구조를 해석한 뒤 업무 의미로 다시 번역해야 합니다.

### 결정

분석 화면의 기본 표시에는 한국어 업무 라벨과 `항목/값` 요약 표를 우선 사용합니다. commit hash, program ID, file path, API/model name처럼 증거 추적에 필요한 기술 식별자는 유지하되, 원본 객체 구조와 내부 코드값은 기본 화면의 주요 요약으로 직접 노출하지 않습니다.

### 이유

- 사용자는 분석 결과의 의미와 다음 행동을 먼저 판단해야 합니다.
- 기술 식별자는 근거 추적에 필요하지만, 화면 제목이나 필터, 요약 표의 주언어가 되면 스캔 비용이 커집니다.
- 공통 `display_utils.py` helper로 날짜와 key/value 표 표시를 맞추면 화면별 미세한 포맷 차이를 줄일 수 있습니다.

### 검토한 대안

- Raw JSON을 접힌 기술 상세에 유지: 디버깅에는 좋지만 이번 범위의 주요 문제는 기본 화면 노출이므로 우선 제거했습니다. 필요한 화면은 후속으로 별도 `기술 상세` expander를 추가할 수 있습니다.
- 모든 컬럼명을 한국어로 강제 변환: commit hash, file path, program ID처럼 그대로 두는 편이 더 명확한 식별자까지 번역하려는 부작용이 있습니다.

### 영향과 tradeoff

- 기본 화면은 읽기 쉬워지지만, 개발자가 raw payload를 즉시 확인하던 편의는 줄어듭니다.
- AI 응답 payload 전체 검토가 필요한 경우에는 별도 debug/technical detail UI를 추가하는 것이 좋습니다.

### 관련 문서

- `ROADMAP.md`의 `User-Facing Analysis Display Cleanup`
- `docs/feature-guide.md`
- `docs/architecture.md`
- `AI_CHANGELOG.md`의 `분석 화면 표시 정리`

## 2026-06-14 - 현재 프로젝트 선택은 URL query parameter로도 보존한다

### 배경

전역 현재 프로젝트 selector는 Home, Mapping, RAG, Project Chat, Git History, AI Code Review 등 대부분의 프로젝트 단위 화면을 결정합니다. 선택값이 Streamlit session state에만 있으면 브라우저 새로고침이나 새 tab 진입 후 첫 프로젝트로 되돌아갈 수 있습니다. 샘플·검증 프로젝트처럼 이름이 비슷한 프로젝트가 여러 개 있으면 사용자는 같은 화면을 보고 있다고 생각하지만 실제로는 다른 프로젝트 지표를 보게 됩니다.

### 결정

`src/ui/project_context.py`가 현재 프로젝트 ID를 Streamlit session state와 URL `project_id` query parameter에 함께 저장합니다. 화면 진입 시에는 유효한 `project_id` query parameter를 먼저 복원하고, 값이 없거나 삭제된 프로젝트를 가리키면 기존 session state 또는 첫 프로젝트로 복구합니다.

### 이유

- 새로고침 후에도 사용자가 보고 있던 프로젝트 컨텍스트를 유지할 수 있습니다.
- URL만으로 특정 프로젝트 화면을 다시 열 수 있어 검증과 협업이 쉬워집니다.
- 각 페이지가 별도 저장 규칙을 갖지 않고 기존 `project_context.py` 진입점을 계속 사용합니다.

### 검토한 대안

- Session state만 유지: 구현은 가장 단순하지만 reload에서 같은 문제가 반복됩니다.
- 브라우저 local storage 사용: URL 공유에는 도움이 되지 않고 Streamlit 공식 API보다 구현 부담이 큽니다.
- DB에 사용자별 마지막 프로젝트 저장: 로그인/사용자 식별 정책이 없는 현재 검증 범위보다 무겁습니다.

### 영향과 tradeoff

- URL에 `project_id`가 노출됩니다. 민감한 값은 아니지만, 사용자는 URL을 공유할 때 특정 프로젝트 컨텍스트도 함께 공유한다는 점을 이해해야 합니다.
- 삭제되거나 잘못된 `project_id`는 자동으로 복구되므로, 공유된 오래된 URL이 항상 같은 프로젝트를 보장하지는 않습니다.
- 프로젝트별 widget key namespacing은 별도 결정으로 분리해 관리합니다.

### 관련 문서

- `ROADMAP.md`의 `Current Project Selection Persistence`
- `docs/feature-guide.md`
- `docs/architecture.md`
- `AI_CHANGELOG.md`의 `현재 프로젝트 선택 유지`

## 2026-06-14 - 프로젝트별 UI 상태는 key namespacing으로 분리한다

### 배경

전역 현재 프로젝트 selector가 생기면서 대부분의 분석 화면은 같은 sidebar 프로젝트를 기준으로 동작합니다. 하지만 Streamlit widget state는 key가 같으면 프로젝트를 바꿔도 남을 수 있습니다. 예를 들어 A 프로젝트에서 선택한 프로그램, 커밋, 리스크 필터, RAG 검색 조건이 B 프로젝트 화면에 그대로 남으면 사용자는 다른 프로젝트 데이터를 보고 있다는 사실을 놓칠 수 있습니다.

반대로 모든 입력값을 프로젝트 전환 때마다 지우면, 사용자가 여러 프로젝트에서 같은 검색어를 비교하거나 같은 분석 조건을 반복 확인하는 흐름까지 끊을 수 있습니다.

### 결정

`src/ui/project_context.py`에 `project_scoped_key(project_id, name)` helper를 두고, 프로젝트 데이터에 직접 묶인 widget state는 이 helper로 key를 만듭니다. Mapping, Program Detail, Commit Impact, Git History, Risk Analysis, AI Progress, RAG 검색/준비/질문 화면의 프로그램·커밋·필터·선택값은 프로젝트별 key를 사용합니다.

### 이유

- 프로젝트 전환 시 stale 프로그램/커밋 선택이 다른 프로젝트 화면에 남아 보이는 문제를 줄입니다.
- `st.session_state` 전체를 지우지 않아 navigation, 현재 프로젝트, 같은 프로젝트 안의 작업 흐름은 유지됩니다.
- helper 이름이 명시적이라 새 프로젝트 단위 화면을 만들 때 어떤 key가 프로젝트 범위인지 판단하기 쉽습니다.
- 프로젝트별 state 분리는 UI 동작 변화라 DB schema나 서비스 계층 변경 없이 위험을 낮출 수 있습니다.

### 검토한 대안

- 프로젝트 전환 때 모든 session state 삭제: stale state는 줄지만 navigation, 임시 입력, 비교 검색 흐름까지 사라집니다.
- 각 화면에서 ad hoc prefix 사용: 빠르게 고칠 수 있지만 key 규칙이 흩어지고 누락을 찾기 어렵습니다.
- 프로젝트별 state를 별도 dict에 저장: 구조는 명확하지만 Streamlit widget key와 별도 동기화가 필요해 구현이 커집니다.

### 영향과 tradeoff

- 같은 검색어를 여러 프로젝트에 그대로 유지하려면 사용자가 다시 입력해야 하는 화면이 있습니다. 혼동 방지를 우선해 Git/RAG/분석 화면의 검색 조건은 프로젝트별로 분리했습니다.
- 프로젝트별 key가 늘어나므로 오래 실행한 session의 state 항목 수는 증가할 수 있습니다. 현재는 lightweight widget 값 중심이라 별도 cleanup은 두지 않습니다.
- 프로젝트 단위 새 화면을 추가할 때는 선택한 프로그램, 커밋, row, 필터가 다른 프로젝트에서 의미를 잃는지 먼저 보고 `project_scoped_key()` 적용 여부를 결정합니다.

### 관련 문서

- `ROADMAP.md`의 `Project-Scoped UI State Namespacing`
- `docs/feature-guide.md`
- `docs/architecture.md`
- `AI_CHANGELOG.md`의 `Project-scoped UI state namespacing`

## 2026-06-14 - 자원관리 추세 분석은 수동 snapshot부터 시작한다

### 배경

AX 자원관리 지표는 현재 DB 상태를 계산해 PL에게 일정 리스크, 업무량, 난이도, AI 리뷰 가치 신호를 제공합니다. 하지만 계산형 지표만으로는 지난 점검 대비 리스크가 줄었는지, workload concentration이 계속 높은지, AI 리뷰 효과가 누적되고 있는지를 설명하기 어렵습니다.

### 결정

첫 추세 분석은 Dashboard에서 사용자가 `현재 지표 저장`을 눌러 `resource_metric_snapshots`에 기준 시점을 남기는 방식으로 구현합니다. Snapshot에는 핵심 KPI 컬럼과 raw summary JSON을 함께 저장하고, Dashboard의 `추세 분석` 탭은 최근 snapshot을 시간순으로 비교합니다.

### 이유

- 검증에서는 주간 점검, 리스크 리뷰, 검증 기준점처럼 사람이 의미 있는 시점을 고르는 흐름이 자동 배치보다 설명하기 쉽습니다.
- 자동 스케줄러, webhook, CI 연동 없이도 추세 분석 가치를 검증할 수 있습니다.
- 핵심 KPI를 컬럼으로 저장하면 차트와 테이블이 단순하고, raw summary를 함께 남기면 산식 검토와 후속 확장 근거를 보존할 수 있습니다.

### 검토한 대안

- 조회할 때마다 자동 저장: 데이터가 빠르게 불어나고 사용자가 의도하지 않은 snapshot이 추세를 흐릴 수 있습니다.
- 백그라운드 일/주간 배치: 운영 배포와 스케줄 실패 처리 정책이 필요해 검증 범위보다 큽니다.
- raw JSON만 저장: 유연하지만 차트와 쿼리, 검증이 불편합니다.

### 영향과 tradeoff

- 추세는 사용자가 저장한 시점 사이에서만 해석할 수 있습니다.
- Snapshot은 산식 변경 이후의 재계산값이 아니라 저장 당시 payload입니다.
- 장기 운영에서는 보관 기간, 자동 저장 주기, 프로젝트별 snapshot 삭제/보존 정책을 별도 결정해야 합니다.

### 관련 문서

- `ROADMAP.md`의 `Resource Metric Snapshot And Trend Dashboard`
- `docs/feature-guide.md`
- `docs/architecture.md`
- `docs/ai-technical-overview.md`
- `docs/db-migrations.md`
- `AI_CHANGELOG.md`의 `자원관리 지표 시계열 snapshot과 추세 분석`

## 2026-06-14 - AI Code Review는 서버 저장소 커밋 이력을 기본 대상으로 둔다

### 배경

AI Code Review 화면은 working tree, staged changes, latest commit, selected commit을 모두 지원합니다. 이 구조는 개발자 개인 PC에서 앱을 직접 실행할 때는 자연스럽지만, 현재 검증 범위와 사내 서버 운영 모델에서는 대상 Git 저장소가 앱 서버에 있습니다. 사용자가 브라우저로 접속하는 구조에서는 앱이 각 개발자 PC의 미커밋 변경이나 staged 변경을 직접 읽을 수 없습니다.

### 결정

AI Code Review의 기본 UX와 문서는 앱 서버 Git 저장소의 최신 커밋과 특정 커밋 리뷰를 중심으로 설명합니다. working tree와 staged changes는 `서버 작업트리 변경`, `서버 Staged 변경`으로 표현하고, 분석용 서버 clone에 local 변경이 남아 있을 때만 쓰는 보조 옵션으로 둡니다.

### 이유

- 중앙 서버 검증에서 실제로 안정적인 리뷰 근거는 Git sync/fetch 이후 확인 가능한 commit 이력입니다.
- 개발자 개인 PC의 작업 상태를 앱 서버가 볼 수 있다고 오해하면 사용 가이드와 데모 흐름이 실제 운영 모델과 어긋납니다.
- 기존 service 기능은 유지하면서 UI와 문서의 기본 경로만 바꾸면 local 실행자와 서버 운영자 모두 필요한 옵션을 사용할 수 있습니다.

### 검토한 대안

- working tree/staged 옵션 제거: 서버 모델에는 단순하지만, 로컬 실행이나 운영자가 서버 clone의 임시 변경을 점검하는 사용성을 잃습니다.
- Git hook, CI, webhook 기반 자동 리뷰를 즉시 추가: 운영 제품에는 자연스럽지만 검증 범위보다 크고, 인증/권한/실패 처리 정책이 먼저 필요합니다.
- 기존 라벨 유지: 기능 구현은 그대로지만 중앙 서버 사용자가 리뷰 대상의 위치를 잘못 이해할 가능성이 큽니다.

### 영향과 tradeoff

- 화면의 대표 흐름은 커밋 이력 기반 리뷰로 단순해집니다.
- 서버 작업트리/staged 옵션은 남아 있지만 고급/보조 옵션으로 해석해야 합니다.
- 개발자별 커밋 전 자동 리뷰가 필요하면 이후 Git hook, CI, GitHub/GitLab webhook 연동을 별도 로드맵으로 검토해야 합니다.

### 관련 문서

- `ROADMAP.md`의 `AI Code Review Server Repository Target Wording`
- `docs/feature-guide.md`
- `docs/demo-user-guide.md`
- `docs/architecture.md`
- `docs/ai-technical-overview.md`
- `AI_CHANGELOG.md`의 `AI Code Review 서버 저장소 대상 설명 정리`

## 2026-06-14 - AX 자원관리 지표는 계산형 foundation부터 시작

### 배경

AX Use Case는 AI 커밋 분석 기반 프로젝트 자원 관리 서비스를 목표로 하며, 개발 진척도, 개발자별 업무량, 진행도, 난이도, AI 코드리뷰, 일정 리스크 사전 방어를 요구합니다. 현재 제품은 Git sync, Mapping, AI Progress, Risk Analysis, 개발자 Git 활동, AI Code Review를 이미 갖고 있지만, 예상 종료 일정과 개발자별 업무 난이도·부하 지표는 별도 공통 산식 없이 화면별 보조 지표로 흩어질 위험이 있었습니다.

### 결정

첫 구현은 DB schema를 늘리지 않고 `resource_metrics_service.py`의 계산형 foundation으로 시작합니다. 이 서비스는 기존 `Program`, `GitCommit`, `CommitFile`, `ProgramCommitMapping`, `RiskFinding`, `CodeReviewResult` 데이터를 조합해 프로그램별 예상 종료일·난이도·업무량 근거, 개발자별 업무량·난이도 집계, 검증 수준의 고객가치 추정 KPI를 계산합니다.

지표는 의사결정 보조 신호로 정의하고, 개인 성과를 확정 평가하는 값이 아니라는 해석 경계를 서비스 결과와 사용자 문서에 함께 남깁니다.

### 이유

- 기존 테이블만으로 AX gap을 줄이는 첫 기능을 빠르게 검증할 수 있습니다.
- 산식과 aggregation boundary를 한 서비스에 모아 후속 Dashboard, Risk Analysis, 예상 종료 일정 기능이 같은 기준을 재사용할 수 있습니다.
- schema snapshot 저장을 미루면 migration과 보관 정책을 확정하기 전에도 UI/문서/테스트에서 지표의 유용성을 검증할 수 있습니다.

### 검토한 대안

- 별도 metric snapshot 테이블을 즉시 추가: 추세 분석에는 좋지만, 지표 산식이 안정되기 전 migration과 보관 정책 부담이 큽니다.
- Dashboard 화면 안에서 직접 계산: 빠르게 보일 수 있지만 산식이 UI에 묶여 테스트와 재사용이 어려워집니다.
- LLM으로 난이도를 바로 판단: 설명력은 높을 수 있으나 비용, 일관성, 재현성이 낮아 검증 기본 지표로 쓰기 어렵습니다.

### 영향과 tradeoff

- 계산형 지표는 현재 DB 상태의 스냅샷이며 과거 추세를 보관하지 않습니다.
- 난이도와 업무량 점수는 변경 파일, diff line, 관련 commit, 리스크 같은 관측 가능한 신호에 기반하므로 실제 업무 난도나 개인 생산성을 완전히 설명하지 않습니다.
- 예상 종료 일정, Risk Analysis의 `FORECAST_DELAY`, 자원관리 Dashboard는 이 서비스를 재사용하되, 지표 산식이 바뀌면 관련 문서와 테스트를 함께 갱신해야 합니다.

### 후속 확인

- 추세 분석이나 기간별 비교가 필요해지면 저장형 metric snapshot이 필요한지 재검토합니다.
- 개발자 대시보드 UI의 지표 라벨이 인사평가처럼 보이지 않는지 계속 점검합니다.

### 관련 문서

- `ROADMAP.md`의 `AX Resource Management Metrics Foundation`
- `docs/architecture.md`
- `docs/feature-guide.md`
- `docs/ai-technical-overview.md`
- `AI_CHANGELOG.md`의 `AX 자원관리 metric foundation`

## 2026-06-14 - AI change log uses Korean by default

### 배경

프로젝트의 사용자 문서는 이미 한국어 우선 정책을 따르고 있지만, `AI_CHANGELOG.md`에는 영문 항목과 한국어 항목이 섞여 있었습니다. changelog는 개발자와 기획자가 변경 흐름과 검증 결과를 같이 확인하는 문서이므로, 설명 문장이 영어로 계속 쌓이면 팀 내 공유성이 떨어질 수 있습니다.

반대로 기존 전체 이력을 한 번에 번역하면 오래된 검증 문구나 commit 맥락이 불필요하게 크게 흔들리고, 실제 기능 변경과 무관한 diff가 과도하게 커집니다.

### 결정

새 `AI_CHANGELOG.md` 항목은 기본적으로 한국어로 작성합니다. 항목 제목, 변경 요약, 주요 파일 설명, 검증 결과 설명을 한국어로 쓰되, 파일 경로, 명령어, 환경 변수, API 이름, model/provider 이름, table/class/function 이름 같은 기술 식별자는 원문을 유지합니다.

기존 영문 이력은 전체 소급 번역하지 않습니다. 다만 사용자가 명시적으로 요청하거나 해당 항목을 다른 이유로 수정하는 경우에는 자연스러운 한국어로 정리합니다.

### 이유

- 변경 의도와 검증 결과를 팀원이 빠르게 읽을 수 있습니다.
- 기술 식별자는 원문을 유지하므로 검색성과 정확성을 해치지 않습니다.
- 과거 이력을 대량 번역하지 않아 불필요한 문서 churn을 줄입니다.

### 검토한 대안

- 기존 `AI_CHANGELOG.md` 전체를 즉시 번역: 일관성은 높지만 실제 변경과 무관한 diff가 커지고 검증 이력 추적이 어려워질 수 있습니다.
- 계속 영어/한국어 혼용 허용: 작성자는 편하지만 문서 품질과 읽는 흐름이 일정하지 않습니다.

### 영향과 tradeoff

- 오래된 changelog에는 영문 항목이 남습니다.
- 새 항목은 한국어가 기본이므로, 영어 제목이 필요한 경우에도 설명 문장은 한국어로 작성합니다.

### 관련 문서

- `AGENTS.md`
- `AI_CHANGELOG.md`의 `AI 변경 이력 한국어 작성 정책`

## 2026-06-14 - Roadmap은 commit hash를 직접 관리하지 않는다

### 배경

완료된 Roadmap 작업의 commit hash를 `ROADMAP.md` 표에 기록하는 정책은 추적성을 높이려는 의도였습니다. 하지만 commit hash는 커밋이 만들어진 뒤에야 알 수 있기 때문에, 실제 작업 커밋 이후 Roadmap hash 칸만 채우는 후속 bookkeeping commit이 필요했습니다. 작업이 많아질수록 빈칸이 생기거나, hash 기록만을 위한 커밋이 늘어나는 관리 비용이 커졌습니다.

### 결정

`ROADMAP.md`의 Priority Overview에서 `Commit` 컬럼을 제거합니다. Roadmap은 작업 우선순위, 상태, 관련 `AI_CHANGELOG.md` heading만 관리하고, commit-level traceability는 Git history에 맡깁니다. 특정 장애, 릴리스, 외부 감사처럼 commit hash 자체가 설명의 핵심인 경우에만 해당 문서 본문에 예외적으로 기록할 수 있습니다.

### 이유

- Git은 이미 commit 추적 시스템이므로 Roadmap이 같은 정보를 수동으로 중복 관리할 필요가 없습니다.
- hash 기록만을 위한 후속 커밋은 문서 이력을 늘리지만 제품이나 설명 품질을 직접 개선하지 않습니다.
- Roadmap은 계획과 상태를 빠르게 읽는 문서일 때 유지보수 비용이 낮습니다.
- `AI_CHANGELOG.md` heading이 있으면 변경 요약과 검증 결과를 찾을 수 있고, 실제 commit은 Git log로 확인할 수 있습니다.

### 검토한 대안

- 기존처럼 `Commit` 컬럼 유지: 표에서 바로 hash를 볼 수 있지만, 커밋 후 별도 업데이트가 필요하고 빈칸이 쉽게 생깁니다.
- `Commit` 컬럼을 optional로 유지: 전환 비용은 낮지만, 어떤 항목은 채워지고 어떤 항목은 비는 애매한 상태가 계속됩니다.
- `AI_CHANGELOG.md`에 hash 기록: changelog가 변경 내용과 검증 결과보다 Git bookkeeping에 가까워질 수 있습니다.

### 영향과 tradeoff

- Roadmap 표에서 commit hash로 바로 점프하는 편의는 사라집니다.
- 대신 Roadmap 업데이트가 작업 완료 시점 안에서 끝나며, 후속 hash 기록 누락 문제가 사라집니다.
- 완료 작업의 정확한 commit이 필요하면 `AI_CHANGELOG.md` heading이나 작업명을 기준으로 Git log를 검색합니다.

### 관련 문서

- `ROADMAP.md` Management Rules
- `AGENTS.md` Roadmap instructions
- `AI_CHANGELOG.md`의 `Roadmap commit hash tracking cleanup`
- Supersedes `2026-06-14 - Roadmap owns commit hash tracking`

## 2026-06-14 - Roadmap owns commit hash tracking (Superseded)

### 배경

로드맵 작업은 `ROADMAP.md`, `AI_CHANGELOG.md`, commit history가 함께 움직입니다. `AI_CHANGELOG.md`에도 commit hash를 넣고 `ROADMAP.md`에도 같은 hash를 넣으면 추적 지점이 중복되고, amend/rebase/squash 같은 Git 정리 후 문서를 여러 곳에서 다시 맞춰야 합니다.

이 결정은 같은 날 `Roadmap은 commit hash를 직접 관리하지 않는다` 결정으로 대체되었습니다. 아래 내용은 이전 정책의 배경을 보존하기 위한 기록입니다.

### 당시 결정

완료된 로드맵 작업의 commit hash는 `ROADMAP.md`의 `Commit` 컬럼에 기록합니다. `AI_CHANGELOG.md`는 변경 요약, 주요 파일, 검증 명령과 결과를 기록하고, commit hash는 기본적으로 넣지 않습니다.

### 이유

- `ROADMAP.md`는 작업 상태와 완료 commit을 한 표에서 추적하기에 적합합니다.
- `AI_CHANGELOG.md`는 코드와 문서가 어떻게 바뀌었는지, 무엇으로 검증했는지에 집중하는 편이 읽기 쉽습니다.
- commit hash 중복 기록을 줄이면 후속 amend/rebase/squash 이후 문서 불일치 가능성이 줄어듭니다.

### 검토한 대안

- `AI_CHANGELOG.md`와 `ROADMAP.md`에 모두 commit hash 기록: 추적성은 높지만 중복 관리 비용이 큽니다.
- commit hash를 어디에도 기록하지 않음: changelog와 Git log를 직접 대조해야 하므로 완료된 로드맵 작업 추적성이 떨어집니다.

### 영향과 tradeoff

- 로드맵에 없는 작은 변경은 commit hash 문서 연결이 없을 수 있습니다.
- 특정 장애, 릴리스, 외부 감사처럼 commit hash 자체가 설명에 필요한 경우에는 해당 문서에 예외적으로 남길 수 있습니다.

### 관련 문서

- `ROADMAP.md` Management Rules
- `AI_CHANGELOG.md`의 `로드맵 커밋 해시 기록 정책`

## 2026-06-10 - App-server Git repository operating model (Superseded)

> Superseded: 앱 서버 기준 Git 저장소 모델 자체는 유지되지만, "앱이 remote URL 기반 clone/fetch를 관리하지 않는다"는 범위 제한은 `2026-06-14 - 서버 저장소 clone/fetch는 인증정보 저장 없이 지원한다` 결정으로 대체되었습니다.

### 배경

프로젝트/Git 설정과 Git Sync, RAG source indexing, Project Chat, AI Code Review는 모두 Git 저장소의 실제 파일과 `git` 명령에 의존합니다. 기존 문구는 `로컬 Git 저장소`라고 표현되어 개인 PC 실행에는 자연스러웠지만, 사내 서버에서 앱을 실행하고 여러 사용자가 브라우저로 접속하는 운영 모델에서는 오해를 만들 수 있었습니다.

브라우저 사용자의 PC 경로는 앱 서버가 직접 읽을 수 없습니다. 반면 사내 서버에 clone된 저장소는 앱 서버 프로세스가 접근할 수 있으므로 Git 분석 기능이 정상 동작합니다.

### 결정

제품의 공식 Git 접근 모델을 "앱 서버에서 접근 가능한 Git 저장소"로 정의합니다.

`projects.git_repo_path` 컬럼명은 호환성을 위해 유지하되, 사용자-facing 문구와 문서는 앱 서버 기준 경로로 설명합니다. 운영 서버에서는 `REPO_STORAGE_ROOT`를 설정해 프로젝트 Git 경로를 승인된 저장소 root 하위로 제한할 수 있게 합니다.

초기 사내 운영 정책은 앱이 Git remote URL, access token, SSH key를 받아 clone/fetch까지 관리하지 않는 것이었습니다. 운영자나 배포/운영 스크립트가 앱 서버의 저장소 root 아래에 repo를 준비하고 갱신하며, AI Commit Advisor는 준비된 경로를 검증하고 Git Sync로 commit/diff를 DB에 수집했습니다. 현재는 앱이 인증정보를 저장하지 않는 조건으로 `git_remote_url`과 branch 기반 clone/fetch/reset을 지원합니다.

### 이유

- 개인 PC 실행과 사내 서버 실행을 같은 모델로 설명할 수 있습니다. 둘 다 앱 서버가 접근 가능한 경로를 읽는 구조입니다.
- Git Sync, RAG, Project Chat, Code Review가 공유하는 핵심 전제를 문서와 UI에서 일관되게 표현할 수 있습니다.
- 사내 서버에서는 `/srv/ai-commit-advisor/repos` 같은 저장소 root를 정하고 여러 사용자가 같은 분석 결과를 공유할 수 있습니다.
- `REPO_STORAGE_ROOT`는 운영 서버에서 임의 서버 경로 입력을 줄이는 최소 안전장치입니다.
- Git 인증 정보, SSH key, access token, branch 보호, 동시 fetch lock, 저장소 용량 관리를 분석 앱의 1차 책임에 섞지 않아 보안 검토 범위를 줄입니다.

### 검토한 대안

- 사용자 PC 로컬 경로 모델 유지: 사내 서버 운영에서 사용자가 입력한 PC 경로를 서버가 읽을 수 없으므로 제품 설명이 틀려집니다.
- 즉시 remote URL 기반 clone/fetch 모델로 전환: 당시에는 인증 정보, branch 정책, sync lock, 저장소 용량 관리까지 함께 설계해야 하므로 범위가 크다고 판단했습니다. 이후 `2026-06-14 - 서버 저장소 clone/fetch는 인증정보 저장 없이 지원한다`에서 인증정보 비저장, 경로 제한, repository lock, dirty working tree guard를 포함한 제한된 형태로 채택했습니다.
- 앱에 단순 `git pull` 버튼만 추가: 구현은 쉬워 보이지만 merge/rebase 동작, 충돌, 권한 실패, 장기 실행 lock 처리가 모호해 운영 장애를 만들 수 있습니다.
- DB schema를 바로 변경해 `server_repo_path`로 rename: 의미는 더 정확하지만 migration과 전체 코드 변경량이 커집니다. 현재는 문구와 검증 정책을 먼저 정리하고, schema rename은 필요성이 커질 때 별도 작업으로 다룹니다.

### 영향과 tradeoff

- README, feature guide, setup/operations, architecture 문서가 앱 서버 기준 Git 저장소 모델을 설명해야 합니다.
- 화면 라벨은 더 정확해지지만 `git_repo_path` 내부 이름과 일부 과거 문서에는 이전 용어가 남을 수 있습니다.
- `REPO_STORAGE_ROOT`를 설정하지 않으면 기존 검증처럼 자유 경로를 사용할 수 있습니다. 이 유연성은 개발에는 편하지만 운영 서버에서는 반드시 제한값을 설정해야 합니다.
- 저장소 최신화는 당시 운영자나 외부 스크립트 책임이었습니다. 현재는 pre-cloned 운영과 앱의 제한적 clone/fetch/reset 운영을 함께 지원합니다.

### 후속 확인

- Git History 화면을 추가할 때도 서버 repo path를 기준으로 `git show`와 `git log`를 실행해야 합니다.
- 서버가 remote URL과 branch를 받아 clone/fetch를 관리하는 기능은 `2026-06-14 - 서버 저장소 clone/fetch는 인증정보 저장 없이 지원한다` 결정과 `Server-managed clone/fetch workflow`로 구현되었습니다.
- 운영 스크립트와 pre-cloned 방식은 앱 내 clone/fetch를 쓰지 않는 배포에서 계속 사용할 수 있습니다.
- 인증/권한 관리가 없으므로 내부망 운영에서도 reverse proxy 인증이나 사내 SSO를 검토해야 합니다.

### 관련 문서

- `docs/git-repository-operating-model.md`
- `docs/server-repository-update-runbook.md`
- `docs/setup-and-operations.md`
- `docs/architecture.md`
- `README.md`
- `AI_CHANGELOG.md`의 `App-server Git repository operating model`
- `AI_CHANGELOG.md`의 `Server-managed clone/fetch workflow`

## 2026-06-14 - Project developer membership keeps the global master compatible

### 배경

프로젝트 삭제 기능 이후에도 `developers`가 전역 마스터로 남기 때문에, 개발자 목록 화면을 현재 프로젝트 기준으로 보여주려면 별도 연결 기준이 필요했습니다. 단순히 `developers.project_id`를 추가하면 같은 개발자가 여러 프로젝트에 참여하는 경우를 표현하기 어렵고, 기존 `programs.developer_id` FK와 Excel 업로드 흐름까지 한 번에 바꿔야 합니다.

반대로 전역 마스터만 계속 보여주면 반복 검증이나 여러 프로젝트 운영에서 현재 프로젝트와 무관한 개발자가 섞여 보여 사용자가 데이터를 잘못 이해할 수 있습니다.

### 결정

`developers`는 전역 개발자 마스터로 유지하고, `project_developers` 연결 테이블을 추가합니다. 현재 프로젝트 개발자 목록은 이 연결 테이블을 기준으로 조회합니다.

Git author 자동 추출, 직접 추가, Excel 업로드는 먼저 전역 `developers` row를 생성하거나 업데이트한 뒤, 현재 프로젝트가 있으면 `project_developers` 연결을 생성합니다. 같은 프로젝트에서 반복 실행해도 `(project_id, developer_id)` unique constraint로 중복 연결을 만들지 않습니다.

v1에서는 `programs.developer_id` FK를 그대로 유지합니다. 개발자 role/skills도 기존 `developers` 값을 계속 표시하고 수정하며, 프로젝트별 role 편집은 후속 범위로 둡니다.

### 이유

- 기존 프로그램 담당자 연결과 Excel 업로드 호환성을 보존합니다.
- 같은 개발자가 여러 프로젝트에 등장하는 운영 모델을 지원합니다.
- 현재 프로젝트 화면에서는 불필요한 전역 개발자가 섞이지 않아 검증과 실사용 흐름이 명확해집니다.
- 연결 테이블만 프로젝트 삭제 cascade 대상이므로, 프로젝트를 삭제해도 전역 개발자 마스터는 유지됩니다.

### 검토한 대안

- `developers.project_id` 추가: 단순하지만 multi-project developer 표현과 기존 unique/FK 정책 변경 부담이 큽니다.
- `programs.developer_id`를 프로젝트별 FK로 변경: 장기적으로 검토할 수 있지만 기존 산출물 업로드와 분석 서비스의 회귀 위험이 큽니다.
- 화면에서만 Git author나 프로그램 담당자 기준으로 필터링: schema가 없어서 직접 추가/Excel/Git author 흐름의 연결 상태를 일관되게 저장하기 어렵습니다.

### 영향과 tradeoff

- 프로젝트별 연결 상태는 명확해졌지만, v1의 삭제 버튼은 여전히 전역 개발자 삭제입니다. 현재 프로젝트에서만 연결 해제하는 기능은 별도 후속 작업입니다.
- `project_role`은 저장 컬럼으로 준비했지만, v1 UI는 기존 `developers.role/skills`를 그대로 편집합니다.
- migration은 기존 `programs.developer_id`를 기준으로 연결을 백필합니다. 담당 프로그램이 없던 기존 전역 개발자는 Git author 추출, 직접 추가, Excel 업로드를 다시 수행해야 특정 프로젝트에 연결됩니다.

### 관련 문서

- `ROADMAP.md`의 `Project Developer Membership Model`
- `docs/architecture.md`
- `docs/feature-guide.md`
- `docs/db-migrations.md`
- `AI_CHANGELOG.md`의 `Project developer membership model`

## 2026-06-14 - Project deletion keeps global developer master

### 배경

샘플 프로젝트 검증 가이드를 반복 수행하려면 기존 샘플 프로젝트를 깨끗하게 지울 수 있어야 합니다. 전체 DB volume을 삭제하면 다른 프로젝트와 분석 결과까지 사라지므로 사내 공유 DB나 장기 검증 환경에는 맞지 않습니다.

동시에 현재 `developers` 테이블은 프로젝트별 데이터가 아니라 전역 개발자 마스터입니다. `programs.developer_id`가 전역 `developers.developer_id`를 참조하고, `개발자 목록` 화면도 프로젝트 필터 없이 전체 개발자를 관리합니다. 따라서 프로젝트 삭제가 개발자 row까지 지우면 다른 프로젝트의 담당자 연결이나 개발자 관리 데이터에 영향을 줄 수 있습니다.

### 결정

프로젝트 삭제 기능은 프로젝트 소유 데이터만 삭제합니다. 프로그램, Git commit, 변경 파일, 매핑, 분석 실행 이력, 구현상태 분석, 리스크, RAG chunk/vector, Project Chat, AI Code Review, 표준용어/표준단어는 삭제 대상입니다.

전역 `developers` row는 프로젝트 삭제 시 자동 삭제하지 않습니다. 프로젝트별 개발자 범위가 필요하면 `developers`에 `project_id`를 직접 추가하지 않고, 후속 작업에서 `project_developers` membership table을 도입해 점진적으로 연결합니다.

### 이유

- 반복 검증에는 프로젝트 단위 삭제만으로 충분하며, 전체 DB 초기화보다 안전합니다.
- 기존 개발자 Excel 업로드, Git author 추출, 프로그램 담당자 연결을 깨지 않습니다.
- 전역 개발자 마스터를 유지하면 여러 프로젝트에 같은 개발자가 등장하는 운영 모델을 보존할 수 있습니다.
- project-scoped developer UX는 별도 schema migration과 화면 정책이 필요한 작업이므로 삭제 기능과 분리하는 편이 회귀 위험이 작습니다.

### 검토한 대안

- 전체 DB 초기화 버튼: 검증 환경에서는 빠르지만 공유 DB에서 위험하고, 운영 기능으로 노출하기 어렵습니다.
- 프로젝트 삭제 시 개발자도 삭제: 샘플 정리는 편하지만 현재 전역 developer model과 충돌합니다.
- `developers.project_id`를 즉시 추가: 직관적이지만 unique constraint, Excel 업로드, 프로그램 담당자 FK, 기존 데이터 migration을 한 번에 바꿔야 합니다.
- 프로젝트 reset 기능부터 구현: 프로젝트명과 경로를 유지할 수 있지만 산출물/분석 결과 중 무엇을 남길지 정책 결정이 더 필요합니다.

### 영향과 tradeoff

- 샘플 프로젝트를 삭제해도 개발자 목록에는 샘플 개발자가 남을 수 있습니다.
- 이 동작은 현재 데이터 모델을 보존하는 의도된 제한입니다.
- 완전히 프로젝트별 개발자 목록을 원하면 후속 `project_developers` membership 작업이 필요합니다.

### 후속 확인

- 프로젝트 삭제 후 현재 프로젝트 선택이 삭제된 ID를 계속 가리키지 않아야 합니다.
- 삭제 영향 건수와 실제 삭제 결과가 일치하는지 테스트로 검증합니다.
- 프로젝트 reset action은 삭제 flow가 안정화된 뒤 별도 후보 작업으로 다룹니다.

### 관련 문서

- `ROADMAP.md`의 `Project delete and demo reset safety`
- `docs/feature-guide.md`
- `docs/demo-user-guide.md`
- `docs/architecture.md`
- `AI_CHANGELOG.md`의 `Project delete and demo reset safety`

## 2026-06-10 - Roadmap candidate tasks preserve unresolved product concerns

### 배경

전역 프로젝트 컨텍스트와 Home 현재 프로젝트 중심 개선 이후, 바로 구현하지는 않지만 잊으면 안 되는 UX 고민이 남았습니다. 예를 들어 프로젝트별 UI 상태 key 정리, 프로그램 관리의 프로젝트 저장 흐름, 개발자 목록의 전역/프로젝트별 범위 결정은 모두 제품 방향과 유지보수성에 영향을 줄 수 있습니다.

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
- `프로그램 목록`은 사이드바 현재 프로젝트를 기준으로만 조회, 직접 추가, Excel 업로드를 수행합니다. 새 프로젝트 생성은 `프로젝트/Git 설정`에서 처리합니다.

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
- 전역 선택이 없는 상태에서는 프로그램 목록이 저장 UI를 열지 않고, 프로젝트/Git 설정에서 프로젝트를 먼저 등록하도록 안내합니다.
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
- README 최상단 대표 screenshot은 Application Preview Home과 같은 `docs/images/features/home.png`를 사용합니다. 캐시 회피를 위해 별도 versioned 대표 이미지 파일을 만들면 source of truth가 갈라지므로 사용하지 않습니다.

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

# Failure History

이 문서는 프로젝트 전반에서 발생한 실패, 시행착오, 운영상 누락, 검증 누락 중 재발 방지 가치가 있는 사례를 기록합니다. 범위는 CI에 한정하지 않습니다. 기능 설계, UX, 데이터, schema, RAG/LLM, embedding, sample data, 문서, 배포, local 검증, GitHub Actions, 운영 절차에서 배운 내용을 남깁니다.

실패나 incident가 아닌 설계, 운영, 검증, 자동화, 문서 구조 결정은 [Engineering Decisions](engineering-decisions.md)에 기록합니다. 실패 이력이 더 넓은 운영 기준으로 이어질 때는 두 문서를 서로 연결합니다.

단순한 일시적 네트워크 실패, 사용자가 즉시 취소한 run, 방향을 바꾸지 않은 read-only 조사, 재현 불가능하고 조치가 없는 현상은 기록하지 않습니다.

## 기록 기준

다음 중 하나에 해당하면 이 문서에 항목을 추가합니다.

- 기능 설계나 구현이 실제 사용 시나리오를 충분히 반영하지 못했습니다.
- local에서는 통과했지만 CI, 다른 PC, demo, 운영 환경에서는 실패했습니다.
- 테스트, schema, migration, dependency, workflow, 환경 변수, 외부 service, sample data 전제가 누락됐습니다.
- LLM/RAG/embedding 동작이 stale evidence, 비용, hallucination, 검증 불가 근거 같은 안전 문제를 만들었습니다.
- 사용자 문서만 보고는 기능 목적, 사용 조건, 복구 방법, 한계를 이해하기 어려웠습니다.
- 실패를 해결하기 위해 코드, 테스트, workflow, 문서, agent policy, 운영 절차를 변경했습니다.
- 같은 종류의 실수를 피하기 위한 명확한 예방 규칙이 생겼습니다.

각 항목은 가능한 한 다음 정보를 포함합니다.

- 날짜
- 관련 기능, 문서, run/job URL, commit
- 증상
- 직접 원인
- 배경 또는 구조적 원인
- 왜 사전 검증에서 놓쳤는지
- 수정 내용
- 재발 방지 규칙
- 남은 한계 또는 후속 확인 사항
- 검증 명령과 결과

## 2026-06-17 - Application Preview Project Chat 질문은 같은 질문 재실행으로 검증해야 한다

분류:

- Project Chat/RAG replay failure
- Application Preview verification gap
- Local LLM prompt/context limit finding

관련 기능 및 문서:

- `src/rag/chat_service.py`
- `src/services/llm_client.py`
- `scripts/capture_feature_screenshot.py`
- `docs/images/usage-verification/project-chat-repro-2026-06-17.png`
- `docs/images/usage-verification/project-chat-graph-repro-2026-06-17.png`
- `AI_CHANGELOG.md` 항목 `Project Chat preview 질문 재현 안정화`

### 증상

Application Preview에 올린 Project Chat 화면은 `PaymentService`와 `OrderMapper`의 관계를 잘 보여줬지만, 같은 한국어 질문을 다시 실행하면 `현재 검증된 소스 근거만으로는 답변하기 어렵습니다.`가 반환될 수 있었습니다. 근거 수를 늘려 다시 시도하면 LM Studio의 `qwen2.5-coder-7b-instruct` 4096 token context를 넘을 가능성도 있었습니다.

### 직접 원인

Project Chat prompt가 verified source가 있는 경우에도 정확한 insufficient-evidence 문구를 instruction 안에 그대로 포함해 local LLM이 그 문구를 과하게 따를 수 있었습니다. 또한 질문의 `PaymentService와`, `OrderMapper는` 같은 한국어 조사 결합 identifier가 source chunk 우선순위에서 충분히 강하게 작동하지 않아, 관계 질문에 필요한 named file 근거가 prompt 앞쪽에 안정적으로 들어가지 않았습니다.

`LLMClient` system prompt는 모든 응답에 JSON만 강제하는 문구를 사용하고 있었고, Project Chat은 자연어 Markdown 답변을 기대했습니다. 작은 context local LLM에서는 source, history, graph evidence를 모두 많이 넣으면 답변 품질 문제가 아니라 context overflow 문제가 먼저 생길 수 있었습니다.

### 배경 또는 구조적 원인

이전 screenshot 검증은 저장된 chat session을 화면에서 다시 여는 데 집중했습니다. 이 방식은 provider/model/fallback metadata와 화면 표시는 확인하지만, 사용자가 같은 질문을 다시 눌렀을 때 LLM/RAG pipeline이 같은 수준으로 답하는지는 별도로 보장하지 않습니다. Application Preview는 제품 가치 증거 역할을 하므로, 저장 결과 확인과 같은 질문 재실행 검증을 분리해서 봐야 합니다.

### 사전 검증에서 놓친 이유

Capture script는 화면에 기대 문자열이 보이는지 확인했지만, screenshot에 쓰인 질문을 새로 실행해 답변 내용을 비교하는 replay 검증은 없었습니다. 테스트도 source verification과 citation 위주였고, 한국어 조사 결합 identifier가 실제 prompt source ordering과 named relationship answer에 어떤 영향을 주는지 검증하지 않았습니다.

### 수정 내용

- 질문에서 code identifier를 추출할 때 한국어 조사가 붙은 입력을 처리하고, 질문 identifier와 일치하는 `source_file` chunk를 verified source에 추가했습니다.
- verified source를 prompt에 넣기 전에 질문 identifier가 포함된 파일과 chunk를 우선 정렬했습니다.
- named identifier focus block을 만들어 import line, method call, graph `class_import` 관계가 LLM context 앞쪽에 들어가게 했습니다.
- verified source가 있을 때 prompt가 insufficient-evidence 답변을 그대로 유도하지 않도록 바꾸고, 확인 가능한 부분은 답변하되 부족한 세부사항만 제한적으로 말하도록 했습니다.
- 작은 local LLM context를 고려해 LLM prompt의 source/history/graph evidence 수를 제한했습니다.
- Project Chat 답변 정규화에서 Markdown fence를 제거하고, `LLMClient` system prompt가 JSON만 강제하지 않고 사용자 요청 형식을 따르도록 바꿨습니다.
- screenshot capture가 Streamlit sidebar 로딩을 기다리게 했습니다.

### 재발 방지 규칙

- Application Preview에 AI 답변 screenshot을 갱신하거나 보존할 때는 저장된 화면 캡처만 확인하지 말고, 같은 질문을 실제 provider로 다시 실행해 `fallback=False`, `insufficient=False`, 핵심 답변 token, source file, graph evidence를 함께 확인합니다.
- Project Chat 관계 질문은 질문에 등장한 class/file/method identifier가 prompt source ordering에 반영되는지 테스트로 고정합니다.
- local LLM 검증에서는 답변 품질 문제와 context overflow 문제를 분리해서 기록하고, `TOP K`, graph evidence, history context 포함 여부를 남깁니다.
- screenshot capture는 의미 있는 workflow state를 보여주되, `Mock answer`, `fallback=True`, `Traceback` 같은 금지 조건을 함께 둡니다.

### 남은 한계 또는 후속 확인 사항

Local LLM 답변 문장 자체는 모델 상태와 sampling에 따라 달라질 수 있습니다. 재현 기준은 동일 문장 복제가 아니라 실제 provider가 verified source와 graph evidence를 사용해 같은 핵심 사실, 즉 `PaymentService`가 `OrderMapper`를 import하고 `updateOrderStatus(orderId, "PAID")`로 주문 상태를 갱신한다는 내용을 답하는지입니다.

### 검증 명령과 결과

```powershell
.\.venv\Scripts\python.exe -m py_compile src\rag\chat_service.py src\services\llm_client.py tests\test_project_chat_service.py tests\test_project_chat_answer_format.py
.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_service.py tests\test_project_chat_answer_format.py -q
```

결과: focused test 13개 통과.

실제 local LLM 재실행 결과:

- `chat_session=353`
- `provider=local_openai`
- `model=qwen2.5-coder-7b-instruct`
- `fallback=False`
- `insufficient=False`
- `used_sources=12`
- `graph_evidence=8`
- 첫 graph evidence: `class_import PaymentService -> OrderMapper`
- 답변 핵심 token: `updateOrderStatus`, `PAID`, `PaymentService.java`, `OrderMapper.java`

Screenshot capture:

```powershell
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url "http://localhost:8520/?project_id=97" --feature project-chat-answer --screenshot docs\images\usage-verification\project-chat-repro-2026-06-17.png --surface local --height 1500 --expect-text "Provider: local_openai" --expect-text "fallback=False" --expect-text "updateOrderStatus" --expect-text "PAID" --expect-text "PaymentService.java" --expect-text "OrderMapper.java" --forbid-text "Mock answer" --forbid-text "fallback=True" --forbid-text "StreamlitAPIException" --forbid-text "Traceback"
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url "http://localhost:8520/?project_id=97" --feature project-chat-graph-evidence --screenshot docs\images\usage-verification\project-chat-graph-repro-2026-06-17.png --surface local --height 1500 --expect-text "Provider: local_openai" --expect-text "fallback=False" --expect-text "PaymentService" --expect-text "OrderMapper" --expect-text "class_import" --expect-text "updateOrderStatus" --forbid-text "Mock answer" --forbid-text "fallback=True" --forbid-text "StreamlitAPIException" --forbid-text "Traceback"
```

결과: 두 screenshot capture 모두 통과.

## 2026-06-17 - 샘플 Project Chat 검증은 source_file 인덱스와 context budget을 먼저 확인해야 한다

분류:

- Sample verification procedure
- RAG/source indexing workflow gap
- Local LLM context limit finding

관련 기능 및 문서:

- `src/rag/source_index_service.py`
- `src/rag/chunker.py`
- `src/rag/chat_service.py`
- revert된 commit `103577a Harden final sample operations evidence`
- revert commit `171ca89 Revert "Harden final sample operations evidence"`

### 증상

샘플 프로젝트를 처음부터 다시 분석하는 과정에서 Project Chat이 `현재 검증된 소스 근거만으로는 답변하기 어렵습니다.`를 반환했습니다. 이후 더 많은 근거를 넣어 다시 시도했을 때는 local LLM이 context overflow를 반환할 수 있다는 점도 확인했습니다.

### 직접 원인

`build_project_chunks()` 기본값만 실행하면 `commit`, `commit_file`, `program` chunk는 생성되지만 `source_file` chunk는 생성되지 않습니다. Project Chat은 현재 코드 사실을 답할 때 verified `source_file` 근거를 요구하므로, Git Sync 후 `refresh_source_file_index()`를 실행하지 않으면 RAG 준비가 끝난 것처럼 보여도 현재 소스 답변은 실패합니다.

또한 LM Studio에서 `qwen2.5-coder-7b-instruct`가 4096 token context로 실행되는 경우, `TOP K=8`, graph evidence, history context가 함께 들어가면 prompt가 context limit을 넘을 수 있습니다.

### 배경 또는 구조적 원인

Project Chat의 안전 모델은 현재 코드 답변을 verified `source_file`에 묶어 둡니다. 이 설계는 맞지만, 샘플 검증 절차가 `source_file` 인덱싱을 명시하지 않으면 commit/history chunk만 있는 상태를 실제 답변 준비 완료로 오해할 수 있습니다. 또한 샘플 데모 검증에서는 근거를 많이 넣을수록 좋아 보이지만, 작은 local LLM context에서는 근거 수가 많을수록 실패 가능성이 커집니다.

### 사전 검증에서 놓친 이유

이전 검증은 이미 `source_file` index가 존재하는 프로젝트 상태에서 수행되어 누락 단계를 드러내지 못했습니다. 또한 provider/model/fallback 여부는 확인했지만, prompt context budget과 `TOP K` 조합은 별도 검증 기준으로 두지 않았습니다.

### 재발 방지 규칙

- 샘플 프로젝트를 처음부터 다시 검증할 때는 Git Sync 뒤 `refresh_source_file_index()`를 먼저 실행하고 `source_file` chunk/vector 수를 기록합니다.
- Project Chat 검증 결과는 `fallback=False`, `insufficient_evidence=False`, provider/model, used source count와 함께 기록합니다.
- 4096 token local LLM 환경에서는 Project Chat 검증 시 `TOP K`, graph evidence, history context 포함 여부를 명시합니다.
- context overflow가 발생하면 샘플 데이터 품질 문제로 단정하지 말고, source_file 근거 수와 prompt 크기를 먼저 줄여 재검증합니다.
- 샘플 검증 수치는 실제 source-only 재설계 검증의 비교 기준으로만 사용하고, Markdown 산출물 보강 결과를 최종 샘플 품질 증거로 되살리지 않습니다.

### 검증 명령과 결과

되돌려진 `103577a`에서 확인한 참고 수치:

- Git Sync: 48 commits / 110 files
- `source_file` chunks: 88
- total chunks/vectors: 291 / 291
- Mapping: 80건, 실패 0건
- Risk Analysis: 21건
- Neo4j: 192 nodes / 558 edges
- AI Code Review: 2개 commit, 각 bug finding 1건

이 수치는 Markdown 산출물 보강이 포함된 잘못된 샘플 위에서 나온 결과이므로 최종 데모 증거로 사용하지 않습니다. 향후 소스코드 중심 재설계 검증의 절차와 비교 기준으로만 참고합니다.

## 2026-06-17 - 샘플 프로젝트 내부 Markdown 정답지로 AI 결과를 유도하면 안 된다

분류:

- Sample data design failure
- Agent workflow correction
- AI verification trust boundary

관련 기능 및 문서:

- `scripts/create_sample_target_repo.py`
- `docs/sample-target-repo-demo-design.md`
- `docs/sample-project-test-playbook.md`
- `ROADMAP.md`의 `P2 - Source-First Sample Project And Demo Verification Guide`
- revert된 commit `103577a Harden final sample operations evidence`

### 증상

샘플 프로젝트 보강 과정에서 AI Code Review, Project Chat, Risk/AI Progress가 풍부한 결과를 내도록 하겠다는 목적을 샘플 프로젝트 내부 Markdown 설명 파일 보강으로 잘못 해석했습니다. 사용자는 샘플 프로젝트 소스코드 자체가 기능 검증에 충분한 판단 재료를 제공해야 한다는 의도였고, Markdown 정답지나 demo guide를 샘플 repo에 넣는 방식은 결과를 유도하는 것처럼 보일 수 있었습니다.

### 직접 원인

샘플 repo 내부에 `docs/review-targets`, `docs/business-rules`, `docs/release-evidence`, `docs/demo-guide` 같은 설명 파일을 생성하고, 테스트도 이 Markdown 파일 존재를 핵심 evidence로 기대했습니다.

### 배경 또는 구조적 원인

샘플 데이터의 목적을 "LLM이 읽을 재료를 풍부하게 한다"로만 두고, 그 재료가 source/diff/test/XML/Excel인지, 별도 설명 문서인지 경계를 충분히 세우지 않았습니다. 또한 이미 실제 local LLM으로 검증된 `Application Preview` screenshot이 있는 상태에서 샘플 재생성과 preview 갱신을 분리하지 않으면 좋은 증거 화면을 깨뜨릴 위험이 있었습니다.

### 사전 검증에서 놓친 이유

테스트가 Markdown 파일 존재와 특정 문구를 검증했기 때문에, source-only 관점에서는 잘못된 방향임에도 자동 검증이 통과할 수 있었습니다. 사용자 의도 확인 없이 샘플 내부 산출물처럼 보이는 파일을 늘린 것도 문제였습니다.

### 수정 내용

샘플 생성 스크립트에서 `docs/...` evidence 파일을 제거하고 Java source, MyBatis XML, test/probe class, Excel 표준용어 데이터로 대체했습니다. 기능별 질문과 리뷰 대상 가이드는 샘플 repo 내부가 아니라 애플리케이션 저장소의 `docs/sample-project-test-playbook.md`에 두었습니다. 기존 `Application Preview` screenshot은 덮어쓰지 않고, 새 샘플은 `C:\dev\ai-advisor-sample-shop-source-demo` 별도 경로에서 먼저 생성 검증했습니다.

### 재발 방지 규칙

- 샘플 프로젝트 내부에는 AI 답변을 고정하는 Markdown 정답지, review target 문서, demo guide를 넣지 않습니다.
- 샘플 기능 가이드는 애플리케이션 저장소 `docs/`에 둡니다.
- source-first sample generation test는 생성된 commit file path에 `docs/`가 없는지 확인합니다.
- `Application Preview` AI 결과 screenshot은 실제 local LLM/embedding/Neo4j 검증이 통과하기 전까지 덮어쓰지 않습니다.

### 남은 한계 또는 후속 확인 사항

이번 변경은 별도 target path에서 샘플 생성과 구조를 검증했습니다. 기본 샘플 경로와 프로젝트 97의 실제 local LLM/embedding/Neo4j 재분석, screenshot 재캡처는 기존 preview를 훼손하지 않도록 별도 단계에서 수행해야 합니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -m py_compile scripts\create_sample_target_repo.py tests\test_sample_data_generation.py` 통과.
- `.\.venv\Scripts\python.exe -m pytest tests\test_sample_data_generation.py -q` 결과 14개 통과.
- `.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py --target-path C:\dev\ai-advisor-sample-shop-source-demo --force` 성공.
- `git -C C:\dev\ai-advisor-sample-shop-source-demo rev-list --count HEAD` 결과 48.
- `git -C C:\dev\ai-advisor-sample-shop-source-demo log -1 --format="%h %ad %s" --date=short` 결과 최신 날짜 2026-06-14.
- `git -C C:\dev\ai-advisor-sample-shop-source-demo ls-files docs` 결과 없음.

## 2026-06-17 - 한국어 조사 때문에 GraphRAG class seed가 빗나갔다

분류:

- GraphRAG retrieval quality failure
- Korean query normalization gap
- Screenshot verification finding

관련 기능 및 문서:

- `src/services/neo4j_graph_service.py`
- `src/ui/project_chat_page.py`
- `scripts/capture_feature_screenshot.py`
- `tests/test_neo4j_graph_service.py`
- `docs/ai-technical-overview.md`
- `AI_CHANGELOG.md`의 `Korean Project Chat class relationship evidence screenshot`
- commit `ebe48cd show korean graphrag class evidence`

### 증상

한국어 질문 `PaymentService와 OrderMapper는 어떤 클래스 import 관계로 연결돼 있고...`로 실제 local LLM Project Chat을 실행했지만, GraphRAG 관계도는 처음에 `PaymentService -> OrderMapper` class import 관계보다 `OrderStatusService`, `OrderStatusMapper`, 주문 상태 변경 impact path를 더 앞에 보여줬습니다. 질문은 class import 관계를 묻고 있었지만, 화면에서 가장 먼저 읽히는 graph evidence가 질문 의도와 어긋났습니다.

### 직접 원인

GraphRAG seed 추출이 코드 식별자 뒤에 붙은 한국어 조사를 제거하지 않았습니다. 질문에서 `PaymentService와`, `OrderMapper는`이 그대로 seed 후보가 되었고, Neo4j label인 `PaymentService`, `OrderMapper`와 정확히 매칭되지 않았습니다. 대신 `주문`, `상태`, `order`, `status` 같은 일반 seed가 강하게 작동해 주문 상태 관련 graph path가 앞에 배치되었습니다.

### 배경 또는 구조적 원인

기존 GraphRAG seed 추출은 file path, package/class name, expanded query, 영문 identifier token에는 비교적 강했지만, 한국어 문장 안에 code identifier가 자연스럽게 섞이고 바로 뒤에 조사가 붙는 SI/업무 질문 형태를 충분히 반영하지 못했습니다. 또한 evidence 선택은 `impact_path`가 많은 경우 한 evidence type이 화면을 독점할 수 있어, class import 관계가 있어도 compact graph에서 뒤로 밀릴 수 있었습니다.

### 사전 검증에서 놓친 이유

기존 테스트는 `payment service order mapper` 같은 영문 확장 질의와 source symbol 기반 seed를 확인했지만, `PaymentService와`, `OrderMapper는`처럼 코드 식별자 뒤에 한국어 조사가 붙는 입력은 없었습니다. Screenshot 검증도 `class_import` 문자열이 있는지 정도는 확인할 수 있었지만, 첫 graph evidence가 실제 질문 의도와 맞는지까지는 자동으로 검증하지 않았습니다.

### 수정 내용

- Graph seed 정규화에서 영문/코드 식별자 뒤에 붙은 한국어 조사(`와`, `과`, `은`, `는`, `이`, `가`, `을`, `를`, `의`, `로`, `으로`, `에서`, `에게`, `도`, `만`)를 제거합니다.
- GraphRAG evidence 선택에서 `class_import`, `impact_path`, `domain_summary`가 균형 있게 남도록 조정해 한 종류가 결과를 독점하지 않게 했습니다.
- Project Chat GraphRAG expander에 `관계 유형: class_import ...` 요약을 추가해 표 내부를 보지 않아도 evidence type을 확인할 수 있게 했습니다.
- 한국어 질문으로 실제 `local_openai / qwen2.5-coder-7b-instruct` Project Chat을 다시 실행하고, 첫 graph evidence가 `class_import PaymentService -> OrderMapper`인지 확인한 뒤 screenshot을 갱신했습니다.

### 재발 방지 규칙

- 한국어 업무 질문에서 code identifier를 추출하는 로직은 조사, 종결 어미, punctuation이 붙은 identifier를 포함해 테스트합니다.
- GraphRAG screenshot 검증은 단순히 graph가 열리는지뿐 아니라, 질문 의도와 맞는 핵심 evidence type과 대표 node/class가 화면에 보이는지 확인합니다.
- Compact graph evidence는 한 relation type이 결과를 독점하지 않도록 type balance 또는 explicit ranking 기준을 둡니다.
- 실제 데모 screenshot은 `provider=local_openai`, `fallback=False`, `mock_logs=0`, `fallback_logs=0`과 함께 질문/근거가 자연어 사용 맥락에 맞는지 시각적으로 확인합니다.

### 남은 한계 또는 후속 확인

현재 조사는 대표적인 식별자 뒤 조사만 제거합니다. `PaymentService에서는`, `OrderMapper까지는`, `updateOrderStatus를`처럼 더 다양한 한국어 어절이나 method name 뒤 조사가 붙는 경우는 추가 테스트와 정규화가 필요할 수 있습니다. Graph evidence ranking도 seed 수와 type balance를 함께 쓰므로, 질문이 여러 domain을 동시에 묻는 경우에는 여전히 사용자가 기대한 하나의 관계만 최상단에 오지 않을 수 있습니다.

### 검증 명령과 결과

- 실제 Project Chat 실행: `chat_session=333`, `provider=local_openai`, `model=qwen2.5-coder-7b-instruct`, `fallback=False`, `used_sources=8`, `graph_evidence=8`, 첫 graph evidence `class_import PaymentService -> OrderMapper`, `mock_logs=0`, `fallback_logs=0`.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url "http://localhost:8515/?project_id=97" --feature project-chat-answer --surface local --height 1500 --expect-text "PaymentService와 OrderMapper" --expect-text "Provider: local_openai" --expect-text "fallback=False" --expect-text "답변에 사용된 현재 소스 근거 8건" --expect-text "답변에 사용된 그래프 관계 근거 8건" --forbid-text "Mock answer" --forbid-text "fallback=True" --forbid-text "StreamlitAPIException" --forbid-text "Traceback"`: 통과.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url "http://localhost:8515/?project_id=97" --feature project-chat-graph-evidence --surface local --height 1700 --expect-text "PaymentService와 OrderMapper" --expect-text "Provider: local_openai" --expect-text "fallback=False" --expect-text "답변에 사용된 그래프 관계 근거 8건" --expect-text "GraphRAG 관계도" --expect-text "class_import" --expect-text "OrderMapper" --forbid-text "Mock answer" --forbid-text "fallback=True" --forbid-text "StreamlitAPIException" --forbid-text "Traceback"`: 통과.
- `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_project_chat_page.py tests\test_documentation_images.py -q`: 25개 통과.
- `.\.venv\Scripts\python.exe -m pytest -q`: 162개 통과.

## 2026-06-17 - Mock AI Code Review 결과를 실제 분석처럼 보이게 만들었다

분류:

- Demo evidence integrity failure
- AI verification policy gap
- Agent-caused mistake

관련 기능 및 문서:

- `src/services/code_review_service.py`
- `scripts/capture_feature_screenshot.py`
- `docs/application-preview.md`
- `ROADMAP.md`의 `AI Code Review Demo Evidence And Preview Screenshot`
- commit `1a0e60f show AI Code Review demo findings`

### 증상

Application Preview의 AI Code Review screenshot을 결과 중심으로 갱신하면서, 실제 local LLM 호출 결과가 아니라 `mock` provider로 샘플 commit diff를 해석한 deterministic 결과를 저장하고 캡처했습니다. 화면과 문서만 보면 실제 LLM 분석 결과처럼 보일 수 있었습니다.

### 직접 원인

AI Code Review mock/default path에 샘플 payment/dashboard/refactoring commit 신호를 읽는 rich payload를 추가했고, screenshot automation이 `LLMClient(provider="mock")`로 review result를 preseed한 뒤 화면을 캡처했습니다.

### 배경 또는 구조적 원인

사용자의 의도는 샘플 프로젝트의 commit, plan, source, graph 관계를 풍부하게 설계해 실제 local LLM이 좋은 판단을 내릴 수 있게 만드는 것이었습니다. 하지만 작업 중 "데모 화면을 그럴싸하게 보이게 한다"는 목표를 mock 결과 품질 보강으로 잘못 해석했습니다. 기존 문서에는 mock smoke check와 live local provider 검증을 분리해야 한다는 기준이 있었지만, Application Preview screenshot 갱신 작업에 그 기준을 강제하는 장치가 없었습니다.

### 사전 검증에서 놓친 이유

테스트와 screenshot verification은 화면에 `리뷰 결과`, `PaymentService.java`, `0원 결제`가 보이는지만 확인했습니다. provider가 `local_openai`인지, fallback이 없었는지, `ai_invocation_logs`에 실제 local LLM telemetry가 남았는지는 screenshot 검증 조건에 포함하지 않았습니다.

### 수정 내용

- mock provider의 샘플별 rich review payload를 제거합니다.
- screenshot automation의 mock preseed를 제거합니다.
- AI Code Review Application Preview는 실제 local LLM 실행으로 저장된 결과만 사용하도록 검증 절차를 바꿉니다.
- 샘플 데이터 보강은 mock 결과 생성이 아니라 실제 LLM이 판단할 수 있는 commit/diff/source/plan/graph evidence 설계로 분리합니다.

### 재발 방지 규칙

- Application Preview, README, 데모 가이드, 검증 문서에서 AI 결과를 보여줄 때는 provider와 fallback 여부를 확인합니다.
- `mock` 또는 fallback 결과를 제품 가치 증거로 캡처하지 않습니다. mock은 설치/화면 흐름 smoke check에만 사용합니다.
- 샘플 프로젝트 보강은 LLM 판단 재료를 설계하는 작업이지, mock output을 그럴듯하게 만드는 작업이 아닙니다.
- screenshot automation이 AI 결과를 preseed해야 할 때는 local provider telemetry가 있는 저장 결과를 사용하고, mock provider를 직접 호출하지 않습니다.

### 남은 한계 또는 후속 확인

실제 local LLM 품질은 모델과 설정에 따라 달라질 수 있습니다. 따라서 샘플 commit은 affected method, input condition, user impact, suggested fix가 diff와 commit message에서 충분히 드러나도록 계속 설계해야 합니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe scripts\run_local_ai_verification.py --project-id 97 --features code-review --code-review-target commit --code-review-ref 2d80976 --output docs\local-llm-verification-result.md`: 실제 `local_openai / qwen2.5-coder-7b-instruct` 호출로 완료, fallback 0건, validation `parsed`.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url "http://localhost:8514/?project_id=97" --feature ai-code-review --surface local --height 1500 --expect-text "리뷰 결과" --expect-text "local_openai" --expect-text "PaymentService.java" --expect-text "zero amount" --expect-text "리뷰 기록" --forbid-text "StreamlitAPIException" --forbid-text "Traceback" --forbid-text "Mock review"`: 통과, `docs/images/features/ai-code-review.png` 갱신.
- Focused test와 diff check 결과는 `AI_CHANGELOG.md`의 `Real local LLM demo evidence correction` 항목에 기록합니다.

## 2026-06-15 - Project Chat GraphRAG 메타데이터에서 Streamlit expander를 다시 중첩했다

분류:

- Streamlit UI runtime failure
- Screenshot verification finding
- Recurring layout policy gap

관련 기능 및 문서:

- `src/ui/project_chat_page.py`
- `scripts/capture_feature_screenshot.py`
- `AI_CHANGELOG.md`의 `Project Chat GraphRAG interactive visualization`
- `docs/engineering-decisions.md`의 `Project Chat GraphRAG는 compact interactive evidence graph로 보여준다`

### 증상

Project Chat의 `그래프 관계 근거 보기`에 interactive GraphRAG 관계도를 추가한 뒤 screenshot capture가 금지 text 검증에서 실패했습니다. 화면의 숨은 오류 text에는 `StreamlitAPIException`과 다음 메시지가 포함되었습니다.

```text
Expanders may not be nested inside other expanders.
```

### 직접 원인

Assistant 답변의 `그래프 관계 근거 보기` 자체가 `st.expander`인데, 그 내부에 raw graph metadata를 접기 위해 다시 `st.expander("원본 메타데이터")`를 추가했습니다. Streamlit은 expander 안의 expander를 허용하지 않으므로 렌더링 중 예외가 발생했습니다.

### 배경 또는 구조적 원인

이전에 Git Sync 후속 작업 패널에서 같은 유형의 문제가 있었지만, "검증용 raw metadata는 접어 두면 된다"는 UI 패턴을 다시 적용하면서 현재 container가 expander 내부인지 확인하지 않았습니다. 재사용 가능한 graph evidence 변환 테스트는 추가했지만, Streamlit container 제약은 단위 테스트만으로 검출되지 않았습니다.

### 사전 검증에서 놓친 이유

초기 focused tests는 graph evidence를 node/edge/table로 변환하는 데이터 로직을 검증했습니다. 실제 Streamlit 화면에서는 오류가 graph evidence 아래쪽에 생겼고, 시각적으로 관계도와 표가 먼저 보였기 때문에 screenshot의 금지 text 확인 전까지 문제를 놓칠 수 있었습니다.

### 수정 내용

raw metadata 영역을 nested expander 대신 `원본 메타데이터 표시` checkbox와 inline JSON 표시로 바꿨습니다. 사용자는 필요할 때만 원본 metadata를 볼 수 있고, `그래프 관계 근거 보기` expander 안에는 또 다른 expander가 생기지 않습니다.

### 재발 방지 규칙

- Streamlit `st.expander` 내부에서는 또 다른 `st.expander`를 만들지 않습니다.
- 이미 접힌 영역 안에서 보조 detail을 숨겨야 하면 checkbox, toggle, tabs, caption+dataframe 같은 container-safe control을 사용합니다.
- UI screenshot 검증은 관련 expander를 실제로 연 뒤 `StreamlitAPIException`과 `Traceback` 금지 text를 확인합니다.

### 남은 한계 또는 후속 확인

Streamlit layout 제약은 정적 type check나 service test로 충분히 잡기 어렵습니다. 공통 UI helper가 layout container를 생성할 때는 호출 위치가 이미 expander/form/tab 내부인지 인자로 드러내는 방식이 필요합니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -m py_compile src\ui\project_chat_page.py tests\test_project_chat_page.py`: 통과.
- `.\.venv\Scripts\python.exe -m pytest tests\test_project_chat_page.py -q`: 6개 테스트 통과.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --url "http://localhost:8501/?project_id=97" --feature project-chat-graph-evidence --surface local --height 1500 --expect-text "GraphRAG 관계도" --expect-text "PaymentService" --expect-text "OrderMapper" --expect-text "관계 근거 표" --expect-text "원본 메타데이터 표시" --forbid-text "StreamlitAPIException" --forbid-text "Traceback"`: 통과.

## 2026-06-15 - Git Sync 후속 작업 패널에서 Streamlit expander를 중첩했다

분류:

- Streamlit UI runtime failure
- Browser verification finding

관련 기능 및 문서:

- `src/ui/git_page.py`
- `src/services/git_followup_service.py`
- `AI_CHANGELOG.md`의 `Git Sync follow-up action orchestrator`

### 증상

`Git 동기화` 화면에 `동기화 후 다음 작업` 패널을 추가한 뒤 Browser 검증에서 `나중에 해도 됨` 영역에 `StreamlitAPIException`이 표시되었습니다.

오류 요지:

```text
Expanders may not be nested inside other expanders.
```

### 직접 원인

`나중에 해도 됨`을 `st.expander`로 감싼 뒤, 공통 렌더링 helper가 내부에서 다시 `상세 표`용 `st.expander`를 만들었습니다. Streamlit은 expander 안의 expander를 허용하지 않으므로 화면 렌더링 중 예외가 발생했습니다.

### 배경 또는 구조적 원인

권장 작업과 나중 작업을 같은 helper로 렌더링하면서, 호출 위치가 이미 expander 내부인지 구분하지 않았습니다. 단위 테스트는 service 계산만 검증했기 때문에 Streamlit layout 제약을 잡지 못했습니다.

### 사전 검증에서 놓친 이유

초기 focused tests는 Python compile과 service 결과 중심이었고, 실제 Streamlit 화면을 열기 전까지 layout runtime 제약을 확인하지 못했습니다.

### 수정 내용

후속 작업 렌더링 helper에 `detail_expander` 옵션을 추가했습니다. 일반 권장 영역에서는 `상세 표`를 expander로 접고, 이미 expander 안에서 렌더링되는 `나중에 해도 됨` 영역에서는 caption과 dataframe만 표시해 expander 중첩을 피했습니다.

### 재발 방지 규칙

- Streamlit 공통 UI helper가 `st.expander`, `st.tabs`, `st.form` 같은 layout container를 만들 때는 호출 위치의 container 제약을 인자로 분리합니다.
- layout 변경은 service 테스트뿐 아니라 실제 Streamlit 화면 Browser 검증으로 확인합니다.

### 남은 한계 또는 후속 확인

Streamlit layout 제약은 정적 테스트로 모두 잡기 어렵습니다. UI 구조를 바꾸는 작업은 최소 한 번 실제 화면을 열어 주요 텍스트와 예외 표시 여부를 확인해야 합니다.

### 검증 명령과 결과

- Browser로 `http://127.0.0.1:8507`의 `Git 동기화` 화면에서 `동기화 후 다음 작업`, `권장 순서`, `현재 소스 근거 갱신`, `검색 준비 생성`, `Mapping 분석`, `Risk Analysis 재계산` 표시와 `StreamlitAPIException` 미표시 확인.
- `.\.venv\Scripts\python.exe -m pytest tests\test_git_followup_service.py tests\test_runtime_estimator.py tests\test_documentation_images.py -q`: 6개 테스트 통과.

## 2026-06-15 - Neo4j impact path 조회에서 Cypher alias가 node 변수와 충돌했다

분류:

- Neo4j query failure
- Screenshot verification gap
- Graph read model readback

관련 기능 및 문서:

- `src/services/neo4j_graph_service.py`
- `src/ui/knowledge_graph_page.py`
- `scripts/capture_feature_screenshot.py`
- `AI_CHANGELOG.md`의 `Knowledge Graph 저장 그래프 조회와 탭별 screenshot 보강`

### 증상

Knowledge Graph 탭별 screenshot 기준을 `Neo4j 저장 그래프 기준` 문구로 강화한 뒤, 클래스 관계도/영향 경로 캡처가 실패했습니다. 실제 Neo4j preview 조회를 직접 실행하자 class 관계와 impact path query 중 impact path query가 실패했습니다.

실패 당시 오류:

```text
Neo.ClientError.Statement.TypeError: Type mismatch: expected a map but was String("...")
```

### 직접 원인

Cypher query에서 commit node 변수와 `RETURN ... AS commit` alias를 함께 사용했고, `ORDER BY coalesce(commit.committed_at, '')`가 `commit` alias 문자열을 node처럼 참조했습니다. Neo4j가 문자열에 property 접근을 시도하면서 type mismatch가 발생했습니다.

### 배경 또는 구조적 원인

초기 구현은 payload 생성과 graph write 중심으로 검증했고, 저장된 Neo4j graph를 다시 읽어 클래스 관계도와 영향 경로를 구성하는 readback query 검증은 뒤늦게 추가됐습니다. screenshot 자동화도 탭 제목과 일부 데이터만 확인하면 통과할 수 있었기 때문에, 실제 저장 그래프 조회 여부가 충분히 드러나지 않았습니다.

### 사전 검증에서 놓친 이유

`Knowledge Graph` 대표 screenshot은 Neo4j 동기화 성공과 node/edge count만 확인했습니다. 클래스 관계도, 영향 경로, 노드/엣지 탭을 각각 열어 `Neo4j 저장 그래프 기준`과 실제 관계 타입을 확인하는 시나리오가 없었습니다.

### 수정 내용

impact path query의 node 변수를 `commit_node`로 바꾸고, 정렬 기준은 `WITH ... committed_at`으로 분리했습니다. 화면은 저장된 Neo4j graph에서 class import 관계, impact path, node/edge count를 우선 조회하고, 저장 graph가 없을 때만 동기화 대상 preview를 fallback으로 보여주도록 변경했습니다. screenshot 자동화에는 `knowledge-graph-class`, `knowledge-graph-impact`, `knowledge-graph-nodes-edges` 시나리오를 추가했습니다.

### 재발 방지 규칙

- Cypher query에서 node 변수명과 `RETURN` alias를 같은 이름으로 쓰지 않습니다.
- graph write 기능을 추가하면 저장 성공뿐 아니라 저장된 graph를 다시 읽는 query를 테스트합니다.
- Application Preview screenshot은 대표 화면만 찍지 말고, 기능 가치가 탭 안에 있으면 탭별 readback 상태까지 캡처합니다.

### 남은 한계 또는 후속 확인

현재 Neo4j graph는 Knowledge Graph 화면에서 관계 탐색 근거로 사용됩니다. Project Chat이나 RAG 답변 context에 graph path를 자동 주입하는 GraphRAG는 아직 후속 확장 범위입니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py tests\test_documentation_images.py -q`: 5개 테스트 통과.
- `.\.venv\Scripts\python.exe -m pytest -q`: 130개 테스트 통과.
- `get_neo4j_project_preview(4)`: `status=completed`, class 관계 17개, 영향 경로 47개 조회 확인.
- `scripts\capture_feature_screenshot.py --feature knowledge-graph-class`, `knowledge-graph-impact`, `knowledge-graph-nodes-edges`: 각 screenshot 캡처 통과.

## 2026-06-15 - Neo4j schema 변경과 graph write를 같은 transaction에서 실행했다

분류:

- Neo4j integration failure
- Infrastructure verification gap
- Graph read model lifecycle

관련 기능 및 문서:

- `src/services/neo4j_graph_service.py`
- `tests/test_neo4j_graph_service.py`
- `docs/engineering-decisions.md`의 `Neo4j는 프로젝트 관계 그래프 read model로 적용한다`
- `AI_CHANGELOG.md`의 `Neo4j Knowledge Graph 기반 추가`

### 증상

Neo4j container를 실제로 띄운 뒤 `sync_project_graph_to_neo4j`를 실행하자 graph payload 생성은 성공했지만 Neo4j write가 실패했습니다. 오류는 `Neo.ClientError.Transaction.ForbiddenDueToTransactionType`였고, 같은 transaction 안에서 schema modification과 일반 write query를 섞었다는 메시지가 나왔습니다.

실패 당시 출력:

```text
sync_status=failed nodes=1076 edges=10263 errors=1
first_error=... Tried to execute Write query after executing Schema modification ...
```

### 직접 원인

`_sync_project_graph_tx`가 `CREATE CONSTRAINT ... IF NOT EXISTS`를 실행한 뒤 같은 write transaction에서 기존 graph 삭제와 node/edge upsert를 이어서 실행했습니다. Neo4j 5는 schema 변경과 일반 write를 같은 transaction에 섞는 것을 허용하지 않습니다.

### 배경 또는 구조적 원인

초기 구현 검증은 graph payload 생성, UI preview, Docker Compose 구문, 단위 테스트 중심이었습니다. 실제 Neo4j Bolt 연결과 write transaction을 실행하기 전까지는 schema statement와 write statement의 transaction type 충돌이 드러나지 않았습니다.

### 사전 검증에서 놓친 이유

Neo4j service를 실제로 띄워 동기화하지 않고 `docker compose config -q`까지만 먼저 확인했습니다. 단위 테스트도 Java symbol 추출과 payload edge 구성을 검증했지만, driver/session transaction sequencing을 검증하지 않았습니다.

### 수정 내용

Neo4j schema 준비를 `_ensure_neo4j_schema(session)`로 분리하고, `session.run(...).consume()`으로 constraint 생성을 먼저 끝낸 뒤 별도 `session.execute_write(...)` transaction에서 graph cleanup과 node/edge upsert를 실행하도록 변경했습니다.

`tests/test_neo4j_graph_service.py`에는 fake Neo4j session test를 추가해 schema 준비가 write transaction 밖에서 먼저 실행되는지 확인합니다.

### 재발 방지 규칙

- Neo4j schema 변경, index/constraint 생성, 일반 write query는 같은 explicit write transaction에 섞지 않습니다.
- Graph DB 기능을 추가하거나 transaction 흐름을 바꿀 때는 payload unit test만으로 끝내지 말고 최소 1회 실제 Neo4j service against sync를 실행합니다.
- 외부 read model은 "연결 확인"과 "실제 write path"를 별도 verification 항목으로 기록합니다.

### 남은 한계 또는 후속 확인

현재 graph sync는 실제 Neo4j에 node/edge를 저장하는 smoke까지 확인했습니다. 다만 대용량 프로젝트에서 batch size, transaction memory, dynamic relationship type 설계, Neo4j backup/restore 정책은 별도 운영 검증이 필요합니다.

### 검증 명령과 결과

- `docker compose up -d neo4j`: `neo4j:5-community` image pull 및 `ai_commit_advisor_neo4j` container 시작 성공.
- `docker compose ps neo4j`: `7474`, `7687` port 노출과 `Up` 상태 확인.
- `$env:NEO4J_ENABLED='true'; ...; get_neo4j_connection_status()`: `connected=True`, `Neo4j 연결됨`.
- `.\.venv\Scripts\python.exe -m pytest tests\test_neo4j_graph_service.py -q`: 3개 테스트 통과.
- 실제 sync 재실행: `project_id=1`, `nodes=1076`, `edges=10263`, `sync_status=completed`, `summary_status=completed`.

## 2026-06-14 - README top screenshot stayed stale after Application Preview refresh

분류:

- Documentation screenshot drift
- Verification gap
- README entry-point UX

관련 기능 및 문서:

- `README.md`
- `docs/application-preview.md`
- `docs/images/features/home.png`
- `docs/images/ai-commit-advisor-home-48.png`
- `tests/test_documentation_images.py`

### 증상

Application Preview screenshot과 하단 기능 screenshot을 여러 차례 갱신했지만, README 최상단에 보이는 대표 화면은 예전 sidebar/menu 상태로 남아 있었습니다. 사용자가 README 첫 화면이 바뀌지 않았다고 지적했습니다.

### 직접 원인

README에는 Home screenshot이 두 군데 있었습니다. 최상단 이미지는 `docs/images/ai-commit-advisor-home-48.png`를 참조했고, `스크린샷` 섹션은 `docs/images/features/home.png`를 참조했습니다. 최근 캡처 작업은 Application Preview와 `docs/images/features/home.png`만 갱신했기 때문에 README 최상단의 별도 대표 이미지가 stale 상태로 남았습니다.

### 배경 또는 구조적 원인

과거 GitHub/browser image cache를 피하려고 versioned filename인 `ai-commit-advisor-home-48.png`를 추가한 뒤, README 대표 이미지와 Application Preview Home 이미지의 source of truth가 갈라졌습니다. 이후 작업에서는 "Application Preview screenshot 갱신"을 README 최상단 screenshot 갱신과 같은 일로 착각했습니다.

### 사전 검증에서 놓친 이유

검증은 `docs/application-preview.md`의 image reference와 `docs/images/features/*.png` 중심이었습니다. README의 모든 image reference를 점검하거나, README 최상단 대표 이미지가 Application Preview Home과 같은 파일을 쓰는지 확인하는 테스트가 없었습니다.

### 수정 내용

README 최상단 대표 이미지를 `docs/images/features/home.png`로 통일하고, 중복 `스크린샷` 섹션 이미지는 제거했습니다. 더 이상 사용하지 않는 legacy 대표 이미지 파일은 삭제합니다. README가 legacy `ai-commit-advisor-home*.png`를 다시 참조하지 않도록 문서 테스트를 추가했습니다.

### 재발 방지 규칙

README 대표 screenshot은 Application Preview의 Home screenshot과 같은 `docs/images/features/home.png`를 사용합니다. README에 별도 versioned representative screenshot 파일을 만들지 않습니다. Application Preview나 Home screenshot을 갱신할 때는 README image reference도 함께 확인합니다.

### 남은 한계 또는 후속 확인 사항

GitHub 캐시 문제를 다시 만나면 파일명을 바꾸기보다 query/cache 정책이나 release note 안내를 검토합니다. 같은 이미지를 두 파일로 복제하는 방식은 사용하지 않습니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -m pytest tests\test_documentation_images.py -q` 1개 테스트 통과.
- `rg -n "ai-commit-advisor-home" README.md docs\application-preview.md docs\feature-guide.md docs\setup-and-operations.md` 결과 없음.
- `Test-Path docs\images\ai-commit-advisor-home.png`, `Test-Path docs\images\ai-commit-advisor-home-48.png` 모두 `False` 확인.

## 2026-06-14 - Risk Analysis screenshot verification exposed Streamlit `rename()` error

분류:

- UI rendering
- Screenshot verification
- Streamlit dataframe usage

관련 기능 및 문서:

- `Risk Analysis`
- `src/ui/risk_page.py`
- `scripts/capture_feature_screenshot.py`
- `docs/application-preview.md`

### 증상

Application Preview screenshot을 현재 접이식 sidebar 메뉴 기준으로 갱신하던 중 `Risk Analysis` 화면에서 unresolved risk table을 렌더링할 때 다음 오류가 표시됐습니다.

```text
streamlit.errors.StreamlitAPIException: rename() is not a valid Streamlit command.
```

### 직접 원인

`src/ui/risk_page.py`의 `_render_findings()`가 Pandas `DataFrame.rename()`을 `st.dataframe(...)` 호출 뒤에 체이닝했습니다. 이 경우 `rename()`은 Pandas 객체가 아니라 Streamlit `DeltaGenerator`에 호출되어 Streamlit command로 해석됩니다.

### 배경 또는 구조적 원인

Risk Analysis 표시는 한국어 업무 라벨로 정리하는 과정에서 dataframe 변환과 Streamlit 렌더링 경계가 섞였습니다. Pandas chain이 길어질 때 마지막 렌더링 호출까지 같은 chain에 포함되면, UI에서만 드러나는 런타임 오류가 생길 수 있습니다.

### 사전 검증에서 놓친 이유

기존 단위 테스트와 compile 검증은 `risk_page.py`의 실제 Streamlit 렌더링 경로를 실행하지 않았습니다. 또 Application Preview 캡처가 메뉴 구조 변경 뒤 전체 화면을 다시 돌기 전까지 해당 table까지 도달하지 않았습니다.

### 수정 내용

컬럼 rename을 먼저 적용한 `display_df`를 만든 뒤 `st.dataframe(display_df, ...)`에 넘기도록 수정했습니다. 캡처 자동화는 접이식 sidebar 그룹을 열고 이동할 수 있게 보강했습니다.

### 재발 방지 규칙

Pandas 변환은 Streamlit 렌더링 호출 전에 끝냅니다. `st.dataframe()`, `st.table()`, `st.plotly_chart()` 같은 렌더링 함수 뒤에 Pandas/DataFrame method를 체이닝하지 않습니다. Application Preview screenshot을 갱신할 때는 최소한 관련 화면의 실제 렌더링까지 확인합니다.

### 남은 한계 또는 후속 확인 사항

현재 screenshot 자동화는 대표 분석 화면 중심입니다. 개발자/프로그램/개발계획 업로드 검증 같은 일부 Application Preview 이미지는 별도 수동 또는 후속 자동화가 필요할 수 있습니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -m py_compile src\ui\risk_page.py scripts\capture_feature_screenshot.py` 통과.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature risk-analysis --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local --forbid-text "rename() is not a valid Streamlit command"` 통과.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature all --url http://localhost:8501 --project-name "AAA Sample Shop Rich Demo (4)" --surface local --forbid-text "가정값" --forbid-text "고객가치 KPI" --forbid-text "자원관리 KPI 추세" --forbid-text "rename() is not a valid Streamlit command"` 통과.

## 2026-06-14 - Existing Windows `.venv` binary packages broke Quick Start

분류:

- Local environment
- Dependency installation
- Quick Start verification gap

관련 기능 및 문서:

- `README.md` Quick Start
- `docs/setup-and-operations.md`
- `requirements.txt`
- `AI_CHANGELOG.md`

### 증상

사용자가 VS Code terminal에서 Quick Start 흐름대로 로컬 Python 앱을 실행했을 때 앱이 시작되지 않았습니다. 코드나 문서를 직접 수정하지 않았는데도 import 단계에서 다음 오류가 순차적으로 발생했습니다.

```text
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
ModuleNotFoundError: No module named 'psycopg2._psycopg'
ModuleNotFoundError: No module named 'pandas._libs.pandas_parser'
```

### 직접 원인

로컬 `.venv` 안의 Windows native wheel 기반 패키지가 부분적으로 깨져 있었습니다. `pydantic`, `psycopg2-binary`, `pandas` metadata는 남아 있었지만 실제 import에 필요한 compiled extension module이 없거나 불완전했습니다.

### 배경 또는 구조적 원인

`.venv`는 Git으로 관리되지 않는 로컬 실행 환경입니다. 기존 `.venv` 위에 `pip install -r requirements.txt`나 개별 패키지 재설치가 실행되는 동안 Python/Streamlit/VS Code가 파일을 잡고 있거나, 설치가 중간에 끊기거나, Windows 파일 잠금/백신/네트워크 영향이 있으면 package metadata와 실제 `.pyd` extension file 상태가 어긋날 수 있습니다.

Quick Start 문서도 기존 `.venv`가 있을 때의 안전한 재사용 기준과, native package import 오류가 났을 때 `.venv`를 새로 만드는 복구 기준을 충분히 설명하지 않았습니다.

추가로 README Quick Start가 PowerShell `Activate.ps1` 실행을 기본 경로로 안내했습니다. 사용자가 cmd.exe나 Git Bash 같은 다른 터미널에서 따라 하면 activation 명령이 맞지 않고, PowerShell에서도 실행 정책에 따라 `Activate.ps1`이 막힐 수 있습니다. 처음 설치하는 사용자가 가상환경 생성 직후 터미널별 차이에 걸릴 수 있는 문서 문제가 있었습니다.

### 사전 검증에서 놓친 이유

기능 구현 검증은 당시 정상 상태였던 로컬 `.venv`에서 `py_compile`, Alembic migration, `compileall`, focused pytest, full pytest, `git diff --check`를 실행했습니다. 이 검증은 코드와 DB migration 회귀를 확인했지만, 기존 `.venv`가 부분적으로 깨진 상태에서 Quick Start를 새로 따라 하는 사용자의 환경 재현까지 포함하지 않았습니다.

Docker app을 중지하고 로컬 Python 실행을 확인하는 과정도 늦게 수행되어, 사용자가 직접 VS Code에서 실행하기 전까지 broken `.venv` 증상이 노출되지 않았습니다.

### 수정 내용

로컬 `.venv`의 깨진 binary package를 재설치해 복구했습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall --no-cache-dir pydantic-core==2.46.4
.\.venv\Scripts\python.exe -m pip install --force-reinstall --no-cache-dir pandas==2.2.3 numpy==2.2.6 python-dateutil==2.9.0.post0 pytz==2026.2 tzdata==2026.1
```

중간에 `requirements.txt` 전체 강제 재설치를 시도했지만 시간 제한으로 완료 여부가 불명확했으므로, 최종적으로 깨진 binary import를 직접 확인하며 필요한 패키지를 재설치했습니다.

`README.md`와 `docs/setup-and-operations.md`는 기본 설치/실행 명령을 `.\.venv\Scripts\python.exe -m ...` 형태로 바꿔 터미널별 activation 명령을 몰라도 Quick Start를 수행할 수 있게 합니다. `docs/setup-and-operations.md`에는 기존 `.venv` 재사용 주의사항과 native extension import 오류가 날 때의 복구 절차도 추가합니다.

### 재발 방지 규칙

- Windows 로컬 Quick Start를 검증할 때는 앱을 실제로 `.\.venv\Scripts\python.exe -m streamlit run app.py`로 기동하고 `/_stcore/health`가 HTTP 200을 반환하는지 확인합니다.
- 기존 `.venv`에서 `pydantic_core`, `psycopg2`, `pandas._libs` 같은 native extension import 오류가 나면 코드 변경보다 `.venv` 손상을 먼저 의심합니다.
- 기존 `.venv`가 의심스러우면 부분 재설치보다 `.venv` 삭제 후 새로 생성하는 절차를 우선 안내합니다. 단, 실행 중인 Python/Streamlit/VS Code terminal이 파일을 잡고 있으면 먼저 종료합니다.
- Quick Start 문서는 “이미 `.venv`가 있으면 활성화만 한다”뿐 아니라 “깨진 `.venv`를 어떻게 복구할지”도 포함해야 합니다.
- Windows 로컬 Quick Start 문서에서는 특정 shell의 activation 명령을 필수 경로로 두지 않습니다. 기본 명령은 `.venv\Scripts\python.exe -m pip`, `.venv\Scripts\python.exe -m streamlit`처럼 activation이 필요 없는 형태로 작성합니다.

### 남은 한계 또는 후속 확인 사항

이번에는 증상 발생 직전 어떤 설치 작업이 `.venv`를 깨뜨렸는지 확정하지 못했습니다. Windows 파일 잠금, 중단된 pip 실행, 백신/동기화 도구, 기존 `.venv` 위 재설치 등이 가능한 원인입니다.

새 PC에서 빈 `.venv`를 처음부터 만드는 end-to-end Quick Start 검증은 별도로 수행하지 않았습니다. 문서 보강 후에는 깨끗한 `.venv` 생성, dependency install, DB init, Streamlit health check까지 한 번에 확인하는 명령을 검증에 포함하는 것이 좋습니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -c "import pandas; print('pandas ok', pandas.__version__); import psycopg2; print('psycopg2 ok'); import pydantic; print('pydantic ok', pydantic.__version__); from src.db.init_db import init_db; init_db(); print('init ok')"` passed.
- `.\.venv\Scripts\python.exe -m compileall src app.py` passed.
- `.\.venv\Scripts\python.exe -m pip check` passed with `No broken requirements found`.
- `.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501` started successfully.
- `Invoke-WebRequest http://localhost:8501/_stcore/health -UseBasicParsing` returned HTTP 200.
- `Get-NetTCPConnection -LocalPort 8501` showed no remaining process after stopping the test Streamlit process.

## 2026-06-10 - Git default branch mismatch broke CI-only repository status test

분류:

- CI
- Git test portability
- Local/CI environment mismatch

관련 기능 및 문서:

- GitHub Actions run: `https://github.com/ino5/ai-commit-advisor-26/actions/runs/27279235820`
- `tests/test_git_repository_status_service.py`
- `ROADMAP.md`
- `AI_CHANGELOG.md`

### 증상

GitHub Actions `Run tests` 단계가 exit code 1로 실패했습니다. 화면에는 Node.js 20 deprecation warning도 함께 보였지만, 실제 실패 단계는 `Run tests`였습니다.

Linux 컨테이너에서 CI 환경을 재현했을 때 `test_repository_status_reports_upstream_ahead_behind`가 `git push -u origin main`에서 실패했습니다. 오류는 `src refspec main does not match any`였습니다.

### 직접 원인

테스트가 임시 Git repository의 기본 branch가 `main`이라고 가정했습니다. Windows 로컬 Git 설정에서는 기본 branch가 `main`이라 통과했지만, Linux/CI 쪽 Git 기본값은 `master`일 수 있어 local `main` ref가 없었습니다.

### 배경 또는 구조적 원인

Git-dependent test가 host Git 설정인 `init.defaultBranch`에 의존했습니다. repository status 기능 자체는 branch 이름을 읽는 기능인데, 테스트 fixture가 branch 이름을 명시하지 않아 환경별 차이가 테스트 실패로 드러났습니다.

### 사전 검증에서 놓친 이유

로컬 Windows `.venv` 전체 테스트와 CI 환경변수 재현은 통과했지만, 둘 다 로컬 Git 전역 설정의 영향을 받았습니다. Ubuntu/Linux runner의 Git 기본 branch 차이를 별도로 재현하지 않았습니다.

### 수정 내용

임시 repository 생성 시 `git init --initial-branch=main`을 사용하고, clone 기반 upstream 테스트에서는 첫 commit 뒤 `git branch -M main`으로 local branch를 명시적으로 맞춘 뒤 `origin/main`에 push하도록 수정했습니다.

### 재발 방지 규칙

- Git repository를 만드는 테스트는 host 전역 Git 설정에 의존하지 않고 branch 이름을 명시합니다.
- CI 실패 원인을 볼 때 GitHub Actions warning은 별도로 분리하고, 실제 실패 step과 stderr를 기준으로 원인을 기록합니다.
- Windows에서 통과한 Git 테스트라도 branch, path, executable availability처럼 Linux runner에서 달라질 수 있는 전제는 Linux 컨테이너로 확인합니다.

### 남은 한계 또는 후속 확인 사항

GitHub API 로그 다운로드는 인증 권한이 없어 직접 내려받지 못했습니다. 이번 원인은 Linux 컨테이너 재현으로 확인했지만, 이후에는 GitHub 웹 UI의 failed test output도 함께 확인하면 더 빠르게 좁힐 수 있습니다.

### 검증 명령과 결과

- `docker run ... python -m pytest -q` with Git installed reproduced the failure before the fix: 1 failed, 94 passed.
- `.\.venv\Scripts\python.exe -m compileall src app.py tests` passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_git_repository_status_service.py -q` passed with 4 tests.
- `.\.venv\Scripts\python.exe -m pytest -q` passed with 95 tests.
- Linux container verification with Git installed and CI-like environment variables passed with 95 tests.

## 2026-06-10 - Commit-based Mapping malformed JSON blocked complete sample verification

분류:

- Mapping
- LLM output robustness
- Sample demo verification

관련 기능 및 문서:

- `src/services/mapping_service.py`
- `tests/test_mapping_service.py`
- `docs/ai-technical-overview.md`
- `AI_CHANGELOG.md`

### 증상

48개 commit 샘플 프로젝트에서 commit-based Mapping을 실행했을 때 `Add QA checklist for Spring MyBatis flows` commit 1건이 `failed` 상태로 남았습니다. 재시도해도 `LLM response did not match commit-based mapping JSON format` 오류가 반복되어 Mapping 화면에 실패 커밋 1건이 보였고, 분석 완료 상태의 스크린샷을 찍기 어려웠습니다.

### 직접 원인

commit-based Mapping은 LLM에게 `{"related_programs": [...]}` shape을 요구했지만, local LLM이 해당 commit에서 요구 JSON shape을 지키지 않았습니다. 기존 commit-based 경로는 JSON 파싱 실패를 바로 commit failure로 처리했습니다.

### 배경 또는 구조적 원인

program-based Mapping에는 token similarity fallback이 있었지만 commit-based Mapping에는 같은 fallback이 없었습니다. 문서/QA/test-only commit처럼 여러 프로그램과 느슨하게 관련된 commit은 LLM이 설명형 응답으로 벗어날 가능성이 더 큽니다.

### 사전 검증에서 놓친 이유

샘플 데이터 확장 직후에는 Git sync, upload, count, focused unit test 중심으로 확인했고, 전체 48개 commit에 대한 real local LLM commit-based Mapping batch를 먼저 돌리지 않았습니다.

### 수정 내용

commit-based Mapping에서 LLM 응답을 요구 JSON으로 파싱하지 못하면 후보 프로그램과 commit message, changed file path, diff snippet의 token similarity로 보수적인 fallback mapping을 저장하도록 변경했습니다. fallback 사용 사실은 mapping reason과 `raw_response.fallback`에 남깁니다.

### 재발 방지 규칙

- 샘플 스크린샷 갱신 전에는 Git sync/upload뿐 아니라 Mapping, Risk Analysis, AI Progress, RAG, Project Chat까지 핵심 분석 상태를 먼저 검증합니다.
- LLM batch 분석은 한 항목의 malformed response가 전체 downstream 검증을 막지 않도록 fallback 또는 부분 성공 처리를 갖춰야 합니다.
- fallback은 완전한 AI 판단이 아니므로 reason/raw metadata에 사용 사실을 남깁니다.

### 남은 한계 또는 후속 확인 사항

fallback은 token overlap 기반이므로 false positive 가능성이 있습니다. Mapping feedback review queue에서 낮은 관련도, weak reason, unrelated decision을 계속 검토해야 합니다.

### 검증 명령과 결과

- `.\.venv\Scripts\python.exe -m pytest tests\test_mapping_service.py -q` passed with 4 tests.
- 48개 sample commit Mapping 재검증 결과: completed 48, failed 0, mappings 59.
- Risk Analysis 재실행 결과: unresolved risk 12건.
- AI Progress 확인 결과: 8개 program, plan average 90.6%, AI average 50.0%, implementation status 8건.

## 2026-06-10 - Parallel screenshot capture triggered Alembic migration context collision

분류:

- Screenshot verification
- Streamlit startup
- Alembic migration concurrency

관련 기능 및 문서:

- `src/db/init_db.py`
- `scripts/capture_feature_screenshot.py`
- `AI_CHANGELOG.md`

### 증상

Application Preview 캡처를 병렬로 실행하던 중 새 Streamlit browser session에서 `KeyError: 'script'`가 표시됐습니다. traceback은 `init_db() -> run_migrations() -> alembic.command.upgrade()` 종료 시 Alembic `EnvironmentContext._remove_proxy()`에서 발생했습니다.

### 직접 원인

여러 Streamlit session이 거의 동시에 page load를 시작하면서 `load_projects()`가 각각 `init_db()`를 호출했고, 같은 Python process 안에서 Alembic migration command가 중복 실행됐습니다. Alembic proxy context는 이 동시 실행에 안전하지 않았습니다.

### 배경 또는 구조적 원인

`init_db()`는 앱 화면 진입마다 migration을 다시 호출했습니다. 단일 사용자의 순차 실행에서는 잘 드러나지 않았지만, screenshot automation을 병렬로 돌리면 같은 process에서 migration 초기화가 겹칠 수 있었습니다.

### 사전 검증에서 놓친 이유

기존 캡처 자동화는 feature를 순차 실행하는 전제를 주로 사용했습니다. 이번 작업에서 시간을 줄이려고 여러 screenshot command를 병렬 실행하면서 Streamlit startup path의 동시성 문제가 드러났습니다.

### 수정 내용

`init_db()`에 process-local lock과 initialized flag를 추가해 같은 process에서는 migration을 한 번만 실행하도록 했습니다. 캡처는 병렬 대신 순차 실행으로 진행했습니다.

### 재발 방지 규칙

- Streamlit app startup에서 migration 같은 global side effect는 process-local lock으로 보호합니다.
- screenshot automation은 앱 초기화 경로를 건드리는 경우 병렬 실행을 피하거나, 각 worker가 독립 process/server를 쓰도록 합니다.
- GitHub Actions warning이나 generic Playwright wrapper message보다 실제 traceback의 failed step을 기준으로 원인을 기록합니다.

### 남은 한계 또는 후속 확인 사항

process-local lock은 같은 Python process 안의 중복 migration을 막습니다. 여러 app process가 동시에 시작되는 운영 배포에서는 DB migration을 app startup 밖의 deployment step으로 분리하는 정책을 별도로 검토할 수 있습니다.

### 검증 명령과 결과

- 확인용 Streamlit 서버 재시작 후 sequential screenshot capture가 성공했습니다.
- `.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature rag-search --url http://localhost:8537 --surface local --project-name "AAA Sample Shop Rich Demo 48"` passed.

## 2026-06-10 - Sidebar active menu jitter returned after CSS-only stabilization

분류:

- UX
- Streamlit sidebar navigation
- Visual verification gap

관련 문서:

- `app.py`
- `scripts/capture_feature_screenshot.py`
- `docs/engineering-decisions.md`
- `ROADMAP.md`
- `AI_CHANGELOG.md`

### 증상

사이드바 메뉴 클릭 시 선택 항목의 색상만 바뀌는 것이 아니라 위치와 간격이 미묘하게 깨져 보였습니다. 이전에 `Sidebar 메뉴 위치 흔들림 보정` 작업으로 높이, margin, box sizing, 왼쪽 border 폭을 맞췄지만, 사용자가 다시 같은 종류의 어색함을 확인했습니다.

read-only 계측에서 `Dashboard` 같은 항목이 비활성 버튼일 때와 활성 custom `div`일 때 같은 메뉴 슬롯 안에서 `y` 위치가 약 16px 달라지는 사례가 확인됐습니다.

### 직접 원인

활성 메뉴는 `st.sidebar.markdown('<div class="nav-active">...')`로 렌더링했고, 비활성 메뉴는 `st.sidebar.button(...)`으로 렌더링했습니다. 두 항목은 CSS 값 일부가 같아도 Streamlit wrapper, button 내부 `p` 구조, margin 적용 위치가 달랐습니다.

### 배경 또는 구조적 원인

이전 보정은 active/inactive box sizing을 맞추는 CSS 조정에 집중했습니다. 하지만 상태에 따라 DOM 구조가 달라지는 설계 자체는 유지됐기 때문에, Streamlit 내부 구조나 특정 선택 상태에서 다시 시각 차이가 드러날 수 있었습니다.

### 사전 검증에서 놓친 이유

기존 Playwright 검증은 클릭 전후 `Mapping` 항목의 `x`, `y`, `width`가 크게 밀리는지 확인했습니다. 이 검증은 메뉴 전체가 이동하는 문제는 잡지만, 선택된 항목 자체가 비활성 버튼에서 활성 `div`로 바뀌며 슬롯 위치와 텍스트 기준선이 달라지는 문제는 충분히 확인하지 못했습니다.

### 수정 내용

사이드바 메뉴 항목을 활성/비활성 상태와 관계없이 모두 `st.button`으로 렌더링하도록 변경했습니다. 선택된 메뉴를 다시 클릭하면 상태 변경과 rerun을 하지 않습니다.

검증 스크립트는 custom `.nav-active` markup이 남아 있으면 실패하고, `Home`, `Dashboard`, `AI Progress` 항목의 클릭 전후 box 위치, 크기, text relative offset, 인접 간격이 바뀌면 실패하도록 보강했습니다.

### 재발 방지 규칙

- 같은 역할의 UI 항목은 상태가 달라도 같은 Streamlit 컴포넌트 구조로 렌더링합니다.
- CSS 보정으로 시각 차이를 줄이기 전에 DOM 구조가 갈라져 있는지 먼저 확인합니다.
- 메뉴 안정성 검증은 주변 항목 이동뿐 아니라 선택 항목 자체의 box, text offset, adjacent spacing을 확인합니다.
- active highlight를 다시 추가하려면 같은 button 구조 위에서 구현하거나, 동일 wrapper 구조를 유지하는 설계를 먼저 검증합니다.

### 남은 한계

- 메뉴 행 자체의 active highlight는 제거됐고, 현재 선택 상태는 사이드바 상단 `현재 위치` 경로로 확인합니다.
- Streamlit이 button DOM 구조를 크게 바꾸면 검증 스크립트 selector도 함께 조정해야 합니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py src scripts
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8518 --screenshot .tmp\sidebar-structure-home.png --surface local
git diff --check
```

결과:

- `compileall` passed for `app.py`, `src`, and `scripts`.
- Home screenshot verification passed against local Streamlit port 8518 and confirmed sidebar structure stability.
- `git diff --check` passed with only Git line-ending warnings.

## 2026-06-10 - Engineering decision review was missed during maintainability planning

분류:

- Agent policy
- Documentation workflow
- Engineering decision review

관련 문서:

- `AGENTS.md`
- `docs/engineering-decisions.md`
- `ROADMAP.md`
- `AI_CHANGELOG.md`

### 증상

사이드바 메뉴 위치 흔들림 재발을 read-only로 조사한 뒤, 사용자가 유지보수성 관점의 처리 계획을 요청했습니다. 초기 계획은 `AI_CHANGELOG.md`, `ROADMAP.md`, 검증 스크립트 보강을 중심으로 정리됐지만, `docs/engineering-decisions.md` 검토가 바로 포함되지 않았습니다.

사용자가 "기능 개선하면 적는 md"와 `AGENTS.md` 기준을 다시 지적한 뒤에야, 이 작업이 반복 가능한 유지보수 원칙과 검증 정책을 바꾸는 engineering decision 후보라는 점을 명확히 반영했습니다.

### 직접 원인

에이전트가 변경을 "사이드바 UX 버그와 CSS/렌더링 구조 개선"으로 좁게 분류했고, 사용자가 유지보수성을 핵심 판단 기준으로 제시한 시점에도 `docs/engineering-decisions.md`를 필수 검토 후보로 즉시 승격하지 않았습니다.

### 배경 또는 구조적 원인

`AGENTS.md`에는 이미 Engineering Decisions 기준과 Pre-Commit Documentation Check가 있었지만, 의미 있는 작업을 제안하거나 시작하기 전에 문서 영향도를 한 번에 분류하는 명시적 게이트는 없었습니다.

그 결과 개별 문서 기준은 존재했지만, 계획 단계에서 "이 변경은 앞으로 반복될 정책이나 유지보수 원칙을 만드는가?"라는 질문이 빠질 수 있었습니다.

### 사전 검증에서 놓친 이유

read-only 조사와 계획 수립 단계였기 때문에 코드 검증이나 commit 전 체크리스트를 아직 실행하지 않았습니다. 하지만 문서 영향도 검토는 구현 후가 아니라 계획 단계에서 필요한 작업이었고, 기존 체크리스트는 그 타이밍을 충분히 강제하지 못했습니다.

### 수정 내용

`AGENTS.md`에 `Documentation Impact Gate`를 추가했습니다. 에이전트는 의미 있는 code, UX, test, behavior, automation, operations, documentation 작업을 제안하거나 시작하기 전에 `AI_CHANGELOG.md`, `ROADMAP.md`, `docs/engineering-decisions.md`, `docs/failure-history.md`, user-facing docs, architecture, AI technical overview, DB migration, sample project design 문서 영향도를 명시적으로 분류해야 합니다.

또한 사용자가 유지보수성, future reuse, verification policy, structural tradeoff, operating policy, agent behavior 관점으로 변경을 설명하면 `docs/engineering-decisions.md`를 필수 검토 후보로 취급하도록 했습니다.

### 재발 방지 규칙

- 작업 계획을 세울 때 문서 영향도 분류를 별도 단계로 수행합니다.
- 유지보수성이나 반복 가능한 검증·운영·문서화 정책을 다루는 변경은 `docs/engineering-decisions.md`를 먼저 검토합니다.
- 재발, 검증 공백, agent-caused mistake가 드러난 경우 `docs/failure-history.md` 기록 여부를 계획 단계에서 판단합니다.
- 문서를 업데이트하지 않는 경우에는 계획, 최종 응답, commit note 중 한 곳에 이유를 남깁니다.

### 남은 한계

- 문서 영향도 게이트는 판단 누락을 줄이는 정책입니다. 모든 변경에 대해 모든 문서를 수정하라는 뜻은 아니므로, 에이전트가 변경 범위와 문서 역할을 계속 구분해야 합니다.
- 작은 read-only 조사만으로 끝나는 경우에는 기록하지 않아도 되지만, 조사 결과가 작업 방향이나 운영 정책을 바꾸면 다시 문서 영향도 분류를 해야 합니다.

### 검증

Local verification:

```powershell
Get-Content -Path AGENTS.md -Encoding UTF8
Get-Content -Path docs\engineering-decisions.md -Encoding UTF8
Get-Content -Path docs\failure-history.md -Encoding UTF8
rg -n "Documentation Impact Gate|Documentation impact gate|Engineering decision review" AGENTS.md docs AI_CHANGELOG.md ROADMAP.md
git diff --check
```

결과:

- `Get-Content -Encoding UTF8` rendered the new Korean and English policy text correctly.
- `rg` confirmed the new gate, engineering decision, failure-history entry, roadmap task, and changelog references.
- `git diff --check` passed with only Git line-ending warnings.

## 2026-06-09 / 2026-06-10 - Incremental source indexing tests failed in CI

분류:

- Test/CI environment
- RAG source indexing
- pgvector service dependency

관련 run:

- `https://github.com/ino5/ai-commit-advisor-26/actions/runs/27214745786/job/80353181820`
- Workflow: `CI`
- Job: `test`
- Failed step: `Run tests`
- Failed commit shown by GitHub: `1b8dd93 Document incremental source indexing operations`
- Fix commit: `140c2d2 Add database service to CI`

### 증상

GitHub Actions job page에서 `Run tests` 단계가 `Process completed with exit code 1`로 실패했습니다. 공개 페이지에서는 상세 pytest log가 로그인 없이 보이지 않았지만, job summary에는 `Run tests` 실패와 Node.js 20 deprecation warning이 함께 표시되었습니다.

Node.js 20 warning은 `actions/checkout@v4`, `actions/setup-python@v5`에 대한 GitHub Actions platform warning이었고, 이번 실패의 직접 원인은 아니었습니다.

### 직접 원인

`tests/test_incremental_source_index_service.py`가 추가되면서 source indexing test가 실제 PostgreSQL/pgvector DB를 사용하게 되었습니다.

Local 개발 환경에는 `docker-compose.yml`의 `pgvector/pgvector:pg16` 컨테이너가 떠 있었기 때문에 다음 명령이 통과했습니다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

하지만 기존 GitHub Actions workflow에는 PostgreSQL service가 없었습니다.

```yaml
steps:
  - name: Run tests
    run: python -m pytest -q
```

따라서 CI runner에서 pytest가 DB 연결 또는 migration 초기화가 필요한 테스트를 실행할 때 실패했습니다.

### 배경 또는 구조적 원인

증분 source indexing 기능은 `DocumentChunk`, `VectorItem`, pgvector column, Alembic migration 상태를 함께 다루는 기능입니다. 수정/삭제/rename 처리에서 vector cleanup을 검증하려면 순수 unit test보다 DB-backed integration test가 더 적합했습니다.

문제는 테스트의 성격이 바뀌었는데도 CI workflow의 실행 전제 조건은 Python-only 상태로 남아 있었다는 점입니다.

### 사전 검증에서 놓친 이유

로컬 검증은 실제 DB가 있는 개발 PC 기준으로 수행됐고, CI workflow의 service dependency까지 함께 검토하지 않았습니다. 테스트가 순수 unit test에서 DB-backed integration test로 확장됐는데, CI 실행 환경은 사전에 DB 없는 workflow였습니다.

### 수정 내용

`.github/workflows/ci.yml`에 pgvector PostgreSQL service를 추가했습니다.

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    env:
      POSTGRES_DB: ai_commit_advisor
      POSTGRES_USER: ai_user
      POSTGRES_PASSWORD: ai_password
    ports:
      - 5432:5432
    options: >-
      --health-cmd "pg_isready -U ai_user -d ai_commit_advisor"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
env:
  DATABASE_URL: postgresql+psycopg2://ai_user:ai_password@localhost:5432/ai_commit_advisor
  PGVECTOR_DIMENSION: "768"
  LLM_PROVIDER: mock
  EMBEDDING_PROVIDER: mock
```

이 변경으로 CI가 local test 환경과 같은 DB 전제 조건을 갖게 되었습니다. LLM과 embedding은 CI에서 외부 server에 의존하지 않도록 mock provider를 명시했습니다.

### 재발 방지 규칙

- DB, pgvector, Docker service, external API, browser, local model server가 필요한 테스트를 추가하면 같은 commit 또는 같은 change set에서 CI workflow 전제 조건도 함께 확인합니다.
- local에서 통과한 테스트라도 CI가 같은 service를 제공하는지 확인합니다.
- CI에서 외부 LLM/embedding server가 필요하지 않도록 기본 provider는 mock으로 고정합니다.
- 자동 검증 실패를 사용자가 보고하거나 agent가 확인하면 원인과 조치 내용을 이 문서에 기록합니다.
- GitHub Actions warning과 failure를 구분합니다. Warning은 별도 개선 후보로 기록하되, 실패 원인으로 단정하지 않습니다.

### 남은 한계

- GitHub Actions 상세 log는 비로그인 공개 화면에서 제한적으로만 보입니다. 가능한 경우 GitHub CLI 또는 로그인된 UI로 raw log를 확인해야 합니다.
- Node.js 20 deprecation warning은 직접 실패 원인은 아니지만, 이후 GitHub Actions runtime 변경 전에 `actions/checkout`, `actions/setup-python` 버전 또는 runner 정책을 별도 점검할 수 있습니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m compileall src tests
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

결과:

- `compileall` passed
- `pytest` passed with 78 tests
- `git diff --check` passed without whitespace errors

GitHub Actions verification:

- Fix commit `140c2d2` was pushed to `main`.
- The new workflow run was queued with the PostgreSQL service configuration.

## 2026-06-10 - GitHub hosted runner acquisition failure

분류:

- GitHub Actions platform
- CI operation
- External infrastructure

관련 run:

- Workflow: `CI`
- Run: `docs: explain RAG chat rationale #42`
- Commit shown by GitHub: `731c436`
- 증상 annotation:
  - `The job was not acquired by Runner of type hosted even after multiple attempts`
  - `Internal server error. Correlation ID: 6837253b-ba61-49c9-b3d3-ffc082e3424c`

### 증상

GitHub Actions summary에서 job duration이 약 15분으로 표시됐지만, 실제 실패 annotation은 test command나 pytest assertion이 아니라 hosted runner 배정 실패와 GitHub internal server error였습니다.

### 직접 원인

GitHub-hosted runner가 job을 가져가지 못했습니다. 이 경우 repository code, workflow step, dependency 설치, pytest 결과와 무관하게 GitHub Actions platform 단계에서 실패할 수 있습니다.

### 배경 또는 구조적 원인

CI workflow는 GitHub-hosted `ubuntu-latest` runner에 의존합니다. Runner pool 또는 GitHub Actions service에 일시적인 문제가 있으면 workflow file이 올바르고 local verification이 통과해도 job이 시작되지 못할 수 있습니다.

### 사전 검증에서 놓친 이유

Local verification은 code와 test 실행 가능성을 확인하지만, GitHub-hosted runner acquisition 자체는 local에서 재현하거나 사전에 검증할 수 없습니다.

### 수정 내용

`.github/workflows/ci.yml`에 `workflow_dispatch`를 추가했습니다. 이제 push 없이도 Actions UI에서 CI를 수동 재실행할 수 있습니다.

```yaml
on:
  push:
  pull_request:
  workflow_dispatch:
```

### 재발 방지 규칙

- Annotation이 runner acquisition, internal server error, GitHub platform error를 가리키면 code/test failure로 단정하지 않습니다.
- 먼저 같은 commit에서 workflow를 rerun하거나 `workflow_dispatch`로 수동 실행합니다.
- 반복되면 GitHub status와 Actions service 상태를 확인합니다.
- `Run tests`, `Compile Python files`, dependency install 같은 실제 step log가 실패한 경우에만 code, test, workflow dependency 문제로 조사합니다.

### 남은 한계

- GitHub-hosted runner 장애는 repository 안에서 완전히 방지할 수 없습니다.
- `workflow_dispatch`는 재실행 편의를 높일 뿐, GitHub platform 장애 자체를 해결하지는 않습니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m compileall src app.py
.\.venv\Scripts\python.exe -m pytest -q
```

결과:

- `compileall` passed
- `pytest` passed with 80 tests

## 2026-06-10 - Docker app could not verify host Git repository paths

분류:

- Docker deployment
- Project Chat/RAG source verification
- Screenshot verification

관련 기능:

- Docker app service
- Project Chat persisted history screenshot
- `docs/images/features/project-chat.png`

### 증상

Docker app(`http://localhost:8501`)에서 Project Chat 캡처를 갱신했을 때, 샘플 프로젝트의 `결제금액 검증은 어디에서 수행되나요?` 질문에 대해 원래 답변이 가능해야 하는데 `현재 검증된 소스 근거만으로는 답변하기 어렵습니다`가 표시됐습니다.

Project Chat status도 Current HEAD가 `-`로 보이고 source_file chunk 70건이 `검증 불가`로 표시됐습니다.

### 직접 원인

DB에 저장된 프로젝트 Git 경로는 Windows host 기준 `C:\dev\ai-advisor-sample-shop`였습니다. 그러나 Docker app 컨테이너는 Linux filesystem에서 실행되므로 해당 경로를 직접 읽을 수 없었습니다.

그 결과 Git HEAD 확인, source_file line 검증, Project Chat source verification이 모두 실패했습니다.

### 배경 또는 구조적 원인

Docker 배포 기능을 추가하면서 PostgreSQL과 Streamlit app 실행은 컨테이너화했지만, 앱이 분석 대상 로컬 Git 저장소를 어떻게 읽을지는 명시하지 않았습니다. 로컬 Python 실행에서는 Windows 경로가 바로 동작했기 때문에 이 차이가 캡처 검증 전까지 드러나지 않았습니다.

### 사전 검증에서 놓친 이유

Docker smoke check는 Streamlit health endpoint와 DB migration 성공만 확인했습니다. Project Chat이 실제 host Git repository file을 읽어 source_file chunk를 검증하는 흐름은 Docker 컨테이너 기준으로 확인하지 않았습니다.

### 수정 내용

Docker app에 host repo mount와 path mapping을 추가했습니다.

```yaml
volumes:
  - C:/dev:/host-dev:ro
environment:
  REPO_PATH_HOST_PREFIX: "C:\\dev"
  REPO_PATH_CONTAINER_PREFIX: /host-dev
```

앱은 DB에 저장된 `C:\dev\...` 경로를 파일 접근 시 `/host-dev/...`로 변환합니다. 이 변환은 Git 명령, source_file 인덱싱, source verification, Project Chat current source 검증에 적용됩니다.

또한 Python slim base image에는 Git binary가 기본 포함되어 있지 않으므로 Dockerfile에 `git` 설치를 추가했습니다. Git Sync와 현재 HEAD 확인은 GitPython만으로는 충분하지 않고 컨테이너 안의 `git` command가 필요합니다.

### 재발 방지 규칙

- Docker 앱에서 RAG 또는 Project Chat을 검증할 때는 health endpoint뿐 아니라 Current HEAD와 source_file verification 상태를 확인합니다.
- DB에 저장된 repo path가 host OS 경로라면 컨테이너 mount와 path prefix mapping이 함께 설정되어야 합니다.
- Project Chat 캡처는 단순 UI 표시뿐 아니라 실제 답변 근거가 정상인지 확인한 뒤 갱신합니다.

### 남은 한계

- 기본 Compose 설정은 `C:/dev` 아래 저장소를 대상으로 합니다. 다른 drive나 directory를 쓰는 환경에서는 mount와 `REPO_PATH_*` 환경 변수를 변경해야 합니다.
- 읽기 전용 mount이므로 컨테이너에서 대상 repo 파일을 수정하는 기능에는 적합하지 않습니다. 현재 Git Sync/RAG/Project Chat 검증은 읽기 작업이므로 충분합니다.

### 검증

Local verification:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/utils/config.py src/utils/repo_path.py src/services/git_service.py src/rag/source_verifier.py src/rag/source_index_service.py src/rag/chunker.py
.\.venv\Scripts\python.exe -m pytest tests/test_repo_path.py tests/test_source_file_rag.py tests/test_source_index_service.py tests/test_project_chat_service.py -q
docker compose config
docker compose up -d --build app
```

Docker verification:

- app container can read `/host-dev/ai-advisor-sample-shop`
- Project Chat source index status shows Current HEAD matching Indexed HEAD for the sample project

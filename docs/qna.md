# Q&A

## Q. AI는 어느 단계에서 어떻게 활용됐나?

이 프로젝트에서 AI는 `LLM`과 `Embedding model` 두 종류로 나뉩니다. LLM은 commit이나 코드의 의미를 해석하고 문장을 생성하며, Embedding model은 텍스트를 vector로 바꿔 관련 근거를 찾습니다. 모든 단계에서 모델을 호출하는 것은 아니며, 전체 흐름은 다음과 같습니다.

```text
개발계획 등록 + Git Sync                    모델 호출 없음
             ↓
RAG chunk 생성                              모델 호출 없음
             ↓
검색 준비·질의 vector 생성                  Embedding model
             ↓
프로그램-commit 후보 검색                   Embedding + token 규칙
             ↓
Mapping                                     LLM
             ↓
프로그램 구현상태 분석                      LLM
             ↓
AI Progress · Risk · 예상 일정 · Radar      규칙 계산, 새 모델 호출 없음
             ↓
PL Briefing                                 LLM
```

단계별 역할은 다음과 같습니다.

| 단계 | 모델 사용 여부 | 실제 처리 |
|---|---|---|
| 개발계획 등록 | 없음 | 프로그램 ID, 설명, 계획 일정, 계획 진척도와 담당자를 구조화해 저장합니다. |
| Git Sync | 없음 | Git에서 commit, 메시지, 작성자, 변경 파일과 diff를 수집해 PostgreSQL에 저장합니다. |
| RAG chunk 생성 | 없음 | 현재 소스, 프로그램, commit과 diff 텍스트를 검색 단위로 나누고 metadata를 저장합니다. 이 시점에는 아직 vector를 만들지 않습니다. |
| 검색 준비 | Embedding | vector가 없는 chunk만 `text-embedding-nomic-embed-text-v2-moe`로 변환해 pgvector에 저장합니다. Git Sync 직후 자동 호출하지 않고 사용자가 검색 준비를 실행할 때 처리합니다. |
| Mapping 후보 검색 | Embedding + 규칙 | commit 메시지·변경 파일·diff를 query vector로 바꿔 유사한 `program` chunk를 찾습니다. 프로그램명·모듈·파일 경로의 token 유사도 후보도 합칩니다. Embedding 검색이 실패하면 token 후보만 사용합니다. |
| 프로그램-commit Mapping | LLM | 후보 프로그램이 있을 때 commit 정보와 후보 프로그램만 prompt에 넣어 관련 프로그램, 관련도 점수, commit 단위 구현상태와 근거를 JSON으로 받습니다. 후보가 없으면 호출하지 않고, 호출·파싱 실패 시 token 유사도 규칙으로 fallback합니다. |
| 프로그램 구현상태 분석 | LLM | 관련 commit이 있을 때 프로그램 계획과 commit·Mapping 근거를 종합해 `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `UNKNOWN`, 완료·미완료 항목과 근거 commit을 구조화해 저장합니다. 입력은 관련도순 최대 10개 commit과 commit당 최대 12개 변경 파일로 제한하며, 관련 commit이 없거나 호출에 실패하면 보수적인 규칙 결과를 사용합니다. |
| `AI Progress` 표시 | 새 호출 없음 | 저장된 프로그램 구현상태를 `0/50/100` 진척도로 환산하고 계획 진척도와 비교합니다. 관련 commit 구성이 바뀌었으면 기존 분석을 `재분석 필요`로 표시합니다. 화면을 조회하는 것만으로 LLM을 다시 호출하지 않습니다. |
| `Risk Analysis` | 새 호출 없음 | 관련 commit 없음, 계획 종료일 경과, 진척도 차이, 판단불가, 최근 commit 없음, 담당자 누락, 예상 지연을 규칙으로 판정합니다. Mapping과 구현상태라는 AI 결과를 입력으로 사용하지만 리스크 자체는 LLM이 단정하지 않습니다. |
| 예상 일정·자원 지표 | 새 호출 없음 | 계획일, AI 진척도, commit·diff 규모, 리스크를 산식으로 결합해 예상 종료일, 난이도와 관리 부담을 계산합니다. |
| `AI Resource Radar` | 새 호출 없음 | 앞 단계의 AI 결과와 규칙 지표를 고정 가중치로 합산해 PL 우선 검토 순위를 만듭니다. |
| `PL Briefing` | LLM | live provider에서 Radar 상위 항목의 점수와 근거만 전달해 요약, 회의 질문과 다음 액션을 JSON으로 생성합니다. 순위는 LLM이 바꾸지 않으며, `mock`이나 호출·검증 실패 시 규칙 기반 브리핑을 사용합니다. |

`Project Chat`, Knowledge Graph와 코드리뷰는 위 자원관리 흐름에서 갈라지는 별도 AI 사용 경로입니다.

| 기능 | 모델 사용 여부 | 실제 처리 |
|---|---|---|
| Knowledge Graph 동기화 | 없음 | 저장된 프로젝트·프로그램·commit·파일 데이터와 현재 Java 소스 parser 결과로 Neo4j node와 관계를 만듭니다. LLM이 관계를 추출하지 않습니다. |
| `Project Chat` 검색 | Embedding | 질문과 확장 질의를 vector로 만들고 pgvector에서 관련 소스 청크를 검색합니다. |
| `Project Chat` 근거 준비 | 없음 | 검색한 소스를 현재 파일·라인·hash와 비교하고, 검증된 파일과 class를 시작점으로 Neo4j 관계를 조회합니다. |
| `Project Chat` 답변 | LLM | 검증된 소스와 GraphRAG 관계를 context로 전달해 한국어 답변을 만듭니다. 검증된 현재 소스가 하나도 없으면 LLM을 호출하지 않고 근거 부족으로 종료합니다. |
| `AI Code Review` | LLM | live provider와 비어 있지 않은 diff가 있을 때 사용자가 고른 commit의 메시지와 diff를 전달해 변경 의도, 영향 범위, 위험도, 버그 후보와 리팩토링 제안을 구조화 JSON으로 생성합니다. 빈 diff나 `mock`, 호출 실패는 별도 결과로 표시합니다. |
| `AI 운영 현황`·품질 점검 | 새 호출 없음 | 저장된 provider/model, fallback, validation, latency, source·graph evidence와 결과 분포를 집계해 보여줍니다. |

정리하면 LLM 호출 지점은 `Mapping`, 프로그램 구현상태 분석, `Project Chat` 답변, `AI Code Review`, `PL Briefing`입니다. Embedding 호출 지점은 문서 vector 준비와 Mapping/RAG/Project Chat의 query 검색입니다. `Risk Analysis`, `AI Progress` 화면, 예상 일정, Resource Radar와 Knowledge Graph 구성은 애플리케이션 규칙과 검증 로직이 담당합니다.

이 분리는 LLM이 잘하는 의미 해석과 문장 생성을 활용하면서도 일정·리스크·우선순위처럼 설명 가능성과 재현성이 필요한 판단은 코드로 통제하기 위한 것입니다. 준비된 시연 환경에서는 두 모델 모두 외부 cloud가 아닌 LM Studio에서 실행되므로 프로젝트 코드와 diff가 외부 서비스로 전달되지 않습니다.

## Q. 현재 프로젝트에 연결된 AI 모델은 무엇이며, LLM 성능은 어느 정도인가?

2026년 7월 23일 실제 실행 환경을 확인한 결과, 외부 cloud AI가 아니라 LM Studio의 OpenAI-compatible API에 연결된 두 개의 local model을 사용하고 있습니다.

- LLM: `qwen2.5-coder-7b-instruct`
- Embedding: `text-embedding-nomic-embed-text-v2-moe`

`qwen2.5-coder-7b-instruct`는 프로그램-commit Mapping, 프로그램 구현상태 분석, `Project Chat`, `AI Code Review`와 PL Briefing 생성에 사용합니다. `text-embedding-nomic-embed-text-v2-moe`는 답변을 생성하는 LLM이 아니라, 소스·프로그램·commit·diff 청크와 질문을 768차원 vector로 변환해 RAG 검색 및 Mapping 후보 검색에 사용하는 모델입니다.

두 모델은 host의 LM Studio `12345` 포트에서 실행됩니다. 로컬 Python은 `http://127.0.0.1:12345/v1`, Docker 앱은 `http://host.docker.internal:12345/v1`로 같은 서버에 접근합니다. Docker 환경변수와 LM Studio의 실제 로드 목록, Chat·Embedding 시험 호출에서 위 model 연결을 확인했습니다. Neo4j와 PostgreSQL/pgvector는 AI model이 아니라 각각 GraphRAG 관계 저장소와 RAG 청크·vector 저장소입니다.

### 현재 LLM 실행 설정

| 항목 | 현재 값 | 의미 |
|---|---|---|
| Model | `Qwen2.5-Coder-7B-Instruct` | 코드 생성·추론·수정에 맞춰 학습한 instruction model |
| Parameter | 7.61B | 공식 model card 기준. 일반적으로 14B·32B보다 가볍지만 복잡한 추론 능력도 더 제한적임 |
| 실행 파일 | `qwen2.5-coder-7b-instruct-q4_k_m.gguf` | LM Studio에서 사용하는 GGUF 양자화본 |
| Quantization | `Q4_K_M`, 4-bit | 파일 크기 약 4.68 GB로 줄여 8 GB VRAM급 PC에서 실행하기 쉬운 대신 원본 BF16보다 일부 품질 손실 가능 |
| 실제 context length | 8,192 tokens | 모델의 최대 표기 길이와 별개로 현재 LM Studio가 한 요청에 허용하는 실효 상한 |
| 생성 설정 | `temperature=0.1`, non-streaming | 결과 변동을 낮추고 전체 응답이 끝난 뒤 한 번에 받음 |
| 기능별 최대 출력 | Mapping 350, 구현상태·Chat·Briefing 900, Code Review 1,200 tokens | 필요 이상으로 긴 응답과 대기시간을 제한 |
| LM Studio 병렬도 | `parallel=1` | 동시에 여러 요청이 들어오면 한 번에 하나를 생성하고 나머지는 대기 |
| 점검 PC | RTX 3060 Ti 8 GB, i5-12400F | 응답시간은 이 hardware와 당시 부하를 기준으로 한 값 |

공식 Qwen 자료에서 이 모델은 7.61B parameter의 code-specific instruction model이며, code generation·reasoning·repair를 주요 평가 대상으로 삼습니다. 현재 사용하는 것은 `Q4_K_M` 양자화본이고 앱은 context를 8,192로 제한하므로, 공식 최대 context나 원본 precision benchmark를 현재 앱 성능으로 그대로 해석하면 안 됩니다. 자세한 사양은 [Qwen 공식 GGUF model card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF)와 [Qwen2.5-Coder Technical Report](https://arxiv.org/abs/2409.12186)를 기준으로 확인할 수 있습니다.

### 이 프로젝트에서 관찰한 응답 성능

2026년 7월 23일 `Sample Shop Demo` 프로젝트의 `ai_invocation_logs`에서 현재 provider와 model이 일치하는 저장 호출을 집계한 결과입니다. 시간은 순수한 model token 생성 속도가 아니라 각 기능이 기록한 전체 호출 처리시간이며, 표본이 적은 기능은 일반화하기 어렵습니다.

| 기능 | 완료 호출 | 유효 시간 표본 | 중앙값 | 범위 | 보정·fallback |
|---|---:|---:|---:|---:|---:|
| Commit Mapping | 48/48 | 45 | 1.29초 | 0.34~11.69초 | 0건 |
| AI Code Review | 5/5 | 5 | 4.28초 | 2.37~13.14초 | 한국어 표현 보정 1건 |
| PL Briefing | 2/2 | 2 | 6.29초 | 5.11~7.47초 | 0건 |
| Project Chat | 7/7 | 7 | 7.21초 | 2.41~10.31초 | 현재 소스 근거 기반 deterministic repair 1건 |

기록된 62회 호출은 모두 `completed`이고 model 연결 실패는 0건이었습니다. 다만 `completed`는 호출·저장 절차가 끝났다는 뜻이지 답변 내용이 모두 정답이라는 뜻은 아닙니다. 2건은 model 초안을 그대로 쓰지 않고 애플리케이션이 표현이나 근거를 보정했습니다.

Mapping 시간 기록 3건은 `finished_at`이 `started_at`보다 앞선 음수 값이어서 표에서 제외했습니다. 현재 telemetry가 monotonic timer가 아니라 시스템 시각 차이로 시간을 계산하므로, 실행 중 PC 시계가 보정되면 이런 값이 생길 수 있습니다. 또한 `prompt_length`와 `response_length`는 token 수가 아니라 Python 문자열 길이이므로 현재 기록만으로 tokens/sec를 계산할 수 없습니다. 프로그램 구현상태 분석도 같은 LLM을 사용하지만 별도 `AIInvocationLog` latency를 남기지 않아 위 표에는 없습니다.

### 성능을 어떻게 평가해야 하는가

- 강점: 7B Q4 모델이라 한 대의 개발 PC에서 외부 전송 없이 실행할 수 있고, 코드·diff를 제한된 근거와 함께 분석하는 Mapping과 Code Review에 맞습니다. 낮은 temperature와 JSON Schema가 출력 형식을 안정화합니다.
- 한계: 7B·4-bit 모델은 큰 모델보다 복잡한 다단계 추론, 긴 변경 이력 종합, 미묘한 한국어 표현에서 오류가 날 가능성이 큽니다. context 8,192 제한 때문에 저장소 전체를 한 번에 읽지 않고 후보와 근거를 잘라 전달합니다.
- 품질 보호: RAG source 검증, 후보 제한, JSON parsing·validation, deterministic repair·fallback, 사람의 Mapping feedback을 함께 사용합니다. LLM 단독 판단을 확정값으로 사용하지 않습니다.
- 아직 말할 수 없는 값: 이 프로젝트에는 정답 label이 붙은 Mapping·리뷰 평가 세트와 반복 benchmark가 없으므로 의미 정확도, 재현율, hallucination 비율을 퍼센트로 제시할 수 없습니다. 공식 코드 benchmark 결과도 이 프로젝트의 업무 프로그램 Mapping 정확도를 직접 증명하지 않습니다.

따라서 현재 모델은 “시연과 소규모 프로젝트에서 수 초 안에 근거 기반 분석 초안을 만드는 local LLM”으로 보는 것이 정확합니다. 대규모 저장소, 동시 사용자, 높은 정확도가 필요한 운영 환경에서는 14B·32B급 모델 비교, hardware별 반복 측정, 정답 데이터 기반 기능별 평가가 추가로 필요합니다.

## Q. 프론트엔드·백엔드·DB 기술 스택은 무엇이며, Streamlit이 백엔드 framework 역할도 하나?

결론부터 말하면 맞습니다. 이 프로젝트에서 `Streamlit 1.41.1`은 브라우저 화면을 구성하는 UI framework이자, Python server를 띄우고 HTTP·WebSocket 연결, 사용자 session, widget event, script rerun과 화면 갱신 protocol을 처리하는 백엔드 web application framework·server runtime 역할도 합니다.

다만 Streamlit이 백엔드 framework 역할을 한다는 말과 업무 로직 전부가 Streamlit 코드로 작성됐다는 말은 다릅니다. `Python 3.11 service layer`는 framework 이름이 아니라 `src/services/`와 `src/rag/`에 분리한 일반 Python 함수·class 모듈입니다. Streamlit은 web 연결·session·실행 주기를 담당하고, 이 service layer는 Mapping·RAG·Code Review 같은 업무 로직을 담당합니다. Streamlit page가 service 모듈을 import해 같은 app process에서 직접 호출하므로 두 계층 사이에 REST API나 JSON 통신은 없습니다.

따라서 “프론트엔드는 Streamlit, 백엔드는 Python 3.11 service layer”라고만 적으면 오해의 소지가 있습니다. 더 정확한 표현은 “web application framework·server runtime은 Streamlit, 업무 백엔드는 일반 Python service 모듈”입니다. React 같은 별도 frontend project와 FastAPI·Flask·Django 기반 API backend는 없습니다. Browser에 로드되는 frontend client도 이 repository에서 별도로 개발한 코드가 아니라 Streamlit이 제공합니다.

호출 흐름은 다음과 같습니다.

```text
Browser
  ⇅ Streamlit의 내장 web 연결
Streamlit server (`streamlit run app.py`)
  → `app.py`가 선택한 `src/ui/*_page.py` render 함수 실행
  → widget event 발생 시 `app.py`부터 선택된 page render 함수까지 rerun
  → `src/services/*` 또는 `src/rag/*` 함수·class 직접 호출
  → SQLAlchemy / Neo4j driver / GitPython / LLM·Embedding HTTP 호출
  → 결과를 같은 page 실행에서 Streamlit component로 렌더링
```

“Python page를 다시 실행한다”는 말은 Streamlit server, Python process 또는 Docker container를 재시작한다는 뜻이 아닙니다. 서버 process와 browser tab의 session은 계속 유지되고, 해당 사용자 session을 위한 Python script 실행만 새로 시작합니다. “page rerun”은 짧게 표현한 말이고, 이 repository에서는 엄밀히 `app.py`가 위에서 아래로 다시 실행된 뒤 현재 menu가 선택한 `render_*_page()` 함수를 다시 호출한다는 뜻입니다. 이 repository는 `st.fragment`를 사용하지 않으므로 현재는 page 일부만 부분 rerun하지 않습니다.

분석 버튼을 누를 때의 실제 순서는 다음과 같습니다.

1. Browser가 버튼 event를 Streamlit server에 전달합니다.
2. Streamlit이 그 browser tab의 widget value와 `st.session_state`를 반영하고 `app.py`를 위에서부터 다시 실행합니다.
3. `app.py`가 session state에 저장된 현재 menu를 읽고, 선택된 page의 render 함수를 호출합니다.
4. 해당 실행에서만 `st.button(...)`이 `True`를 반환하므로 버튼 아래의 service 호출 분기에 진입합니다.
5. Service 함수가 같은 Python process에서 동기적으로 실행되고, 반환된 결과를 `st.dataframe`, `st.metric` 등으로 다시 구성해 browser에 보냅니다.

따라서 rerun때 일반 Python local variable은 새로 계산되지만, 다음 상태까지 모두 초기화되는 것은 아닙니다.

- `st.session_state`에 넣은 현재 project, menu, chat session 같은 값은 같은 browser tab session의 rerun 사이에 유지됩니다.
- PostgreSQL·Neo4j에 저장한 데이터와 Git repository, 로컬 LLM server 상태는 page rerun과 무관하게 남습니다.
- 다른 사용자나 다른 browser tab의 session을 재시작하지 않습니다.
- `st.form` 안의 입력은 각 필드를 바꿀 때마다 rerun하지 않고, submit 버튼을 눌렀을 때 모은 값을 함께 전달하며 한 번 rerun합니다.
- `st.rerun()`을 명시적으로 호출하면 현재 실행을 그 지점에서 멈추고 즉시 다시 시작합니다. 이 앱의 menu button은 선택 page를 `st.session_state`에 저장한 뒤 `st.rerun()`해 새 page를 그립니다.

### Thread는 누가 관리하는가?

Thread 생성·종료와 session 연결은 앱 코드가 아니라 Streamlit runtime이 관리합니다. Streamlit Python process 안에는 HTTP·WebSocket 연결을 담당하는 Tornado server thread와 page 코드를 실행하는 script thread가 있습니다. Browser tab마다 독립 session이 만들어지고, 최초 접속과 각 rerun은 그 session에 속한 script thread에서 실행됩니다.

```text
Streamlit Python process
├─ Tornado server thread: HTTP·WebSocket·session event 처리
├─ Browser tab A → Session A → script thread A-1, rerun 시 A-2, ...
└─ Browser tab B → Session B → script thread B-1, rerun 시 B-2, ...
```

이 repository는 `threading.Thread`, `ThreadPoolExecutor`, `asyncio`, Celery·RQ 같은 background worker를 사용하지 않습니다. Mapping·RAG·Code Review service는 Streamlit이 할당한 현재 script thread에서 일반 Python 함수로 순차 실행됩니다. LLM·embedding HTTP 요청도 `urlopen(..., timeout=120)`의 동기 호출이므로 응답이 올 때까지 해당 script thread가 기다립니다.

다른 browser tab이나 사용자는 별도 session의 script thread를 사용하므로 여러 session 실행이 같은 Python process에서 겹칠 수는 있습니다. 다만 이것은 앱이 분석 job을 thread pool에 나누어 병렬 처리한다는 뜻은 아닙니다. Python CPU 작업은 GIL과 host 자원의 영향을 받고, PostgreSQL·Neo4j·LM Studio 같은 외부 자원도 여러 session이 함께 사용하면 경합할 수 있습니다.

공유 자원의 thread 경계는 다음과 같습니다.

- SQLAlchemy `engine`은 process 전역에 하나만 있고 기본 `QueuePool`로 PostgreSQL connection을 재사용합니다. 별도 pool size tuning은 하지 않았습니다.
- ORM `Session`은 thread 사이에 공유하지 않습니다. Page·service가 필요한 작업마다 `with SessionLocal() as db:`로 새 `Session`을 만들고 끝나면 닫습니다.
- Neo4j는 각 graph 작업에서 driver와 session을 context manager로 열고 닫습니다. LLM과 embedding client도 필요한 service 실행에서 생성해 호출합니다.
- `src/db/init_db.py`의 `_INIT_LOCK`은 예외적인 thread 보호 장치입니다. 여러 session이 동시에 접속해도 같은 process에서 Alembic migration을 한 번만 실행하도록 합니다. Mapping 등 일반 분석 작업을 직렬화하는 lock은 아닙니다.

현재는 project별 분석 job queue, 전역 semaphore, 실행 취소, worker 수 제한을 담당하는 공통 concurrency manager가 없습니다. 두 session이 같은 project에서 긴 분석을 동시에 시작하면 실행이 겹치고 DB connection pool과 LM Studio 자원을 경쟁할 수 있습니다. 동시 사용자가 많아지거나 긴 작업의 재시도·취소·상태 조회가 필요하면 Streamlit script thread에서 분리한 job table과 worker queue를 두는 구조가 필요합니다. `_INIT_LOCK`도 process-local이므로 app process를 여러 개 띄우는 배포의 중복 migration까지 막지는 못합니다.

예를 들어 Mapping 화면에서 사용자가 분석 버튼을 누르면 브라우저가 별도 `/api/mapping` REST endpoint를 호출하는 것이 아닙니다. Streamlit이 해당 session의 Python script를 다시 실행하고, `src/ui/mapping_page.py`가 `SessionLocal()`로 DB session을 만든 뒤 `MappingService().analyze_commits(...)`를 일반 Python method처럼 직접 호출합니다. 분석 결과가 반환되면 같은 실행 흐름에서 `st.dataframe`, `st.metric` 등으로 화면을 갱신합니다.

따라서 “백엔드도 Streamlit인가?”에 대한 답은 “web framework·runtime 관점에서는 맞고, 업무 service 코드까지 Streamlit이라고 부르는 것은 부정확하다”입니다.

- Web server, browser 연결, widget event, 사용자 session과 Python script 실행은 Streamlit이 담당합니다.
- 입력 검증과 service 호출 조정은 `app.py`와 `src/ui/*.py`, 업무·AI 로직은 `src/services/*.py`와 `src/rag/*.py`가 담당합니다. 모두 같은 Streamlit app process 안에서 실행됩니다.
- 외부 client가 호출할 REST API backend나 Streamlit과 독립적으로 배포·확장할 backend process는 없습니다.
- PostgreSQL과 Neo4j는 별도 server/container이며, 브라우저가 직접 접속하지 않고 Streamlit server 안의 Python 코드가 접속합니다.

기술을 실행 역할별로 정리하면 다음과 같습니다.

| 영역 | 주요 기술 | 역할 |
|---|---|---|
| Browser frontend client | Streamlit 제공 frontend | Python 코드의 component 결과를 표시하고 widget event를 server에 전달. 별도 frontend project 없음 |
| Web application framework·server runtime | `Streamlit 1.41.1` | HTTP·WebSocket, widget event, session state, script thread·rerun과 화면 갱신 protocol 처리 |
| Server-side UI·controller 계층 | `app.py`, `src/ui/*.py` | 메뉴·form·table 구성, 입력 검증과 service 호출 조정 |
| 업무 백엔드·service 계층 | `Python 3.11`, `src/services/*.py`, `src/rag/*.py` | Git Sync, Mapping, Risk Analysis, RAG, Project Chat, Code Review와 Graph 동기화 처리. framework가 아닌 일반 Python 모듈 |
| 시각화 | `Plotly 5.24.1`, `streamlit-agraph 0.0.45` | Dashboard chart와 Knowledge Graph 관계도 표시 |
| 데이터 화면·Excel | `pandas 2.2.3`, `openpyxl 3.1.5` | 표 데이터 처리와 Excel 업로드·다운로드 |
| ORM·설정 | `SQLAlchemy 2.0.36`, `pydantic-settings 2.7.1` | DB model·transaction과 환경변수 기반 설정 관리 |
| Git 연동 | `GitPython 3.1.43` | 대상 저장소의 commit, 변경 파일과 diff 수집 |
| 기본 DB | `PostgreSQL 16` | 프로젝트, 프로그램, Git 데이터, 분석 결과, 대화와 운영 이력 저장 |
| Vector DB 기능 | PostgreSQL의 `pgvector 0.3.6` | RAG embedding vector 저장과 cosine 유사도 검색 |
| Graph DB | `Neo4j 5 Community` | 프로그램–commit–파일–class–domain 관계를 GraphRAG read model로 저장 |
| DB migration | `Alembic 1.14.0` | PostgreSQL schema version 관리 |
| DB driver | `psycopg2-binary 2.9.10`, `neo4j 6.2.0` | Python에서 PostgreSQL과 Neo4j 연결 |
| 실행 환경 | Docker, Docker Compose | Streamlit app, PostgreSQL과 Neo4j를 분리된 container로 실행 |

Docker에서도 `app` container는 `streamlit run app.py` 하나만 실행합니다. 별도 backend container는 없습니다. 이 구조는 한 저장소 안에서 화면과 분석 workflow를 빠르게 구현하기에는 단순하지만, 외부 client용 API, 독립적인 backend 배포, background job queue 또는 수평 확장이 필요해지면 FastAPI 같은 API 계층과 worker를 별도로 분리해야 합니다. 현재 긴 분석 작업은 Streamlit page 실행 안에서 동기적으로 service를 호출하는 구조입니다.

핵심 저장소는 PostgreSQL입니다. 업무 데이터와 AI 분석 결과뿐 아니라 RAG 청크와 vector도 PostgreSQL에 저장합니다. Neo4j는 원본 데이터의 source of truth가 아니라 PostgreSQL과 현재 Java 소스에서 만든 관계 탐색용 read model입니다.

## Q. 커밋 내용만으로 어떻게 관련 프로그램 후보를 찾나?

여기서 커밋 내용은 커밋 메시지만 의미하지 않습니다. 커밋 해시, 메시지, 작성자, 변경 파일 경로와 diff 일부를 하나의 검색 질의로 구성합니다. 현재 구현은 최대 20개 변경 파일 경로와 최대 3개 파일의 diff 일부를 포함하고, 전체 질의 길이도 제한해 과도한 입력을 막습니다.

이 질의를 embedding으로 변환한 뒤 같은 프로젝트의 `program` 청크와 vector 유사도를 비교합니다. `program` 청크에는 프로그램 ID, 프로그램명, 모듈, 화면명과 설명이 들어 있습니다. 유사도가 높은 프로그램을 최대 10개 후보로 가져옵니다.

Vector 검색만 사용하지는 않습니다. 프로그램 정보와 커밋 메시지·파일 경로·diff의 단어가 얼마나 겹치는지도 계산하고, 모듈명이나 프로그램명이 파일 경로에 포함되면 가중치를 더합니다. Vector 검색 결과를 먼저 후보 목록에 넣고, 남은 자리를 token·파일 경로 후보로 채우면서 중복을 제거합니다. 두 점수를 가중 평균해 다시 순위를 매기는 방식은 아닙니다. LLM은 이 후보 안에서 실제 관련 프로그램, 관련도 점수, 구현상태와 판단 근거를 결정합니다.

### 파일 경로 유사도 후보는 어떻게 계산하는가

현재 구현에서 “파일 경로 유사도”는 두 경로 사이의 편집거리나 경로 전용 embedding을 뜻하지 않습니다. `_candidate_score()`가 프로그램 정보와 commit 정보의 token 겹침을 계산한 뒤, 변경 파일 경로에 모듈명이나 프로그램명 일부가 들어 있으면 보너스를 더하는 규칙 기반 점수입니다.

```text
program_tokens = tokens(
  program_id + program_name + module + screen_name + description
)

commit_tokens = tokens(commit message)
              ∪ tokens(모든 변경 파일 경로)
              ∪ tokens(각 파일 diff의 앞 3,000자)

base_score = floor(
  |program_tokens ∩ commit_tokens| / |program_tokens| × 100
)

각 변경 파일 경로마다
  module 문자열이 경로에 포함됨             → +20
  program_name을 공백으로 나눈 단어가 포함됨 → +10

candidate_score = min(base_score + 경로 보너스, 100)
```

#### 여기서 token은 무엇인가

여기서 `token`은 LLM이 prompt 길이·과금 계산에 사용하는 모델별 tokenizer token이 아닙니다. Mapping 후보를 빠르게 비교하기 위해 `_tokens()`가 문자열에서 정규식으로 잘라낸 검색용 단어 조각입니다. Embedding model과 LLM은 입력을 처리할 때 각자의 tokenizer를 별도로 사용하며, 이 집합에는 그 결과가 들어오지 않습니다.

`_tokens()`는 문자열을 소문자로 바꾼 뒤 영문·숫자·한글이 2자 이상 연속된 부분을 찾습니다. `/`, `.`, `_`, `-`, 공백 같은 문자는 경계가 됩니다. 결과는 `set`이므로 같은 token이 반복돼도 한 번만 세며, `src`, `main`, `java`, `html`, `class`, `public`, `private`, `return`, `null`은 제외합니다.

```text
"src/auth/login_service.py"
→ src, auth, login, service, py
→ stop word인 src 제외
→ {auth, login, service, py}

"결제 승인 결제"
→ {결제, 승인}      # 반복된 결제는 한 번만 유지

"PaymentService.java"
→ {paymentservice} # CamelCase는 payment와 service로 나누지 않음
```

프로그램 쪽에서는 프로그램 ID·이름·모듈·화면명·설명에서 만든 token 집합을 사용하고, commit 쪽에서는 메시지·변경 파일 경로·diff에서 만든 token 집합을 사용합니다. 두 집합에 같은 문자열이 있으면 겹치는 token으로 셉니다. 예를 들어 양쪽에 `login`이 있으면 1개가 겹치지만 `로그인`과 `login`은 서로 다른 token이므로 겹치지 않습니다.

기본 점수의 분모가 전체 합집합이 아니라 `program_tokens` 수이므로 이 값은 Jaccard 유사도나 확률이 아니라 “프로그램 정보의 token을 commit이 얼마나 포함하는가”에 가까운 휴리스틱 점수입니다.

예를 들어 프로그램명이 `Login API`, 모듈이 `auth`이고 commit에 `src/auth/login_service.py`가 있으면, 경로의 `auth` 때문에 20점, 프로그램명 단어 `login` 때문에 10점이 더해집니다. 여기에 commit 메시지·경로·diff에서 겹친 token의 기본 점수를 합칩니다. 점수가 0인 프로그램은 제외하고, 나머지는 점수 내림차순으로 정렬해 token·파일 경로 후보를 만듭니다.

Vector 후보와 합칠 때는 vector 후보를 먼저 넣고, 같은 프로그램을 건너뛰면서 token·파일 경로 후보를 TOP N의 남은 자리에 추가합니다. 따라서 vector 후보가 이미 N개를 채우면 규칙 기반 후보는 추가되지 않으며, vector 점수와 위 `candidate_score`를 하나의 점수로 합산하지도 않습니다. Vector 검색이 실패하면 규칙 기반 후보만 사용합니다.

이 규칙에는 다음 한계가 있습니다.

- 경로 포함 여부는 단순 substring 비교이므로 디렉터리 구간 경계나 CamelCase 의미를 해석하지 않습니다. 예를 들어 짧은 이름이 다른 단어 안에 우연히 포함될 수 있습니다.
- 프로그램명이 한글이고 경로가 영문인 경우처럼 표기가 다르면 경로 보너스를 받기 어렵습니다.
- 보너스는 변경 파일마다 반복해서 더해지므로 일치하는 파일이 여러 개면 100점 상한에 빨리 도달할 수 있습니다.
- 프로그램 정보를 label이 포함된 문자열로 만든 뒤 token화하므로 `program`, `name`, `module` 같은 label token도 현재 분모에 포함될 수 있습니다.

후보 점수는 LLM이 검토할 대상을 줄이는 용도이며 최종 관련도 판정이 아닙니다. 또한 이 규칙 기반 계산은 모든 변경 파일 경로와 파일별 diff 앞 3,000자를 보지만, vector 검색 문장은 최대 20개 경로·3개 diff 일부·총 2,200자로 별도 제한됩니다.

### 여기서 Mapping 결과란 무엇인가

GraphRAG 설명에서 말하는 Mapping 결과는 Mapping 실행 화면의 `분석·생성·갱신·건너뜀·실패 건수` 요약이 아닙니다. PostgreSQL의 `program_commit_mappings` 테이블에 저장된 “이 프로그램과 이 commit이 어떤 관계인가”에 대한 한 쌍의 판정 레코드를 뜻합니다. `program_id` × `commit_id`는 unique하므로 같은 쌍을 다시 분석하면 새 행을 중복 생성하지 않고 기존 행을 갱신합니다.

핵심 필드의 의미는 다음과 같습니다.

| 필드 | 의미 |
|---|---|
| `program_id`, `commit_id` | 어떤 프로그램과 어떤 Git commit을 비교했는지 |
| `is_related` | 해당 commit이 그 프로그램 구현과 관련 있다고 판단했는지 |
| `relevance_score` | 관련 강도를 표시하는 0~100 점수. 통계적 확률이 아니라 LLM 판단 또는 fallback 규칙의 점수 |
| `implementation_status` | 해당 commit 하나를 기준으로 본 구현 신호. `구현완료` 또는 `구현됨`, `일부구현`, `판단불가` |
| `reason` | 커밋 메시지, 변경 파일, diff와 프로그램 정보를 비교한 판단 근거 |
| `analysis_run_id` | 어느 Mapping 실행에서 만든 결과인지 |
| `raw_response` | LLM 응답 또는 token 유사도 fallback 내용과 prompt·후보 metadata |
| `feedback_*` | 사람이 관련 여부·점수·상태·근거를 보정한 값과 보정 시각 |

### Mapping 레코드는 어떤 과정으로 저장되는가

현재 기본 흐름인 “커밋 기준 분석”은 다음 순서로 실행됩니다.

```text
Program 목록 + Git Sync로 저장한 commit·file·diff
                         ↓
             commit 검색 문장 구성
                         ↓
     program vector 후보 → token·파일 경로 후보로 빈자리 보충
                         ↓
             중복 제거 후 TOP N
                         ↓
       LLM structured output 관련성 판단
          └─ 실패 시 token 유사도 fallback
                         ↓
       (program_id, commit_id) 기존 행 조회
          ├─ 없음: PostgreSQL INSERT
          └─ 있음: PostgreSQL UPDATE
                         ↓
             commit 단위 transaction COMMIT
                         ↓
      별도 Graph 동기화 시 Neo4j MERGE
```

1. 선행 데이터로 프로그램 목록이 `programs`에, `Git Sync`가 수집한 commit·변경 파일·diff가 `git_commits`와 `commit_files`에 있어야 합니다. `program` chunk와 vector가 있으면 후보 검색에 사용하고, 없거나 vector 검색이 실패하면 token·파일 경로 유사도로만 후보를 만듭니다.
2. 사용자가 Mapping 화면에서 `미완료 커밋 전체 분석` 또는 `선택한 커밋 분석`을 누르면 Streamlit page가 `MappingService.analyze_commits(...)`를 직접 호출합니다. Service는 batch 추적용 `AnalysisRun` 행을 먼저 만듭니다.
3. 각 commit에 대해 hash, 메시지, 작성자, 최대 20개 변경 파일 경로와 최대 3개 파일의 diff 일부를 검색 문장으로 만듭니다. 전체 commit 입력은 최대 2,200자로 제한합니다.
4. 이 문장으로 `program` chunk vector 검색을 하고, 별도로 프로그램 정보와 commit 메시지·파일·diff의 token 겹침 및 모듈·프로그램명의 파일 경로 포함 여부를 계산합니다. Vector 후보를 먼저 넣고, 중복되지 않는 token 후보로 남은 자리만 채워 커밋당 TOP N을 만듭니다. 두 후보 점수를 합산해 재정렬하지 않습니다. 기본 N은 10이며 UI에서 3~30으로 조정할 수 있습니다.
5. LLM에는 해당 commit과 후보 program 목록만 전달합니다. LLM은 관련 program 0개 이상을 고르고 각 program의 `relevance_score`, `implementation_status`, `reason`을 JSON Schema에 맞춰 반환합니다. 후보 목록 밖의 program ID는 파싱 단계에서 제외하고, 점수는 0~100으로 제한합니다.
6. LLM 호출이 실패하거나 JSON을 구조화하지 못하면 token·파일 경로 유사도 fallback을 사용합니다. Fallback 점수가 30점 이상인 쌍만 관련 Mapping으로 남깁니다. Fallback으로 Mapping이 저장되는 경우 사용 여부와 오류를 `raw_response`와 AI 호출 이력에 남깁니다.
7. 관련 후보마다 `(program_id, commit_id)` 행을 조회합니다. 행이 없으면 `ProgramCommitMapping(...)`을 `db.add()`해 INSERT하고, 이미 있으면 점수·상태·근거·원본 응답을 UPDATE합니다. DB unique constraint도 같은 program–commit 쌍의 중복 행을 막습니다.
8. commit의 `mapping_analysis_status`를 `completed`로, `mapping_analyzed_at`을 현재 시각으로 갱신한 뒤 commit 하나를 처리할 때마다 `db.commit()`합니다. 따라서 batch 중간에 재시작해도 완료된 commit을 건너뛸 수 있습니다. Batch 종료 후에는 관련 Mapping 여러 건을 사용한 프로그램 전체 구현상태 분석도 이어서 실행합니다.

커밋 기준 분석에서 LLM이 관련 program을 하나도 고르지 않으면 그 commit은 분석 완료로 표시하지만 `program_commit_mappings` 행은 만들지 않습니다. 반면 기존 방식인 “프로그램 기준 분석”은 program마다 token 유사도로 commit 후보를 고른 뒤 각 쌍을 LLM으로 판단합니다. UI의 `관련 커밋으로 판단된 결과만 저장`이 꺼져 있으면 `is_related=false`인 쌍도 저장할 수 있습니다.

PostgreSQL Mapping 저장 자체가 Neo4j relationship을 즉시 만드는 것은 아닙니다. 현재 Mapping의 최신 `updated_at`이 마지막 Graph 동기화 때 기록한 `last_mapping_updated_at`보다 새로우면 Graph를 `stale`로 표시합니다. 이후 `Knowledge Graph`의 증분 또는 전체 동기화를 실행해야 현재 `is_related=true` Mapping이 Neo4j `MAPPED_TO_COMMIT` relationship으로 `MERGE`됩니다.

예를 들어 다음과 같은 결과는 “`abc123` commit이 `PAY-001 결제 승인` 프로그램의 일부 구현 근거로 판단됐다”는 뜻입니다.

```text
program: PAY-001 결제 승인
commit: abc123 결제 취소 오류 수정
is_related: true
relevance_score: 87
implementation_status: 일부구현
reason: PaymentService와 결제 상태 처리 파일이 변경됨
```

`implementation_status`는 프로그램 전체가 87% 완료됐다는 뜻이 아닙니다. 한 commit이 해당 프로그램 구현에 어떤 신호를 주는지를 표시한 것입니다. 프로그램 전체 상태인 `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `UNKNOWN`은 관련 Mapping 여러 건과 프로그램 정보를 모아 `program_implementation_status` 테이블에 별도로 분석·저장합니다. 또한 87점은 관련도이지 진척률 87%가 아닙니다.

현재 commit 기준 Mapping과 program 기준 Mapping의 output schema가 달라 완료 표기가 `구현완료` 또는 `구현됨`으로 저장될 수 있습니다. 이 표현 차이는 현재 구현의 한계이며, 의미는 모두 해당 커밋에서 구현 완료 신호를 보았다는 뜻입니다. Mapping review에서 사람이 보정하면 주요 필드와 `feedback_*` 이력을 함께 갱신하며, 이후 Graph 동기화는 보정된 현재 값을 읽습니다.

따라서 GraphRAG에서 Mapping 결과를 사용한다는 말은 `is_related=true`인 프로그램–commit 쌍을 `MAPPED_TO_COMMIT` relationship으로 만들고, 관련도·commit 기준 구현상태·근거를 relationship 속성으로 복사한다는 뜻입니다. Mapping 결과가 없거나 `is_related=false`이면 program node와 commit node는 각각 있어도 둘 사이의 `MAPPED_TO_COMMIT` 관계는 만들지 않습니다.

따라서 Mapping 단계에서 찾는 청크는 임의의 전체 소스 청크가 아니라 우선 `program` 후보 청크입니다. 현재 소스 청크를 검색해 답변하는 과정은 `Project Chat`의 별도 RAG 흐름입니다. 커밋 메시지와 diff가 부실하거나 프로그램 설명이 부족하면 후보를 놓칠 수 있으므로, 낮은 관련도나 판단불가 결과는 Mapping 리뷰 큐에서 사람이 확인하도록 했습니다.

## Q. AI Resource Radar는 어떤 원리로 우선순위를 정하나?

`AI Resource Radar`는 LLM이 프로그램 순위를 직접 판단하는 기능이 아닙니다. Mapping과 구현상태 분석에서 얻은 AI 근거에 일정, 리스크, Git 변경 범위와 프로그램별 관리 부담 신호를 더해 고정된 가중치로 계산하는 규칙 기반 우선순위 목록입니다. 같은 날짜에 같은 데이터가 들어오면 같은 점수가 나옵니다.

### 어떤 데이터를 사용하는가

프로젝트의 각 프로그램에 대해 다음 신호를 계산합니다.

| 신호 | 계산에 사용하는 데이터 | 의미 |
|---|---|---|
| 계획 진척도 | 프로그램의 `progress_rate` | PL이 입력한 계획상 진척도 |
| AI 진척도 | 최신 프로그램 구현상태 분석 결과 | `COMPLETED=100`, `IN_PROGRESS=50`, `NOT_STARTED/UNKNOWN=0`; 분석이 없거나 관련 commit이 바뀌어 오래됐으면 수치 대신 `분석 필요` 또는 `재분석 필요` |
| 진척도 차이 | `계획 진척도 - AI 진척도` | 계획보다 코드 구현 근거가 뒤처진 정도. 음수는 위험 점수를 차감하지 않음 |
| 리스크 | 해결되지 않은 `RiskFinding`과 그중 `HIGH` 건수 | 일정·품질상 우선 확인할 문제 |
| 예상 종료일 | 계획 시작일, 계획 종료일, 오늘 날짜, AI 진척도 | 지금까지의 일평균 진척도를 단순 연장해 종료일과 지연일을 추정 |
| 변경 난이도 | 관련 commit 수, 변경 파일 수, diff 증감 라인, 변경 영역, 여러 프로그램에 걸친 commit, 미해결 리스크 | 변경 범위가 넓고 복잡한 정도 |
| commit 근거 | Mapping에서 `is_related=true`인 commit | 구현 근거 존재 여부와 관련성이 높은 commit 메시지 |
| 프로그램 관리 부담 | 미완료 여부, 리스크, 진척도 차이와 난이도 | 해당 프로그램을 점검하는 데 필요한 부담의 참고값인 `workload_points` |

예상 종료일은 AI 진척도가 있고 계획 시작일이 있을 때 다음 방식으로 계산합니다.

```text
경과일 = max(오늘 - 계획 시작일, 1일)
일평균 진척도 = AI 진척도 / 경과일
남은 일수 = ceil((100 - AI 진척도) / 일평균 진척도)
예상 종료일 = 오늘 + 남은 일수
예상 지연일 = max(예상 종료일 - 계획 종료일, 0일)
```

예상 지연이 7일 이상이면 `DELAY_EXPECTED`, 1~6일이거나 계획 종료일까지 7일 이하인데 AI 진척도가 80% 미만이면 `AT_RISK`로 분류합니다. 구현상태 분석이 없거나 계획 종료일이 없으면 일부 예상값은 `UNKNOWN`이 됩니다. AI 진척도가 0이거나 계획 시작일이 없으면 계획 종료일과 오늘 중 늦은 날짜에서 14일을 더하는 보수적인 기본값을 사용합니다.

### 점수는 어떻게 계산하는가

각 프로그램은 0점에서 시작해 다음 위험 신호를 더합니다.

| 조건 | Radar 가산점 |
|---|---:|
| 구현상태 분석이 없거나 오래됨 | `+18` |
| `HIGH` 미해결 리스크 존재 | `+30 + min(HIGH 건수 × 8, 16)` |
| `HIGH`는 없지만 미해결 리스크 존재 | `+min(미해결 건수 × 10, 25)` |
| 예상 지연 7일 이상 | `+28` |
| 예상 종료일 주의 | `+16` |
| 계획 대비 AI 진척도 차이가 양수 | `+min(차이 × 0.45, 22)` |
| 난이도 `HIGH` | `+18` |
| 난이도 `MEDIUM` | `+8` |
| 여러 프로그램에 걸친 commit | `+min(commit 수 × 8, 16)` |
| 미완료 상태인데 관련 commit 없음 | `+18` |
| 프로그램 관리 부담 | `+min(workload_points × 0.15, 12)` |

난이도와 프로그램 관리 부담의 내부 계산식은 다음과 같습니다. 난이도 점수는 `70점 이상=HIGH`, `35점 이상=MEDIUM`, 그 미만은 `LOW`입니다.

```text
난이도 = min(
  관련 commit 수 × 8
  + 변경 파일 수 × 4
  + min(diff 증감 라인, 300) × 0.08
  + 변경 영역 수 × 8
  + cross-program commit 수 × 10
  + 미해결 리스크 수 × 12,
  100
)

workload_points =
  10
  + 미완료이면 15
  + 미해결 리스크 수 × 15
  + max(진척도 차이, 0) × 0.5
  + 난이도 × 0.25
```

최종 점수는 모든 가산점을 합한 뒤 100점으로 제한하고 소수점 첫째 자리까지 표시합니다. Radar 등급은 `75점 이상=HIGH`, `45점 이상=MEDIUM`, 그 미만은 `LOW`입니다.

점수가 같으면 `HIGH` 리스크 수, 전체 미해결 리스크 수, 예상 지연일, 난이도 순으로 다시 비교합니다. Dashboard에는 기본적으로 상위 5개 프로그램을 표시하고, 각 프로그램에는 Mapping 관련도 순으로 최대 3개의 commit 해시와 메시지를 근거로 붙입니다.

권장 액션도 LLM 생성물이 아니라 다음 우선순위 규칙으로 정합니다.

1. AI 진척도가 없으면 구현상태 분석 실행 또는 갱신을 안내합니다.
2. `HIGH` 리스크나 예상 지연이 있으면 담당자와 범위·일정 조정 여부를 확인하게 합니다.
3. 진척도 차이가 30%p 이상이면 `Program Detail`의 commit과 구현상태 근거를 확인하게 합니다.
4. 난이도가 높거나 cross-program commit이 있으면 `AI Code Review`와 `Commit Impact` 확인을 안내합니다.
5. 관련 commit이 없으면 Git 동기화와 실제 구현 착수 여부를 확인하게 합니다.
6. 어느 조건에도 해당하지 않으면 다음 주 추세 관찰 대상으로 둡니다.

### 여기서 AI가 담당하는 부분과 한계

Radar를 화면에 계산하는 순간에는 LLM, embedding 또는 GraphRAG를 호출하지 않습니다. 이름에 `AI`가 붙은 이유는 프로그램-commit Mapping과 프로그램 구현상태 분석처럼 앞 단계에서 LLM이 만든 결과를 입력 신호로 사용하기 때문입니다. Radar 계산 뒤 사용자가 `PL Briefing 생성`을 눌렀을 때만 별도로 LLM을 호출해 상위 항목을 회의 문장으로 정리합니다.

이 점수는 학습된 예측 모델의 확률이나 개인 성과 점수가 아닙니다. 현재 상태에서 PL이 먼저 확인할 프로그램을 놓치지 않기 위한 위험 가산식입니다. 좋은 신호가 위험 점수를 상쇄하지 않고, 리스크가 직접 점수뿐 아니라 난이도와 프로그램 관리 부담에도 일부 중복 반영되므로 100점이 실제 실패 확률 100%를 뜻하지 않습니다. 또한 Radar에는 담당자별 전체 `workload_score`가 아니라 각 프로그램의 `workload_points`가 들어갑니다. 프로젝트 규모별 통계 보정이나 과거 결과에 따른 자동 가중치 학습도 하지 않으므로, 화면의 근거 상세와 실제 일정 상황을 PL이 함께 확인해야 합니다.

## Q. PL Briefing은 정확히 LLM을 어떻게 사용하며, 어떤 prompt를 보내나?

`PL Briefing`에서 LLM은 프로그램 우선순위를 결정하지 않습니다. 애플리케이션이 먼저 `AI Resource Radar`의 점수와 순위를 계산하고, LLM은 그 근거를 PL 회의에서 읽을 수 있는 요약, 우선 확인 항목, 회의 질문과 다음 액션으로 정리합니다.

처리 순서는 다음과 같습니다.

1. Dashboard가 프로젝트의 프로그램별 계획/AI 진척도, 진척도 차이, 미해결 리스크, 예상 지연, 난이도, 관련 commit 수, 변경 파일 수, cross-program commit과 프로그램 관리 부담을 모읍니다.
2. 애플리케이션 코드가 정해진 가중치로 우선순위 점수를 계산하고 상위 5개 프로그램을 고릅니다. `HIGH` 리스크, 예상 지연, 큰 진척도 차이, 높은 난이도처럼 점수에 영향을 준 이유도 함께 남깁니다.
3. 사용자가 `PL Briefing 생성`을 누르면 상위 항목을 다음 구조의 JSON으로 만듭니다.

```json
{
  "generated_on": "2026-07-23",
  "items": [
    {
      "rank": 1,
      "program_id": "SMP-ORD-001",
      "program_name": "주문 접수",
      "developer": "김민수",
      "priority_score": 88.0,
      "priority_level": "HIGH",
      "reasons": ["HIGH 리스크 2건", "예상 종료일 기준 53일 지연 가능성"],
      "recommended_action": "담당자와 범위/일정 조정 필요 여부를 먼저 확인하세요.",
      "evidence": [{"label": "미해결 리스크", "value": "2"}],
      "related_commits": ["커밋 해시와 메시지"]
    }
  ]
}
```

4. 이 JSON을 아래 user prompt의 마지막에 붙입니다. 실제 실행 시 `[Radar JSON]` 자리에 위 데이터가 들어갑니다.

```text
다음 AI Resource Radar 근거를 바탕으로 PL 주간 점검 브리핑 데이터를 작성하세요.

규칙:
- 응답은 JSON object 하나만 반환하세요. Markdown, code fence, 표를 쓰지 마세요.
- 모든 문장은 한국어로 작성하되, 제목에는 "한국어 브리핑" 같은 언어 설명을 넣지 마세요.
- title은 "PL 주간 점검 브리핑"으로 작성하세요.
- 근거에 없는 사실을 추가하지 마세요.
- 위험 단정 대신 "확인 필요", "주의", "우선 검토"처럼 보조 판단으로 표현하세요.
- priority_items와 next_actions에는 program_id 또는 program_name과 근거 숫자를 포함하세요.
- 다음 schema를 지키세요:
{
  "title": "PL 주간 점검 브리핑",
  "summary": "한 문단 요약",
  "priority_items": [
    {"program_id": "SMP-ORD-001", "program_name": "주문 접수", "reason": "미해결 리스크 2건, 예상 지연 53일", "owner": "김민수"}
  ],
  "meeting_questions": ["회의에서 확인할 질문"],
  "next_actions": [
    {"program_id": "SMP-ORD-001", "action": "담당자와 범위/일정 조정 필요 여부 확인"}
  ]
}

AI Resource Radar JSON:
[Radar JSON]
```

LLM 요청은 OpenAI-compatible `POST {LLM_BASE_URL}/chat/completions`로 전송합니다. 준비된 Docker 시연 환경에서는 host LM Studio의 `http://host.docker.internal:12345/v1`와 `qwen2.5-coder-7b-instruct`를 사용합니다. 핵심 요청 설정은 다음과 같습니다.

```json
{
  "model": "qwen2.5-coder-7b-instruct",
  "messages": [
    {
      "role": "system",
      "content": "You are a precise software analysis assistant. Follow the user's requested output format."
    },
    {"role": "user", "content": "위 PL Briefing prompt와 실제 Radar JSON"}
  ],
  "temperature": 0.1,
  "max_tokens": 900,
  "stream": false,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "pl_weekly_briefing",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "title": {"type": "string", "enum": ["PL 주간 점검 브리핑"]},
          "summary": {"type": "string"},
          "priority_items": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "program_id": {"type": "string"},
                "program_name": {"type": "string"},
                "reason": {"type": "string"},
                "owner": {"type": "string"}
              },
              "required": ["program_id", "program_name", "reason", "owner"],
              "additionalProperties": false
            }
          },
          "meeting_questions": {"type": "array", "items": {"type": "string"}},
          "next_actions": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "program_id": {"type": "string"},
                "action": {"type": "string"}
              },
              "required": ["program_id", "action"],
              "additionalProperties": false
            }
          }
        },
        "required": ["title", "summary", "priority_items", "meeting_questions", "next_actions"],
        "additionalProperties": false
      }
    }
  }
}
```

`PL_BRIEFING_SCHEMA`는 `title`, `summary`, `priority_items`, `meeting_questions`, `next_actions`를 필수로 하고 정의하지 않은 필드는 허용하지 않습니다. 응답을 받으면 앱이 JSON을 파싱하고 필수 항목을 확인합니다. 형식이 맞지 않으면 오류 목록과 원본 응답을 넣어 한 번만 보정 요청을 보냅니다. 호출 실패, 두 번째 형식 오류 또는 `mock` provider 사용 시에는 같은 Radar 근거로 규칙 기반 fallback 브리핑을 만듭니다.

화면의 Markdown은 LLM이 직접 만드는 것이 아닙니다. 앱이 구조화 JSON을 `요약`, `우선 확인 항목`, `회의 질문`, `다음 액션` 순서로 렌더링합니다. 결과와 함께 provider/model, LLM 또는 fallback 여부, Radar 근거 JSON, 원본 응답과 검증 상태를 `pl_briefing_history` 및 AI 호출 이력에 저장합니다.

따라서 `PL Briefing` 생성 시점에는 embedding 검색이나 GraphRAG를 새로 호출하지 않고, 전체 소스나 diff 원문도 prompt에 넣지 않습니다. 다만 Radar가 사용하는 `AI Progress`와 Mapping 같은 선행 데이터에는 앞서 LLM이 분석한 결과가 포함될 수 있으며, PL Briefing은 그 결과와 규칙 기반 리스크·일정 지표를 다시 요약하는 단계입니다.

## Q. 이 프로젝트에서 RAG가 있고 없고의 정확한 차이는 무엇인가?

이 프로젝트에서 RAG는 LLM 자체가 아니라, 프로젝트 데이터 중 질문과 관련된 근거를 찾아 LLM에 전달하는 검색 계층입니다.

RAG가 없으면 LLM은 사용자의 질문만 받거나, 사람이 직접 골라 준 소스와 diff만 볼 수 있습니다. 저장소 전체를 매 질문마다 prompt에 넣는 것은 입력 크기와 처리 시간 때문에 현실적이지 않습니다. 결국 어떤 파일을 봐야 하는지 찾기 어렵고, 모델의 일반 지식으로 빈 부분을 추측할 가능성이 커집니다.

RAG가 있으면 현재 소스, 프로그램 정보, 커밋과 diff를 미리 청크와 vector로 준비해 두고, 질문과 의미적으로 가까운 일부 근거만 검색합니다. 현재 소스 청크는 실제 파일과 일치하는지 다시 검증한 뒤 LLM에 전달하며, 파일 경로와 라인 범위를 답변 근거로 남깁니다.

기능별 차이는 다음과 같습니다.

| 기능 | RAG가 있을 때 | RAG가 없을 때 |
|---|---|---|
| `Project Chat` | 관련 소스 청크를 검색·검증하고 근거 기반 답변과 citation을 생성 | 검증된 소스 근거가 없으므로 현재 코드에 대한 답변을 만들지 않고 근거 부족으로 처리 |
| `RAG Search` | 질문과 유사한 소스·프로그램·커밋·diff를 검색 | 해당 검색 기능 자체를 사용할 수 없음 |
| Mapping | Vector 검색으로 관련 `program` 후보를 찾고 token 후보와 결합 | 커밋 메시지·파일 경로·diff와 프로그램 정보의 token 유사도만으로 후보를 선정 |
| GraphRAG | 검색된 파일·클래스를 Neo4j 관계 탐색의 시작점으로 사용 | 질문과 관련된 graph 시작점을 잡기 어려우며, graph만으로 현재 코드 사실을 답하지 않음 |
| `AI Code Review` | 필수 의존성은 아님 | 선택한 commit diff를 직접 전달하므로 계속 실행 가능 |
| `Risk Analysis` | Mapping 등 RAG가 보조한 선행 결과를 활용할 수 있음 | 규칙 기반 분석 자체는 실행 가능하지만 Mapping 근거 품질의 영향을 받을 수 있음 |

예를 들어 “결제 승인 후 주문 상태는 어디서 바뀌나?”라는 질문에서 RAG가 없으면 LLM은 어떤 파일을 읽어야 하는지 모릅니다. RAG가 있으면 `PaymentService`와 `OrderStatusService` 주변의 관련 라인을 먼저 찾고, 현재 파일 검증을 통과한 부분만 LLM에 제공합니다. GraphRAG가 준비되어 있으면 두 클래스의 관계도 보조 근거로 추가합니다.

정리하면 RAG가 없다고 LLM이 없어지는 것은 아닙니다. 차이는 LLM이 프로젝트에 대한 답을 일반적인 추론으로 만드는지, 검색하고 검증한 프로젝트 근거 안에서 만드는지에 있습니다. 이 프로젝트는 현재 코드 질문에 대해서는 후자만 허용하도록 설계했습니다.

## Q. RAG에는 무엇을 저장하나?

RAG에는 검색할 원문을 잘게 나눈 청크와 각 청크의 embedding vector를 PostgreSQL에 저장합니다.

`document_chunks`에는 다음 네 종류의 검색 근거가 들어갑니다.

- `source_file`: 현재 소스 파일의 일부 내용
- `program`: 프로그램 ID, 프로그램명, 모듈, 화면명과 설명
- `commit`: 커밋 해시, 메시지와 작성자
- `commit_file`: 변경 파일 경로, 변경 유형과 diff 내용

현재 소스 청크에는 파일 경로, 시작·종료 라인, 파일 및 청크 content hash, 인덱싱 당시 `Repo HEAD`, embedding 처리 상태 같은 metadata도 저장합니다. 이 정보로 검색 결과가 현재 checkout의 실제 파일과 같은지 검증하고, 오래된 청크는 답변 근거에서 제외합니다. 반면 commit과 diff는 현재 코드가 아니라 변경 이력 근거로 구분합니다.

`vector_items`에는 각 청크를 embedding model로 변환한 숫자 vector와 사용한 model 이름을 저장합니다. 검색할 때 질문도 같은 방식으로 vector로 변환하고, pgvector가 가까운 청크를 찾습니다. 같은 청크라도 embedding model이 달라지면 별도 vector로 관리해 다른 모델의 결과를 섞지 않습니다.

저장소 전체를 하나의 문서로 복사하는 방식은 아닙니다. 검색에 필요한 텍스트만 일정 크기로 나누어 저장합니다. `Project Chat`의 질문·답변 이력은 별도 대화 테이블에 저장하고, GraphRAG 관계 데이터는 Neo4j에 저장하므로 RAG 청크·vector와 역할이 구분됩니다.

## Q. Vector 정보는 PostgreSQL에 저장하는가?

네. 별도의 vector database 제품을 추가하지 않고 PostgreSQL의 `pgvector` extension을 사용해 저장합니다.

원문 청크는 `document_chunks` 테이블에 저장하고, 해당 청크를 embedding model로 변환한 숫자 vector는 `vector_items` 테이블의 `embedding` column에 저장합니다. `vector_items`는 `chunk_id`로 원문 청크와 연결되며, 어떤 model로 만든 vector인지 `embedding_model`도 함께 기록합니다. 현재 vector dimension은 768입니다.

질문이 들어오면 질문도 같은 embedding model로 vector화한 뒤, PostgreSQL에서 pgvector cosine distance를 사용해 가까운 청크를 찾습니다. 검색할 때는 현재 프로젝트, `source_type`과 embedding model을 함께 제한해 다른 프로젝트나 다른 model의 vector가 섞이지 않도록 합니다.

따라서 PostgreSQL은 업무·Git·분석 데이터뿐 아니라 RAG 원문 청크와 vector까지 저장하는 핵심 저장소입니다. Neo4j에는 vector를 저장하지 않으며, 프로그램–commit–파일–class 같은 GraphRAG 관계만 저장합니다.

## Q. PostgreSQL은 RDB인데 어떻게 vector를 저장하며, 테이블은 어떻게 구성되어 있는가?

PostgreSQL은 기본적으로 관계형 DB가 맞습니다. 이 프로젝트는 `pgvector` extension을 설치해 PostgreSQL에 `vector` column type과 vector 거리 계산 연산을 추가했습니다. Alembic migration에서 `CREATE EXTENSION IF NOT EXISTS vector`를 실행하고, embedding column을 `vector(768)`로 정의합니다.

구조는 원문과 vector를 두 테이블로 분리한 1:N 관계입니다.

### `document_chunks`

| Column | Type | 설명 |
|---|---|---|
| `id` | `integer` PK | 청크 ID |
| `project_id` | `integer` FK | 청크가 속한 프로젝트 |
| `source_type` | `varchar(100)` | `source_file`, `program`, `commit`, `commit_file` 구분 |
| `source_id` | `varchar(255)` | 원본 파일·프로그램·commit 등의 식별자 |
| `chunk_index` | `integer` | 원문 안에서의 청크 순서 |
| `chunk_text` | `text` | 실제 검색 근거가 되는 텍스트 |
| `raw_metadata` | `jsonb` | 파일 경로, 라인 범위, hash, indexed HEAD와 embedding 상태 |
| `created_at`, `updated_at` | `timestamptz` | 생성·수정 시각 |

### `vector_items`

| Column | Type | 설명 |
|---|---|---|
| `id` | `integer` PK | Vector row ID |
| `chunk_id` | `integer` FK | `document_chunks.id`와 연결하며 청크 삭제 시 함께 삭제 |
| `embedding_model` | `varchar(255)` | Vector를 생성한 embedding model |
| `embedding` | `vector(768)` | 768개의 실수로 이루어진 embedding vector |
| `raw_metadata` | `jsonb` | Vector 관련 추가 metadata |
| `created_at`, `updated_at` | `timestamptz` | 생성·수정 시각 |

개념적으로는 다음과 같이 저장됩니다.

```text
document_chunks
id=101, chunk_text="결제 승인 처리 소스 ...", source_type="source_file"

vector_items
id=501, chunk_id=101, embedding_model="text-embedding-nomic-embed-text-v2-moe",
embedding=[0.021, -0.114, 0.307, ... 총 768개]
```

질문의 vector가 만들어지면 SQLAlchemy의 pgvector 연동이 `embedding <=> query_vector`에 해당하는 cosine distance를 계산하고, 거리가 가까운 순서로 `ORDER BY`한 뒤 `TOP K`를 가져옵니다. 일반 SQL JOIN과 FK를 그대로 사용할 수 있으므로 검색된 vector에서 원문 청크와 프로젝트 정보를 바로 연결할 수 있습니다.

현재 실제 DB를 확인한 결과 `embedding` column은 `vector(768)`이고, 두 테이블 모두 PK와 FK는 구성되어 있습니다. 다만 현재 `vector_items`에는 HNSW나 IVFFlat 같은 vector index와 `(chunk_id, embedding_model)` unique constraint가 없습니다. 애플리케이션이 같은 model의 vector 존재 여부를 먼저 확인해 중복 생성을 막고 있으며, 현재 데이터 규모에서는 exact cosine 검색을 사용합니다. 데이터가 크게 늘어나면 vector index와 DB 수준 unique constraint를 추가로 검토해야 합니다.

## Q. 즉, RAG는 관련 소스 파일 후보를 찾기 위한 진입 목적으로 봐도 되는가?

`Project Chat` 기준으로는 대체로 맞습니다. RAG의 첫 번째 역할은 전체 저장소를 LLM에 보내지 않고, 질문과 관련성이 높은 소스 파일과 라인 구간을 빠르게 좁히는 것입니다.

다만 후보 파일을 찾는 것으로 끝나지는 않습니다. 검색된 소스 청크가 실제 파일과 일치하는지 검증을 통과하면, 그 청크 내용 자체가 LLM의 답변 context와 파일·라인 citation으로 사용됩니다. Java 관계 질문에서는 검색된 파일과 클래스가 GraphRAG 탐색 및 메서드 단위 검증의 시작점도 됩니다.

따라서 전체 흐름은 다음과 같이 설명할 수 있습니다.

1. RAG가 관련 소스 청크 후보를 찾습니다.
2. 애플리케이션이 해당 청크를 현재 파일과 비교해 검증합니다.
3. 검증된 청크를 실제 답변 근거로 LLM에 전달합니다.
4. 필요하면 해당 파일과 클래스를 시작점으로 GraphRAG 관계를 추가합니다.

즉 RAG는 관련 소스를 찾는 진입점이면서, 검증을 통과한 뒤에는 답변을 제한하는 근거 계층이기도 합니다. 검색되지 않았거나 검증되지 않은 코드는 LLM이 임의로 추측하지 않도록 했습니다.

## Q. RAG는 최신 변경분만 반영하도록 어떻게 했나?

Git Sync가 저장한 변경 파일 목록과 마지막으로 인덱싱한 commit을 기준으로 증분 인덱싱하도록 구현했습니다.

사용자가 RAG 또는 `Project Chat`에서 `최신 변경분 반영`을 실행하면, 최근 indexed HEAD 이후의 `CommitFile`만 확인합니다. 따라서 저장소 전체를 다시 읽지 않고 다음과 같이 변경 종류별로 처리합니다.

- 추가·수정·복사된 소스 파일은 기존 청크를 교체하고 현재 내용으로 새 청크를 만듭니다.
- 삭제된 파일은 해당 소스 청크와 연결된 vector를 제거합니다.
- 이름이 변경된 파일은 이전 경로의 데이터를 제거하고 새 경로를 인덱싱합니다.
- 이미지, Excel, binary, cache, virtualenv, 너무 큰 파일과 저장소 밖의 경로는 제외합니다.

새 청크에는 `embedding_status=pending`을 기록합니다. 이 단계에서 임베딩을 자동 생성하지 않고, 사용자가 `RAG 검색 > 검색 준비`를 실행했을 때 현재 embedding model의 vector가 없는 청크만 제한된 수량으로 생성합니다. 이미 같은 청크와 모델 조합의 vector가 있으면 재사용합니다.

이렇게 소스 인덱싱 범위와 임베딩 호출 범위를 모두 변경된 부분으로 제한했습니다. Git Sync 직후 자동 실행하지 않는 이유는 cloud embedding 비용이나 local LM Studio의 GPU 부하를 사용자가 통제할 수 있게 하기 위해서입니다. 최초 구축, 큰 브랜치 변경 또는 인덱스 불일치가 의심될 때만 `전체 소스 다시 읽기`를 사용합니다.

## Q. 그렇다면 이미 수정된 소스가 RAG에 남아 있을 수 있는 것 아닌가?

맞습니다. 소스를 수정한 시점과 인덱스를 갱신하는 시점이 분리되어 있기 때문에, 이전 소스 청크와 vector가 DB에 잠시 남아 있을 수 있습니다. RAG 저장소는 원본 데이터가 아니라 검색용 인덱스이므로, DB에 존재한다는 사실만으로 현재 코드 근거로 신뢰하지 않습니다.

`Project Chat`은 검색된 `source_file` 청크를 LLM에 전달하기 전에 다음 항목을 실제 저장소와 비교합니다.

- 인덱싱 당시 `Repo HEAD`와 현재 `Repo HEAD`
- 파일이 현재도 존재하는지
- 저장된 라인 범위가 현재 파일에도 존재하는지
- 해당 라인 내용의 hash가 저장된 청크 hash와 같은지

하나라도 일치하지 않으면 해당 청크를 `stale` 또는 `invalid`로 표시하고 현재 코드 답변에서 제외합니다. 검증된 소스 청크가 하나도 없으면 오래된 근거로 추측하지 않고 근거가 부족하다는 답변을 반환합니다. RAG 검색 화면에서도 오래된 결과를 `인덱스 오래됨` 또는 `검증 실패`로 구분해 보여줍니다.

이후 `최신 변경분 반영`을 실행하면 수정 파일의 기존 청크를 교체하고 삭제·이름 변경된 파일의 청크와 vector를 정리합니다. `전체 소스 다시 읽기`는 전체 파일을 다시 확인하면서 검증되지 않은 청크까지 정리합니다.

다만 현재 구현은 안전성을 우선해 `indexed_head_hash`가 현재 HEAD와 다르면 파일 내용이 우연히 같더라도 먼저 stale로 판정합니다. 또한 증분 갱신은 변경된 경로만 새 HEAD로 다시 기록하므로, 변경되지 않은 파일의 기존 청크가 이전 HEAD metadata로 남아 전체 인덱스가 계속 갱신 필요로 표시될 수 있습니다. 이 경우 전체 소스를 다시 읽어야 모든 청크가 현재 HEAD 기준으로 정렬됩니다. 즉 오래된 내용을 최신 사실로 답하는 것은 막지만, 증분 갱신 뒤 검색 가능한 현재 소스 범위가 일시적으로 줄어들 수 있다는 한계가 있습니다.

## Q. 실제 소스와 일치하는지 확인한다는 것인가?

네. `Project Chat`이 답변에 사용하려는 소스 청크를 앱 서버의 Git 저장소에 있는 실제 파일과 직접 비교합니다. 이 검증은 LLM의 판단이 아니라 애플리케이션 코드가 수행하는 hash 비교입니다.

청크에 저장된 파일 경로와 시작·종료 라인으로 현재 파일의 같은 구간을 다시 읽고, 그 내용의 SHA-256 hash를 계산해 인덱싱 당시 저장한 `chunk_content_hash`와 비교합니다. 파일이 삭제됐거나 라인 범위가 달라졌거나 hash가 다르면 해당 청크를 답변 근거에서 제외합니다. 인덱싱 당시 HEAD와 현재 `Repo HEAD`도 함께 비교합니다.

따라서 아직 commit하지 않은 로컬 수정처럼 HEAD가 바뀌지 않은 변경도 해당 라인의 hash가 달라지면 stale로 감지할 수 있습니다.

다만 질문할 때마다 저장소 전체를 검사하는 것은 아닙니다. 질문과 관련해 검색된 청크와 코드 식별자로 추가된 일부 파일만 답변 직전에 검증합니다. 전체 인덱스 상태를 확인하려면 `근거 상태 새로고침`, 전체 청크를 현재 소스로 재구성하려면 `전체 소스 다시 읽기`를 사용합니다.

## Q. GraphRAG는 무엇을 저장하고 `Project Chat`에서 어떻게 활용하나?

GraphRAG는 코드 원문을 vector로 저장하는 RAG와 달리, 프로젝트 요소 사이의 관계를 Neo4j graph로 저장하고 질문과 관련된 경로를 답변의 보조 근거로 사용합니다.

### 무엇을 저장하는가

Neo4j에는 다음 node를 `KnowledgeNode`로 저장합니다.

- `project`: 프로젝트 ID, 이름과 Git 저장소 경로
- `program`: 프로그램 ID·이름, 모듈, 상태와 계획 진척률
- `commit`: commit hash·메시지, 작성자, 일시와 Mapping 분석 상태
- `file`: 파일 경로와 도메인
- `class`: Java class의 이름, FQN, 종류, package, 파일 경로와 도메인
- `domain`: 모듈·화면명 또는 파일 경로에서 구분한 업무·코드 영역

Node 사이에는 다음 관계를 저장합니다.

- `HAS_PROGRAM`, `HAS_COMMIT`, `HAS_FILE`, `HAS_DOMAIN`: 프로젝트가 보유한 항목
- `MAPPED_TO_COMMIT`: 프로그램과 관련 commit의 연결. 관련도, 구현상태와 판단 근거도 관계 속성으로 저장
- `TOUCHES_FILE`, `TOUCHES_DOMAIN`: commit이 변경한 파일과 도메인
- `CONTAINS_CLASS`: 파일 또는 도메인이 포함하는 Java class
- `IMPORTS_CLASS`: 한 Java class가 다른 class를 import하는 관계
- `OWNS_PROGRAM`: 도메인과 프로그램의 연결

프로그램·commit·Mapping은 PostgreSQL 분석 결과에서 가져오고, Java class와 import는 현재 저장소 소스를 경량 parser로 읽어 구성합니다. Neo4j에는 모든 관계를 공통 `RELATED` relationship으로 저장하되, 실제 관계 종류는 `edge_type` 속성으로 구분합니다. 현재 구현은 Java import 관계를 저장하며 실제 runtime 호출 관계나 compiler 수준 type resolution을 graph 자체에 저장하는 것은 아닙니다.

그래프가 어느 코드 시점의 결과인지 확인하기 위해 `Repo HEAD`, DB Git Sync HEAD, Graph HEAD, node·edge 수와 동기화 상태는 PostgreSQL의 graph sync state에 별도로 기록합니다.

### 기존 RAG 저장 데이터를 읽어 Neo4j에 넣는가

아닙니다. Graph 동기화는 RAG 테이블인 `document_chunks`나 `vector_items`를 조회하지 않고, 저장된 embedding vector를 Neo4j node나 relationship으로 변환하지도 않습니다. Graph 동기화 중에 LLM이나 embedding model을 호출하지도 않습니다.

Graph 적재 흐름은 다음과 같습니다.

```text
PostgreSQL의 Project·Program·GitCommit·CommitFile·Mapping ─┐
현재 Git 작업 트리의 Java class·import 관계 ──────├→ GraphPayload → Neo4j MERGE
document_chunks·vector_items ─────────────────╳  (사용하지 않음)
```

전체 동기화는 해당 project의 기존 Neo4j graph를 지우고 위 데이터로 만든 node·edge를 batch `MERGE`합니다. 증분 동기화는 Git Sync 이후 추가된 commit·file과 변경된 Mapping을 읽고, 변경된 Java 파일을 현재 저장소에서 다시 parse해 해당 관계를 정리한 뒤 upsert합니다. 따라서 RAG source index가 없어도 project·Git 데이터와 현재 소스가 있으면 Graph 자체는 구성할 수 있습니다. Mapping 결과가 없으면 program과 commit을 잇는 `MAPPED_TO_COMMIT` 관계만 생성되지 않습니다.

`neo4j_graph_service.py`가 `src.rag.chunker`의 `_is_source_file`, `_read_text_file`을 import하지만, 이는 소스 파일을 고르고 직접 읽는 공통 helper를 재사용한 것입니다. PostgreSQL에 저장된 RAG chunk나 vector를 읽는 것은 아닙니다.

RAG와 GraphRAG의 간접 연결은 두 군데에 있습니다.

1. `MAPPED_TO_COMMIT` 관계의 원본은 PostgreSQL의 `ProgramCommitMapping`입니다. 이 Mapping을 만드는 앞 단계에서 embedding 검색과 LLM을 사용할 수는 있지만, Graph 동기화가 RAG vector를 다시 읽는 것은 아닙니다. 이미 저장된 최종 Mapping 결과를 읽습니다.
2. `Project Chat` 질문 시에는 일반 RAG가 먼저 `document_chunks`·`vector_items`로 관련 소스를 찾고 현재 파일과 일치하는지 검증합니다. 그 소스의 file·class 정보와 질문을 seed로 삼아 Neo4j의 관련 경로를 조회합니다. 이는 Graph에 데이터를 넣는 단계가 아니라 이미 만든 Graph에서 질문과 관련된 부분을 찾는 조회 단계입니다.

### 어떻게 활용하는가

`Project Chat`에서 먼저 일반 RAG가 질문과 관련된 현재 소스 청크를 찾고 실제 파일과 일치하는지 검증합니다. 그다음 질문, 한글 업무용어 확장 결과와 검색된 파일·class·program·commit 정보에서 GraphRAG 검색어인 seed를 추출합니다.

전체 답변 흐름은 다음과 같습니다.

1. Embedding 검색으로 질문과 관련된 현재 소스 파일과 라인 구간을 찾습니다.
2. 검색된 파일과 class를 시작점으로 Neo4j에서 연결된 프로그램, commit, class와 영향 경로를 조회합니다.
3. 검증된 소스 내용과 그래프 관계를 구분해 LLM context에 전달합니다.
4. 답변 아래에 사용된 파일·라인 근거와 그래프 관계도·표를 함께 보여줍니다.

이 seed로 Neo4j에서 주로 세 종류의 근거를 조회합니다.

1. `program → commit → file → class` 영향 경로
2. `class → IMPORTS_CLASS → class` 의존 관계
3. 도메인별 program·file·class 수를 보여주는 domain summary

조회 결과는 중복을 제거하고 유형별로 균형 있게 제한한 뒤, 검증된 소스 근거와 구분된 graph context로 LLM에 전달합니다. 답변 화면에서는 작은 node-edge 관계도와 표로 표시하고, 사용된 graph evidence는 대화 metadata에도 저장합니다.

예를 들어 “결제 승인 후 주문 상태는 어떤 순서로 변경되나요?”라는 질문에서 RAG가 `PaymentService.java`를 찾으면, GraphRAG는 이 파일의 `PaymentService` class가 어떤 class를 import하는지, 어떤 commit이 이 파일을 변경했는지, 그 commit이 어떤 프로그램에 Mapping됐는지를 연결해 보여줄 수 있습니다. `PaymentController → PaymentService → OrderStatusService → OrderStatusMapper` 같은 실제 호출 순서는 그래프만으로 단정하지 않고, 현재 Java 소스에서 메서드 단위 근거를 다시 확인합니다.

GraphRAG는 현재 코드 사실을 단독으로 증명하지 않습니다. 검증된 `source_file` 근거가 없으면 graph만으로 답변하지 않으며, Neo4j가 비활성화됐거나 graph가 오래된 경우에는 일반 RAG 답변만 사용합니다. 실제 메서드 호출 순서와 조건식은 graph의 import 관계가 아니라 현재 Java 소스를 다시 읽는 별도 검증 로직으로 확인합니다.

## Q. 프로그램 소스가 변경되면 GraphRAG는 어떻게 하나?

프로그램 소스가 변경되면 GraphRAG 그래프를 자동으로 그대로 신뢰하지 않고, 먼저 `갱신 필요` 상태로 표시합니다.

변경 사항이 커밋된 뒤에는 Git Sync를 공통 출발점으로 RAG 인덱스와 Graph를 각각 갱신합니다. Graph가 새 RAG chunk나 vector를 입력으로 받는 순차 의존 관계는 아닙니다.

1. `Git Sync`가 새 커밋과 변경 파일, diff를 PostgreSQL에 수집합니다.
2. 새 commit의 프로그램 연결이 필요하면 Mapping을 실행해 `ProgramCommitMapping`을 갱신합니다. Mapping 후 graph를 다시 갱신하지 않으면 해당 연결이 구버전으로 남아 `stale`로 표시됩니다.
3. 일반 RAG 경로는 `최신 변경분 반영`으로 변경된 소스 chunk를 다시 만들고 embedding이 없는 항목의 vector를 생성합니다.
4. Graph 경로는 `Knowledge Graph`의 `최신 변경분만 Neo4j 반영`으로 PostgreSQL의 Git·Mapping 데이터와 현재 Java 파일을 직접 읽습니다.
5. Graph service가 변경된 Java 파일의 class·import 관계와 commit–file–program 연결을 증분 upsert한 뒤 현재 `Repo HEAD`와 `Graph HEAD`를 맞춥니다.
6. `Project Chat`은 갱신된 RAG 소스 근거와 Graph 관계 근거를 질문 시점에 결합합니다.

그래프가 오래된 상태에서는 관계 질문 기능을 제한하고, `Project Chat`이 오래된 관계를 최신 사실처럼 사용하지 않도록 합니다. 그래프를 사용할 수 없더라도 현재 파일과 일치한다고 검증된 소스가 있으면 일반 RAG 방식으로는 답변할 수 있습니다.

전체 그래프를 매번 다시 만드는 것이 아니라 변경된 부분만 반영하기 때문에 대규모 저장소에서도 갱신 비용을 줄였습니다. 다만 브랜치가 크게 변경됐거나 그래프 관계가 어긋난 경우에는 `전체 재동기화`를 실행합니다.

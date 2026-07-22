# 시연 Runbook

이 문서는 2026년 7월 23일 목요일 시연을 위한 진행 대본과 당일 점검 기준입니다. 운영 전환을 승인받는 발표가 아니라, `AX Use Case` 과제로 만든 결과와 검증 가능한 화면을 짧게 공유하는 자리로 가정합니다.

## 시연 기준

| 항목 | 기준 |
|---|---|
| 권장 시간 | 핵심 시연 10~12분 + 질의응답 10분 |
| 압축 시간 | 5분 |
| 실행 위치 | 발표 PC의 Docker Streamlit |
| 접속 방식 | Chrome 원격 데스크톱 |
| 앱 URL | `http://127.0.0.1:8501/?project_id=1` |
| 시연 프로젝트 | `Sample Shop Demo` (`project_id=1`) |
| 샘플 저장소 | `C:\dev\ai-advisor-sample-shop`, 48 commits |
| Chat model | `qwen2.5-coder-7b-instruct` |
| Embedding model | `text-embedding-nomic-embed-text-v2-moe` (`Q8_0`), 768 dimensions |
| LM Studio endpoint | host `http://127.0.0.1:12345/v1`, Docker `http://host.docker.internal:12345/v1` |
| LLM context length | 8192 |

기본 원칙은 저장된 검증 결과를 안정적으로 보여주는 것입니다. 시연 중에는 `Git 동기화`, `Mapping 실행`, `리스크 분석 실행`, `전체 소스 다시 읽기`, `Neo4j 동기화`를 누르지 않습니다. 이 작업들은 저장된 분석 상태를 바꾸거나 수 분 이상 걸릴 수 있습니다. 새 Project Chat 질문도 기본 동선에서는 실행하지 않고, 미리 검증한 저장 대화 `#32`를 보여줍니다.

## 새 프로젝트로도 시연할 수 있나

가능합니다. `프로젝트 설정 > 프로젝트/Git 설정`에서 `새 프로젝트`를 선택하고 다른 분석 대상 저장소를 등록할 수 있습니다. 같은 Sample Shop 저장소를 같은 DB의 여러 프로젝트에 연결해도 commit identity는 `(project_id, commit_hash)`로 분리됩니다. 새 프로젝트의 Git 수집, Mapping, RAG/vector, Knowledge Graph는 각각 다시 준비해야 하며 기존 프로젝트의 저장 결과는 이동하지 않습니다.

같은 샘플 저장소로 새 시연 프로젝트를 준비하는 순서:

1. 새 프로젝트명과 `C:\dev\ai-advisor-sample-shop` 경로를 저장합니다.
2. `Git 동기화 > 전체 수집`으로 48개 commit을 수집합니다.
3. `advisor_uploads`의 개발자, 프로그램, 개발계획, 표준용어 Excel 파일을 현재 프로젝트에 업로드합니다.
4. Mapping에서 48개 commit을 분석합니다. Mapping 완료 후 8개 프로그램의 구현상태 분석도 함께 실행됩니다.
5. Risk Analysis를 실행합니다.
6. RAG 검색에서 전체 소스를 읽고 79개 source의 embedding을 준비합니다.
7. Knowledge Graph를 전체 동기화합니다.
8. 대표 Project Chat 질문과 `2325182` AI Code Review를 실행해 저장 결과를 만듭니다.
9. 새 project ID로 `demo_preflight.ps1`를 실행하고 `FAIL=0`인지 확인합니다.

```powershell
$demoProjectId = 1  # 프로젝트/Git 설정 화면에서 확인한 실제 ID로 변경
.\scripts\demo_preflight.ps1 -ProjectId $demoProjectId
```

새 프로젝트 생성 자체는 몇 분이면 되지만, 48개 commit Mapping, 프로그램 구현상태 분석, embedding, GraphRAG, 대표 AI 결과 준비에는 local model 상태에 따라 수십 분에서 한 시간 이상 걸릴 수 있습니다. 발표 당일 새로 만들기보다 전날 전체 흐름을 끝내고 DB dump와 화면 증적을 남깁니다.

다른 실제 저장소를 새로 등록하는 것도 가능하지만, 그 저장소에 맞는 프로그램 목록과 개발계획을 준비해야 Mapping과 AI Progress가 의미를 갖습니다. Java/Spring/MyBatis가 아닌 기술 스택은 source parser와 GraphRAG 관계 추출 범위를 별도로 확인해야 합니다.

## 시연 전에 기억할 숫자

| 화면 | 확인할 상태 | 설명할 때의 주의점 |
|---|---|---|
| Home | 프로그램 8, commit 48, 리스크 프로그램 8, 운영 점검 `필수 준비 완료` | 리스크 프로그램 수와 Risk Finding 수는 단위가 다릅니다. |
| Dashboard | 계획 90.6%, AI Progress 50.0%, 차이 40.6% | 40.6%p는 지연 확정값이 아니라 검토가 필요한 차이입니다. |
| AI Progress | 최신 구현상태 분석 8건, Mapping 참고값 분리 | AI가 완료를 승인하는 화면이 아닙니다. |
| Risk Analysis | Finding 32건: HIGH 8, MEDIUM 15, LOW 9 | 규칙과 저장 근거가 만든 검토 목록입니다. |
| Project Chat | source 79, vector 79, 코드 `최신`, graph `최신` | 저장 대화 `#32`를 선택합니다. |
| Project Chat `#32` | 실제 답변 source 6건, graph 4건, 검증 `deterministic_repair` | local LLM 초안을 현재 소스 근거로 자동 보정해 저장했습니다. `fallback=True`는 이 보정 경로를 뜻하며 model 연결 실패가 아닙니다. |
| AI Code Review | commit `2325182`, 위험도 보통, bug finding 1건 | 모델 결과는 리뷰 후보이며 최종 결함 판정은 사람이 합니다. |
| Knowledge Graph | node 213, edge 590 | vector 검색과 달리 program-commit-file-class 관계를 확인하는 용도입니다. |

## 10~12분 기본 시나리오

### 0. 시작 — 30초

말할 내용:

> 오늘은 개발계획과 Git 변경 이력을 연결해서, 진척도와 위험 신호를 어떤 근거로 확인할 수 있는지 보여드리겠습니다. 운영 전환 제안보다는 이번 AX Use Case에서 실제로 구현하고 검증한 범위를 짧게 공유드리겠습니다.

화면은 `Home`에서 시작합니다. 현재 프로젝트가 `Sample Shop Demo (1)`인지 먼저 확인합니다.

### 1. Home — 1분

보여줄 것:

1. 프로그램 8개와 commit 48개가 같은 프로젝트 기준으로 묶여 있는지 확인합니다.
2. 계획 진척도 90.6%, AI Progress 50.0%, 차이 40.6%를 가리킵니다.
3. `다음 작업`의 `운영 점검 · 필수 준비 완료`를 보여줍니다.

말할 내용:

> 첫 화면은 계획 데이터, Git 분석, 리스크 결과가 준비됐는지를 확인하는 출발점입니다. 여기서 차이가 크다고 바로 지연으로 판정하지 않고, 어떤 프로그램을 더 확인해야 하는지 다음 화면으로 좁혀 갑니다.

전환 문장:

> 이 차이가 프로젝트 전체에서 어떻게 보이는지 Dashboard로 들어가겠습니다.

### 2. Dashboard와 AI Resource Radar — 1분 30초

보여줄 것:

1. 프로젝트 현황 카드의 계획, AI Progress, 리스크를 짚습니다.
2. `AI Resource Radar`의 우선 확인 항목을 보여줍니다.
3. 아래쪽 자원관리 지표는 길게 설명하지 말고, 검토 순서를 정하는 참고값이라고 말합니다.

말할 내용:

> Dashboard는 보고용 숫자를 하나 더 만드는 화면이 아니라, 어떤 프로그램과 근거부터 확인할지를 정하는 화면입니다. 검토 시간 절감이나 추가 투입 예방 수치는 현재 가정에 따른 추정치라서 실적이나 개인 평가 값으로 쓰지 않습니다.

전환 문장:

> 전체 수치가 왜 낮게 나왔는지는 AI Progress에서 프로그램 단위로 확인할 수 있습니다.

### 3. AI Progress — 1분 30초

보여줄 것:

1. 계획 90.6%, AI Progress 50.0%, 차이 40.6%를 다시 확인합니다.
2. 프로그램별 비교에서 `SMP-CPN-001` 쿠폰 프로그램을 선택합니다.
3. 계획 80%, AI Progress 50%, 관련 commit 4개, 구현상태 `진행중 추정`과 근거 commit을 보여줍니다.

말할 내용:

> AI Progress는 commit 수를 많이 쌓았다고 완료로 올리는 점수가 아닙니다. 프로그램별 구현상태 분석이 현재 관련 commit과 일치할 때만 값을 쓰고, Mapping 값은 관련 변경을 찾기 위한 참고값으로 따로 둡니다. 그래서 계획상 80%여도 완료 근거가 부족하면 50%에서 보수적으로 멈춥니다.

전환 문장:

> 이 차이를 위험 신호로 정리한 결과를 Risk Analysis에서 보겠습니다.

### 4. Risk Analysis — 1분

보여줄 것:

1. 전체 Risk Finding 32건을 보여줍니다.
2. HIGH 8, MEDIUM 15, LOW 9를 확인합니다.
3. `계획 대비 AI 진척 차이`와 근거 설명을 한 건 펼쳐 봅니다.

말할 내용:

> Risk Analysis는 장애나 일정 지연을 확정하는 기능이 아닙니다. 계획과 구현 근거의 차이, 일정, Mapping 상태를 규칙으로 묶어 사람이 먼저 확인할 목록을 만듭니다. Home의 리스크 프로그램 8개와 여기의 Finding 32건은 프로그램 수와 발견 건수의 차이입니다.

전환 문장:

> 숫자만으로는 원인을 설명하기 어려우니, 현재 코드 근거를 질문으로 찾아보겠습니다.

### 5. Project Chat과 GraphRAG — 2분 30초

보여줄 것:

1. `답변 근거 상태`에서 source 79, 검색 준비 79/79, 코드 반영 `최신`, 추가 준비 0을 확인합니다.
2. `Knowledge Graph가 최신입니다` 안내를 보여줍니다.
3. 저장된 대화에서 `#1`을 선택합니다. 질문은 네 Java 파일을 지정하고 결제 조건과 `PAID` 전환의 직접 호출 흐름을 묻습니다.
4. `PaymentController.authorize → PaymentService.authorize → OrderStatusService.markPaid → OrderStatusService.changeStatus`와 두 Mapper 호출을 단계별로 짚습니다.
5. `답변 근거 보기`와 `그래프 관계 근거 보기`를 펼쳐 source 6건, graph 4건, 검증 `valid`, `class_import`, `impact_path`를 보여줍니다.

말할 내용:

> Project Chat은 모델 기억만으로 답하지 않고, 현재 저장소에서 확인한 소스 조각과 Knowledge Graph 관계를 함께 전달합니다. 이번 저장 답변은 직접 호출 순서와 조건식, 파일 근거 검증을 통과했습니다. 검증 상태와 source·graph 근거 수를 화면에서 확인할 수 있습니다.

주의:

- 기본 시연에서는 새 질문을 보내지 않습니다. 요청을 받았을 때만 같은 질문을 실행하며, local model 응답에 약 5~45초가 걸릴 수 있다고 먼저 말합니다.
- 답변에 어색한 설명이 있으면 숨기지 말고 source와 graph 근거를 기준으로 확인해야 한다고 설명합니다.

전환 문장:

> 같은 코드 변경을 질문이 아니라 리뷰 대상으로 보면 어떻게 나타나는지도 이어서 보겠습니다.

### 6. AI Code Review — 1분 30초

보여줄 것:

1. 가장 최근 저장 결과가 특정 commit `2325182`인지 확인합니다.
2. 요약의 `pilot channel`, 위험도 `보통`, `PaymentService.java`를 보여줍니다.
3. bug finding에서 `amount == 0` 또는 `0원 결제`가 새로 허용되는 경계값을 짚습니다.
4. `리팩토링 제안이 없습니다`를 보여 중복 제안을 억지로 만들지 않는 것도 설명합니다.

말할 내용:

> 이 commit은 검증 조건이 `amount <= 0`에서 `amount < 0`으로 바뀌어 `amount == 0`이 새로 허용되는 변경입니다. Code Review는 diff를 읽어 이 경계값을 bug 후보로 남깁니다. 기존 정적 분석이나 사람의 리뷰를 대체하기보다, 먼저 확인할 변경과 질문을 좁히는 용도입니다.

### 7. 마무리 — 30초

말할 내용:

> 이번 결과의 핵심은 AI가 프로젝트 상태를 대신 결정하는 것이 아니라, 개발계획과 commit, 현재 소스, 관계 근거를 한 흐름에서 찾아볼 수 있게 만든 점입니다. 다음 단계에서는 실제 프로젝트 한 곳을 대상으로 Mapping 정확도, 답변 근거 적합성, 리뷰 재현 시간과 절감 시간을 측정해야 합니다.

질문이 기술 운영 쪽이면 `AI 운영 현황`에서 provider, embedding, GraphRAG, 호출 이력을 추가로 보여줍니다. 질문이 없으면 여기서 화면 시연을 끝냅니다.

## 5분 압축 시나리오

시간이 줄면 아래 네 화면만 보여줍니다.

1. `Home` — 8 programs, 48 commits, 계획 90.6%, AI Progress 50.0%, 준비 완료.
2. `Dashboard` — 전체 차이와 Radar가 검토 순서를 정한다는 점.
3. `Project Chat #32` — 현재 source 79/79, graph 최신, 직접 호출 흐름과 실제 답변 근거 6+4건.
4. `AI Code Review 2325182` — `amount == 0` 경계값 bug 후보.

압축 마무리 문장:

> 계획과 Git을 연결해 차이를 찾고, 현재 소스와 관계 근거로 원인을 확인한 뒤, 특정 변경의 리뷰 후보까지 이어지는 흐름을 구현했습니다.

## 예상 질문과 답변

| 예상 질문 | 짧은 답변 |
|---|---|
| 기존 프로젝트 Dashboard와 무엇이 다른가요? | 일정 숫자만 모으는 대신 개발계획, commit/diff, 현재 소스, program-file-class 관계를 한 프로젝트 기준으로 연결하고 근거까지 내려가게 한 점이 다릅니다. |
| AI가 진척도를 결정하나요? | 아닙니다. 프로그램 단위 구현상태를 보수적으로 추정해 확인 대상을 좁히며, 완료 승인과 일정 판단은 담당자가 합니다. |
| 계획 90.6%와 AI Progress 50% 차이가 곧 지연인가요? | 아닙니다. 최신 구현 근거와 계획의 차이가 크다는 점검 신호입니다. 프로그램 상세와 담당자 확인을 거쳐야 합니다. |
| Home은 리스크 8인데 Risk 화면은 32인 이유가 뭔가요? | 8은 리스크가 있는 프로그램 수이고, 32는 한 프로그램에 여러 유형이 생길 수 있는 Risk Finding 수입니다. |
| Mapping 38건인데 commit은 48개면 실패한 건가요? | 아닙니다. 48개 commit 모두 분석됐고, 38은 program-commit 관계 행 수입니다. 한 commit에 관계가 없거나 여러 관계가 생길 수 있어 완료 기준으로 쓰지 않습니다. |
| AI 답변이 틀리면 어떻게 하나요? | 답변 아래 verified source와 graph 관계를 확인하고, 근거가 부족하면 부족 상태로 표시합니다. 최종 판단은 코드와 담당자 검토로 확정합니다. |
| 왜 GraphRAG가 필요한가요? | vector 검색은 비슷한 문장을 찾는 데 적합하고, GraphRAG는 program-commit-file-class 연결 경로를 설명할 때 유용합니다. 두 근거를 함께 사용합니다. |
| 현재 코드가 반영됐는지 어떻게 아나요? | Project Chat이 저장소 HEAD와 source index metadata를 비교해 `최신`, stale, 재인덱싱 필요 상태를 표시합니다. 이번 시연은 79/79로 확인했습니다. |
| Code Review는 SonarQube나 GitHub review를 대체하나요? | 대체하지 않습니다. diff의 의미와 경계값 위험을 먼저 제시해 사람 리뷰와 기존 정적 분석을 보조합니다. |
| 같은 commit을 다시 돌리면 같은 결과가 나오나요? | 핵심 경계값은 재현되도록 prompt와 후처리를 보강했지만 문장과 세부 제안은 모델 상태에 따라 달라질 수 있습니다. 시연에서는 검증한 저장 결과를 사용합니다. |
| 왜 local LLM을 썼나요? | PoC에서 코드가 외부 API로 나가지 않는 실행 경로와 OpenAI-compatible provider 교체 구조를 검증하기 위해서입니다. 운영 보안 통제까지 완료됐다는 뜻은 아닙니다. |
| 어떤 모델을 썼나요? | Chat과 Code Review는 `qwen2.5-coder-7b-instruct`, embedding은 `text-embedding-nomic-embed-text-v2-moe` `Q8_0` 768 dimensions를 사용합니다. |
| 응답이 왜 느린가요? | 7B local model을 발표 PC 자원으로 실행하므로 질문 길이와 현재 부하에 따라 약 5~45초가 걸립니다. 저장 결과를 기본으로 보여주는 이유입니다. |
| 실제 GitHub에 바로 연결되나요? | 현재는 app-server가 접근하는 Git 저장소 경로를 분석합니다. 운영하려면 중앙 clone/fetch, 인증, branch 정책, 접근 통제를 실제 환경에 맞게 붙여야 합니다. |
| 개발자 PC의 미커밋 코드도 볼 수 있나요? | 중앙 앱이 접근하는 저장소의 작업트리만 볼 수 있습니다. 개인 PC의 미커밋 변경을 자동으로 읽는 구조는 아닙니다. |
| 실시간 분석인가요? | 아닙니다. 현재 PoC는 Git 동기화와 분석을 명시적으로 실행하는 batch 방식입니다. 비용과 local PC 부하를 통제하기 위한 선택입니다. |
| Java 외 다른 언어도 되나요? | 이번 검증 범위는 Spring/MyBatis 샘플입니다. 다른 언어는 file parser와 class 관계 추출 정확도를 별도 평가해야 합니다. |
| 2.5시간 절감, 1.2MM 같은 숫자는 실제 성과인가요? | 아닙니다. 현재 규칙과 가정에 따른 참고 추정치입니다. 실제 효과는 pilot에서 기준 시간과 사후 시간을 함께 측정해야 합니다. |
| 개발자 평가에 쓸 수 있나요? | 현재 지표는 프로젝트 검토 순서를 위한 신호이며 개인 성과 평가용이 아닙니다. commit 수만으로 생산성을 판단하지 않습니다. |
| 샘플 결과를 실제 프로젝트 정확도로 봐도 되나요? | 안 됩니다. 시나리오를 설계한 48-commit 샘플에서 end-to-end 흐름을 검증한 결과입니다. 실제 프로젝트로 정확도와 운영 비용을 다시 측정해야 합니다. |
| 운영 전환에 무엇이 더 필요한가요? | 실제 repo pilot, 접근 권한과 비밀정보 처리, 모델·embedding 용량, 정답 데이터 기반 품질 기준, 장애/백업, 사용 로그와 책임 범위가 필요합니다. |
| 데이터는 어디에 저장되나요? | 프로젝트 분석 결과와 vector는 PostgreSQL/pgvector, 관계 그래프는 Neo4j, model은 local LM Studio에서 실행됩니다. 운영 보존 기간과 삭제 정책은 별도로 정해야 합니다. |

## 장애별 대체 동선

| 상황 | 바로 할 일 | 보여줄 자료 |
|---|---|---|
| LM Studio가 응답하지 않음 | live 질문과 새 Code Review를 생략하고 저장 결과만 사용 | 앱의 Project Chat `#32`, 저장 Code Review `2325182` |
| Project Chat 답변이 늦음 | 10초가 지나면 “local model 실행 시간”을 설명하고 저장 대화로 전환 | `#32` 또는 13장 발표자료의 Project Chat 장표 |
| Project Chat 답변이 어색함 | 답변을 방어하지 말고 source/graph 근거 확인 흐름을 보여줌 | `답변 근거 보기`, `그래프 관계 근거 보기` |
| PostgreSQL 또는 Streamlit 장애 | 한 번만 health와 process를 확인하고, 2분 안에 복구되지 않으면 화면 자료로 전환 | `outputs\20260630_0547_application-preview-summary.pptx` |
| Neo4j 장애 | GraphRAG 확장을 생략하고 source evidence만 설명 | 저장 screenshot과 13장 발표자료의 GraphRAG 장표 |
| Chrome 원격 데스크톱 지연 | animation/scroll을 줄이고 이미 열린 탭만 이동 | 13장 발표자료 |
| Chrome 원격 데스크톱 연결 끊김 | 재접속을 한 번 시도하고 2분 안에 안 되면 로컬 참석 팀원에게 PPT 공유 요청 | 아래 대체 발표자료 |
| 앱 프로젝트 선택이 바뀜 | sidebar에서 `Sample Shop Demo (1)` 선택 | Home의 8 programs/48 commits로 재확인 |
| Code Review 최신 결과가 다른 commit | 실행 버튼을 누르지 말고 리뷰 기록에서 `2325182` 결과 확인 | 13장 발표자료의 Code Review 장표 |
| 시간이 5분으로 줄어듦 | Home → Dashboard → Project Chat → Code Review만 진행 | 5분 압축 시나리오 |

대체 발표자료 우선순위:

1. 발표용 최신 로컬 수정본: `outputs\20260630_0735_ai-use-case-team-share_수정1_로컬.pptx`
2. 13장 검증본: `outputs\ai-use-case-team-share.pptx`
3. 전체 화면 순회용 24장 자료: `outputs\20260630_0547_application-preview-summary.pptx`

## 기동 절차

시연 전날 한 번 재부팅한 뒤 통합 script로 전체 조건을 확인합니다. 당일에는 정상 동작 중인 서비스와 Quick Tunnel을 불필요하게 재시작하지 않습니다.

### 1. 기준 명령

```powershell
.\scripts\demo_start.ps1
```

이 명령은 다음 순서를 지킵니다.

1. Docker daemon이 없을 때만 Docker Desktop을 시작합니다.
2. LM Studio port `12345`를 확인하고, 필요한 경우 Chat model과 embedding model만 로드합니다.
3. Chat model의 `contextLength=8192`를 확인합니다. 다른 값으로 이미 로드돼 있으면 임의로 unload하지 않고 오류로 알려줍니다.
4. Docker app이 꺼져 있을 때 `docker compose up -d app`으로 기본 DB `ai_commit_advisor`, Neo4j, 8501 앱을 기동합니다.
5. 기존 `ai_commit_advisor_demo_tunnel` 또는 legacy `ai_commit_advisor_quick_tunnel`을 먼저 찾아 주소를 재사용합니다. 명시적인 종료 요청이 없으면 Tunnel을 중지하지 않으며, Docker daemon 재시작 뒤에는 현재 실행에서 새로 발급된 URL을 확인합니다.
6. local health와 `demo_preflight.ps1 -ProjectId 1`을 실행합니다.

코드나 Docker image가 바뀐 경우에만 `-Build`, 실행 중인 Tunnel이 없고 외부 주소가 필요한 경우에만 `-StartTunnel`을 사용합니다.

```powershell
.\scripts\demo_start.ps1 -Build
.\scripts\demo_start.ps1 -StartTunnel
```

현재 상태만 확인하려면 어떤 서비스도 시작하지 않는 check-only 모드를 사용합니다.

```powershell
.\scripts\demo_start.ps1 -CheckOnly
```

### 2. 수동 확인이 필요할 때

이 PC에서는 Windows 제외 포트 범위에 `1234`가 포함돼 있어 LM Studio server가 `EACCES`로 시작되지 않습니다. 시연 환경은 `12345` 하나만 사용합니다. 먼저 `ps`로 현재 상태를 확인하고, 없는 항목만 시작하거나 로드합니다.

```powershell
$lms = "$env:USERPROFILE\.lmstudio\bin\lms.exe"
& $lms ps --port 12345 --json
& $lms server start --port 12345
& $lms load "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/qwen2.5-coder-7b-instruct-q4_k_m.gguf" --port 12345 --identifier qwen2.5-coder-7b-instruct --context-length 8192 --yes
& $lms load "text-embedding-nomic-embed-text-v2-moe" --port 12345 --identifier text-embedding-nomic-embed-text-v2-moe --context-length 512 --gpu max --yes
docker compose up -d app
docker compose ps
```

이미 실행 중인 model과 server에는 해당 start/load 명령을 반복하지 않습니다. host script용 `.env`는 `http://127.0.0.1:12345/v1`, Docker는 `http://host.docker.internal:12345/v1`을 사용합니다.
`ai_commit_advisor_app`과 `ai_commit_advisor_postgres`가 `healthy`, `ai_commit_advisor_neo4j`가 `Up`인지 확인합니다. Docker 앱은 기본 DB `ai_commit_advisor`, 실제 local LLM/embedding, 768차원을 사용합니다. 별도 override가 필요할 때만 `.env`에 `DOCKER_LLM_*`, `DOCKER_EMBEDDING_*`, `DOCKER_PGVECTOR_DIMENSION`을 둡니다.

### 3. Streamlit과 외부 URL

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8501/_stcore/health
.\.venv\Scripts\python.exe scripts\quick_tunnel.py status
```

로컬에서는 `http://127.0.0.1:8501/?project_id=1`을 엽니다. `status`가 정상 URL을 출력하면 기존 Tunnel을 그대로 사용하고 주소 뒤에 `/?project_id=1`을 붙입니다. 실행 중인 Tunnel이 없을 때만 `demo_start.ps1 -StartTunnel`을 사용합니다. Tunnel process가 Docker daemon 재시작 등으로 다시 뜨면 Quick Tunnel URL도 바뀔 수 있으므로 과거 주소 대신 `status`가 표시한 현재 URL을 사용합니다. 화면 자체를 원격으로 조작할 때는 Chrome 원격 데스크톱을 사용할 수 있습니다.

### 4. 사전 점검 결과

```powershell
.\scripts\demo_preflight.ps1 -ProjectId 1
```

통합 script가 실행하는 preflight의 정상 기준은 `FAIL=0`입니다. 저장 분석 HEAD와 현재 샘플 저장소 HEAD가 `221eb9ac9c83`으로 일치해야 합니다. 불일치 경고가 나오면 원인을 확인하기 전까지 `Git 동기화`와 `Mapping 실행`을 누르지 않습니다. `-SkipPreflight`는 문제 원인을 이미 알고 별도로 검증할 때만 사용합니다.

## 당일 체크리스트

### 수요일 최종 리허설

- [ ] `demo_start.ps1 -CheckOnly`가 끝까지 통과하고 내부 preflight가 `FAIL=0`으로 끝난다.
- [ ] Chrome 원격 데스크톱으로 다른 기기에서 한 번 접속하고 끊은 뒤 재접속한다.
- [ ] 기본 시나리오를 소리 내어 12분 안에 한 번 끝낸다.
- [ ] 5분 압축 시나리오도 한 번 실행한다.
- [ ] Project Chat `#32`와 AI Code Review `2325182`가 저장돼 있는지 확인한다.
- [ ] 세 개의 대체 PPTX를 실제로 열어 본다.

### 목요일 T-60분

- [ ] 전원 어댑터를 연결한다.
- [ ] Windows 자동 절전과 화면 꺼짐을 시연 시간 동안 사용하지 않도록 설정한다.
- [ ] Docker Desktop, PostgreSQL, Neo4j, LM Studio, Streamlit을 확인한다.
- [ ] `demo_start.ps1 -CheckOnly`를 실행한다.
- [ ] Windows Update, 재부팅 예약, 대용량 download를 멈춘다.

### T-20분

- [ ] Chrome 원격 데스크톱으로 재접속해 mouse, keyboard, scroll이 동작하는지 확인한다.
- [ ] Chrome 창 하나만 사용하고 zoom 100%로 맞춘다.
- [ ] 앱 탭, 13장 발표자료, 24장 화면 자료를 미리 연다.
- [ ] 앱은 Home, 프로젝트는 `1`로 맞춘다.
- [ ] 알림, 메신저 popup, mail popup을 끈다.
- [ ] 개인 정보나 다른 프로젝트 tab이 화면에 남아 있지 않은지 확인한다.

### T-5분

- [ ] `http://127.0.0.1:8501/_stcore/health`가 `ok`인지 확인한다.
- [ ] Home이 8 programs, 48 commits, `필수 준비 완료`를 표시하는지 확인한다.
- [ ] 더 이상 Git sync, reindex, Mapping, Risk, graph sync를 실행하지 않는다.
- [ ] 물 한 잔과 첫 문장, 마지막 문장만 다시 확인한다.

## 하지 않을 것

- 시연 직전에 sample data를 다시 만들지 않습니다.
- 저장 결과가 정상인데 model, DB, 앱을 재시작하지 않습니다.
- 숫자를 실제 절감 성과나 개발자 생산성으로 단정하지 않습니다.
- AI 답변의 어색한 문장을 즉석에서 변명하지 않습니다. source와 graph 근거로 확인 범위를 설명합니다.
- 질문을 받았다고 production readiness, 보안 통제, 다언어 정확도가 이미 검증됐다고 넓혀 말하지 않습니다.

# 시연 Q&A

## Q. AI는 어디에 활용됐나?

AI는 크게 다섯 부분에 활용됐습니다.

첫째, Git 커밋과 변경 파일을 분석해 어떤 프로그램과 관련된 변경인지 매핑합니다.

둘째, 관련 커밋 전체를 바탕으로 프로그램별 구현 상태를 판단하고, 계획 진척도와 비교해 `AI Progress`로 보여줍니다.

셋째, 소스 코드를 임베딩으로 검색한 뒤 `Project Chat`에서 현재 코드와 GraphRAG 관계를 근거로 질문에 답합니다. 이때 파일과 라인 등 답변 근거도 함께 제공합니다.

넷째, 특정 커밋의 diff를 분석해 버그 가능성과 개선 사항을 제안하는 `AI Code Review`에 사용했습니다.

다섯째, 이미 계산된 리스크와 진척도 근거를 PL 회의용 브리핑으로 요약합니다.

다만 모든 판단을 AI에 맡긴 것은 아닙니다. 일정 지연, 담당자 누락 같은 `Risk Analysis`와 우선순위 점수는 설명 가능한 규칙으로 계산하고, AI는 코드의 의미를 해석하거나 근거를 요약하는 역할에 집중했습니다. 또한 시연 환경에서는 로컬 LLM과 임베딩 모델을 사용해 프로젝트 코드가 외부로 전달되지 않도록 구성했습니다.

## Q. GraphRAG는 구체적으로 어떻게 활용했나?

GraphRAG는 단순히 소스 문장을 검색하는 RAG에 코드 간 관계 정보를 추가하는 방식으로 활용했습니다.

먼저 Git과 분석 데이터를 바탕으로 Neo4j에 `프로젝트–프로그램–커밋–파일–Java 클래스–도메인` 관계를 저장합니다. Java의 import와 클래스 연결 관계도 함께 구성합니다.

사용자가 `Project Chat`에서 질문하면 다음 순서로 동작합니다.

1. 임베딩 검색으로 질문과 관련된 현재 소스 파일을 찾습니다.
2. 검색된 파일과 클래스를 시작점으로 Neo4j에서 연결된 프로그램, 커밋, 클래스와 영향 경로를 조회합니다.
3. 검증된 소스 내용과 그래프 관계를 함께 LLM에 전달합니다.
4. 답변 아래에 사용된 파일·라인 근거와 그래프 관계도를 구분해 보여줍니다.

예를 들어 “결제 승인 후 주문 상태는 어떤 순서로 변경되나요?”라고 질문하면, 소스 내용뿐 아니라 `PaymentController → PaymentService → OrderStatusService → OrderStatusMapper`와 같은 호출·의존 관계를 찾아 전체 흐름을 설명할 수 있습니다.

중요한 점은 그래프 관계만으로 코드 동작을 단정하지 않는다는 것입니다. 현재 소스와 일치한다고 검증된 근거가 있어야 사실로 답하고, GraphRAG는 영향 범위와 연결 구조를 설명하는 보조 근거로 사용했습니다. Neo4j가 준비되지 않았거나 그래프가 오래된 경우에는 일반 RAG 방식으로만 답변합니다.

## Q. 프로그램 소스가 변경되면 GraphRAG는 어떻게 하나?

프로그램 소스가 변경되면 GraphRAG 그래프를 자동으로 그대로 신뢰하지 않고, 먼저 `갱신 필요` 상태로 표시합니다.

변경 사항이 커밋된 뒤의 갱신 흐름은 다음과 같습니다.

1. `Git Sync`가 새 커밋과 변경 파일, diff를 PostgreSQL에 수집합니다.
2. RAG의 `최신 변경분 반영`으로 변경된 소스만 다시 인덱싱합니다.
3. 새 소스 청크 중 임베딩이 없는 항목만 임베딩을 생성합니다.
4. `Knowledge Graph`에서 `최신 변경분만 Neo4j 반영`을 실행합니다.
5. 변경된 Java 파일의 클래스와 import 관계, 커밋–파일–프로그램 연결만 증분 갱신합니다.
6. 갱신이 끝나면 현재 `Repo HEAD`와 `Graph HEAD`를 맞추고 GraphRAG를 다시 사용할 수 있게 합니다.

그래프가 오래된 상태에서는 관계 질문 기능을 제한하고, `Project Chat`이 오래된 관계를 최신 사실처럼 사용하지 않도록 합니다. 그래프를 사용할 수 없더라도 현재 파일과 일치한다고 검증된 소스가 있으면 일반 RAG 방식으로는 답변할 수 있습니다.

전체 그래프를 매번 다시 만드는 것이 아니라 변경된 부분만 반영하기 때문에 대규모 저장소에서도 갱신 비용을 줄였습니다. 다만 브랜치가 크게 변경됐거나 그래프 관계가 어긋난 경우에는 `전체 재동기화`를 실행합니다.

## Q. RAG는 최신 변경분만 반영하도록 어떻게 했나?

Git Sync가 저장한 변경 파일 목록과 마지막으로 인덱싱한 commit을 기준으로 증분 인덱싱하도록 구현했습니다.

사용자가 RAG 또는 `Project Chat`에서 `최신 변경분 반영`을 실행하면, 최근 indexed HEAD 이후의 `CommitFile`만 확인합니다. 따라서 저장소 전체를 다시 읽지 않고 다음과 같이 변경 종류별로 처리합니다.

- 추가·수정·복사된 소스 파일은 기존 청크를 교체하고 현재 내용으로 새 청크를 만듭니다.
- 삭제된 파일은 해당 소스 청크와 연결된 vector를 제거합니다.
- 이름이 변경된 파일은 이전 경로의 데이터를 제거하고 새 경로를 인덱싱합니다.
- 이미지, Excel, binary, cache, virtualenv, 너무 큰 파일과 저장소 밖의 경로는 제외합니다.

새 청크에는 `embedding_status=pending`을 기록합니다. 이 단계에서 임베딩을 자동 생성하지 않고, 사용자가 `RAG 검색 > 검색 준비`를 실행했을 때 현재 embedding model의 vector가 없는 청크만 제한된 수량으로 생성합니다. 이미 같은 청크와 모델 조합의 vector가 있으면 재사용합니다.

이렇게 소스 인덱싱 범위와 임베딩 호출 범위를 모두 변경된 부분으로 제한했습니다. Git Sync 직후 자동 실행하지 않는 이유는 cloud embedding 비용이나 local LM Studio의 GPU 부하를 사용자가 통제할 수 있게 하기 위해서입니다. 최초 구축, 큰 브랜치 변경 또는 인덱스 불일치가 의심될 때만 `전체 소스 다시 읽기`를 사용합니다.

## Q. 커밋 내용만으로 어떻게 관련 청크를 찾나?

여기서 커밋 내용은 커밋 메시지만 의미하지 않습니다. 커밋 해시, 메시지, 작성자, 변경 파일 경로와 diff 일부를 하나의 검색 질의로 구성합니다. 현재 구현은 최대 20개 변경 파일 경로와 최대 3개 파일의 diff 일부를 포함하고, 전체 질의 길이도 제한해 과도한 입력을 막습니다.

이 질의를 embedding으로 변환한 뒤 같은 프로젝트의 `program` 청크와 vector 유사도를 비교합니다. `program` 청크에는 프로그램 ID, 프로그램명, 모듈, 화면명과 설명이 들어 있습니다. 유사도가 높은 프로그램을 최대 10개 후보로 가져옵니다.

Vector 검색만 사용하지는 않습니다. 프로그램 정보와 커밋 메시지·파일 경로·diff의 단어가 얼마나 겹치는지도 계산하고, 모듈명이나 프로그램명이 파일 경로에 포함되면 가중치를 더합니다. Vector 검색 후보와 token 유사도 후보를 합치고 중복을 제거한 뒤 LLM에 전달합니다. LLM은 이 후보 안에서 실제 관련 프로그램, 관련도 점수, 구현상태와 판단 근거를 결정합니다.

따라서 Mapping 단계에서 찾는 청크는 임의의 전체 소스 청크가 아니라 우선 `program` 후보 청크입니다. 현재 소스 청크를 검색해 답변하는 과정은 `Project Chat`의 별도 RAG 흐름입니다. 커밋 메시지와 diff가 부실하거나 프로그램 설명이 부족하면 후보를 놓칠 수 있으므로, 낮은 관련도나 판단불가 결과는 Mapping 리뷰 큐에서 사람이 확인하도록 했습니다.

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

## Q. 즉, RAG는 관련 소스 파일 후보를 찾기 위한 진입 목적으로 봐도 되는가?

`Project Chat` 기준으로는 대체로 맞습니다. RAG의 첫 번째 역할은 전체 저장소를 LLM에 보내지 않고, 질문과 관련성이 높은 소스 파일과 라인 구간을 빠르게 좁히는 것입니다.

다만 후보 파일을 찾는 것으로 끝나지는 않습니다. 검색된 소스 청크가 실제 파일과 일치하는지 검증을 통과하면, 그 청크 내용 자체가 LLM의 답변 context와 파일·라인 citation으로 사용됩니다. Java 관계 질문에서는 검색된 파일과 클래스가 GraphRAG 탐색 및 메서드 단위 검증의 시작점도 됩니다.

따라서 전체 흐름은 다음과 같이 설명할 수 있습니다.

1. RAG가 관련 소스 청크 후보를 찾습니다.
2. 애플리케이션이 해당 청크를 현재 파일과 비교해 검증합니다.
3. 검증된 청크를 실제 답변 근거로 LLM에 전달합니다.
4. 필요하면 해당 파일과 클래스를 시작점으로 GraphRAG 관계를 추가합니다.

즉 RAG는 관련 소스를 찾는 진입점이면서, 검증을 통과한 뒤에는 답변을 제한하는 근거 계층이기도 합니다. 검색되지 않았거나 검증되지 않은 코드는 LLM이 임의로 추측하지 않도록 했습니다.

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

## Q. GraphRAG는 구체적으로 무엇을 어떻게 저장하고 활용하는가?

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

### 어떻게 활용하는가

`Project Chat`에서 먼저 일반 RAG가 질문과 관련된 현재 소스 청크를 찾고 실제 파일과 일치하는지 검증합니다. 그다음 질문, 한글 업무용어 확장 결과와 검색된 파일·class·program·commit 정보에서 GraphRAG 검색어인 seed를 추출합니다.

이 seed로 Neo4j에서 주로 세 종류의 근거를 조회합니다.

1. `program → commit → file → class` 영향 경로
2. `class → IMPORTS_CLASS → class` 의존 관계
3. 도메인별 program·file·class 수를 보여주는 domain summary

조회 결과는 중복을 제거하고 유형별로 균형 있게 제한한 뒤, 검증된 소스 근거와 구분된 graph context로 LLM에 전달합니다. 답변 화면에서는 작은 node-edge 관계도와 표로 표시하고, 사용된 graph evidence는 대화 metadata에도 저장합니다.

예를 들어 결제 질문에서 RAG가 `PaymentService.java`를 찾으면, GraphRAG는 이 파일의 `PaymentService` class가 어떤 class를 import하는지, 어떤 commit이 이 파일을 변경했는지, 그 commit이 어떤 프로그램에 Mapping됐는지를 연결해 보여줄 수 있습니다.

GraphRAG는 현재 코드 사실을 단독으로 증명하지 않습니다. 검증된 `source_file` 근거가 없으면 graph만으로 답변하지 않으며, Neo4j가 비활성화됐거나 graph가 오래된 경우에는 일반 RAG 답변만 사용합니다. 실제 메서드 호출 순서와 조건식은 graph의 import 관계가 아니라 현재 Java 소스를 다시 읽는 별도 검증 로직으로 확인합니다.

## Q. 현재 프로젝트에 연결된 AI는 무엇인가?

현재 시연 환경은 외부 cloud AI가 아니라 LM Studio의 OpenAI-compatible API에 연결된 두 개의 local model을 사용합니다.

- LLM: `qwen2.5-coder-7b-instruct`
- Embedding: `text-embedding-nomic-embed-text-v2-moe`

`qwen2.5-coder-7b-instruct`는 프로그램-commit Mapping, 프로그램 구현상태 분석, `Project Chat`, `AI Code Review`와 PL Briefing 요약에 사용합니다.

`text-embedding-nomic-embed-text-v2-moe`는 소스·프로그램·commit·diff 청크와 질문을 vector로 변환해 RAG 검색 및 Mapping 후보 검색에 사용합니다. 현재 vector dimension은 768이며, 문서와 질문에 서로 다른 Nomic retrieval task profile을 적용합니다.

두 모델은 host의 LM Studio `12345` 포트에서 실행됩니다. 로컬 Python은 `http://127.0.0.1:12345/v1`, 현재 Docker 앱은 `http://host.docker.internal:12345/v1`로 같은 서버에 접근합니다. 현재 LM Studio model 목록에서도 두 model이 실제로 로드된 것을 확인했습니다.

LM Studio에는 다른 model도 로드되어 있지만, 앱 설정상 실제 호출 대상으로 지정된 model은 위 두 개입니다. Neo4j와 PostgreSQL/pgvector는 AI model이 아니라 각각 GraphRAG 관계 저장소와 RAG 청크·vector 저장소 역할을 합니다.

## Q. 백엔드, 프론트엔드, DB는 각각 어떤 기술 스택을 사용했나?

이 프로젝트는 React 프론트엔드와 별도 REST API 서버를 나눈 구조가 아니라, Streamlit을 중심으로 화면과 Python service가 함께 실행되는 Python 애플리케이션입니다.

| 영역 | 주요 기술 | 역할 |
|---|---|---|
| 프론트엔드 | `Streamlit 1.41.1` | 페이지, sidebar, form, table과 사용자 workflow 구성 |
| 시각화 | `Plotly 5.24.1`, `streamlit-agraph 0.0.45` | Dashboard chart와 Knowledge Graph 관계도 표시 |
| 데이터 화면·Excel | `pandas 2.2.3`, `openpyxl 3.1.5` | 표 데이터 처리와 Excel 업로드·다운로드 |
| 백엔드 | `Python 3.11` service layer | Git Sync, Mapping, Risk Analysis, RAG, Project Chat, Code Review와 Graph 동기화 처리 |
| ORM·설정 | `SQLAlchemy 2.0.36`, `pydantic-settings 2.7.1` | DB model·transaction과 환경변수 기반 설정 관리 |
| Git 연동 | `GitPython 3.1.43` | 대상 저장소의 commit, 변경 파일과 diff 수집 |
| 기본 DB | `PostgreSQL 16` | 프로젝트, 프로그램, Git 데이터, 분석 결과, 대화와 운영 이력 저장 |
| Vector DB 기능 | PostgreSQL의 `pgvector 0.3.6` | RAG embedding vector 저장과 cosine 유사도 검색 |
| Graph DB | `Neo4j 5 Community` | 프로그램–commit–파일–class–domain 관계를 GraphRAG read model로 저장 |
| DB migration | `Alembic 1.14.0` | PostgreSQL schema version 관리 |
| DB driver | `psycopg2-binary 2.9.10`, `neo4j 6.2.0` | Python에서 PostgreSQL과 Neo4j 연결 |
| 실행 환경 | Docker, Docker Compose | 앱, PostgreSQL과 Neo4j를 분리된 container로 실행 |

핵심 저장소는 PostgreSQL입니다. 업무 데이터와 AI 분석 결과뿐 아니라 RAG 청크와 vector도 PostgreSQL에 저장합니다. Neo4j는 원본 데이터의 source of truth가 아니라 PostgreSQL과 현재 Java 소스에서 만든 관계 탐색용 read model입니다.

정리하면 화면은 Streamlit, 업무·AI 처리 로직은 Python service, 정형 데이터와 vector는 PostgreSQL+pgvector, 관계 graph는 Neo4j를 사용했습니다.

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

## Q. 새 세션에서 `qna ON`으로 Q&A 기록 모드를 켜고 `qna OFF`로 해제할 수 있는가?

가능하며 현재 repository의 `AGENTS.md`에 규칙을 반영했습니다. 새 세션은 이전 대화를 기억하지 않지만, repository 지침을 읽은 agent가 `qna ON/OFF` 명령을 같은 의미로 처리합니다.

현재 프로젝트에만 적용한다면 `AGENTS.md`에 다음 규칙을 추가하는 방식이 적합합니다.

- 기본 상태는 Q&A 모드 `OFF`
- 사용자가 `qna ON`이라고 입력하면 현재 세션의 Q&A 모드를 활성화
- 활성화 중에는 사용자의 질문에 답한 뒤 질문과 답변을 `docs/qna.md`에 자동 추가
- 활성화 중에는 `docs/qna.md` 외의 프로젝트 파일을 읽기 전용으로 취급
- 새 질문을 저장하기 전에 기존 Q&A에서 같은 주제와 유사 질문을 먼저 검색
- 같은 의미의 질문이 있으면 새 항목을 중복 추가하지 않고 기존 질문과 답변을 수정·보완
- 기존 질문의 후속 질문이면 관련 답변 바로 아래에 내용을 통합하고, 서로 다른 설명이 충돌하면 실제 구현과 검증 결과를 기준으로 정리
- 새로운 주제라면 문서 끝에 무조건 추가하지 않고 관련 section의 적절한 위치에 배치하며, 필요하면 주제별 section을 생성·재정렬
- 통합할 때 기존 답변의 고유한 근거나 중요한 한계는 삭제하지 않고, 시연에서 읽기 쉬운 하나의 답변으로 정돈
- 사용자가 `qna OFF`라고 입력하면 자동 기록과 파일 수정 제한을 해제하고 일반 작업 모드로 복귀
- 새 세션에서는 다시 `qna ON`을 입력하기 전까지 기본 `OFF`

따라서 Q&A 모드의 저장 동작은 단순 append가 아니라 기존 문서를 먼저 읽고 `추가`, `통합`, `수정·보완`, `재배치` 중 적절한 방식을 선택하는 것으로 정의할 수 있습니다. 질문 표현이 달라도 답변의 핵심이 같으면 하나로 합치고, 새 질문이 기존 답변의 빈 부분이나 오류를 드러내면 해당 답변을 최신 구현 기준으로 보완합니다.

이 규칙은 현재 repository에 적용됩니다. 여러 프로젝트에서 공통으로 사용하려면 별도의 personal skill로 만드는 편이 적합합니다.

주의할 점은 `qna OFF`가 이미 저장한 Q&A를 삭제한다는 뜻은 아니라는 것입니다. 자동 저장 동작과 `qna.md` 외 파일의 읽기 전용 제한만 해제합니다. 또한 Q&A 모드가 켜진 동안 PR 생성이나 commit처럼 `qna.md` 이외의 상태를 변경하는 작업이 필요하면 사용자가 별도로 허용해야 합니다.

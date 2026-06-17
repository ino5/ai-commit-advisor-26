# 샘플 프로젝트 기능 테스트 가이드

이 문서는 샘플 프로젝트를 이용해 AI Commit Advisor 기능을 검증할 때 어떤 질문과 커밋을 쓰면 좋은지 정리합니다. 샘플 프로젝트 내부에는 답변을 유도하는 Markdown 정답지를 넣지 않고, 여기의 가이드는 앱 저장소에서만 관리합니다.

## 기본 원칙

- AI 결과는 `local_openai` 같은 실제 local LLM provider로 실행한 결과만 데모 증거로 사용합니다.
- mock/fallback 결과는 기능 개발 테스트에는 쓸 수 있지만 `Application Preview`나 사용자 안내의 결과 증거로 쓰지 않습니다.
- 기존 `Application Preview` screenshot은 새 샘플을 별도 경로에서 재생성하고 실제 LLM/embedding/Neo4j 검증을 통과하기 전까지 덮어쓰지 않습니다.
- 샘플 프로젝트 내부 판단 근거는 Java source, MyBatis XML, test/probe class, Git diff, Excel upload 데이터에서 나와야 합니다.

## Project Chat 질문 예시

추천 질문:

- `PaymentController, PaymentService, OrderStatusService는 결제 승인 요청부터 주문 상태를 PAID로 바꾸는 흐름에서 어떻게 이어지는지 한국어로 설명해줘.`
- `결제금액이 0원 이하일 때 어떤 검증 로직이 동작하나요? 관련 파일을 근거로 설명해줘.`
- `쿠폰 할인은 왜 아직 완료로 보기 어렵나요? CouponDiscountService, CouponMapper, CouponPolicyStatus 기준으로 설명해줘.`
- `정산 내보내기는 왜 아직 완료가 아닌가요? SettlementController와 SettlementReadiness 근거로 설명해줘.`
- `운영 대시보드의 stale payment warning은 어떤 조건에서 계산되나요?`

좋은 답변 신호:

- `Provider: local_openai`, `fallback=False`가 화면에 표시됩니다.
- 답변 근거에 `PaymentController.java`, `PaymentService.java`, `OrderStatusService.java`, `DashboardMapper.xml`, `CouponPolicyStatus.java`, `SettlementReadiness.java` 같은 source file이 포함됩니다.
- GraphRAG 질문에서는 `class_import PaymentController -> PaymentService`, `class_import PaymentService -> OrderStatusService`처럼 관계 유형과 node 이름이 함께 보입니다.

나쁜 답변 신호:

- `Mock answer`, `fallback=True`, source file 없는 일반론이 보입니다.
- 정산이나 쿠폰을 controller/class 존재만으로 완료라고 단정합니다.
- `minimum_order_amount`, `NOT_READY`, `EXPORT_FILE_WRITER_READY = false` 같은 source evidence를 놓칩니다.

## AI Code Review 대상

좋게 나와야 하는 high-risk 리뷰:

- `Relax partner payment validation for pilot channel`
- 기대 finding: `amount == 0`이 새로 허용되고 `orderStatusService.markPaid(orderId)`가 실행되어 주문이 결제완료처럼 흘러갈 수 있다는 지적.

좋게 나와야 하는 cross-module 리뷰:

- `Change dashboard summary query across operations modules`
- 기대 finding: `count(o.order_id)`, `count(s.signal_id)`, `count(p.payment_id)`가 join multiplication에 영향을 받아 운영 지표를 과대 집계할 수 있다는 지적.

낮은 위험으로 나와야 하는 리뷰:

- `Refactor dashboard indicator names`
- 기대 결과: behavior change가 작고 naming/refactoring 중심이라는 평가. high-risk bug처럼 과장되면 prompt나 sample evidence를 다시 확인합니다.

비교용 fix commit:

- `Reject zero and negative payment amounts`
- `Fix dashboard summary over-counting`
- 기대 결과: 이전 위험을 줄이는 방향의 수정으로 설명되어야 합니다.

## Mapping, Risk Analysis, AI Progress

확인 포인트:

- `SMP-CPN-001`은 `CouponDiscountService`, `CouponMapper`, `CouponPolicyStatus` source가 있어 partial/in-progress로 읽혀야 합니다.
- `SMP-SET-001`은 plan에는 있지만 assignee가 비어 있고 `SettlementController`가 `NOT_READY`를 반환하므로 complete로 판단하면 안 됩니다.
- `SMP-RPT-001`은 sales report tax fix와 canceled payment query가 연결되어야 합니다.
- `SMP-UI-001`은 dashboard query 변경과 stale payment warning commit을 통해 cross-module 영향이 보여야 합니다.

## Application Preview 보존

현재 preview screenshot 중 AI 결과가 보이는 화면은 실제 local LLM/Neo4j 결과를 기준으로 캡처되어 있습니다. 새 샘플을 검증할 때는 먼저 별도 target path에 생성하고, 기존 project/screenshot state를 덮어쓰기 전에 다음 조건을 확인합니다.

- sample repo commit count와 최신 commit date가 설계 범위와 맞습니다.
- Git Sync, source indexing, embedding, Mapping, Risk/AI Progress, Neo4j graph sync가 실제 provider로 완료됩니다.
- `project-chat-answer`, `project-chat-graph-evidence`, `ai-code-review` capture 조건이 `local_openai`, `fallback=False`, 핵심 source file, mock/fallback 금지를 통과합니다.
- 통과 전에는 `docs/images/features/*.png`를 갱신하지 않습니다.

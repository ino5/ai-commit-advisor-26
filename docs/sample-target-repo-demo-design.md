# 샘플 프로젝트 설계

## 목적

데모용 샘플 프로젝트는 실제 고객 코드나 제품 코드를 사용하지 않고 AI Commit Advisor를 시연하기 위해 존재합니다. Git sync, program mapping, risk analysis, RAG, Project Chat, AI Code Review, AI Progress가 의미 있는 결과를 만들 수 있을 만큼 현실적인 구조를 가져야 합니다.

샘플 프로젝트는 이 애플리케이션 저장소와 의도적으로 분리되어 있습니다.

- 애플리케이션 저장소: `C:\dev\ai-commit-advisor`
- 샘플 프로젝트 Git 저장소: `C:\dev\ai-advisor-sample-shop`
- 생성 스크립트: `scripts/create_sample_target_repo.py`
- 생성된 upload 파일: `C:\dev\ai-advisor-sample-shop\advisor_uploads`

## 현재 상태

현재 샘플 프로젝트는 데모용 Spring MVC + MyBatis retail operations project입니다.

- Programs: 8
- Developers: 6
- Git commits: 30
- Main stack: Java, Spring MVC, JSP, MyBatis XML
- Current domains: orders, inventory, payments, reports, dashboard, coupon, settlement planning
- Generated files: developers, programs, development plans, standard terminology용 program CSV와 upload Excel files

강점:

- 샘플 프로젝트가 애플리케이션 저장소 밖의 sibling Git repository로 격리되어 있습니다.
- Git sync, developer extraction, program upload, development plan upload, Mapping, RAG, Project Chat, Risk Analysis, AI Code Review, Commit Impact, AI Progress 확인에 필요한 구조가 충분합니다.
- package path와 program module이 명확해 program-commit mapping 후보 선택에 도움이 됩니다.
- 생성된 Excel file이 커밋 이력과 서로 맞습니다.
- history에는 feature addition, bug-introducing change, bug fix, test, refactoring, documentation, cross-module change, incomplete work가 포함되어 있습니다.

알려진 한계:

- 샘플은 Maven build 성공보다 분석 가치에 최적화되어 있습니다.
- 코드는 데모용 예제 코드이며 production implementation guidance로 취급하면 안 됩니다.
- 일부 risk scenario는 generated development-plan override를 통해 만들어져 Risk Analysis가 delayed, unassigned, no-related-commit case를 보여줄 수 있게 합니다.

## 목표 데모 규모

권장 목표 규모:

- Programs: 6 to 8
- Developers: 6 to 7
- Commits: 25 to 40
- 선호 기준: 약 30 commits

근거:

- 15개 미만 commit은 smoke test에는 유용하지만 설득력 있는 demo에는 작습니다.
- 약 30개 commit이면 주요 program마다 implementation, fix, test, documentation event를 여러 개 배치할 수 있습니다.
- 70개를 넘는 commit은 발표 가치가 크게 늘지 않으면서 local LLM과 embedding demo를 느리게 만들 수 있습니다.

## 시연해야 할 제품 기능

샘플은 다음 제품 workflow를 의도적으로 지원해야 합니다.

| 제품 기능 | 샘플 데이터 요구사항 | 데모 신호 |
|---|---|---|
| Git Sync | 다양한 author와 date를 가진 25 to 40 commits | Commit table, changed files, diffs, author extraction |
| Developer management | PM, PL, developers, QA, optional operations role | Auto extraction과 의미 있는 roles/skills |
| Program upload | module, screen, description이 있는 6 to 8 business programs | Program table과 mapping candidates |
| Development plan upload | complete, in-progress, delayed, unassigned row 혼합 | AI Progress와 Risk Analysis 차이 |
| Mapping | program-specific commit과 cross-module commit | 관련 program mapping과 다양한 relevance score |
| Program Detail | program별 multiple commits, 일부 program의 multiple contributor | Commit history, contribution split, evidence details |
| Commit Impact | order, inventory, payment, dashboard를 함께 건드리는 commit | 하나의 commit이 여러 program에 영향 |
| Risk Analysis | no related commits, overdue incomplete work, progress gaps, no recent commits, missing assignee | 여러 risk type이 한 번에 표시 |
| RAG Search | current source, docs, commit messages, diffs와 searchable business terms | Source/history retrieval results |
| Project Chat | 현실적인 한국어 업무 질문에 답할 current source, docs, standard terminology | file/line evidence가 있는 답변 |
| AI Code Review | concrete bug risk와 refactoring opportunity가 있는 latest 또는 selected commit | Bug findings와 actionable suggestions |
| AI Progress | completed, in-progress, not-started, uncertain program 혼합 | Plan progress와 AI-estimated implementation status 비교 |

## 표준용어 데모 데이터셋

샘플 프로젝트는 외부 고객 산출물 없이도 glossary upload와 Korean query expansion workflow를 시연할 수 있도록 `advisor_uploads/sample_standard_terms.xlsx`를 포함해야 합니다.

첫 구현의 Excel shape은 의도적으로 가볍게 유지합니다.

- `term_type`
- `korean_term`
- `english_term`
- `abbreviation`
- `description`

실제 팀의 필수 입력은 Korean term과 English term으로 제한하고, abbreviation은 강하게 권장합니다. 애플리케이션은 camelCase, PascalCase, snake_case, upper snake case, compact lowercase, token list 같은 search variant를 자동 파생합니다.

샘플 용어는 생성된 Spring/MyBatis source에 이미 존재하는 code와 SQL identifier를 포괄해야 합니다.

| Korean term | English term | Abbreviation | Demo linkage |
|---|---|---|---|
| 결제금액 | payment amount | pay amt | `amount`, `payments.amount`, `PaymentService` |
| 결제승인 | payment authorization | pay auth | `authorize`, `PaymentController`, `PaymentMapper` |
| 주문번호 | order number | ord no | `orderId`, `order_id` |
| 주문상태 | order status | ord stat | `updateOrderStatus`, `status` |
| 쿠폰할인 | coupon discount | cpn dc | `CouponDiscountService`, `previewDiscount` |
| 재고예약 | inventory reservation | inv rsv | `InventoryService.reserve` |
| 정산내보내기 | settlement export | stl exp | settlement planning/risk scenario |
| 매출현황 | sales report | sales rpt | `SalesReportService`, `ReportMapper.xml` |

이 dataset은 `결제 금액이 0원 이하일 때 어떤 검증 로직이 동작하나요?` 같은 한국어 Project Chat 질문을 `payment amount`, `amount`, `PaymentService`, `payment_amount` 같은 code identifier 후보로 확장할 수 있어야 합니다.

## Commit Scenario 설계

확장된 history는 의도적으로 설계되어야 합니다. 각 commit은 demo 안에서 존재 이유가 있어야 합니다.

| Order | Scenario | Example commit message | Related programs | Demonstrates |
|---|---|---|---|---|
| 1 | Initial project setup | Initialize Spring MyBatis market operations project | All | Git Sync, RAG source indexing |
| 2 | Requirements baseline | Add program baseline and interface policy | All | RAG, Project Chat, planning context |
| 3 | Order skeleton | Add order creation controller and mapper | Order creation | Mapping, Program Detail |
| 4 | Order validation | Validate customer and cart input for order creation | Order creation | Code Review, Project Chat |
| 5 | Inventory reservation | Reserve inventory with MyBatis mapper | Inventory reservation | Mapping, database layer detection |
| 6 | Inventory shortage handling | Add shortage branch and reservation failure message | Inventory reservation, dashboard | Risk and cross-program impact |
| 7 | Payment authorization | Add payment authorization flow | Payment approval, order status | Commit Impact |
| 8 | Payment bug introduction | Relax amount validation for partner payments | Payment approval | AI Code Review high-value target |
| 9 | Payment bug fix | Reject zero and negative payment amounts | Payment approval | Bug fix history, review contrast |
| 10 | Order status history | Track order status transition history | Order status | Mapping, AI Progress |
| 11 | Invalid transition guard | Block invalid order status transitions | Order status | Project Chat, Code Review |
| 12 | Sales report query | Add sales report aggregation query | Sales report | RAG, database query search |
| 13 | Report correction | Exclude canceled payments from sales totals | Sales report, payment approval | Bug fix, cross-program impact |
| 14 | Dashboard view | Build operations dashboard JSP | Dashboard | Frontend/source search |
| 15 | Dashboard refresh endpoint | Add dashboard refresh API | Dashboard, orders, inventory, payments | Commit Impact |
| 16 | Risk indicator | Show payment waiting and inventory shortage indicators | Dashboard, inventory, payments | Program Detail |
| 17 | QA checklist | Add QA checklist for Spring MyBatis flows | All | Documentation, RAG |
| 18 | Unit tests | Add service tests for order and payment validation | Orders, payments | Test coverage signal |
| 19 | Refactoring | Extract common status constants | Orders, payments, dashboard | Refactoring review |
| 20 | Mapper cleanup | Normalize MyBatis result mappings | Orders, reports | Database review |
| 21 | Security hardening | Add basic operator role check to admin flows | Dashboard, reports | Code Review, risk discussion |
| 22 | Incomplete feature stub | Add coupon discount service skeleton | Coupon or payment | In-progress AI status |
| 23 | Unmapped program plan | Add return request program to plan without source implementation | Returns | No-related-commits risk |
| 24 | Missing assignee plan | Add settlement export plan without developer assignment | Settlement | Assignee missing risk |
| 25 | Stale activity | Leave report enhancement with old last commit | Reports | No recent commits risk |
| 26 | Ambiguous rename | Rename order status helper without behavior change | Orders | Mapping review queue |
| 27 | Documentation update | Document payment and inventory business rules | Payments, inventory | Project Chat citations |
| 28 | Latest risky change | Change dashboard summary query across modules | Dashboard, orders, inventory, payments | Best selected commit for AI Code Review |
| 29 | Latest fix | Fix dashboard summary over-counting | Dashboard, reports | Bug fix and Commit Impact |
| 30 | Final QA evidence | Add release verification checklist | All | RAG, AI Progress caveat |

정확한 commit 수는 구현 중 달라질 수 있지만, 최종 history는 위 scenario category를 보존해야 합니다.

## 의도된 분석 포인트

샘플은 정상 변경과 문제성 변경을 모두 포함해야 합니다.

- 일반 feature addition commit
- 현실적인 review finding을 만들 bug-introducing commit
- history-based analysis가 의미 있게 보이도록 하는 bug-fix commit
- 새 feature completion으로 오해하면 안 되는 refactoring commit
- Test-only commit
- Documentation-only commit
- 여러 program을 건드리는 cross-module commit
- Incomplete feature skeleton
- 관련 commit이 없는 planned program
- assignee information이 빠진 plan row
- no-recent-commit risk를 만들 old related commit
- Mapping review queue에 나타날 수 있는 ambiguous commit

## 데모 질문

Project Chat은 다음과 같은 질문에 current-source answer를 제공할 수 있어야 합니다.

- 결제대기에서 결제완료로 주문상태가 어떻게 이동하나요?
- 재고가 부족하면 어떤 일이 발생하나요?
- 결제금액 검증은 어디에서 수행되나요?
- 일별 매출현황을 만드는 query는 무엇인가요?
- 운영자 dashboard에는 어떤 indicator가 표시되나요?
- 결제와 재고에 대해 문서화된 business rule은 무엇인가요?

RAG Search는 다음 term을 지원해야 합니다.

- `payment authorization`
- `inventory shortage`
- `order status history`
- `sales report canceled`
- `dashboard payment waiting`
- `operator role check`

AI Code Review 추천 대상:

- 선택된 bug-introducing payment commit
- cross-module dashboard summary query change
- low-risk refactoring-focused feedback이 나와야 하는 refactoring commit

Risk Analysis는 최소한 다음 case를 보여야 합니다.

- Program has no related commits.
- Program is overdue and AI progress is incomplete.
- Plan progress is much higher than AI progress.
- Related commits exist but none are recent.
- Program assignment is missing or unclear.

AI Progress는 다음을 보여야 합니다.

- supporting implementation commit이 있는 completed-looking programs
- partial source evidence가 있는 in-progress programs
- plan row는 있지만 source commit이 없는 not-started programs
- evidence가 부족하거나 애매한 unknown/ambiguous programs

## 구현 체크리스트

이 설계를 구현할 때는 다음을 지킵니다.

- `scripts/create_sample_target_repo.py`를 수정해 더 현실적인 commit history를 생성합니다.
- 샘플 프로젝트 Git 저장소는 `C:\dev\ai-commit-advisor` 밖의 sibling repo로 유지합니다.
- 필요하면 `sample_data`와 `advisor_uploads` output을 update 또는 regenerate합니다.
- expected sample shape, developer profile, program row, risk/demo scenario에 대한 test를 추가하거나 수정합니다.
- generation 또는 recommended demo flow가 바뀌면 README sample usage instruction을 업데이트합니다.
- `AI_CHANGELOG.md`에 verification command와 result를 기록합니다.

## 비목표

- 샘플 프로젝트가 실제 external service에 의존하게 만들지 않습니다.
- 실제 고객명, production code, secret, internal business data를 포함하지 않습니다.
- 샘플을 분석 가치보다 buildability에 맞춰 최적화하지 않습니다. 그럴듯한 source code여야 하지만 주 목적은 AI Commit Advisor demonstration입니다.

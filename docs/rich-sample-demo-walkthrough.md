# 샘플 프로젝트 검증 가이드

## 목적

이 가이드는 synthetic sample target repository로 AI Commit Advisor를 검증하거나 시연할 때, local LLM 또는 embedding 작업을 과도하게 실행하지 않는 방법을 설명합니다.

다음을 사용할 때 이 문서를 확인하세요.

- sample target repo: `C:\dev\ai-advisor-sample-shop`
- generator script: `scripts/create_sample_target_repo.py`
- demo upload files: `C:\dev\ai-advisor-sample-shop\advisor_uploads`

샘플 저장소는 8개 program과 30개 commit으로 Git Sync, Mapping, Program Detail, Commit Impact, Risk Analysis, RAG, Project Chat, AI Code Review, AI Progress를 보여주도록 설계되어 있습니다.

## 권장 실행 기준

Demo verification 중에는 다음 기준을 권장합니다.

- Mapping은 commit-based analysis mode를 우선 사용합니다.
- batch 실행 전 selected commit 1개를 먼저 분석합니다.
- candidate limit은 default 이하로 유지합니다.
- UI flow만 확인할 때는 full embedding generation부터 시작하지 않습니다.
- Project Chat/RAG 확인 전 source chunk를 먼저 refresh하고, embedding은 small batch로 생성합니다.
- AI Code Review는 selected review-target commit에 대해서만 실행합니다.
- navigation, screen layout, workflow만 검증할 때는 `LLM_PROVIDER=mock`을 사용합니다.
- 실제 mapping/review/chat 품질이 필요할 때만 real local OpenAI-compatible LLM을 사용합니다.

## 권장 순서

1. 필요하면 sample repository를 다시 생성합니다.

```powershell
.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py --force
```

2. 앱에서 project path를 등록하거나 갱신합니다.

반복 가능한 screenshot verification을 위해, 이전 sample data와 섞이지 않도록 전용 project name을 사용합니다.

```text
AAA Sample Shop Rich Demo
```

```text
C:\dev\ai-advisor-sample-shop
```

3. Git sync를 실행합니다.

깨끗한 demo project에서는 full sync를 사용합니다. 예상 sample commit count는 30입니다.

4. 샘플 저장소에서 생성된 Excel file을 업로드합니다.

전체 demo scenario에는 새로 추론한 generic output이 아니라 아래 file을 사용합니다.

```text
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_developers.xlsx
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_programs.xlsx
C:\dev\ai-advisor-sample-shop\advisor_uploads\sample_development_plan.xlsx
```

`advisor_uploads` file에는 delayed coupon work, missing settlement assignee, no-related-commit risk scenario를 위한 demo-specific plan override가 포함되어 있습니다.

5. Mapping은 작은 범위부터 실행합니다.

- commit-based analysis를 선택합니다.
- selected commit 1개를 먼저 분석합니다.
- 결과가 합리적으로 보이면 unprocessed commit batch analysis를 실행합니다.
- 첫 verification pass에서는 program-based analysis를 피합니다.

`LLM_PROVIDER=mock`으로 UI-only verification을 할 때는 program-based analysis 또는 pre-generated validation data를 사용합니다. commit-based path는 LLM의 JSON 응답을 기대하기 때문입니다. Mock provider는 real local model을 호출하지 않고 screen과 downstream risk/progress view를 확인하는 데 유용합니다.

6. Risk Analysis를 실행합니다.

기대 demo signal:

- coupon discount work가 delayed이고 partially implemented 상태입니다.
- settlement export가 delayed, unassigned이고 related implementation commit이 없습니다.
- older completed program은 current date와 mapping result에 따라 no-recent-commit signal을 보일 수 있습니다.

7. AI Progress를 확인합니다.

Completed, delayed, partial, no-evidence program이 섞여 있는지 확인합니다.

8. Commit Impact를 확인합니다.

추천 commit:

- `Change dashboard summary query across operations modules`
- `Fix dashboard summary over-counting`
- `Add payment authorization flow`

이 commit은 cross-program impact를 더 쉽게 확인하게 해 줍니다.

9. AI Code Review는 selected commit에 대해서만 실행합니다.

추천 review target:

- `Relax partner payment validation for pilot channel`
- `Change dashboard summary query across operations modules`
- `Extract shared order status constants`

10. RAG와 Project Chat은 bounded embedding work로 실행합니다.

권장 flow:

- current source chunk를 먼저 refresh합니다.
- small limit으로 embedding을 생성합니다.
- focused question으로 검색하거나 질문합니다.

샘플 project는 Spring MVC + JSP + MyBatis입니다. Project Chat verification 전 current source indexing 대상에 Java, JSP, XML, Markdown, JavaScript, CSS file이 포함되어야 합니다.

유용한 Project Chat 질문:

- 결제금액 검증은 어디에서 수행되나요?
- 재고가 부족하면 어떤 일이 발생하나요?
- 결제승인 후 주문상태는 어떻게 이동하나요?
- dashboard summary를 만드는 query는 무엇인가요?
- 의도적으로 incomplete 또는 risky하게 만든 sample program은 무엇인가요?

## 스크린샷 갱신

README screenshot을 갱신할 때는 위에서 검증한 sample state를 사용합니다. Screenshot은 다음을 반영해야 합니다.

- 8 sample programs
- 30 sample commits
- commit-based analysis에서 나온 Mapping result
- coupon과 settlement demo signal이 보이는 Risk Analysis
- dashboard/payment commit 기반 Commit Impact example
- recommended review target 기반 AI Code Review example

Screenshot refresh는 `AI_CHANGELOG.md`에 기록합니다.

## 문제 해결

Mapping이 느리게 보이면:

- 현재 commit 처리가 끝난 뒤 중지합니다.
- commit-based mode가 선택되었는지 확인합니다.
- candidate limit을 낮춥니다.
- workflow-only verification이라면 `LLM_PROVIDER=mock`으로 전환합니다.

RAG 또는 Project Chat이 느리게 보이면:

- embedding 없이 chunk refresh부터 실행합니다.
- embedding을 더 작은 batch로 생성합니다.
- workflow가 검증되기 전에는 모든 source type을 선택하지 않습니다.

Risk Analysis가 예상 sample risk를 보여주지 않으면:

- project가 `C:\dev\ai-advisor-sample-shop`을 사용하는지 확인합니다.
- 업로드한 Excel file이 `advisor_uploads`에서 나온 것인지 확인합니다.
- Mapping이 related commit mapping을 생성했는지 확인합니다.
- Mapping 완료 후 Risk Analysis를 다시 실행합니다.

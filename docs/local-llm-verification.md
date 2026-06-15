# Local LLM Verification

이 문서는 mock이 아닌 local OpenAI-compatible LLM/embedding provider로 AI Commit Advisor의 주요 AI 기능을 실제 실행하고, 그 결과를 반복 가능하게 확인하는 방법을 정리합니다.

## 목적

기본 mock 설정은 설치와 화면 흐름을 빠르게 확인하기 위한 안전한 기본값입니다. 하지만 실제 AI 적용 여부를 설명하려면 `local_openai` provider로 PL Briefing, Project Chat, AI Code Review, Mapping 같은 기능을 실행했고, fallback 없이 완료됐다는 증거가 필요합니다.

검증 결과는 새 테이블을 만들지 않고 기존 `ai_invocation_logs` telemetry에 남깁니다. `AI 운영 현황 > 실제 LLM 검증` 탭은 이 기록을 읽어 live provider 실행 범위, fallback/failed count, 최근 실행 provider/model/base URL 상태를 보여줍니다.

## 사전 준비

1. LM Studio 또는 OpenAI-compatible local server에서 chat 모델과 embedding 모델을 로드합니다.
2. `.env.local-llm.example`을 `.env`로 복사하거나 아래 값을 설정합니다.

```env
LLM_PROVIDER=local_openai
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_MODEL=qwen2.5-coder-7b-instruct
EMBEDDING_PROVIDER=local_openai
EMBEDDING_BASE_URL=http://127.0.0.1:1234/v1
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
PGVECTOR_DIMENSION=768
```

3. Streamlit 앱을 재시작합니다.
4. RAG 검색 화면에서 현재 소스 근거와 embedding 검색 준비를 만들어 둡니다.
5. Project Chat graph evidence까지 확인하려면 Knowledge Graph를 최신 상태로 동기화합니다.

## 검증 명령

가장 일반적인 실행은 embedding 연결, PL Briefing, Project Chat, AI Code Review를 한 번에 확인합니다.

```powershell
.\.venv\Scripts\python.exe scripts\run_local_ai_verification.py `
  --project-name "AAA Sample Shop Rich Demo (4)" `
  --features embedding-check pl-briefing project-chat code-review `
  --output docs\local-llm-verification-result.md
```

Mapping까지 함께 검증하려면 최신 commit 1개만 대상으로 추가 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\run_local_ai_verification.py `
  --project-name "AAA Sample Shop Rich Demo (4)" `
  --features mapping `
  --mapping-commit-limit 1 `
  --output docs\local-llm-verification-result.md
```

`LLM_PROVIDER=mock` 또는 `EMBEDDING_PROVIDER=mock`이면 기본적으로 중단합니다. 화면 흐름만 확인하려는 경우에만 `--allow-mock`을 붙입니다. `--allow-mock` 결과는 live 검증 증거로 보지 않습니다.

## 결과 확인

검증 후 `AI 운영 현황 > 실제 LLM 검증`을 확인합니다.

- `Local LLM 설정`: 현재 chat provider/model/base URL이 live 설정인지 확인합니다.
- `Local Embedding 설정`: embedding provider/model/base URL과 `PGVECTOR_DIMENSION`을 확인합니다.
- `Embedding live check`: `/v1/embeddings` 응답과 vector dimension 확인 결과입니다.
- `LLM 기능 live coverage`: `PL Briefing`, `Project Chat`, `AI Code Review`, `Mapping` 중 fallback 없이 성공한 기능 수입니다.
- `Fallback / failure`: live provider 호출 중 fallback이나 실패가 있었는지 보여줍니다.
- `최근 live 증거`: 가장 최근 live provider 호출의 feature/provider/model/time입니다.

검증 기준은 "모델 성능 benchmark"가 아니라 운영 증거입니다. 답변 품질 자체는 기능별 근거, raw response, source verification, code review 결과를 함께 보고 판단해야 합니다.

## CI와 운영 경계

- CI에서는 local LLM이나 외부 유료 API를 호출하지 않습니다.
- 이 스크립트는 사용자가 local model server를 켠 환경에서 명시적으로 실행합니다.
- Project Chat 검증은 current source chunk와 embedding이 준비되어 있어야 실제 LLM 답변까지 진행됩니다.
- AI Code Review는 등록된 앱 서버 Git 저장소에서 diff를 읽습니다. 서버 clone이 최신인지 먼저 확인하세요.

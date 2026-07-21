# 설치와 운영

이 문서는 AI Commit Advisor의 설치, 실행, 환경 변수, DB migration, LLM/embedding 운영 기준을 정리합니다.

## 실행 환경

- Python 3.11 이상
- Git
- Docker Desktop
- PostgreSQL + pgvector
- Neo4j Community Edition
- 선택: LM Studio 또는 OpenAI-compatible 로컬 LLM/embedding 서버

Git 저장소 분석은 브라우저 사용자 PC가 아니라 앱 서버에서 접근 가능한 저장소 경로를 기준으로 동작합니다. 사내 서버 운영 모델은 [Git 저장소 운영 모델](git-repository-operating-model.md)을 먼저 확인하세요.

## 로컬 실행 전 준비물

처음 실행할 때는 먼저 mock 모드로 화면, DB, Git 동기화 흐름을 확인하는 것을 권장합니다. 실제 LLM/RAG/Project Chat 품질까지 확인해야 할 때만 LM Studio와 local model을 준비하세요. mock 모드는 외부 AI 서버를 호출하지 않으므로 Python, Git, Docker Desktop만 있으면 시작할 수 있습니다.

### 1. Python 3.11 이상

Python은 Streamlit 앱과 테스트, DB 초기화 스크립트를 실행하는 데 필요합니다. Windows에서는 Python 설치 시 `Add python.exe to PATH`를 체크하는 것이 가장 단순합니다.

설치 확인:

```powershell
python --version
python -m pip --version
```

`python --version`이 3.11 이상을 출력해야 합니다. 여러 Python이 설치되어 있다면 `py -3.11 --version`으로 3.11 runtime이 있는지 확인하고, 가상환경 생성 때도 같은 Python을 사용하세요.

### 2. Git

AI Commit Advisor는 분석 대상 Git 저장소의 commit, diff, 현재 파일을 읽습니다. 앱 코드 저장소뿐 아니라 분석할 프로젝트 저장소도 로컬 또는 앱 서버에서 접근 가능해야 합니다.

설치 확인:

```powershell
git --version
```

로컬 검증만 할 때는 샘플 프로젝트 생성 스크립트가 `C:\dev\ai-advisor-sample-shop`에 Git 저장소를 만들어 줍니다. 실제 업무 저장소를 분석할 때는 프로젝트/Git 설정에 등록할 저장소 경로가 현재 앱 실행 환경에서 읽히는지 먼저 확인하세요.

### 3. Docker Desktop

Docker Desktop은 PostgreSQL + pgvector와 Neo4j를 로컬에서 띄우는 데 사용합니다. Windows에서는 Docker Desktop 설치 후 WSL 2 backend가 정상 동작해야 합니다.

설치 확인:

```powershell
docker --version
docker compose version
docker info
```

`docker info`가 Docker daemon 연결 오류 없이 끝나야 합니다. 처음 실행에서는 PostgreSQL, Neo4j image를 내려받기 때문에 시간이 걸릴 수 있습니다. 회사 네트워크나 proxy 환경에서 image pull이 막히면 Docker Desktop의 proxy 설정을 먼저 확인하세요.

로컬 Python으로 앱을 실행해도 DB와 Neo4j는 Docker Compose로 띄웁니다. Docker만으로 앱까지 함께 실행할 수도 있지만, 개발과 문서 검증은 로컬 Python 실행이 빠릅니다.

### 4. LM Studio와 local model

LM Studio는 실제 AI 분석을 로컬 PC에서 확인할 때만 필요합니다. mock 모드로 화면 흐름을 보는 단계라면 설치하지 않아도 됩니다.

LM Studio를 사용할 때 준비할 모델은 두 종류입니다.

| 용도 | 권장 모델 이름 | `.env` 값 | 비고 |
|---|---|---|---|
| Chat / Code Review / Mapping / Project Chat 답변 생성 | `qwen2.5-coder-7b-instruct` | `LLM_MODEL=qwen2.5-coder-7b-instruct` | 코드와 한국어 설명을 함께 다루기 위한 기본 권장값입니다. PC 사양이 낮으면 더 작은 instruct model을 사용할 수 있습니다. |
| RAG / Project Chat 검색 준비용 embedding | `text-embedding-nomic-embed-text-v2-moe` | `EMBEDDING_MODEL=text-embedding-nomic-embed-text-v2-moe` | 한국어 질의와 영문 코드·경로가 섞인 검색을 위한 기본값입니다. 출력 차원은 768로 맞춥니다. |

현재 검증 장비는 RTX 3060 Ti 8GB와 RAM 32GB입니다. `Qwen2.5 Coder 7B Q4_K_M`을 context length 8192, parallel 1로 로드하고 `Nomic Embed Text v2 MoE Q8_0`을 함께 올렸을 때 약 1.2GB의 VRAM 여유가 남았습니다. `Qwen3 8B Q4_K_M`은 같은 조건에서 여유가 268MB까지 줄어 기본값으로 바꾸지 않았습니다. `Huihui-Qwen3.5-9B-abliterated Q4_K_M` GGUF 파일은 약 5.7GB이며, model card가 `abliterated`, `uncensored` 변형으로 분류합니다. 8GB 장비의 상시 운영 모델로 바로 적용하지 말고 응답 품질과 운영 경계를 별도로 평가해야 합니다.

LM Studio 준비 순서:

1. [LM Studio](https://lmstudio.ai/)를 설치합니다.
2. LM Studio의 model 검색에서 `qwen2.5-coder-7b-instruct` 계열 GGUF 모델을 내려받습니다.
3. embedding 모델로 `nomic-embed-text-v2-moe` 계열 GGUF를 내려받습니다. 8GB VRAM 기준으로 `Q8_0`을 기본 검증했으며, 여유가 부족하면 더 작은 양자화를 선택합니다.
4. `Developer` 또는 `Local Server` 화면에서 OpenAI-compatible local server를 port `12345`로 켭니다. 이 저장소는 Windows 제외 port와 Docker 기본값이 엇갈리지 않도록 `12345`를 기준으로 사용합니다.
5. Chat model `qwen2.5-coder-7b-instruct`를 context length `8192`로 로드합니다.
6. embedding model `text-embedding-nomic-embed-text-v2-moe`를 함께 로드하고 `/v1/embeddings` 요청에 응답하는지 확인합니다.

LM Studio는 OpenAI-compatible endpoint를 제공하므로 앱은 아래 주소를 사용합니다.

```env
LLM_BASE_URL=http://127.0.0.1:12345/v1
EMBEDDING_BASE_URL=http://127.0.0.1:12345/v1
```

모델 이름은 LM Studio에서 실제로 로드한 model identifier와 `.env` 값이 같아야 합니다. 이름이 다르면 앱의 연결 테스트나 LLM 호출이 model not found 오류로 실패할 수 있습니다.

chat model 후보를 바꿀 때는 두 모델을 동시에 올려 VRAM을 소진하지 말고 하나씩 로드해 같은 진단을 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\benchmark_local_chat_model.py `
  --model qwen2.5-coder-7b-instruct
```

이 스크립트는 Mapping, 결제 Code Review, SQL Code Review 3개 고정 문제에서 JSON 파싱, 기대 판단, 한국어 설명, 지연시간을 기록합니다. 작은 진단 집합이므로 결과 한 번만으로 운영 model을 교체하지 않고, 실제 기능별 검증 이력과 VRAM 여유를 함께 확인합니다.

### 5. 디스크, 메모리, 네트워크 여유

로컬 모델은 파일 크기가 크고 실행 중 메모리를 많이 사용합니다. 7B급 GGUF chat 모델과 embedding 모델을 함께 준비하려면 수 GB 이상의 디스크 여유가 필요하고, 실제 실행 중에는 CPU/GPU와 메모리를 오래 사용할 수 있습니다.

처음에는 다음 순서로 부담을 나누는 것을 권장합니다.

1. `.env.example`의 mock 모드로 앱과 DB 연결을 확인합니다.
2. 샘플 프로젝트를 생성하고 Git Sync, 프로그램/개발자/계획 업로드 흐름을 확인합니다.
3. `.env.local-llm.example`로 전환한 뒤 LM Studio 연결 테스트를 실행합니다.
4. RAG 검색 화면에서 작은 수량으로 검색 준비를 실행합니다.
5. Project Chat, AI Code Review, Mapping을 필요한 범위만 실행합니다.

## 설치 및 실행

로컬 Python으로 실행할 때는 현재 PC가 앱 서버입니다. 프로젝트/Git 설정에 등록하는 Git 저장소 경로도 현재 PC에서 접근 가능한 경로를 사용합니다. 사내 서버에서 실행할 때는 사용자 PC 경로가 아니라 사내 서버에 clone된 저장소 경로를 등록해야 합니다.

### 1. 환경 파일 생성

가볍게 앱 흐름만 확인하려면 mock 설정을 사용합니다.

```powershell
Copy-Item .env.example .env
```

실제 LLM/RAG/Project Chat 품질을 검증하려면 로컬 LLM 설정 예시를 사용합니다.

```powershell
Copy-Item .env.local-llm.example .env
```

local LLM 모드에서는 LM Studio에서 chat 모델과 embedding 모델을 먼저 로드해야 합니다. `.env`를 바꾼 뒤에는 Streamlit 앱을 재시작해야 합니다.

### 2. PostgreSQL + pgvector + Neo4j 실행

```powershell
docker compose up -d postgres neo4j
```

Neo4j는 `Knowledge Graph` 화면의 graph read model에 사용합니다. 첫 실행에서 image를 내려받을 때는 시간이 더 걸릴 수 있지만, 이후에는 기존 image와 volume을 재사용합니다.

Neo4j 없이 PostgreSQL만 켜고 싶을 때는 `.env`에서 `NEO4J_ENABLED=false`로 바꾼 뒤 PostgreSQL만 실행합니다.

```powershell
docker compose up -d postgres
```

### 3. Python 가상환경 준비

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

가상환경 활성화 명령은 터미널마다 다릅니다. PowerShell은 `.\.venv\Scripts\Activate.ps1`, cmd.exe는 `.venv\Scripts\activate`, Git Bash는 `source .venv/Scripts/activate`를 사용합니다. 기본 설치 절차는 터미널 차이와 PowerShell 실행 정책에 덜 영향을 받도록 가상환경을 활성화하지 않고 `.venv\Scripts\python.exe`를 직접 호출합니다.

cmd.exe:

```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

이미 `.venv`가 만들어져 있으면 다시 만들지 말고 `.venv\Scripts\python.exe`를 직접 사용하면 됩니다.

기존 `.venv`가 있는데 `pydantic_core._pydantic_core`, `psycopg2._psycopg`, `pandas._libs.*` 같은 `ModuleNotFoundError`가 발생하면 앱 코드보다 가상환경의 native package 설치가 깨졌을 가능성이 큽니다. 이때는 실행 중인 Streamlit/Python terminal을 모두 종료한 뒤, 가장 안전하게 `.venv`를 새로 만듭니다.

```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m src.db.init_db
```

`.venv`를 지우기 어렵다면 깨진 package를 `--force-reinstall --no-cache-dir`로 재설치할 수 있지만, 여러 native package가 연속으로 실패하면 새 가상환경을 만드는 편이 빠르고 재현성이 좋습니다.

### 4. DB 초기화 및 마이그레이션

```powershell
.\.venv\Scripts\python.exe -m src.db.init_db
```

DB schema는 Alembic migration으로 관리됩니다. 빈 DB는 최신 migration까지 생성되고, 기존 DB에 `alembic_version`이 없으면 현재 schema를 baseline으로 stamp한 뒤 이후 migration만 적용합니다.

직접 migration을 실행하려면:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

자세한 내용은 [DB Migrations](db-migrations.md)를 참고하세요.

### 5. Streamlit 실행

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

가상환경 활성화 없이 실행하려면:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### 샘플 프로젝트 경로 설정

샘플 프로젝트 생성 스크립트의 기본 경로는 `C:\dev\ai-advisor-sample-shop`입니다.

```powershell
.\.venv\Scripts\python.exe scripts\create_sample_target_repo.py
```

로컬 Python 실행에서는 현재 PC가 앱 서버이므로, 프로젝트/Git 설정 화면에 `C:\dev\ai-advisor-sample-shop`을 그대로 등록하면 됩니다.

Docker Compose 기본 설정도 Windows host의 `C:/dev`를 컨테이너의 `/host-dev`로 mount하고, `REPO_STORAGE_ROOT`, `REPO_PATH_HOST_PREFIX`, `REPO_PATH_CONTAINER_PREFIX`를 `C:\dev` 기준으로 맞춰 둡니다. 따라서 기본 샘플 경로를 쓰면 Docker 앱도 같은 샘플 프로젝트를 읽을 수 있습니다.

사내 서버에서 샘플 프로젝트를 검증하려면 샘플 프로젝트를 사내 서버의 저장소 root 아래에 생성하거나 복사한 뒤, 서버 기준 경로를 프로젝트/Git 설정에 등록하세요.

```text
/srv/ai-commit-advisor/repos/ai-advisor-sample-shop
```

이 경우 `REPO_STORAGE_ROOT`도 같은 root로 설정하는 것이 좋습니다.

```env
REPO_STORAGE_ROOT=/srv/ai-commit-advisor/repos
```

## Docker 앱 배포

### 도입 배경과 기대 효과

기존 실행 방식은 PostgreSQL은 Docker Compose로 띄우고 Streamlit 앱은 로컬 Python 가상환경에서 직접 실행하는 흐름이었습니다. 이 방식은 개발 중에는 빠르지만, 다른 환경에서 재현하거나 서버에 올릴 때 Python 버전, 패키지 설치, DB 접속 주소, migration 적용 방식이 사람마다 달라질 수 있습니다.

앱 Dockerfile과 Compose `app` service는 이 차이를 줄이기 위해 추가했습니다. 목표는 다음과 같습니다.

- 처음 실행하는 사람도 `docker compose up`만으로 PostgreSQL + Neo4j + Streamlit 앱 조합을 재현합니다.
- 서버 배포 시 앱 시작 전에 DB schema 초기화와 Alembic migration을 같은 방식으로 실행합니다.
- 현재 시연 구성은 Docker와 로컬 Python이 같은 실제 local LLM/embedding 결과를 읽도록 기본값을 맞춥니다. 외부 AI 없이 화면만 확인할 때는 `DOCKER_*` override로 mock을 명시합니다.
- 배포 후 health endpoint로 최소 기동 상태를 빠르게 확인합니다.
- 앱 서버에서 접근 가능한 Git 저장소 경로를 기준으로 Git Sync, RAG source_file 검증, Project Chat 현재 소스 검증을 실행합니다.
- Windows 개발 PC의 Docker 실행처럼 host 경로와 container 경로가 다를 때는 DB에 저장된 host Git 경로를 컨테이너 내부 mount 경로로 변환합니다.

### Compose 전체 실행과 시연 재기동

처음 image를 만들거나 Dockerfile·dependency가 바뀐 경우에만 build를 포함합니다.

```powershell
docker compose up -d --build
```

이미 검증된 image와 DB를 다시 켤 때는 build 없이 app service만 지정합니다. Compose가 PostgreSQL과 Neo4j dependency도 필요한 상태로 기동합니다.

```powershell
docker compose up -d app
```

시연 환경에서는 상태 확인, LM Studio model 확인, 기존 Tunnel 재사용과 preflight를 한 번에 수행하는 repository script를 우선 사용합니다.

```powershell
.\scripts\demo_start.ps1
```

앱은 `http://127.0.0.1:8501/?project_id=1`에서 열립니다. Compose의 `app` service는 `postgres` healthcheck가 통과하고 `neo4j` service가 시작된 뒤 기동합니다.

실행 상태 확인:

```powershell
docker compose ps
```

로그 확인:

```powershell
docker compose logs app
```

전체 개발 환경을 종료해야 할 때만 다음 명령을 사용합니다.

```powershell
docker compose down
```

시연 서버를 다시 켜려는 목적에는 `down`을 사용하지 않습니다. 앱만 중지해야 하면 `docker compose stop app`을 사용하며 PostgreSQL, Neo4j, Quick Tunnel network는 유지합니다.

DB volume까지 삭제하는 다음 명령은 저장 결과를 제거하므로 백업과 명시적인 초기화 승인이 있을 때만 사용합니다. 일반 시연·장애 복구 절차에서는 실행하지 않습니다.

```powershell
docker compose down -v
```

### 앱 이미지 단독 빌드

Compose 없이 이미지 빌드만 확인하려면 다음 명령을 사용합니다.

```powershell
docker build -t ai-commit-advisor:local .
```

### Docker 환경 변수

`docker-compose.yml`의 `app.environment`는 컨테이너 내부 실행 기준입니다. 로컬 Python 실행의 `.env`와 달리 DB host는 Compose service 이름인 `postgres`, Windows host의 LM Studio는 `host.docker.internal`을 사용합니다. Compose override는 host용 설정과 섞이지 않도록 `DOCKER_*` 이름으로 받습니다.

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://ai_user:ai_password@postgres:5432/ai_commit_advisor` | 앱 컨테이너가 Compose PostgreSQL에 접속하는 SQLAlchemy URL입니다. |
| `PGVECTOR_DIMENSION` | `768` | `DOCKER_PGVECTOR_DIMENSION`으로 덮어쓸 수 있습니다. 실제 embedding 모델과 DB column 차원이 같아야 합니다. |
| `LLM_PROVIDER` | `local_openai` | `DOCKER_LLM_PROVIDER`로 덮어씁니다. 화면만 확인할 때만 `mock`을 명시합니다. |
| `LLM_BASE_URL` | `http://host.docker.internal:12345/v1` | `DOCKER_LLM_BASE_URL`로 덮어씁니다. 컨테이너에서 Windows host의 LM Studio에 접근하는 주소입니다. |
| `LLM_API_KEY` | 빈 값 | `DOCKER_LLM_API_KEY`로 덮어씁니다. local LM Studio는 보통 비워 둡니다. |
| `LLM_MODEL` | `qwen2.5-coder-7b-instruct` | `DOCKER_LLM_MODEL`로 덮어쓸 수 있는 chat model 이름입니다. |
| `EMBEDDING_PROVIDER` | `local_openai` | `DOCKER_EMBEDDING_PROVIDER`로 덮어씁니다. |
| `EMBEDDING_BASE_URL` | `http://host.docker.internal:12345/v1` | `DOCKER_EMBEDDING_BASE_URL`로 덮어씁니다. |
| `EMBEDDING_API_KEY` | 빈 값 | `DOCKER_EMBEDDING_API_KEY`로 덮어씁니다. local embedding server는 보통 비워 둡니다. |
| `EMBEDDING_MODEL` | `text-embedding-nomic-embed-text-v2-moe` | `DOCKER_EMBEDDING_MODEL`로 덮어쓸 수 있는 embedding model 이름입니다. |
| `REPO_STORAGE_ROOT` | Compose: `C:\dev`, `.env`: 빈 값 | 프로젝트 Git 저장소 경로를 이 앱 서버 기준 root 하위로 제한합니다. 비워 두면 제한하지 않습니다. |
| `REPO_PATH_HOST_PREFIX` | `C:\dev` | DB와 화면에 저장되는 host 기준 Git 저장소 경로 prefix입니다. |
| `REPO_PATH_CONTAINER_PREFIX` | `/host-dev` | app 컨테이너가 같은 저장소를 읽을 때 사용하는 mount 경로 prefix입니다. |
| `MANAGED_REPO_STORAGE_ROOT` | `C:\dev\ai-commit-advisor-managed-repos` | `Git URL에서 가져오기`가 프로젝트별 경로를 자동 생성하는 host 기준 전용 root입니다. |
| `MANAGED_REPO_CONTAINER_PREFIX` | `/managed-repos` | app 컨테이너가 관리형 저장소를 clone/fetch하는 쓰기 가능 mount입니다. |
| `MANAGED_GIT_ALLOWED_HOSTS` | `github.com,gitlab.com,bitbucket.org` | 외부 관리형 등록에서 허용할 공개 HTTPS Git host 목록입니다. |
| `GIT_OPERATION_TIMEOUT_SECONDS` | `300` | clone/fetch/reset 한 번의 최대 실행 시간입니다. Git credential prompt는 비활성화됩니다. |
| `NEO4J_ENABLED` | `true` | Knowledge Graph 동기화를 켤지 정합니다. `.env.example`과 Compose 앱 모두 기본 `true`입니다. Neo4j 없이 실행할 때만 `false`로 바꿉니다. |
| `NEO4J_URI` | `bolt://neo4j:7687` | 앱 컨테이너가 Compose Neo4j에 접속하는 Bolt URI입니다. 로컬 Python에서는 보통 `bolt://localhost:7687`을 사용합니다. |
| `NEO4J_USER` | `neo4j` | Neo4j 접속 사용자입니다. |
| `NEO4J_PASSWORD` | `ai_commit_advisor` | Compose Neo4j 기본 비밀번호입니다. 운영 환경에서는 반드시 변경하세요. |
| `NEO4J_DATABASE` | `neo4j` | 사용할 Neo4j database입니다. Community Edition에서는 기본값 `neo4j`를 사용합니다. |
| `NEO4J_WRITE_BATCH_SIZE` | `500` | Neo4j node/edge write를 나누는 batch 크기입니다. 대형 저장소에서 transaction memory나 timeout이 보이면 더 낮춥니다. |
| `NEO4J_RETRY_ATTEMPTS` | `2` | Neo4j health check와 write batch의 retry 횟수입니다. 일시적 연결 실패를 흡수하기 위한 값입니다. |
| `NEO4J_RETRY_BACKOFF_SECONDS` | `0.5` | retry 사이 기본 대기 시간입니다. 실제 대기는 attempt 수에 비례해 조금씩 늘어납니다. |
| `PORT` | `8501` | Dockerfile의 Streamlit 실행 port입니다. Compose는 host `8501`을 container `8501`에 연결합니다. |

기본 Compose 설정은 LM Studio의 실제 provider를 사용합니다. 화면·DB smoke test만 하려면 `.env`에 다음 override를 넣고 앱을 다시 만듭니다.

```dotenv
DOCKER_LLM_PROVIDER=mock
DOCKER_EMBEDDING_PROVIDER=mock
DOCKER_PGVECTOR_DIMENSION=768
```

실제 시연에서는 mock override를 제거하고 LM Studio에서 `qwen2.5-coder-7b-instruct`를 context length 8192로, `text-embedding-nomic-embed-text-v2-moe`를 함께 로드합니다. 검증 장비에서는 embedding 모델의 `Q8_0` 양자화를 사용합니다. `PGVECTOR_DIMENSION`은 embedding 모델 출력 차원과 반드시 맞춰야 합니다. 이미 다른 차원으로 DB가 만들어진 뒤에는 단순 환경 변수 변경만으로 기존 `vector_items.embedding` column 차원이 바뀌지 않습니다. 이 경우 새 DB volume으로 다시 시작하지 말고 먼저 백업한 뒤 schema migration 전략을 별도로 잡습니다.

### Docker에서 앱 서버 Git 저장소 접근

Project Chat과 RAG source_file 검증은 DB에 저장된 Git 저장소 경로의 실제 파일을 읽습니다. 이 경로는 브라우저 사용자 PC가 아니라 앱 서버 기준 경로입니다.

사내 Linux 서버에서는 저장소를 `/srv/ai-commit-advisor/repos` 같은 앱 전용 root 아래에 clone하고, `REPO_STORAGE_ROOT`를 같은 값으로 설정하는 방식을 권장합니다.

```yaml
volumes:
  - /srv/ai-commit-advisor/repos:/srv/ai-commit-advisor/repos
environment:
  REPO_STORAGE_ROOT: /srv/ai-commit-advisor/repos
```

프로젝트 등록 방식은 두 가지입니다.

- `서버에 이미 있는 저장소 사용`: 운영자나 배포 스크립트가 준비한 경로를 등록합니다. Docker 기본 구성의 `C:\dev`는 read-only이므로 Git 수집과 소스 분석은 가능하지만 앱에서 fetch/reset하지 않습니다.
- `Git URL에서 가져오기`: 사용자는 공개 HTTPS Git URL과 branch만 입력합니다. 앱은 `MANAGED_REPO_STORAGE_ROOT` 아래에 `project-<ID>` 폴더를 자동 배정하고 clone/fetch/reset합니다.

관리형 등록은 기본적으로 `github.com`, `gitlab.com`, `bitbucket.org`만 허용하고 access token, SSH key, password를 받지 않습니다. 사내 Git host가 필요하면 `MANAGED_GIT_ALLOWED_HOSTS`에 명시적으로 추가하세요. private repository는 기존 서버 경로 방식에서 서버 OS의 SSH key, credential helper, 배포 계정 등 앱 밖의 인증으로 미리 준비합니다.

반복 가능한 저장소 갱신 절차와 `scripts/update_server_repos.py` 사용법은 [서버 Git 저장소 갱신 Runbook](server-repository-update-runbook.md)을 참고하세요.

Git 동기화 화면은 Repo HEAD, DB sync commit, branch, upstream, ahead/behind, working tree 변경 여부를 함께 보여줍니다. Repo HEAD와 DB sync commit이 다르면 서버 저장소에는 앱 DB가 아직 수집하지 않은 commit이 있는 상태이므로 Git 동기화를 실행하세요. working tree에 local 변경이 있으면 먼저 운영자가 분석용 clone 상태를 확인해야 합니다.

Git Sync가 끝난 뒤에는 같은 화면의 `동기화 후 다음 작업`을 확인합니다. 이 패널은 현재 DB와 source index, embedding, Mapping, Risk, Knowledge Graph 상태를 읽어 권장 순서를 제시합니다. Git Sync 자체는 embedding API나 LLM을 호출하지 않으므로, 검색 준비·Mapping처럼 비용이나 local model 부하가 있는 작업은 각 화면으로 이동한 뒤 사용자가 명시적으로 실행합니다.

처음 프로젝트를 등록했거나 화면이 비어 보이면 `Home`과 `AI 운영 현황 > 운영 준비`의 `다음 준비 작업`을 먼저 확인하세요. 이 영역은 프로젝트/Git/프로그램/Mapping/소스 근거/검색 준비/Knowledge Graph 상태를 읽어 현재 값과 이동할 화면을 함께 보여줍니다.

Windows 개발 PC의 Docker 실행에서는 `C:\dev\ai-advisor-sample-shop` 같은 host 경로가 컨테이너 안에 그대로 존재하지 않습니다.

`docker-compose.yml`은 기본적으로 Windows host의 `C:/dev`를 app 컨테이너의 `/host-dev`에 읽기 전용으로 mount합니다.

```yaml
volumes:
  - C:/dev:/host-dev:ro
  - C:/dev/ai-commit-advisor-managed-repos:/managed-repos:rw
```

그리고 다음 path mapping 환경 변수를 사용합니다. `REPO_STORAGE_ROOT`는 화면에 저장되는 host 기준 경로를 제한하고, `REPO_PATH_*`는 실제 컨테이너 접근 경로로 변환합니다.

```yaml
REPO_STORAGE_ROOT: "C:\\dev"
REPO_PATH_HOST_PREFIX: "C:\\dev"
REPO_PATH_CONTAINER_PREFIX: /host-dev
MANAGED_REPO_STORAGE_ROOT: "C:\\dev\\ai-commit-advisor-managed-repos"
MANAGED_REPO_CONTAINER_PREFIX: /managed-repos
MANAGED_GIT_ALLOWED_HOSTS: github.com,gitlab.com,bitbucket.org
```

예를 들어 DB에 저장된 기존 프로젝트 경로가 `C:\dev\ai-advisor-sample-shop`이면 Docker app은 파일을 읽을 때 `/host-dev/ai-advisor-sample-shop`으로 변환합니다. 관리형 프로젝트 경로 `C:\dev\ai-commit-advisor-managed-repos\project-7`은 `/managed-repos/project-7`로 먼저 변환되므로 read-only 상위 mapping이 아니라 전용 read-write mount를 사용합니다. 이 변환은 clone/fetch, Git Sync, 현재 HEAD 확인, source_file 인덱싱, Project Chat source verification에 적용됩니다.

다른 위치의 저장소를 분석하려면 mount와 prefix를 같이 바꾸세요.

```yaml
volumes:
  - D:/work:/host-work:ro
environment:
  REPO_PATH_HOST_PREFIX: "D:\\work"
  REPO_PATH_CONTAINER_PREFIX: /host-work
```

이 mapping이 없거나 mount가 맞지 않으면 Docker 앱에서는 Current HEAD가 `-`로 보이거나 소스 근거가 `검증 불가`로 표시될 수 있습니다. 이 경우 Project Chat은 현재 소스 근거를 검증하지 못하므로 추측성 답변을 만들지 않습니다.

Docker image에는 Git Sync와 현재 HEAD 확인에 필요한 `git` binary가 포함되어 있습니다. Dockerfile을 수정해 base image를 바꾸는 경우에도 `git` 설치는 유지해야 합니다.

### Neo4j Knowledge Graph 운영

Knowledge Graph는 PostgreSQL 원본 데이터를 대체하지 않습니다. 앱은 PostgreSQL에 저장된 프로젝트, 프로그램, 커밋, 파일, 매핑 결과와 앱 서버 Git 저장소의 Java class/import 구조를 읽고, Neo4j에는 탐색용 read model을 동기화합니다.

로컬 Python 실행에서 기본 권장 순서는 다음과 같습니다.

```powershell
Copy-Item .env.example .env
docker compose up -d postgres neo4j
```

`.env.example`은 Neo4j를 기본으로 켜 둡니다.

```env
NEO4J_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ai_commit_advisor
NEO4J_DATABASE=neo4j
```

그다음 Streamlit 앱을 재시작하고 `분석 결과 > Knowledge Graph`에서 `전체 재동기화`를 실행합니다. Neo4j Browser는 `http://localhost:7474`에서 열 수 있습니다.

Neo4j를 끄고 싶을 때만 `.env`를 아래처럼 바꿉니다.

```env
NEO4J_ENABLED=false
```

Neo4j를 켜지 않아도 Knowledge Graph 화면은 PostgreSQL과 현재 소스 기준으로 동기화 대상 preview를 보여줍니다. 이 상태에서는 Neo4j 저장 action이 비활성 또는 건너뛰기 상태가 되며, 앱의 다른 AI/RAG/분석 기능은 PostgreSQL과 pgvector만으로 계속 동작합니다.

Knowledge Graph 화면의 `Graph 상태`는 세 기준을 비교합니다.

- `Repo HEAD`: 앱 서버 Git 저장소의 현재 commit입니다.
- `DB Sync HEAD`: Git Sync가 PostgreSQL에 마지막으로 저장한 commit입니다.
- `Graph HEAD`: Neo4j graph read model에 마지막으로 반영한 commit입니다.

일반 운영에서는 Git Sync로 새 commit을 가져온 뒤 `최신 변경분만 Neo4j 반영`을 먼저 사용합니다. 이 action은 최근 DB commit/file row를 기준으로 변경된 Java 파일의 current source class/import 관계를 다시 만들고, program mapping edge를 현재 DB 기준으로 새로 맞춥니다. 과거 commit이 어떤 file을 건드렸다는 `TOUCHES_FILE` 이력은 삭제하지 않습니다.

Neo4j 동기화는 node와 edge를 `NEO4J_WRITE_BATCH_SIZE` 단위로 나누어 저장합니다. 일시적인 연결 오류가 나면 `NEO4J_RETRY_ATTEMPTS`와 `NEO4J_RETRY_BACKOFF_SECONDS` 기준으로 같은 batch를 다시 시도합니다. 실패가 계속되면 일부 batch만 반영된 상태일 수 있으므로 `Knowledge Graph` 화면의 실행 세부에서 `completed_*_batch_count`, `written_*_count`, `failed_operation`을 확인하고 `전체 재동기화`로 복구합니다.

`동기화 준비 경고`에 Java parser 제외 파일이나 type 선언 없음이 표시될 수 있습니다. generated source, build output, test fixture, `package-info.java`, `module-info.java`는 graph class/import 근거에서 제외됩니다. 이 경고는 동기화 실패가 아니라 graph coverage 안내입니다. 실제 업무 class가 제외 규칙에 걸렸거나 parser rule이 바뀐 뒤 graph가 어긋나 보이면 `전체 재동기화`를 실행하세요.

`AI 운영 현황` 상단에서도 Neo4j 연결, Knowledge Graph 최신성, 저장 graph readback, 최근 Project Chat GraphRAG evidence 상태를 확인할 수 있습니다. 운영 점검 중 graph 관련 경고가 보이면 `Knowledge Graph로 이동` 버튼으로 graph 동기화 화면에 이동한 뒤 아래 기준에 따라 증분 반영 또는 전체 재동기화를 선택합니다.

주간 점검 보고서에는 같은 graph 상태와 주요 `program -> commit -> file -> class` impact path, Project Chat GraphRAG 사용 여부가 함께 들어갑니다. 보고서에 graph path가 비어 있거나 GraphRAG evidence가 없으면 먼저 `Knowledge Graph` 동기화와 Project Chat 관계 질문 실행 여부를 확인하세요.

다음 경우에는 `전체 재동기화`를 선택하세요.

- 프로젝트에서 처음 Neo4j graph를 저장하는 경우
- 대량 branch 전환, 저장소 경로 교체, parser rule 변경처럼 최근 commit 목록만으로 현재 graph를 보정하기 어려운 경우
- 증분 반영이 실패했거나 오래된 관계가 계속 보이는 경우
- Neo4j Browser에서 직접 graph를 수정했거나 volume 상태가 의심되는 경우

프로젝트 분석 데이터 초기화나 프로젝트 삭제를 실행하면, `NEO4J_ENABLED=true`인 경우 해당 프로젝트의 Neo4j node도 정리합니다. Neo4j가 꺼져 있거나 연결되지 않아도 PostgreSQL 초기화/삭제가 실패하지 않도록 외부 graph cleanup은 best-effort로 처리합니다.

Neo4j volume 자체가 손상되었거나 비밀번호/DB 초기화 상태를 새로 맞춰야 하면 앱을 멈춘 뒤 volume을 재생성합니다. 이 작업은 Neo4j read model만 지우며 PostgreSQL 원본 데이터는 유지됩니다. 재시작 후 `Knowledge Graph`에서 `전체 재동기화`를 실행해 graph를 다시 만듭니다.

```powershell
docker compose stop app neo4j
docker compose rm -f neo4j
docker volume rm ai-commit-advisor_neo4j_data ai-commit-advisor_neo4j_logs
docker compose up -d neo4j app
```

Compose project name이 다르면 volume 이름도 달라질 수 있습니다. 먼저 `docker volume ls`로 실제 이름을 확인하세요.

### Migration 시작 동작

Dockerfile의 기본 command는 앱 시작 전에 다음 순서로 실행됩니다.

```text
python -m src.db.init_db
streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT}
```

`src.db.init_db`는 PostgreSQL 연결을 확인한 뒤 Alembic migration을 최신 revision까지 적용합니다. 빈 DB에는 현재 schema를 만들고, 기존 DB에는 `alembic_version` 상태를 기준으로 누락 migration만 적용합니다. 따라서 Compose 배포에서는 앱 컨테이너가 시작될 때 schema 초기화와 migration 적용이 자동으로 수행됩니다.

운영 중 migration 실패가 보이면 먼저 `docker compose logs app`에서 실패 revision과 DB 접속 정보를 확인하세요. schema 변경은 `migrations/versions/`의 Alembic migration으로 관리해야 하며, `src/db/init_db.py`에 임의 `ALTER TABLE` 목록을 추가하지 않습니다.

### 배포 스모크 체크

앱과 DB가 함께 정상 기동했는지 확인하는 최소 절차입니다.

```powershell
docker compose up -d --build
docker compose ps
```

PostgreSQL healthcheck:

```powershell
docker exec ai_commit_advisor_postgres pg_isready -U ai_user -d ai_commit_advisor
```

Neo4j 실행 확인:

```powershell
docker compose ps neo4j
```

Streamlit health endpoint:

```powershell
Invoke-WebRequest http://localhost:8501/_stcore/health -UseBasicParsing
```

정상이라면 Streamlit health endpoint가 HTTP 200 응답을 반환합니다. 이후 브라우저에서 `http://localhost:8501`을 열어 Home 화면이 표시되는지 확인합니다.

## 하루 시연용 Cloudflare Quick Tunnel

### 도입 목적과 사용 범위

외부 참석자에게 샘플 화면을 하루 정도 보여줘야 하지만 도메인, 공인 IP, 공유기 port forwarding을 준비하기 어려울 수 있습니다. Cloudflare Quick Tunnel은 앱 서버의 `cloudflared`가 Cloudflare로 outbound 연결을 먼저 만들고, Cloudflare가 발급한 임시 `trycloudflare.com` 주소의 요청을 그 연결로 전달합니다. 따라서 건물 공유기나 CGNAT 환경에서도 outbound 연결만 허용되면 사용할 수 있습니다.

이 절차는 다음 조건에 맞는 짧은 시연용입니다.

- 실제 업무 데이터가 아니라 공개해도 되는 샘플 데이터만 사용합니다.
- 실행할 때마다 주소가 바뀌어도 참석자에게 새 주소를 전달할 수 있습니다.
- Quick Tunnel의 가동 시간 보장이 없고 중간에 다시 열어야 할 수 있음을 받아들입니다.
- RAG나 Project Chat을 시연한다면 현재 DB의 pgvector column과 `PGVECTOR_DIMENSION`이 같은지 미리 확인합니다. Quick Tunnel은 embedding 설정 불일치를 보정하지 않습니다.
- 고정 주소, 로그인, 장기 운영이 필요하면 Quick Tunnel 대신 Cloudflare Access를 적용한 Named Tunnel이나 사내 reverse proxy를 사용합니다.

Cloudflare가 공개한 Quick Tunnel 제한은 동시 처리 중인 request 200개와 Server-Sent Events 미지원입니다. Streamlit은 WebSocket을 사용하므로 기본 화면 연결은 가능하지만, Cloudflare나 로컬 네트워크 연결이 끊기면 브라우저가 다시 연결될 수 있습니다. 최신 제한은 [Cloudflare Quick Tunnels 문서](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)를 확인하세요.

### 저장소의 실행 스크립트를 사용하는 이유

`scripts/quick_tunnel.py`는 운영자가 Docker network 이름이나 `cloudflared` 실행 옵션을 외우지 않아도 다음 작업을 같은 절차로 수행하도록 추가했습니다.

1. Docker daemon을 확인합니다.
2. `app` service와 의존 service를 기동하고 로컬 `/_stcore/health`가 `200 ok`인지 기다립니다.
3. Cloudflare 공식 `cloudflare/cloudflared` image를 `restart=unless-stopped`인 별도 container로 실행하고 앱의 Compose network에 연결합니다.
4. 현재 container process가 시작된 이후 로그에서 임시 URL을 찾아 외부 `/_stcore/health`까지 검증합니다.
5. 상태와 URL을 다시 조회하거나 전용 Tunnel container만 종료합니다.

호스트 OS에 `cloudflared`를 별도로 설치하지 않으며 `.cloudflared/config.yaml`도 사용하지 않습니다. 스크립트가 새로 만드는 `ai_commit_advisor_demo_tunnel`만 ownership label을 붙여 종료·제거합니다. 이전 절차로 만든 `ai_commit_advisor_quick_tunnel`이 실행 중이면 상태와 URL을 read-only로 확인하고 그대로 재사용합니다. Legacy container에는 ownership label이 없으므로 스크립트가 자동 삭제하지 않습니다. `docker compose down`, volume 삭제, PostgreSQL/Neo4j 초기화도 실행하지 않습니다.

### 다른 개발 세션과 함께 사용할 때

Git branch나 worktree가 달라도 Docker runtime은 자동으로 분리되지 않습니다. 이 스크립트는 Compose project `ai-commit-advisor`와 `ai_commit_advisor_app`을 사용하고, 새 Tunnel은 `ai_commit_advisor_demo_tunnel`로 만듭니다. 기존 `ai_commit_advisor_quick_tunnel`도 조회 대상입니다. 다른 터미널이나 Agent 세션이 같은 앱 container를 빌드·실행 중이라면 Quick Tunnel 시작 또는 `--stop-app`이 그 세션에도 영향을 줍니다.

시작 전에는 다음을 확인하세요.

- 다른 세션이 Docker 앱을 재빌드하거나 port `8501`을 사용하고 있지 않습니다.
- 로컬 Python Streamlit과 Docker Streamlit을 동시에 실행하지 않습니다.
- 다른 세션이 실행 중이라면 파일용 worktree만 새로 만들지 말고 Docker 실행 시점도 서로 합의합니다.

`status`는 container와 health를 읽기만 하므로 먼저 실행해도 됩니다.

```powershell
.\.venv\Scripts\python.exe scripts\quick_tunnel.py status
```

### 검증된 시연 환경 재기동

정상 재기동은 통합 startup script를 사용합니다. 이 명령은 실행 중인 Tunnel을 먼저 조회하고 새 주소를 임의로 만들지 않습니다.

```powershell
.\scripts\demo_start.ps1
```

현재 source로 app image를 다시 만들어야 할 때만 `-Build`, 실행 중인 Tunnel이 없고 새 외부 URL이 필요할 때만 `-StartTunnel`을 추가합니다.

```powershell
.\scripts\demo_start.ps1 -Build
.\scripts\demo_start.ps1 -StartTunnel
```

### Quick Tunnel만 처음 시작하거나 현재 소스를 다시 빌드할 때

Docker Desktop을 실행한 뒤 저장소 root에서 다음 명령을 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\quick_tunnel.py start --build
```

`--build`는 현재 source로 app image를 다시 만듭니다. PostgreSQL과 Neo4j volume은 유지합니다. 최초 image build와 `cloudflare/cloudflared` image pull에는 시간이 걸릴 수 있습니다.

정상 출력에는 다음 정보가 포함됩니다.

```text
Quick Tunnel 준비가 완료됐습니다.
외부 URL: https://example-random-words.trycloudflare.com
외부 health: 200 ok
```

외부 참석자에게는 출력된 root URL을 전달합니다. 시연 전에는 같은 Wi-Fi가 아닌 휴대전화 데이터망에서 URL을 열어 Home 화면과 주요 시연 동선을 확인하세요.

### 기존 app image로 다시 시작할 때

source 변경 없이 같은 image를 재사용한다면 `--build`를 생략합니다.

```powershell
.\.venv\Scripts\python.exe scripts\quick_tunnel.py start
```

Ownership label이 붙은 전용 Tunnel이나 legacy `ai_commit_advisor_quick_tunnel`이 실행 중이면 기존 주소를 재사용하고 외부 health를 다시 확인합니다. 전용 container가 중지된 상태이거나 실행 중인 Tunnel이 없으면 새 Quick Tunnel을 만들므로 새 주소가 발급됩니다. 새 전용 Tunnel은 `restart=unless-stopped`로 생성되어 Docker daemon 재시작 뒤 자동 복구됩니다. 동시에 두 Tunnel이 실행 중이면 주소를 임의로 선택하지 않고 오류로 중단합니다.

다른 `cloudflared` image를 검증해야 할 때는 `--image`를 명시하거나 `CLOUDFLARED_IMAGE` 환경 변수를 사용합니다.

```powershell
.\.venv\Scripts\python.exe scripts\quick_tunnel.py start --image cloudflare/cloudflared:latest
```

### 상태 확인

```powershell
.\.venv\Scripts\python.exe scripts\quick_tunnel.py status
```

상태 명령은 다음 항목을 표시합니다.

- app container 실행 여부
- 로컬 Streamlit health
- Tunnel container 실행 여부
- 현재 container 실행에서 발급된 외부 URL
- 외부 Streamlit health

앱이나 Tunnel이 중지됐거나 health가 실패하면 종료 code `1`을 반환합니다.

Docker daemon이 재시작되면 같은 Tunnel container도 새 process로 올라오지만 Quick Tunnel URL은 새로 발급될 수 있습니다. 과거 로그의 URL을 재사용하지 말고 `status` 출력에서 현재 URL을 확인합니다. 명시적인 `stop` 또는 `docker stop`을 실행한 container는 자동으로 다시 켜지지 않습니다.

### 시연 종료

Tunnel만 닫고 Docker 앱과 DB를 유지하려면 다음 명령을 사용합니다.

```powershell
.\.venv\Scripts\python.exe scripts\quick_tunnel.py stop
```

Tunnel과 app container를 함께 중지하려면 `--stop-app`을 명시합니다.

```powershell
.\.venv\Scripts\python.exe scripts\quick_tunnel.py stop --stop-app
```

`--stop-app`도 PostgreSQL, Neo4j, Docker volume은 중지하거나 삭제하지 않습니다. Legacy `ai_commit_advisor_quick_tunnel`은 자동 제거 대상이 아니므로 `status`가 알려준 이름을 확인한 뒤 `docker stop ai_commit_advisor_quick_tunnel`로 명시적으로 중지합니다. 외부 공개를 끝내기로 결정했을 때만 이 종료 명령을 사용합니다. 별도 종료 요청이 없으면 운영 스크립트와 Agent는 Tunnel을 유지합니다.

### 보안과 공용 네트워크 주의사항

랜덤 URL은 인증 수단이 아닙니다. 주소를 아는 사용자는 앱의 조회뿐 아니라 화면에 제공되는 저장·동기화·삭제 action도 실행할 수 있습니다. 실제 업무 저장소, 실제 사용자 정보, credential, 민감한 diff는 Quick Tunnel에 노출하지 않습니다.

현재 기본 Compose port mapping은 host interface에 앱 `8501`, PostgreSQL `5432`, Neo4j `7474/7687`을 publish합니다. Quick Tunnel 스크립트는 앱 `8501`이 `0.0.0.0` 또는 `::`에 열려 있으면 경고하지만 Compose나 Windows Firewall을 자동 변경하지 않습니다. 원룸 공용망이나 신뢰할 수 없는 네트워크에서는 host firewall로 inbound 접근을 막거나 port mapping을 loopback으로 제한하는 별도 배포 설정이 필요합니다. LM Studio를 사용할 때도 model server를 공용 network interface에 열지 않습니다.

### 문제 해결

`Docker daemon version을 확인하지 못했습니다`가 표시되면 Docker Desktop을 실행하고 다음 명령이 성공하는지 확인합니다.

```powershell
docker version
```

로컬 health가 실패하면 앱 로그에서 DB 연결, migration, port 충돌을 확인합니다.

```powershell
docker compose --project-name ai-commit-advisor ps
docker compose --project-name ai-commit-advisor logs --tail 100 app
```

Tunnel URL 발급이나 외부 health가 실패하면 `status`가 표시한 container 이름으로 DNS, UDP, TCP precheck 로그를 확인합니다.

```powershell
docker logs ai_commit_advisor_demo_tunnel
# legacy container를 재사용 중인 경우
docker logs ai_commit_advisor_quick_tunnel
```

Cloudflare Tunnel은 outbound `7844/UDP`의 QUIC을 우선 사용하고, 사용할 수 없으면 `7844/TCP`의 HTTP/2를 시도합니다. 두 protocol이 모두 차단된 건물망에서는 공유기 port forwarding과 무관하게 Tunnel을 열 수 없습니다. 연결 요구사항은 [Cloudflare connectivity pre-checks](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/troubleshoot-tunnels/connectivity-prechecks/)에서 확인합니다.

외부 주소에서 `502` 또는 origin 연결 오류가 표시되면 app container와 로컬 health를 먼저 확인합니다. Tunnel container를 재시작해야 한다면 `stop` 후 `start`를 실행하고 새 URL을 참석자에게 전달합니다.

## LLM 설정

기본 `.env.example`은 mock입니다. 실제 LLM 호출 없이 동작 확인용 fallback 결과를 생성합니다.

```env
LLM_PROVIDER=mock
LLM_BASE_URL=http://127.0.0.1:12345/v1
LLM_API_KEY=
LLM_MODEL=exaone-3.5-2.4b-instruct
```

LM Studio를 사용할 경우 `.env.local-llm.example`을 복사하거나 `.env`를 아래처럼 설정합니다.

1. LM Studio에서 모델을 로드합니다.
2. Local Server를 켭니다.
3. 서버 주소가 `http://127.0.0.1:12345`인지 확인합니다.
4. `.env`를 아래처럼 설정합니다.

```env
LLM_PROVIDER=local_openai
LLM_BASE_URL=http://127.0.0.1:12345/v1
LLM_API_KEY=
LLM_MODEL=qwen2.5-coder-7b-instruct
```

일부 모델은 LM Studio prompt template 문제로 `prediction-error` 또는 Jinja template 오류가 날 수 있습니다. 이 경우 `lmstudio-community` 모델을 사용하거나 해당 모델의 Prompt Template을 수정하세요.

## 검색 준비 / RAG 설정

기본값은 mock embedding입니다. 실제 검색 품질을 보려면 OpenAI-compatible embedding 서버를 사용하세요.

```env
EMBEDDING_PROVIDER=local_openai
EMBEDDING_BASE_URL=http://127.0.0.1:12345/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v2-moe
PGVECTOR_DIMENSION=768
```

LM Studio를 사용할 경우 embedding 모델을 로드하고 Local Server를 켠 뒤, RAG 화면의 `검색 준비 연결 테스트`로 `/v1/embeddings` 응답과 vector dimension을 확인합니다. `PGVECTOR_DIMENSION`은 사용하는 embedding 모델의 출력 차원과 같아야 하며, 이미 다른 차원으로 생성된 `vector_items.embedding` 컬럼은 DB를 새로 만들거나 migration해야 합니다.

mock embedding이나 이전 Nomic 모델로 생성한 vector는 새 모델 검색에 사용되지 않습니다. 애플리케이션은 `query`와 `document` task prefix를 구분하고 이 검색 프로필을 model key에 포함합니다. `LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `PGVECTOR_DIMENSION` 또는 prefix 정책을 바꾼 뒤에는 현재 model key 기준으로 embedding을 다시 생성해야 RAG Search와 Project Chat이 같은 근거를 검색할 수 있습니다.

Project Chat을 실제 LLM 모드로 검증하는 권장 순서:

1. LM Studio에서 chat 모델과 embedding 모델을 로드합니다.
2. `Copy-Item .env.local-llm.example .env`로 local LLM 설정을 적용합니다.
3. Streamlit 앱을 재시작합니다.
4. RAG 검색 화면에서 `검색 준비 연결 테스트`를 실행합니다.
5. RAG 검색 화면의 `검색 준비` 탭에서 현재 소스의 검색 준비를 실행합니다.
6. GraphRAG 관계 근거까지 확인하려면 `Knowledge Graph` 화면에서 처음에는 `전체 재동기화`를 실행하고, 이후 Git Sync 변경분은 `최신 변경분만 Neo4j 반영`으로 갱신합니다.
7. Project Chat에서 직접 질문하거나 `관계 질문` 템플릿을 실행하고, `답변 근거 보기`와 `그래프 관계 근거 보기`를 펼쳐 현재 소스 근거와 관계 근거를 확인합니다. 템플릿 버튼이 비활성화되어 있으면 `Knowledge Graph`가 최신 상태인지 먼저 확인하세요.
8. 답변을 기록으로 남겨야 하면 `근거 복사용 Markdown` 내용을 회의록, 리뷰 문서, 이슈에 붙여 넣습니다.

PL Briefing, Project Chat, AI Code Review, Mapping을 같은 방식으로 반복 확인하려면 [Local LLM Verification](local-llm-verification.md)을 사용합니다. 이 루틴은 local provider로 실행한 기능과 fallback 여부를 `ai_invocation_logs`에 남기고, `AI 운영 현황 > 실제 LLM 검증`에서 최근 실행 증거를 확인하게 합니다. CI나 기본 mock 환경에서는 실행하지 않습니다.

## Project Chat 답변 근거 갱신 운영 주의사항

Project Chat은 질문할 때마다 저장소 전체를 다시 읽지 않고, 미리 준비한 소스 근거에서 질문과 관련된 부분을 찾습니다. 이 준비는 두 단계로 나뉩니다. 먼저 현재 코드를 읽어 `소스 근거`를 만들고, 그다음 질문과 비슷한 근거를 찾을 수 있도록 `검색 준비`를 만듭니다. 두 번째 단계는 로컬 LLM/embedding 서버의 CPU/GPU와 메모리를 오래 점유할 수 있으므로 한 번에 많이 실행하지 않고 제한 수량으로 나누어 처리합니다. GraphRAG 관계 근거는 `Knowledge Graph`에서 Neo4j graph를 동기화해 둔 경우에만 추가됩니다.

- `Project Chat > 최신 변경분 반영`: Git 동기화 후 바뀐 파일만 빠르게 읽어 Project Chat 답변 근거를 최신화합니다. 일반적인 개발 흐름에서는 이 버튼을 먼저 사용합니다.
- `Project Chat > 전체 소스 다시 읽기`: 처음 준비하거나 브랜치를 크게 바꿨거나 오래된 근거가 계속 보일 때 현재 소스를 전체 기준으로 다시 읽습니다.
- `RAG 검색 > 최신 변경분 반영`: Project Chat의 `최신 변경분 반영`과 같은 계열의 작업입니다. RAG 화면에서 직접 실행할 때 사용합니다.
- `RAG 검색 > 전체 소스 다시 읽기`: 기본값은 소스 근거 갱신만 수행합니다. `전체 소스 다시 읽은 뒤 검색 준비도 실행`을 직접 체크한 경우에만 제한 수량으로 검색 준비 데이터를 생성합니다.
- `RAG 검색 > 검색 준비`: Project Chat의 `검색 준비`가 전체 근거 수보다 적거나 embedding model을 바꾼 뒤 남은 작업을 처리할 때 사용합니다. 화면에서 남은 작업 수와 예상 소요 시간을 확인한 뒤 여러 번 나눠 실행하세요.

### 증분 인덱싱과 전체 재인덱싱 선택 기준

| 상황 | 권장 action | 이유 |
|---|---|---|
| Git Sync로 최신 commit을 가져온 직후 | `최신 변경분 반영` | 변경된 파일만 읽으므로 대형 repo에서도 빠르고 embedding 비용이 자동 발생하지 않습니다. |
| 특정 파일 수정, 삭제, rename만 반영하면 되는 경우 | `최신 변경분 반영` | `Added`, `Modified`, `Deleted`, `Renamed` path만 chunk 교체/삭제합니다. |
| 처음 Project Chat 근거를 준비하는 경우 | `전체 소스 다시 읽기` | 기준 근거가 없으면 전체 source file scan이 필요합니다. |
| branch를 크게 바꾸었거나 include/exclude/chunking rule이 바뀐 경우 | `전체 소스 다시 읽기` | 최근 commit file 목록만으로는 전체 repository snapshot을 보정하기 어렵습니다. |
| stale/invalid chunk가 많이 보이거나 삭제된 파일이 계속 evidence에 나타나는 경우 | `전체 소스 다시 읽기` | 전체 scan과 검증 cleanup으로 오래된 chunk/vector를 정리합니다. |
| 소스 근거는 최신인데 검색 결과가 없거나 embedding model을 바꾼 경우 | `RAG 검색 > 검색 준비` | 현재 model 기준 missing vector만 제한 수량으로 생성해야 합니다. |

증분 인덱싱의 처리 방식은 다음과 같습니다.

1. 화면에서 현재 `Current HEAD`, `Indexed HEAD`, stale/invalid chunk 수를 확인합니다.
2. Git Sync가 최신 commit을 저장한 상태라면 Project Chat에서 `최신 변경분 반영`을 실행합니다.
3. app은 최근 indexed HEAD 이후 DB에 저장된 `CommitFile` row를 읽습니다.
4. source-like text/code file만 chunk 대상으로 삼고, binary/image/Excel/cache/virtualenv/oversized file은 건너뜁니다.
5. 수정된 파일은 기존 path chunk와 vector를 제거한 뒤 새 chunk를 만들고 `embedding_status=pending`으로 둡니다.
6. 삭제된 파일은 해당 path의 chunk와 vector를 제거합니다.
7. rename은 old path를 제거하고 new path가 source-like file이면 새 chunk를 만듭니다.
8. 검색 품질 확인이 필요하면 `RAG 검색 > 검색 준비`에서 아직 검색 준비가 안 된 근거를 작은 limit으로 나누어 처리합니다.

중요한 비용 제어 규칙:

- Git Sync는 commit/diff metadata만 저장하며 embedding API를 호출하지 않습니다.
- `최신 변경분 반영`은 소스 근거만 갱신하며 embedding API를 호출하지 않습니다.
- Project Chat의 답변 근거 갱신 버튼도 embedding API를 호출하지 않습니다.
- embedding API 호출은 `RAG 검색 > 검색 준비` 또는 RAG 검색의 `한 번에 준비` 화면에서 사용자가 명시적으로 선택한 제한 수량에서만 발생합니다.
- embedding provider/model/dimension을 바꾸면 기존 vector를 조용히 재사용하지 말고 현재 model 기준 missing vector를 다시 생성하세요.

Project Chat 대화는 프로젝트별 DB session으로 저장됩니다. `대화 관리`에서 저장된 대화를 선택할 수 있고, `새 대화 시작`은 기존 이력을 삭제하지 않고 새 session을 만듭니다. 이전 session은 `저장된 대화`에서 다시 선택할 수 있습니다.

재인덱싱이나 embedding 중 앱 또는 LM Studio를 강제 종료하면 PostgreSQL은 열린 transaction을 롤백합니다. 다만 이미 commit된 chunk/vector와 아직 처리되지 않은 chunk가 섞여 `pending` 또는 `failed` 상태가 남을 수 있습니다. 이 상태는 부분 완료 상태이며, RAG 화면에서 인덱스 상태를 확인한 뒤 embedding을 제한 수량으로 이어서 실행하면 됩니다.

강제 종료 후 상태 점검 예시:

```powershell
docker exec ai_commit_advisor_postgres pg_isready -U ai_user -d ai_commit_advisor
```

```powershell
@'
from sqlalchemy import text
from src.db.database import SessionLocal

with SessionLocal() as db:
    for name, sql in {
        "source_file_chunks": "select count(*) from document_chunks where source_type = 'source_file'",
        "source_file_vectors": "select count(*) from vector_items v join document_chunks c on c.id = v.chunk_id where c.source_type = 'source_file'",
        "orphan_vectors": "select count(*) from vector_items v left join document_chunks c on c.id = v.chunk_id where c.id is null",
    }.items():
        print(f"{name}: {db.execute(text(sql)).scalar()}")

    rows = db.execute(text("""
        select coalesce(raw_metadata->>'embedding_status', 'null') as status, count(*)
        from document_chunks
        where source_type = 'source_file'
        group by 1
        order by 1
    """)).all()
    for status, count in rows:
        print(f"{status}: {count}")
'@ | .\.venv\Scripts\python.exe -
```

`orphan_vectors`가 0이면 vector가 없는 chunk는 있어도 참조가 깨진 vector는 없는 상태입니다. `pending`은 아직 embedding이 생성되지 않은 chunk, `failed`는 embedding 호출 실패가 기록된 chunk입니다.

## 로컬 검증 명령

```powershell
.\.venv\Scripts\python.exe -m compileall src app.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "from src.db.init_db import init_db; init_db(); print('init ok')"
streamlit run app.py
```

GitHub Actions의 `CI` workflow도 기본 검증으로 `python -m compileall src app.py`와 `python -m pytest -q`를 실행합니다.

Home 화면 문구와 기본 렌더링을 확인하려면 Streamlit 실행 후 아래 명령을 사용합니다. Chromium 브라우저가 없으면 먼저 `.\.venv\Scripts\python.exe -m playwright install chromium`을 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\verify_home_ui.py
```

검증이 끝나면 `.tmp/home-ui-check.png`에 캡처가 생성됩니다.

README 또는 Application Preview에 들어갈 기능 캡처를 갱신할 때는 공통 캡처 스크립트를 사용합니다.

```powershell
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature home --url http://localhost:8501
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature project-chat --url http://localhost:8501
```

기본 저장 위치는 `docs/images/features/<feature>.png`입니다. 임시 확인용으로 저장하려면 `--screenshot .tmp/project-chat-check.png`처럼 별도 경로를 지정합니다.

큰 기능 변경 후 화면 캡처를 갱신할 때는 빈 화면보다 기능 가치가 드러나는 상태를 사용합니다. 예를 들어 Project Chat은 sample project, 대화 관리, 질문, 답변 근거가 보이는 상태에서 캡처해야 합니다. 현재 실행 surface를 남기려면 `--surface local` 또는 `--surface docker`를 명시합니다.

```powershell
.\.venv\Scripts\python.exe scripts\capture_feature_screenshot.py --feature project-chat --surface docker --expect-text "결제금액 검증은 어디에서 수행되나요?" --expect-text "PaymentService.java" --forbid-text "현재 검증된 소스 근거만으로는 답변하기 어렵습니다"
```

`--expect-text`와 `--forbid-text`는 캡처 전에 화면 상태를 검증합니다. 이 옵션을 사용하면 단순히 화면을 저장하는 데서 끝나지 않고, README에 올릴 캡처가 실제 기능 결과를 보여주는지 확인할 수 있습니다.

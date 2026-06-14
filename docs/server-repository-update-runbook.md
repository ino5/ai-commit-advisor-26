# 서버 Git 저장소 갱신 Runbook

이 문서는 사내 앱 서버에 이미 clone된 Git 저장소를 최신화한 뒤 AI Commit Advisor에서 Git 동기화를 실행하는 절차를 설명합니다.

AI Commit Advisor는 현재 remote URL, access token, SSH key를 받아 저장소를 직접 clone/fetch하지 않습니다. 운영자 또는 배포/운영 스크립트가 `REPO_STORAGE_ROOT` 아래 저장소를 준비하고 갱신합니다.

## 전제 조건

- 앱 서버에 `git` 명령이 설치되어 있어야 합니다.
- 분석 대상 저장소가 `REPO_STORAGE_ROOT` 아래에 clone되어 있어야 합니다.
- 앱 실행 계정 또는 운영 스크립트 실행 계정이 해당 저장소를 읽고 갱신할 권한을 가져야 합니다.
- private repository는 서버 OS의 SSH key, credential helper, 배포 계정 등 앱 밖의 운영 방식으로 인증을 처리합니다.

권장 root 예시:

```text
/srv/ai-commit-advisor/repos
```

## 수동 갱신

단일 저장소를 직접 갱신할 때는 다음 순서로 실행합니다.

```bash
cd /srv/ai-commit-advisor/repos/order-system
git fetch --prune origin
git checkout main
git reset --hard origin/main
```

이 명령은 서버 저장소의 local 변경을 버리고 `origin/main`과 맞춥니다. 운영 서버의 분석용 clone에는 직접 수정한 파일을 남기지 않는 것이 원칙입니다.

갱신 후 AI Commit Advisor의 `Git 동기화` 화면에서 전체 수집 또는 증분 동기화를 실행합니다.

## 스크립트 사용

여러 저장소를 같은 root 아래에서 관리할 때는 `scripts/update_server_repos.py`를 사용할 수 있습니다.

기본 실행은 root 아래 Git 저장소를 찾아 `git fetch --prune origin`만 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\update_server_repos.py --root C:\dev
```

Linux 서버 예시:

```bash
python scripts/update_server_repos.py --root /srv/ai-commit-advisor/repos
```

`.env` 또는 환경 변수에 `REPO_STORAGE_ROOT`가 있으면 `--root`를 생략할 수 있습니다.

```bash
REPO_STORAGE_ROOT=/srv/ai-commit-advisor/repos python scripts/update_server_repos.py
```

특정 저장소만 갱신할 수도 있습니다.

```bash
python scripts/update_server_repos.py \
  --root /srv/ai-commit-advisor/repos \
  --repo /srv/ai-commit-advisor/repos/order-system
```

## Branch reset

분석용 서버 clone을 원격 branch와 정확히 맞추려면 `--reset`을 명시합니다.

```bash
python scripts/update_server_repos.py \
  --root /srv/ai-commit-advisor/repos \
  --branch main \
  --reset
```

`--reset`은 내부적으로 다음 흐름을 수행합니다.

```text
git fetch --prune origin
git checkout main
git reset --hard origin/main
```

working tree에 local 변경이 있으면 기본적으로 reset을 건너뜁니다. 분석용 clone의 local 변경을 버려도 되는 운영 정책이 확실할 때만 `--force`를 추가합니다.

```bash
python scripts/update_server_repos.py \
  --root /srv/ai-commit-advisor/repos \
  --branch main \
  --reset \
  --force
```

## Dry run

실행 전에 대상 저장소와 수행할 작업을 확인하려면 `--dry-run`을 사용합니다.

```bash
python scripts/update_server_repos.py \
  --root /srv/ai-commit-advisor/repos \
  --branch main \
  --reset \
  --dry-run
```

## 운영 순서

1. 운영자 또는 배포 job이 서버 저장소를 갱신합니다.
2. AI Commit Advisor에서 현재 프로젝트를 선택합니다.
3. `Git 동기화` 화면에서 증분 동기화 또는 전체 수집을 실행합니다.
4. 필요한 경우 `RAG 검색` 또는 `Project Chat`에서 `최신 변경분 반영`을 실행합니다.
5. embedding은 별도 화면에서 제한 수량으로 실행합니다.

## 주의사항

- 이 스크립트는 저장소를 새로 clone하지 않습니다.
- 이 스크립트는 access token, SSH key, password를 저장하지 않습니다.
- 앱 서버에서 직접 수정한 파일이 있는 저장소에 `--reset --force`를 사용하면 local 변경이 사라집니다.
- branch 이름이 프로젝트마다 다르면 저장소별로 명령을 나누거나 운영 스크립트에서 branch mapping을 별도로 관리하세요.
- 앱 내 clone/fetch 자동화는 인증 정보와 동시 실행 lock 정책이 필요하므로 별도 후속 작업으로 다룹니다.

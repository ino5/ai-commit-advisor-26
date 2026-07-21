# Git 저장소 운영 모델

AI Commit Advisor는 앱 서버에서 접근 가능한 Git 저장소를 기준으로 분석합니다. 브라우저 사용자의 PC에 있는 `C:\dev\...` 같은 경로를 직접 읽는 구조가 아닙니다.

이 문서는 사내 서버에서 AI Commit Advisor를 실행하고, 여러 사용자가 내부망 브라우저로 접속하는 운영 모델을 설명합니다.

## 핵심 전제

앱이 Git 저장소를 분석하려면 Streamlit 앱 프로세스가 그 저장소 경로를 읽을 수 있어야 합니다.

```text
사내 앱 서버
- AI Commit Advisor 실행
- PostgreSQL 실행
- 분석 대상 Git 저장소 보관
- git log / git show / source indexing / Project Chat 검증 실행

사용자
- 내부망 브라우저로 앱 접속
- 서버가 수집한 Git 이력과 분석 결과를 함께 사용
```

따라서 프로젝트/Git 설정 화면에 입력하는 경로는 사용자 PC 경로가 아니라 앱 서버 기준 경로입니다.

예:

```text
Linux 서버: /srv/ai-commit-advisor/repos/order-system
Windows 서버: D:\ai-commit-advisor\repos\order-system
Docker 컨테이너: /srv/ai-commit-advisor/repos/order-system
```

## 개인 PC 실행과 사내 서버 실행

개인 PC에서 앱을 실행하면 그 PC가 앱 서버입니다. 이 경우 `C:\dev\sample-project` 같은 경로를 등록할 수 있습니다.

사내 서버에서 앱을 실행하면 사내 서버가 앱 서버입니다. 팀원이 브라우저로 접속하더라도 앱은 팀원 PC의 파일을 읽지 않고, 사내 서버에 clone된 저장소만 읽습니다.

이 차이를 명확히 하는 이유는 Git Sync, RAG source indexing, Project Chat, AI Code Review가 모두 실제 Git 저장소 파일과 `git` 명령에 의존하기 때문입니다.

## 권장 사내 서버 디렉터리

사내 서버에서는 앱 전용 저장소 루트를 하나 두는 방식을 권장합니다.

```text
/srv/ai-commit-advisor/repos
  order-system
  payment-system
  settlement-system
```

Linux 서버 예시:

```bash
sudo mkdir -p /srv/ai-commit-advisor/repos
sudo chown -R ai-advisor:ai-advisor /srv/ai-commit-advisor
sudo chmod 750 /srv/ai-commit-advisor/repos
```

분석 대상 저장소는 운영자가 이 경로 아래에 clone해 둘 수 있습니다. 외부 사용자가 공개 저장소를 등록하도록 운영할 때는 read-only 분석 root와 별도로 관리형 clone root를 준비합니다.

```bash
git clone <remote-url> /srv/ai-commit-advisor/repos/order-system
```

## 경로 제한

운영 서버에서는 앱이 서버의 임의 경로를 읽지 못하도록 `REPO_STORAGE_ROOT`를 설정하는 것이 좋습니다.

```env
REPO_STORAGE_ROOT=/srv/ai-commit-advisor/repos
```

이 값이 설정되면 프로젝트/Git 설정 화면은 해당 루트 밖의 Git 저장소 경로 등록을 막습니다. 설정하지 않으면 기존 로컬 검증 범위와 샘플 프로젝트 흐름처럼 자유 경로를 사용할 수 있습니다.

Docker 예시:

```yaml
services:
  app:
    environment:
      REPO_STORAGE_ROOT: /srv/ai-commit-advisor/repos
      MANAGED_REPO_STORAGE_ROOT: /srv/ai-commit-advisor/managed-repos
      MANAGED_GIT_ALLOWED_HOSTS: github.com,gitlab.com,bitbucket.org
    volumes:
      - /srv/ai-commit-advisor/repos:/srv/ai-commit-advisor/repos:ro
      - /srv/ai-commit-advisor/managed-repos:/srv/ai-commit-advisor/managed-repos:rw
```

## Docker와 host path mapping

Windows 개발 PC에서 Docker 앱을 실행할 때는 DB에 저장되는 Windows 경로와 컨테이너 내부 경로가 다를 수 있습니다. 이때는 기존 `REPO_PATH_HOST_PREFIX`, `REPO_PATH_CONTAINER_PREFIX` mapping을 사용합니다.

```yaml
environment:
  REPO_STORAGE_ROOT: "C:\\dev"
  REPO_PATH_HOST_PREFIX: "C:\\dev"
  REPO_PATH_CONTAINER_PREFIX: /host-dev
  MANAGED_REPO_STORAGE_ROOT: "C:\\dev\\ai-commit-advisor-managed-repos"
  MANAGED_REPO_CONTAINER_PREFIX: /managed-repos
volumes:
  - C:/dev:/host-dev:ro
  - C:/dev/ai-commit-advisor-managed-repos:/managed-repos:rw
```

이 설정은 `C:\dev\sample-project`로 저장된 기존 경로를 컨테이너 내부의 `/host-dev/sample-project`로 변환해 읽습니다. `C:\dev\ai-commit-advisor-managed-repos\project-7` 같은 관리형 경로는 더 구체적인 mapping을 먼저 적용해 `/managed-repos/project-7`에서 clone/fetch합니다.

Linux 사내 서버에서 컨테이너와 host가 같은 경로를 쓰도록 volume을 mount한다면 host-prefix mapping 없이도 운영할 수 있습니다.

## Git Sync와 저장소 갱신

Git Sync는 앱 서버 저장소에 존재하는 commit, 변경 파일, diff를 DB에 수집하는 기능입니다. `서버 저장소 clone/fetch`는 원격 저장소를 앱 서버 경로에 준비하거나 갱신하는 작업이고, Git Sync는 그 결과를 DB에 수집하는 별도 단계입니다.

## 권장 운영 정책

권장 정책은 앱이 Git 인증 정보를 저장하지 않고, 기존 read-only 경로와 관리형 read-write 경로를 분리하는 것입니다. 저장소 준비 방식은 두 가지를 지원합니다.

역할을 다음처럼 나눕니다.

| 영역 | 담당 | 설명 |
|---|---|---|
| 기존 저장소 준비/갱신 | 운영자 또는 배포 스크립트 | read-only 분석 root에 저장소를 준비하고 최신화합니다. 앱은 이 경로를 읽어 분석합니다. |
| 관리형 저장소 clone/fetch/reset | AI Commit Advisor | 허용된 공개 HTTPS Git URL을 전용 read-write root의 `project-<ID>` 경로에 clone/fetch합니다. |
| 프로젝트 경로/remote 등록/검증 | AI Commit Advisor | 기존 경로는 허용 root 안인지 확인하고, 관리형 경로는 사용자 입력 없이 자동 배정합니다. |
| Git Sync | AI Commit Advisor | 준비된 저장소에서 commit, 변경 파일, diff를 읽어 DB에 저장합니다. |
| 분석 기능 | AI Commit Advisor | DB에 수집된 Git 이력과 현재 소스를 사용해 Mapping, Risk, RAG, Project Chat, Code Review를 실행합니다. |

이 정책을 선택한 이유는 앱에 필요한 쓰기 권한을 관리형 폴더 하나로 제한하고, 기존 분석 대상과 다른 개발 폴더를 clone/fetch/reset으로 변경하지 않기 위해서입니다.

운영 방식은 두 가지로 나눌 수 있습니다.

1. 운영자가 서버 repo를 직접 갱신합니다.
   - 예: `git fetch --prune`, `git reset --hard origin/main`
   - 이후 앱의 Git 동기화에서 DB 수집을 실행합니다.

2. 앱이 공개 HTTPS remote URL과 branch를 받아 관리형 폴더에서 clone/fetch/reset을 실행합니다.
   - 허용 host 목록, Git credential prompt 비활성화, 작업 timeout, repository lock을 적용합니다.
   - working tree local 변경이 있으면 기본적으로 reset을 건너뜁니다.

private repository는 서버 계정의 SSH key 또는 credential helper로 인증을 미리 준비해야 합니다. 앱 입력창에는 token, password, private key를 넣지 않습니다.

프로젝트 삭제는 DB의 프로젝트 데이터만 삭제하며 관리형 clone 폴더를 자동 삭제하지 않습니다. 운영자는 저장공간 사용량을 확인해 더 이상 참조되지 않는 폴더를 별도 절차로 정리해야 합니다.

구체적인 수동 명령과 `scripts/update_server_repos.py` 사용법은 [서버 Git 저장소 갱신 Runbook](server-repository-update-runbook.md)을 따릅니다.

## 가능한 구조와 불가능한 구조

가능한 구조:

- 개인 PC에서 앱을 실행하고 같은 PC의 Git 저장소를 분석
- 사내 서버에서 앱을 실행하고 서버 디스크의 Git 저장소를 분석
- Docker 앱이 volume으로 mount된 Git 저장소를 분석
- 외부 사용자가 허용된 공개 HTTPS Git URL을 등록하고 서버가 관리형 폴더에 clone

불가능하거나 지원하지 않는 구조:

- 사내 서버 앱이 브라우저 사용자 PC의 `C:\dev\...` 경로를 직접 읽는 방식
- 사용자가 브라우저에 입력한 로컬 파일 경로를 서버가 자동으로 접근하는 방식
- 관리형 등록 화면에서 private repository credential이나 임의 Git host를 받는 방식
- Git 저장소 없이 Project Chat이 현재 소스 검증 근거를 만드는 방식

## 보안과 운영 주의사항

- 내부망에서만 접근하게 하거나 VPN, reverse proxy 인증, 사내 SSO를 사용하세요.
- 운영 서버에서는 `REPO_STORAGE_ROOT`를 설정해 앱이 읽을 수 있는 Git 저장소 범위를 제한하세요.
- 프로젝트 등록 권한을 제한하지 않으면 민감한 서버 경로가 노출될 수 있습니다.
- Git 저장소에는 소스 코드와 diff가 포함되므로 화면 캡처, 로그, DB 백업 관리 정책을 함께 정해야 합니다.
- 앱 서버에는 `git` 명령이 설치되어 있어야 합니다.

## 향후 확장

Git History 화면은 이 운영 모델 위에 붙이는 것이 안전합니다. 커밋 목록과 저장된 diff는 DB에서 보여주고, 전체 diff나 commit graph는 앱 서버 Git 저장소에서 `git show`, `git log --parents`를 읽어 보강할 수 있습니다.

서버가 remote URL을 받아 직접 clone/fetch하는 기능은 인증 정보를 저장하지 않는 범위에서 지원합니다. 향후 앱이 credential vault, 사용자별 권한, 저장소 자동 정리까지 맡아야 한다면 별도 보안 설계가 필요합니다.

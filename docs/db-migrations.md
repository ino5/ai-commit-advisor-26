# DB 마이그레이션

이 프로젝트는 PostgreSQL schema migration에 Alembic을 사용합니다.

## 마이그레이션 적용

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Streamlit 앱도 `init_db()`를 호출하며, 이 과정에서 Alembic migration이 자동 적용됩니다.

## 기존 로컬 DB 처리

이미 application table이 있지만 `alembic_version`이 없는 DB라면, `init_db()`는 현재 schema를 baseline revision으로 stamp한 뒤 이후 migration을 적용합니다.

Baseline revision:

```text
20260608_0001
```

Baseline 이후 revision은 정상적으로 실행됩니다. 예를 들어 mapping feedback column은 다음 revision에서 관리됩니다.

```text
20260608_0002_add_mapping_feedback
```

## 새 마이그레이션 생성

```powershell
.\.venv\Scripts\alembic.exe revision -m "describe schema change"
```

Schema 변경은 생성된 `migrations/versions/*.py` 파일에 작성합니다. 새 schema-upgrade `ALTER TABLE` 목록을 `src/db/init_db.py`에 추가하지 마세요.

## 현재 Revision 확인

```powershell
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe heads
```

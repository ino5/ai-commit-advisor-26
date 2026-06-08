# Database Migrations

This project uses Alembic for PostgreSQL schema migrations.

## Apply Migrations

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

The Streamlit app also calls `init_db()`, which applies Alembic migrations automatically.

## Existing Local Databases

If a database already has the application tables but does not have `alembic_version`,
`init_db()` stamps the existing schema as the baseline revision and then applies later
migrations.

Baseline revision:

```text
20260608_0001
```

Latest revisions after the baseline still run normally. For example, the mapping feedback
columns are managed by:

```text
20260608_0002_add_mapping_feedback
```

## Create a New Migration

```powershell
.\.venv\Scripts\alembic.exe revision -m "describe schema change"
```

Put schema changes in the generated `migrations/versions/*.py` file. Do not add new
schema-upgrade `ALTER TABLE` lists to `src/db/init_db.py`.

## Check Current Revision

```powershell
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe heads
```

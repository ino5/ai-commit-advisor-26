from sqlalchemy import text

from src.db.database import Base, engine
from src.db import models  # noqa: F401


PROGRAM_COLUMN_UPGRADES = [
    "ALTER TABLE programs ADD COLUMN IF NOT EXISTS module VARCHAR(255)",
    "ALTER TABLE programs ADD COLUMN IF NOT EXISTS developer_id VARCHAR(255)",
    "ALTER TABLE programs ADD COLUMN IF NOT EXISTS planned_start_date DATE",
    "ALTER TABLE programs ADD COLUMN IF NOT EXISTS planned_end_date DATE",
    "ALTER TABLE programs ADD COLUMN IF NOT EXISTS actual_start_date DATE",
    "ALTER TABLE programs ADD COLUMN IF NOT EXISTS actual_end_date DATE",
    "ALTER TABLE programs ADD COLUMN IF NOT EXISTS progress_rate DOUBLE PRECISION",
]

DEVELOPER_COLUMN_UPGRADES = [
    "ALTER TABLE developers ADD COLUMN IF NOT EXISTS developer_key VARCHAR(255)",
    "ALTER TABLE developers ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
]

PROJECT_COLUMN_UPGRADES = [
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_synced_commit_hash VARCHAR(64)",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE",
]

GIT_COMMIT_COLUMN_UPGRADES = [
    "ALTER TABLE git_commits ADD COLUMN IF NOT EXISTS author_name VARCHAR(255)",
    "ALTER TABLE git_commits ADD COLUMN IF NOT EXISTS author_email VARCHAR(255)",
    "ALTER TABLE git_commits ADD COLUMN IF NOT EXISTS is_merge_commit BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE git_commits ADD COLUMN IF NOT EXISTS mapping_analyzed_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE git_commits ADD COLUMN IF NOT EXISTS mapping_analysis_status VARCHAR(50)",
]

COMMIT_FILE_COLUMN_UPGRADES = [
    "ALTER TABLE commit_files ADD COLUMN IF NOT EXISTS git_commit_id INTEGER",
]

PROGRAM_COMMIT_MAPPING_COLUMN_UPGRADES = [
    "ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS is_related BOOLEAN",
    "ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_is_related BOOLEAN",
    "ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_relevance_score DOUBLE PRECISION",
    "ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_implementation_status VARCHAR(100)",
    "ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_reason TEXT",
    "ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_updated_at TIMESTAMP WITH TIME ZONE",
]

PROGRAM_IMPLEMENTATION_STATUS_COLUMN_UPGRADES = [
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS status VARCHAR(50)",
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS summary TEXT",
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS completed_features JSONB",
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS incomplete_features JSONB",
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS evidence_commits JSONB",
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS commit_hash_signature VARCHAR(64)",
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE program_implementation_status ADD COLUMN IF NOT EXISTS raw_response JSONB",
]

CODE_REVIEW_COLUMN_UPGRADES = [
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS target_type VARCHAR(50)",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS target_ref VARCHAR(255)",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'completed'",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS summary TEXT",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS commit_analysis JSONB",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS bug_findings JSONB",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS refactoring_suggestions JSONB",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS raw_response JSONB",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE",
    "ALTER TABLE code_review_results ADD COLUMN IF NOT EXISTS finished_at TIMESTAMP WITH TIME ZONE",
]

RISK_FINDING_COLUMN_UPGRADES = [
    "ALTER TABLE risk_findings ADD COLUMN IF NOT EXISTS risk_type VARCHAR(100)",
    "ALTER TABLE risk_findings ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20)",
    "ALTER TABLE risk_findings ADD COLUMN IF NOT EXISTS title VARCHAR(255)",
    "ALTER TABLE risk_findings ADD COLUMN IF NOT EXISTS description TEXT",
    "ALTER TABLE risk_findings ADD COLUMN IF NOT EXISTS evidence JSONB",
    "ALTER TABLE risk_findings ADD COLUMN IF NOT EXISTS detected_at TIMESTAMP WITH TIME ZONE DEFAULT now()",
    "ALTER TABLE risk_findings ADD COLUMN IF NOT EXISTS resolved_yn VARCHAR(1) NOT NULL DEFAULT 'N'",
]

ANALYSIS_RUN_COLUMN_UPGRADES = [
    "ALTER TABLE analysis_runs ADD COLUMN IF NOT EXISTS analysis_type VARCHAR(100)",
    "ALTER TABLE analysis_runs ADD COLUMN IF NOT EXISTS total_count INTEGER",
    "ALTER TABLE analysis_runs ADD COLUMN IF NOT EXISTS processed_count INTEGER",
    "ALTER TABLE analysis_runs ADD COLUMN IF NOT EXISTS failed_count INTEGER",
]


def add_constraint_if_missing(connection, table_name: str, constraint_name: str, ddl: str) -> None:
    connection.execute(
        text(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint c
                    JOIN pg_class t ON c.conrelid = t.oid
                    WHERE c.conname = :constraint_name
                      AND t.relname = :table_name
                ) THEN
                    {ddl};
                END IF;
            END $$;
            """
        ),
        {"constraint_name": constraint_name, "table_name": table_name},
    )


def upgrade_existing_schema() -> None:
    with engine.begin() as connection:
        for statement in PROJECT_COLUMN_UPGRADES:
            connection.execute(text(statement))
        for statement in DEVELOPER_COLUMN_UPGRADES:
            connection.execute(text(statement))
        connection.execute(text("UPDATE developers SET developer_key = developer_id WHERE developer_key IS NULL"))
        add_constraint_if_missing(
            connection,
            "developers",
            "uq_developers_developer_key",
            "ALTER TABLE developers ADD CONSTRAINT uq_developers_developer_key UNIQUE (developer_key)",
        )
        for statement in PROGRAM_COLUMN_UPGRADES:
            connection.execute(text(statement))
        for statement in GIT_COMMIT_COLUMN_UPGRADES:
            connection.execute(text(statement))
        connection.execute(text("UPDATE git_commits SET author_name = author WHERE author_name IS NULL"))
        for statement in COMMIT_FILE_COLUMN_UPGRADES:
            connection.execute(text(statement))
        for statement in PROGRAM_COMMIT_MAPPING_COLUMN_UPGRADES:
            connection.execute(text(statement))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS program_implementation_status (
                    id SERIAL PRIMARY KEY,
                    program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
                    status VARCHAR(50) NOT NULL,
                    summary TEXT,
                    completed_features JSONB,
                    incomplete_features JSONB,
                    evidence_commits JSONB,
                    commit_hash_signature VARCHAR(64),
                    analyzed_at TIMESTAMP WITH TIME ZONE,
                    raw_response JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
                """
            )
        )
        for statement in PROGRAM_IMPLEMENTATION_STATUS_COLUMN_UPGRADES:
            connection.execute(text(statement))
        add_constraint_if_missing(
            connection,
            "program_implementation_status",
            "uq_program_implementation_status_program_id",
            "ALTER TABLE program_implementation_status ADD CONSTRAINT uq_program_implementation_status_program_id UNIQUE (program_id)",
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS code_review_results (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    target_type VARCHAR(50) NOT NULL,
                    target_ref VARCHAR(255),
                    status VARCHAR(50) NOT NULL DEFAULT 'completed',
                    summary TEXT,
                    commit_analysis JSONB,
                    bug_findings JSONB,
                    refactoring_suggestions JSONB,
                    raw_response JSONB,
                    started_at TIMESTAMP WITH TIME ZONE,
                    finished_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
                """
            )
        )
        for statement in CODE_REVIEW_COLUMN_UPGRADES:
            connection.execute(text(statement))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS risk_findings (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
                    risk_type VARCHAR(100) NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    evidence JSONB,
                    detected_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    resolved_yn VARCHAR(1) NOT NULL DEFAULT 'N',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
                """
            )
        )
        for statement in RISK_FINDING_COLUMN_UPGRADES:
            connection.execute(text(statement))
        for statement in ANALYSIS_RUN_COLUMN_UPGRADES:
            connection.execute(text(statement))
        connection.execute(text("UPDATE commit_files SET git_commit_id = commit_id WHERE git_commit_id IS NULL"))
        add_constraint_if_missing(
            connection,
            "git_commits",
            "uq_git_commits_commit_hash",
            "ALTER TABLE git_commits ADD CONSTRAINT uq_git_commits_commit_hash UNIQUE (commit_hash)",
        )
        add_constraint_if_missing(
            connection,
            "git_commits",
            "uq_git_commits_project_hash",
            "ALTER TABLE git_commits ADD CONSTRAINT uq_git_commits_project_hash UNIQUE (project_id, commit_hash)",
        )
        add_constraint_if_missing(
            connection,
            "commit_files",
            "fk_commit_files_git_commit_id",
            """
            ALTER TABLE commit_files
            ADD CONSTRAINT fk_commit_files_git_commit_id
            FOREIGN KEY (git_commit_id)
            REFERENCES git_commits(id)
            ON DELETE CASCADE
            """,
        )
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint c
                        JOIN pg_class t ON c.conrelid = t.oid
                        JOIN pg_class ft ON c.confrelid = ft.oid
                        WHERE c.contype = 'f'
                          AND t.relname = 'programs'
                          AND ft.relname = 'developers'
                          AND c.conkey = ARRAY[
                              (
                                  SELECT attnum
                                  FROM pg_attribute
                                  WHERE attrelid = t.oid
                                    AND attname = 'developer_id'
                              )
                          ]::smallint[]
                    ) THEN
                        ALTER TABLE programs
                        ADD CONSTRAINT fk_programs_developer_id
                        FOREIGN KEY (developer_id)
                        REFERENCES developers(developer_id)
                        ON DELETE SET NULL;
                    END IF;
                END $$;
                """
            )
        )


def init_db() -> None:
    # pgvector extension must exist before tables with Vector columns are created.
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    upgrade_existing_schema()


if __name__ == "__main__":
    init_db()
    print("Database tables initialized.")

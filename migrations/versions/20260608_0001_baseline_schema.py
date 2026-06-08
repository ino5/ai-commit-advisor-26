"""baseline schema

Revision ID: 20260608_0001
Revises:
Create Date: 2026-06-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from src.utils.config import settings


revision: str = "20260608_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("git_repo_path", sa.Text()),
        sa.Column("last_synced_commit_hash", sa.String(length=64)),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "developers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("developer_key", sa.String(length=255), nullable=False),
        sa.Column("developer_id", sa.String(length=255), nullable=False),
        sa.Column("developer_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("role", sa.String(length=255)),
        sa.Column("skills", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("developer_id", name="uq_developers_developer_id"),
        sa.UniqueConstraint("developer_key", name="uq_developers_developer_key"),
    )

    op.create_table(
        "programs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", sa.String(length=255)),
        sa.Column("program_name", sa.String(length=255), nullable=False),
        sa.Column("screen_name", sa.String(length=255)),
        sa.Column("module", sa.String(length=255)),
        sa.Column("description", sa.Text()),
        sa.Column("developer", sa.String(length=255)),
        sa.Column("developer_id", sa.String(length=255), sa.ForeignKey("developers.developer_id", ondelete="SET NULL")),
        sa.Column("planned_start_date", sa.Date()),
        sa.Column("planned_end_date", sa.Date()),
        sa.Column("actual_start_date", sa.Date()),
        sa.Column("actual_end_date", sa.Date()),
        sa.Column("progress_rate", sa.Float()),
        sa.Column("status", sa.String(length=100)),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "git_commits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commit_hash", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("author", sa.String(length=255)),
        sa.Column("author_name", sa.String(length=255)),
        sa.Column("author_email", sa.String(length=255)),
        sa.Column("committed_at", sa.DateTime(timezone=True)),
        sa.Column("is_merge_commit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("mapping_analyzed_at", sa.DateTime(timezone=True)),
        sa.Column("mapping_analysis_status", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("commit_hash", name="uq_git_commits_commit_hash"),
        sa.UniqueConstraint("project_id", "commit_hash", name="uq_git_commits_project_hash"),
    )

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("analysis_type", sa.String(length=100)),
        sa.Column("total_count", sa.Integer()),
        sa.Column("processed_count", sa.Integer()),
        sa.Column("failed_count", sa.Integer()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("summary", sa.Text()),
        sa.Column("parameters", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "commit_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("commit_id", sa.Integer(), sa.ForeignKey("git_commits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("git_commit_id", sa.Integer(), sa.ForeignKey("git_commits.id", ondelete="CASCADE")),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("change_type", sa.String(length=50)),
        sa.Column("diff_text", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "program_commit_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commit_id", sa.Integer(), sa.ForeignKey("git_commits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id", ondelete="SET NULL")),
        sa.Column("relevance_score", sa.Float()),
        sa.Column("is_related", sa.Boolean()),
        sa.Column("implementation_status", sa.String(length=100)),
        sa.Column("reason", sa.Text()),
        sa.Column("raw_response", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("program_id", "commit_id", name="uq_program_commit_mapping"),
    )

    op.create_table(
        "program_implementation_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("completed_features", postgresql.JSONB()),
        sa.Column("incomplete_features", postgresql.JSONB()),
        sa.Column("evidence_commits", postgresql.JSONB()),
        sa.Column("commit_hash_signature", sa.String(length=64)),
        sa.Column("analyzed_at", sa.DateTime(timezone=True)),
        sa.Column("raw_response", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("program_id", name="uq_program_implementation_status_program_id"),
    )

    op.create_table(
        "code_review_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_ref", sa.String(length=255)),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("summary", sa.Text()),
        sa.Column("commit_analysis", postgresql.JSONB()),
        sa.Column("bug_findings", postgresql.JSONB()),
        sa.Column("refactoring_suggestions", postgresql.JSONB()),
        sa.Column("raw_response", postgresql.JSONB()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "risk_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_type", sa.String(length=100), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("evidence", postgresql.JSONB()),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_yn", sa.String(length=1), nullable=False, server_default="N"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_id", sa.String(length=255)),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "vector_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("embedding_model", sa.String(length=255)),
        sa.Column("embedding", Vector(settings.pgvector_dimension)),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("vector_items")
    op.drop_table("document_chunks")
    op.drop_table("risk_findings")
    op.drop_table("code_review_results")
    op.drop_table("program_implementation_status")
    op.drop_table("program_commit_mappings")
    op.drop_table("commit_files")
    op.drop_table("analysis_runs")
    op.drop_table("git_commits")
    op.drop_table("programs")
    op.drop_table("developers")
    op.drop_table("projects")

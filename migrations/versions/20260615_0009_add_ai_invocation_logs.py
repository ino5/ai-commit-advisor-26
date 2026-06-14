"""add ai invocation logs

Revision ID: 20260615_0009
Revises: 20260615_0008
Create Date: 2026-06-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260615_0009"
down_revision: Union[str, None] = "20260615_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_invocation_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("feature", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255)),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("mode", sa.String(length=100)),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("validation_status", sa.String(length=100)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("prompt_length", sa.Integer()),
        sa.Column("response_length", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_ai_invocation_logs_project_feature_created",
        "ai_invocation_logs",
        ["project_id", "feature", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_invocation_logs_project_feature_created", table_name="ai_invocation_logs")
    op.drop_table("ai_invocation_logs")

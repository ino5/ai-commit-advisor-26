"""add pl briefing history

Revision ID: 20260615_0008
Revises: 20260614_0007
Create Date: 2026-06-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260615_0008"
down_revision: Union[str, None] = "20260614_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pl_briefing_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255)),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("priority_items", postgresql.JSONB()),
        sa.Column("meeting_questions", postgresql.JSONB()),
        sa.Column("next_actions", postgresql.JSONB()),
        sa.Column("rendered_text", sa.Text(), nullable=False),
        sa.Column("evidence_payload", postgresql.JSONB()),
        sa.Column("raw_response", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_pl_briefing_history_project_generated",
        "pl_briefing_history",
        ["project_id", "generated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_pl_briefing_history_project_generated", table_name="pl_briefing_history")
    op.drop_table("pl_briefing_history")

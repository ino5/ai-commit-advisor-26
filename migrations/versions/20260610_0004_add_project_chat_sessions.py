"""add project chat sessions

Revision ID: 20260610_0004
Revises: 20260609_0003
Create Date: 2026-06-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260610_0004"
down_revision: Union[str, None] = "20260609_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255)),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_project_chat_sessions_project_id", "project_chat_sessions", ["project_id"])
    op.create_index("ix_project_chat_sessions_last_message_at", "project_chat_sessions", ["last_message_at"])

    op.create_table(
        "project_chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("project_chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_index", sa.Integer(), nullable=False),
        sa.Column("sources", postgresql.JSONB()),
        sa.Column("expanded_queries", postgresql.JSONB()),
        sa.Column("matched_terms", postgresql.JSONB()),
        sa.Column("excluded_count", sa.Integer()),
        sa.Column("used_source_count", sa.Integer()),
        sa.Column("insufficient_evidence", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "message_index", name="uq_project_chat_messages_session_index"),
    )
    op.create_index("ix_project_chat_messages_session_id", "project_chat_messages", ["session_id"])
    op.create_index("ix_project_chat_messages_role", "project_chat_messages", ["role"])


def downgrade() -> None:
    op.drop_index("ix_project_chat_messages_role", table_name="project_chat_messages")
    op.drop_index("ix_project_chat_messages_session_id", table_name="project_chat_messages")
    op.drop_table("project_chat_messages")
    op.drop_index("ix_project_chat_sessions_last_message_at", table_name="project_chat_sessions")
    op.drop_index("ix_project_chat_sessions_project_id", table_name="project_chat_sessions")
    op.drop_table("project_chat_sessions")

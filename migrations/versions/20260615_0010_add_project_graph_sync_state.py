"""add project graph sync state

Revision ID: 20260615_0010
Revises: 20260615_0009
Create Date: 2026-06-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260615_0010"
down_revision: Union[str, None] = "20260615_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_graph_sync_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repo_head_hash", sa.String(length=64)),
        sa.Column("db_sync_head_hash", sa.String(length=64)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
        sa.Column("sync_mode", sa.String(length=50)),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("node_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("edge_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_commit_db_id", sa.Integer()),
        sa.Column("last_mapping_updated_at", sa.DateTime(timezone=True)),
        sa.Column("error_summary", sa.Text()),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", name="uq_project_graph_sync_state_project_id"),
    )
    op.create_index(
        "ix_project_graph_sync_state_project_status",
        "project_graph_sync_state",
        ["project_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_project_graph_sync_state_project_status", table_name="project_graph_sync_state")
    op.drop_table("project_graph_sync_state")

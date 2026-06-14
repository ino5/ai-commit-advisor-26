"""add resource metric snapshots

Revision ID: 20260614_0006
Revises: 20260614_0005
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260614_0006"
down_revision: Union[str, None] = "20260614_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resource_metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_label", sa.String(length=255)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("unresolved_risk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_risk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forecasted_delay_program_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_code_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_review_hours_saved", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimated_extra_mm_avoidance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_workload_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_difficulty_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("developer_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("program_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_summary", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_resource_metric_snapshots_project_captured",
        "resource_metric_snapshots",
        ["project_id", "captured_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_resource_metric_snapshots_project_captured", table_name="resource_metric_snapshots")
    op.drop_table("resource_metric_snapshots")

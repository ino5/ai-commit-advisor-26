"""add project developers

Revision ID: 20260614_0005
Revises: 20260610_0004
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260614_0005"
down_revision: Union[str, None] = "20260610_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_developers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "developer_id",
            sa.String(length=255),
            sa.ForeignKey("developers.developer_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="manual"),
        sa.Column("project_role", sa.String(length=255)),
        sa.Column("active_yn", sa.String(length=1), nullable=False, server_default="Y"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "developer_id", name="uq_project_developers_project_developer"),
    )
    op.execute(
        """
        INSERT INTO project_developers (project_id, developer_id, source, active_yn, created_at, updated_at)
        SELECT DISTINCT programs.project_id, programs.developer_id, 'manual', 'Y', now(), now()
        FROM programs
        JOIN developers ON developers.developer_id = programs.developer_id
        WHERE programs.project_id IS NOT NULL
          AND programs.developer_id IS NOT NULL
        ON CONFLICT (project_id, developer_id) DO NOTHING
        """
    )
    op.create_index("ix_project_developers_project_id", "project_developers", ["project_id"])
    op.create_index("ix_project_developers_developer_id", "project_developers", ["developer_id"])


def downgrade() -> None:
    op.drop_index("ix_project_developers_developer_id", table_name="project_developers")
    op.drop_index("ix_project_developers_project_id", table_name="project_developers")
    op.drop_table("project_developers")

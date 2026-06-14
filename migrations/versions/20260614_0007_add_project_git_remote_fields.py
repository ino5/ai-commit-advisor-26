"""Add project Git remote fields.

Revision ID: 20260614_0007
Revises: 20260614_0006
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260614_0007"
down_revision = "20260614_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("git_remote_url", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("git_branch", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "git_branch")
    op.drop_column("projects", "git_remote_url")

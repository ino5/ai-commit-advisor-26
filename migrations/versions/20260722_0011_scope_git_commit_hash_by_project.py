"""Scope Git commit hash uniqueness by project.

Revision ID: 20260722_0011
Revises: 20260615_0010
Create Date: 2026-07-22
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260722_0011"
down_revision: Union[str, None] = "20260615_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_git_commits_commit_hash", "git_commits", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_git_commits_commit_hash", "git_commits", ["commit_hash"])

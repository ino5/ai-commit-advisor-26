"""add mapping feedback columns

Revision ID: 20260608_0002
Revises: 20260608_0001
Create Date: 2026-06-08
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260608_0002"
down_revision: Union[str, None] = "20260608_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_is_related BOOLEAN")
    op.execute("ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_relevance_score DOUBLE PRECISION")
    op.execute("ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_implementation_status VARCHAR(100)")
    op.execute("ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_reason TEXT")
    op.execute("ALTER TABLE program_commit_mappings ADD COLUMN IF NOT EXISTS feedback_updated_at TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    op.execute("ALTER TABLE program_commit_mappings DROP COLUMN IF EXISTS feedback_updated_at")
    op.execute("ALTER TABLE program_commit_mappings DROP COLUMN IF EXISTS feedback_reason")
    op.execute("ALTER TABLE program_commit_mappings DROP COLUMN IF EXISTS feedback_implementation_status")
    op.execute("ALTER TABLE program_commit_mappings DROP COLUMN IF EXISTS feedback_relevance_score")
    op.execute("ALTER TABLE program_commit_mappings DROP COLUMN IF EXISTS feedback_is_related")

"""add standard terms

Revision ID: 20260609_0003
Revises: 20260608_0002
Create Date: 2026-06-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260609_0003"
down_revision: Union[str, None] = "20260608_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "standard_terms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("term_type", sa.String(length=50)),
        sa.Column("korean_term", sa.String(length=255), nullable=False),
        sa.Column("english_term", sa.String(length=255), nullable=False),
        sa.Column("abbreviation", sa.String(length=255)),
        sa.Column("description", sa.Text()),
        sa.Column("derived_keywords", postgresql.JSONB()),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "korean_term", "english_term", name="uq_standard_terms_project_terms"),
    )
    op.create_index("ix_standard_terms_project_id", "standard_terms", ["project_id"])
    op.create_index("ix_standard_terms_korean_term", "standard_terms", ["korean_term"])


def downgrade() -> None:
    op.drop_index("ix_standard_terms_korean_term", table_name="standard_terms")
    op.drop_index("ix_standard_terms_project_id", table_name="standard_terms")
    op.drop_table("standard_terms")

"""add document processing versions

Revision ID: 8a1d2e4c7f21
Revises: 6f5b0f0d9c12
Create Date: 2026-06-13 12:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8a1d2e4c7f21"
down_revision = "6f5b0f0d9c12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("result_documents", sa.Column("contract_version_used", sa.String(length=50), nullable=True))
    op.add_column("result_documents", sa.Column("normalization_version_used", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("result_documents", "normalization_version_used")
    op.drop_column("result_documents", "contract_version_used")

"""add monitoring failure audit fields

Revision ID: 6f5b0f0d9c12
Revises: 2b4d0d1f9a32
Create Date: 2026-06-13 11:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6f5b0f0d9c12"
down_revision = "2b4d0d1f9a32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("monitoring_jobs", sa.Column("failure_stage", sa.String(length=100), nullable=True))
    op.add_column("monitoring_jobs", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column("publication_signals", sa.Column("failure_stage", sa.String(length=100), nullable=True))
    op.add_column("publication_signals", sa.Column("failure_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("publication_signals", "failure_reason")
    op.drop_column("publication_signals", "failure_stage")
    op.drop_column("monitoring_jobs", "failure_reason")
    op.drop_column("monitoring_jobs", "failure_stage")

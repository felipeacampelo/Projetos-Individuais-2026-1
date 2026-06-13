"""add reprocessing execution audit fields

Revision ID: b91e4f3a1d77
Revises: 8a1d2e4c7f21
Create Date: 2026-06-13 13:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b91e4f3a1d77"
down_revision = "8a1d2e4c7f21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reprocessing_requests", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reprocessing_requests", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reprocessing_requests", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reprocessing_requests", "error_message")
    op.drop_column("reprocessing_requests", "finished_at")
    op.drop_column("reprocessing_requests", "started_at")

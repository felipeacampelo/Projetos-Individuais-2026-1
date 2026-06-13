"""add document versioning

Revision ID: 2b4d0d1f9a32
Revises: 91577f08a2a8
Create Date: 2026-06-13 12:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "2b4d0d1f9a32"
down_revision = "91577f08a2a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_version_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("reference_year", sa.Integer(), nullable=False),
        sa.Column("reference_quarter", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "reference_year",
            "reference_quarter",
            name="uq_document_version_group_company_period",
        ),
    )
    op.create_table(
        "document_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version_group_id", sa.Integer(), nullable=False),
        sa.Column("result_document_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["result_document_id"], ["result_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_group_id"], ["document_version_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("result_document_id", name="uq_document_version_result_document"),
        sa.UniqueConstraint("version_group_id", "version_number", name="uq_document_version_group_number"),
    )


def downgrade() -> None:
    op.drop_table("document_versions")
    op.drop_table("document_version_groups")

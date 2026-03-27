"""add merchant nin verification fields

Revision ID: 20260327_03
Revises: 20260327_02
Create Date: 2026-03-27 23:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_03"
down_revision = "20260327_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("merchant", sa.Column("nin_status", sa.String(length=20), nullable=True))
    op.add_column("merchant", sa.Column("nin_last4", sa.String(length=4), nullable=True))
    op.add_column("merchant", sa.Column("nin_reference", sa.String(length=120), nullable=True))
    op.add_column("merchant", sa.Column("nin_verified_name", sa.String(length=150), nullable=True))
    op.add_column("merchant", sa.Column("nin_submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("merchant", sa.Column("nin_verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("merchant", "nin_verified_at")
    op.drop_column("merchant", "nin_submitted_at")
    op.drop_column("merchant", "nin_verified_name")
    op.drop_column("merchant", "nin_reference")
    op.drop_column("merchant", "nin_last4")
    op.drop_column("merchant", "nin_status")

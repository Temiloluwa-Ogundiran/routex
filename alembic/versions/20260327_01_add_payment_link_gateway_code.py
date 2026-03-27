"""add gateway_code to payment links

Revision ID: 20260327_01
Revises: 20260326_01
Create Date: 2026-03-27 22:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_01"
down_revision = "20260326_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payment_links",
        sa.Column("gateway_code", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payment_links", "gateway_code")

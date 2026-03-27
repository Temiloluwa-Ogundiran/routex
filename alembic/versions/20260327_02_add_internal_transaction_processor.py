"""add internal transaction processor enum

Revision ID: 20260327_02
Revises: 20260327_01
Create Date: 2026-03-27 22:55:00.000000
"""

from alembic import op


revision = "20260327_02"
down_revision = "20260327_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TYPE transactionprocessor
        ADD VALUE IF NOT EXISTS 'INTERNAL'
        """
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass

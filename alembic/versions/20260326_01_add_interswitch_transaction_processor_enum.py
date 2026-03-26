"""add interswitch to transaction processor enum

Revision ID: 20260326_01
Revises: 20260325_02
Create Date: 2026-03-26 10:00:00.000000
"""

from alembic import op


revision = "20260326_01"
down_revision = "20260325_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TYPE transactionprocessor
        ADD VALUE IF NOT EXISTS 'INTERSWITCH'
        """
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass

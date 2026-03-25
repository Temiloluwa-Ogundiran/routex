"""add routing tables

Revision ID: 20260325_01
Revises: 1b54993c47bd
Create Date: 2026-03-25 02:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260325_01"
down_revision: Union[str, None] = "1b54993c47bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("processor", sa.Column("name", sa.String(length=50), nullable=True))
    op.add_column(
        "processor",
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "processor",
        sa.Column(
            "supports_collections",
            sa.Boolean(),
            nullable=True,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "processor",
        sa.Column(
            "supports_payouts",
            sa.Boolean(),
            nullable=True,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "processor",
        sa.Column(
            "priority_weight",
            sa.Float(),
            nullable=True,
            server_default="1.0",
        ),
    )
    op.add_column("transaction", sa.Column("selected_gateway", sa.String(length=20), nullable=True))

    op.create_table(
        "routing_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("gateway_code", sa.String(length=10), nullable=False),
        sa.Column("operation", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("request_hash", sa.String(length=128), nullable=True),
        sa.Column("gateway_reference", sa.String(length=100), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("score_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["gateway_code"], ["processor.code"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transaction.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id", "attempt_no", name="uq_routing_attempt_txn_attempt"),
    )
    op.create_table(
        "gateway_health_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("gateway_code", sa.String(length=10), nullable=False),
        sa.Column("success_rate_5m", sa.Float(), nullable=False, server_default="0"),
        sa.Column("success_rate_1h", sa.Float(), nullable=False, server_default="0"),
        sa.Column("timeout_rate_5m", sa.Float(), nullable=False, server_default="0"),
        sa.Column("p95_latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("circuit_state", sa.String(length=20), nullable=False, server_default="closed"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["gateway_code"], ["processor.code"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "routing_decision_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("decision_id", sa.String(length=50), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("selected_gateway", sa.String(length=10), nullable=False),
        sa.Column("eligible_gateways", sa.JSON(), nullable=True),
        sa.Column("rejected_gateways", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("score_breakdown", sa.JSON(), nullable=True),
        sa.Column("fallback_order", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["selected_gateway"], ["processor.code"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transaction.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_id"),
    )


def downgrade() -> None:
    op.drop_table("routing_decision_audits")
    op.drop_table("gateway_health_snapshots")
    op.drop_table("routing_attempts")
    op.drop_column("transaction", "selected_gateway")
    op.drop_column("processor", "priority_weight")
    op.drop_column("processor", "supports_payouts")
    op.drop_column("processor", "supports_collections")
    op.drop_column("processor", "is_active")
    op.drop_column("processor", "name")

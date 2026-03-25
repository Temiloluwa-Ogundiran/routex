from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.Processor import Processor
from database.models.RoutingAttempt import RoutingAttempt
from database.models.RoutingDecisionAudit import RoutingDecisionAudit
from database.models.Transaction import Transaction
import services.gatewayHealthService as gatewayHealthService
import services.routingService as routingService


async def get_gateway_health_summary(session: AsyncSession) -> list[dict]:
    await routingService.ensure_processor_catalog(session)

    processors_result = await session.execute(
        select(Processor).order_by(Processor.priority_weight.desc(), Processor.code.asc())
    )
    processors = processors_result.scalars().all()
    snapshots = await gatewayHealthService.get_gateway_snapshots(session)

    return [
        {
            "gateway_code": processor.code,
            "gateway_name": processor.name or processor.code.upper(),
            "is_active": bool(processor.is_active),
            "supports_collections": bool(processor.supports_collections),
            "supports_payouts": bool(processor.supports_payouts),
            "priority_weight": float(processor.priority_weight or 0.0),
            "success_rate_5m": float(getattr(snapshots.get(processor.code), "success_rate_5m", 0.0) or 0.0),
            "success_rate_1h": float(getattr(snapshots.get(processor.code), "success_rate_1h", 0.0) or 0.0),
            "timeout_rate_5m": float(getattr(snapshots.get(processor.code), "timeout_rate_5m", 0.0) or 0.0),
            "p95_latency_ms": float(getattr(snapshots.get(processor.code), "p95_latency_ms", 0.0) or 0.0),
            "circuit_state": getattr(snapshots.get(processor.code), "circuit_state", "unknown"),
            "last_checked_at": getattr(snapshots.get(processor.code), "last_checked_at", None),
        }
        for processor in processors
    ]


async def get_recent_routed_transactions(
    session: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.selected_gateway.is_not(None))
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()

    return [
        {
            "reference": transaction.reference,
            "selected_gateway": transaction.selected_gateway,
            "status": transaction.status,
            "amount": float(transaction.amount or 0.0),
            "currency": transaction.currency,
            "created_at": transaction.created_at,
        }
        for transaction in transactions
    ]


async def get_recent_failovers(
    session: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    failover_count = func.count(RoutingAttempt.id).label("attempt_count")
    result = await session.execute(
        select(Transaction, RoutingDecisionAudit, failover_count)
        .join(RoutingAttempt, RoutingAttempt.transaction_id == Transaction.id)
        .join(RoutingDecisionAudit, RoutingDecisionAudit.transaction_id == Transaction.id)
        .group_by(Transaction.id, RoutingDecisionAudit.id)
        .having(func.count(RoutingAttempt.id) > 1)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )

    failovers = []
    for transaction, decision, attempt_count in result.all():
        failovers.append(
            {
                "reference": transaction.reference,
                "selected_gateway": transaction.selected_gateway,
                "attempt_count": int(attempt_count),
                "fallback_order": decision.fallback_order or [],
                "created_at": transaction.created_at,
            }
        )

    return failovers


async def get_dashboard_summary(session: AsyncSession) -> dict:
    gateway_health = await get_gateway_health_summary(session)
    recent_transactions = await get_recent_routed_transactions(session)
    recent_failovers = await get_recent_failovers(session)

    return {
        "summary": {
            "total_gateways": len(gateway_health),
            "active_gateways": sum(1 for gateway in gateway_health if gateway["is_active"]),
            "recent_failover_count": len(recent_failovers),
            "routed_transaction_count": len(recent_transactions),
        },
        "gateway_health": gateway_health,
        "recent_transactions": recent_transactions,
        "recent_failovers": recent_failovers,
    }


async def get_transaction_detail(
    session: AsyncSession,
    reference: str,
    created_at: datetime | None = None,
) -> dict | None:
    query = (
        select(Transaction)
        .options(selectinload(Transaction.merchant), selectinload(Transaction.customer))
        .where(Transaction.reference == reference)
    )
    if created_at is not None:
        exact_result = await session.execute(
            query.where(Transaction.created_at == created_at).order_by(Transaction.id.desc())
        )
        transaction = exact_result.scalars().first()
        if not transaction:
            return None
        return await _build_transaction_detail_payload(session=session, transaction=transaction)

    result = await session.execute(query.order_by(Transaction.created_at.desc(), Transaction.id.desc()))
    transaction = result.scalars().first()
    if not transaction:
        return None

    return await _build_transaction_detail_payload(session=session, transaction=transaction)


async def _build_transaction_detail_payload(session: AsyncSession, transaction: Transaction) -> dict:

    attempts_result = await session.execute(
        select(RoutingAttempt)
        .where(RoutingAttempt.transaction_id == transaction.id)
        .order_by(RoutingAttempt.attempt_no.asc())
    )
    attempts = attempts_result.scalars().all()

    decision_result = await session.execute(
        select(RoutingDecisionAudit)
        .where(RoutingDecisionAudit.transaction_id == transaction.id)
        .order_by(RoutingDecisionAudit.created_at.desc())
    )
    decision = decision_result.scalars().first()

    webhook_trace = transaction.details if isinstance(transaction.details, dict) else {}

    failover_count = 0
    recovered_after_failover = False
    previous_gateway = None
    switch_seen = False
    for attempt in attempts:
        current_gateway = attempt.gateway_code
        if previous_gateway is not None and current_gateway != previous_gateway:
            failover_count += 1
            switch_seen = True
        if switch_seen and (attempt.status or "").lower() == "success":
            recovered_after_failover = True
        previous_gateway = current_gateway

    return {
        "transaction": {
            "reference": transaction.reference,
            "gateway_reference": transaction.processor_reference,
            "type": transaction.type,
            "selected_gateway": transaction.selected_gateway,
            "status": transaction.status,
            "amount": float(transaction.amount or 0.0),
            "currency": transaction.currency,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            "merchant_name": getattr(transaction.merchant, "name", None),
            "customer_email": getattr(transaction.customer, "email", None),
        },
        "routing_decision": {
            "selected_gateway": getattr(decision, "selected_gateway", transaction.selected_gateway),
            "reason": getattr(decision, "reason", None),
            "fallback_order": list(getattr(decision, "fallback_order", []) or []),
            "eligible_gateways": list(getattr(decision, "eligible_gateways", []) or []),
            "rejected_gateways": dict(getattr(decision, "rejected_gateways", {}) or {}),
            "score_breakdown": dict(getattr(decision, "score_breakdown", {}) or {}),
        },
        "attempts": [
            {
                "attempt_no": attempt.attempt_no,
                "gateway": attempt.gateway_code,
                "status": attempt.status,
                "gateway_reference": attempt.gateway_reference,
                "latency_ms": attempt.latency_ms,
                "error_code": attempt.error_code,
                "error_message": attempt.error_message,
                "created_at": attempt.created_at,
            }
            for attempt in attempts
        ],
        "failover_summary": {
            "did_failover": failover_count > 0,
            "failover_count": failover_count,
            "recovered_after_failover": recovered_after_failover,
        },
        "webhook_trace": {
            "last_event": webhook_trace.get("last_webhook_event"),
            "last_status": webhook_trace.get("last_webhook_status"),
            "last_gateway": webhook_trace.get("last_webhook_gateway"),
            "is_reconciling": bool(
                webhook_trace.get("reconciliation_required", webhook_trace.get("is_reconciling", False))
            ),
        },
    }

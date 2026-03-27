from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.Processor import Processor
from database.models.RoutingAttempt import RoutingAttempt
from database.models.RoutingDecisionAudit import RoutingDecisionAudit
from database.models.Transaction import Transaction
from services import gatewayHealthService
from services import routerRuleService


@dataclass(slots=True)
class RoutingDecision:
    selected_gateway: str
    ranked_gateways: list[str]
    score_breakdown: dict[str, float]
    rejected_gateways: dict[str, str]
    selection_reason: str


DEFAULT_PROCESSOR_CATALOG = {
    "fltw": {
        "name": "Flutterwave",
        "charge": 1.4,
        "markup": 0.0,
        "is_active": True,
        "supports_collections": True,
        "supports_payouts": False,
        "priority_weight": 1.0,
    },
    "pstk": {
        "name": "Paystack",
        "charge": 1.5,
        "markup": 0.0,
        "is_active": True,
        "supports_collections": True,
        "supports_payouts": False,
        "priority_weight": 1.0,
    },
    "kora": {
        "name": "Korapay",
        "charge": 1.3,
        "markup": 0.0,
        "is_active": True,
        "supports_collections": True,
        "supports_payouts": True,
        "priority_weight": 1.0,
    },
    "isw": {
        "name": "Interswitch",
        "charge": 1.6,
        "markup": 0.0,
        "is_active": True,
        "supports_collections": True,
        "supports_payouts": False,
        "priority_weight": 1.0,
    },
}


def _validate_routing_request(currency: str, operation: str) -> None:
    if currency != "NGN":
        raise ValueError("Routing service currently supports NGN only.")
    if operation not in {"collection", "payout"}:
        raise ValueError(f"Unsupported routing operation: {operation}")


def _supports_operation(processor: Processor, operation: str) -> bool:
    if operation == "collection":
        return bool(processor.supports_collections)
    if operation == "payout":
        return bool(processor.supports_payouts)
    return False


def _get_rejection_reason(
    processor: Processor,
    operation: str,
    snapshot,
    rule_policy: routerRuleService.EffectiveRoutingRulePolicy | None = None,
) -> str | None:
    if not processor.is_active:
        return "processor_inactive"
    if not _supports_operation(processor, operation):
        return f"unsupported_{operation}"
    if not gatewayHealthService.is_gateway_available(snapshot):
        return "gateway_unavailable"
    if rule_policy and processor.code in rule_policy.deny_gateways:
        return "rule_denied"
    if (
        rule_policy
        and rule_policy.allow_gateways is not None
        and processor.code not in rule_policy.allow_gateways
    ):
        return "not_in_rule_allowlist"
    return None


def _score_processor(processor: Processor, snapshot) -> float:
    recent_success_score = snapshot.success_rate_5m if snapshot else 80.0
    stability_score = snapshot.success_rate_1h if snapshot else 80.0
    timeout_rate = snapshot.timeout_rate_5m if snapshot else 0.0
    latency_score = gatewayHealthService.compute_latency_score(
        snapshot.p95_latency_ms if snapshot else None,
    )
    availability_score = 100.0 if gatewayHealthService.is_gateway_available(snapshot) else 0.0

    return round(
        (0.45 * recent_success_score)
        + (0.20 * stability_score)
        + (0.20 * latency_score)
        + (0.10 * availability_score)
        + (0.05 * max(0.0, 100.0 - (timeout_rate * 10.0))),
        2,
    )


def _requested_gateway_error(gateway_code: str, rejection_reason: str, operation: str) -> str:
    if rejection_reason == "processor_inactive":
        return f"Requested gateway '{gateway_code}' is currently inactive."
    if rejection_reason == "gateway_unavailable":
        return f"Requested gateway '{gateway_code}' is currently unavailable."
    if rejection_reason == "rule_denied":
        return f"Requested gateway '{gateway_code}' is blocked by routing rules."
    if rejection_reason == "not_in_rule_allowlist":
        return f"Requested gateway '{gateway_code}' is not allowed by the active routing rules."
    if rejection_reason == f"unsupported_{operation}":
        return f"Requested gateway '{gateway_code}' does not support {operation}s."
    return f"Requested gateway '{gateway_code}' is not eligible for this request."


async def ensure_processor_catalog(session: AsyncSession) -> None:
    result = await session.execute(select(Processor))
    existing_processors = {
        processor.code: processor
        for processor in result.scalars().all()
    }

    changed = False
    for code, defaults in DEFAULT_PROCESSOR_CATALOG.items():
        processor = existing_processors.get(code)
        if processor is None:
            session.add(Processor(code=code, **defaults))
            changed = True
            continue

        for field, value in defaults.items():
            current_value = getattr(processor, field)
            if field == "priority_weight" and float(current_value or 0.0) != float(value):
                setattr(processor, field, value)
                changed = True
                continue

            if current_value is None:
                setattr(processor, field, value)
                changed = True

    if changed:
        await session.commit()


async def build_routing_decision(
    session: AsyncSession,
    operation: str,
    currency: str,
    amount: float,
    merchant_id: str,
    channel: str | None = None,
) -> RoutingDecision:
    del merchant_id
    _validate_routing_request(currency, operation)

    await ensure_processor_catalog(session)
    result = await session.execute(select(Processor))
    processors = result.scalars().all()
    snapshots = await gatewayHealthService.get_gateway_snapshots(session)
    rule_policy = await routerRuleService.resolve_routing_rule_policy(
        session,
        operation=operation,
        amount=amount,
        channel=channel,
    )

    score_breakdown: dict[str, float] = {}
    rejected_gateways: dict[str, str] = {}

    for processor in processors:
        snapshot = snapshots.get(processor.code)
        rejection_reason = _get_rejection_reason(
            processor,
            operation,
            snapshot,
            rule_policy=rule_policy,
        )
        if rejection_reason:
            rejected_gateways[processor.code] = rejection_reason
            continue

        score_breakdown[processor.code] = _score_processor(processor, snapshot)

    if not score_breakdown:
        if rule_policy.matched_rule_count:
            raise ValueError("No eligible gateways available after applying routing rules.")
        raise ValueError("No eligible gateways available for routing.")

    ranked_gateways = sorted(
        score_breakdown,
        key=lambda gateway_code: score_breakdown[gateway_code],
        reverse=True,
    )
    forced_priority_order = [
        gateway_code
        for gateway_code in rule_policy.force_priority_order
        if gateway_code in score_breakdown
    ]
    if forced_priority_order:
        remaining_gateways = [
            gateway_code
            for gateway_code in ranked_gateways
            if gateway_code not in forced_priority_order
        ]
        ranked_gateways = forced_priority_order + remaining_gateways

    selection_reason = "highest score among eligible gateways"
    if rule_policy.matched_rule_count and forced_priority_order:
        selection_reason = "forced priority order applied by global routing rule"
    elif rule_policy.matched_rule_count:
        selection_reason = (
            f"highest score among eligible gateways after applying "
            f"{rule_policy.matched_rule_count} global rules"
        )

    return RoutingDecision(
        selected_gateway=ranked_gateways[0],
        ranked_gateways=ranked_gateways,
        score_breakdown=score_breakdown,
        rejected_gateways=rejected_gateways,
        selection_reason=selection_reason,
    )


async def build_manual_routing_decision(
    session: AsyncSession,
    operation: str,
    currency: str,
    amount: float,
    merchant_id: str,
    gateway_code: str,
    channel: str | None = None,
) -> RoutingDecision:
    del merchant_id
    _validate_routing_request(currency, operation)

    requested_gateway = gateway_code.strip().lower()
    await ensure_processor_catalog(session)
    result = await session.execute(select(Processor))
    processors = result.scalars().all()
    processor_lookup = {processor.code: processor for processor in processors}
    requested_processor = processor_lookup.get(requested_gateway)

    if requested_processor is None:
        raise ValueError(f"Requested gateway '{requested_gateway}' is not supported.")

    snapshots = await gatewayHealthService.get_gateway_snapshots(session)
    rule_policy = await routerRuleService.resolve_routing_rule_policy(
        session,
        operation=operation,
        amount=amount,
        channel=channel,
    )

    score_breakdown: dict[str, float] = {}
    rejected_gateways: dict[str, str] = {}

    for processor in processors:
        snapshot = snapshots.get(processor.code)
        rejection_reason = _get_rejection_reason(
            processor,
            operation,
            snapshot,
            rule_policy=rule_policy,
        )
        if rejection_reason:
            rejected_gateways[processor.code] = rejection_reason
            continue

        score_breakdown[processor.code] = _score_processor(processor, snapshot)

    requested_rejection = rejected_gateways.get(requested_gateway)
    if requested_rejection:
        raise ValueError(
            _requested_gateway_error(requested_gateway, requested_rejection, operation),
        )

    ranked_remaining_gateways = sorted(
        [gateway for gateway in score_breakdown if gateway != requested_gateway],
        key=lambda gateway_code: score_breakdown[gateway_code],
        reverse=True,
    )

    return RoutingDecision(
        selected_gateway=requested_gateway,
        ranked_gateways=[requested_gateway, *ranked_remaining_gateways],
        score_breakdown=score_breakdown,
        rejected_gateways=rejected_gateways,
        selection_reason="merchant selected gateway override",
    )


async def select_gateway(
    session: AsyncSession,
    operation: str,
    currency: str,
    amount: float,
    merchant_id: str,
    channel: str | None = None,
) -> tuple[str, list[str]]:
    decision = await build_routing_decision(
        session=session,
        operation=operation,
        currency=currency,
        amount=amount,
        merchant_id=merchant_id,
        channel=channel,
    )
    return decision.selected_gateway, decision.ranked_gateways


async def record_routing_result(
    session: AsyncSession,
    transaction: Transaction,
    decision: RoutingDecision,
    operation: str,
    status: str,
    gateway_reference: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> tuple[RoutingDecisionAudit, RoutingAttempt]:
    attempt_count_result = await session.execute(
        select(func.count(RoutingAttempt.id)).where(
            RoutingAttempt.transaction_id == transaction.id,
        )
    )
    attempt_no = int(attempt_count_result.scalar() or 0) + 1

    transaction.selected_gateway = decision.selected_gateway

    attempt = RoutingAttempt(
        transaction_id=transaction.id,
        attempt_no=attempt_no,
        gateway_code=decision.selected_gateway,
        operation=operation,
        status=status,
        gateway_reference=gateway_reference,
        error_code=error_code,
        error_message=error_message,
        score_snapshot=decision.score_breakdown,
    )
    audit = RoutingDecisionAudit(
        transaction_id=transaction.id,
        selected_gateway=decision.selected_gateway,
        eligible_gateways=decision.ranked_gateways,
        rejected_gateways=decision.rejected_gateways,
        reason=decision.selection_reason,
        score_breakdown=decision.score_breakdown,
        fallback_order=decision.ranked_gateways,
    )

    session.add_all([transaction, attempt, audit])
    await session.commit()
    await session.refresh(transaction)
    await session.refresh(audit)
    await session.refresh(attempt)
    return audit, attempt


def build_routing_metadata(decision_id: str | None, decision: RoutingDecision) -> dict:
    return {
        "decision_id": decision_id,
        "selection_reason": decision.selection_reason,
        "fallback_order": decision.ranked_gateways,
        "score_breakdown": decision.score_breakdown,
    }


def build_attempt_summaries(attempts: list[RoutingAttempt]) -> list[dict]:
    return [
        {
            "attempt_no": attempt.attempt_no,
            "gateway": attempt.gateway_code,
            "status": attempt.status,
            "gateway_reference": attempt.gateway_reference,
            "latency_ms": attempt.latency_ms,
        }
        for attempt in attempts
    ]

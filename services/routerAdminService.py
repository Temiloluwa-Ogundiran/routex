from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.Processor import Processor
from database.models.RoutingRule import RoutingRule
from schemas.routerAnalyticsSchema import RouterRuleCreateRequest, RouterRuleUpdateRequest
import services.routingService as routingService


VALID_ROUTING_OPERATIONS = {"collection", "payout"}


def _normalize_gateway_codes(codes: list[str] | None) -> list[str]:
    if not codes:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for code in codes:
        value = code.strip().lower()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def _normalize_channel(channel: str | None) -> str | None:
    if channel is None:
        return None
    value = channel.strip().lower()
    return value or None


def _validate_rule_values(
    *,
    operation: str | None,
    min_amount: float | None,
    max_amount: float | None,
    allow_gateways: list[str],
    deny_gateways: list[str],
) -> None:
    if operation is not None and operation not in VALID_ROUTING_OPERATIONS:
        raise ValueError("operation must be one of: collection, payout")
    if (
        min_amount is not None
        and max_amount is not None
        and min_amount > max_amount
    ):
        raise ValueError("min_amount cannot be greater than max_amount")

    overlapping_gateways = set(allow_gateways).intersection(deny_gateways)
    if overlapping_gateways:
        raise ValueError("allow_gateways and deny_gateways cannot overlap")


def serialize_routing_rule(rule: RoutingRule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "operation": rule.operation,
        "channel": rule.channel,
        "min_amount": float(rule.min_amount) if rule.min_amount is not None else None,
        "max_amount": float(rule.max_amount) if rule.max_amount is not None else None,
        "allow_gateways": list(rule.allow_gateways or []),
        "deny_gateways": list(rule.deny_gateways or []),
        "force_priority_order": list(rule.force_priority_order or []),
        "enabled": bool(rule.enabled),
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


async def update_gateway(
    session: AsyncSession,
    gateway_code: str,
    *,
    is_active: bool | None = None,
    priority_weight: float | None = None,
) -> Processor | None:
    await routingService.ensure_processor_catalog(session)

    result = await session.execute(
        select(Processor).where(Processor.code == gateway_code)
    )
    processor = result.scalar_one_or_none()
    if not processor:
        return None

    if is_active is not None:
        processor.is_active = is_active
    if priority_weight is not None or float(processor.priority_weight or 0.0) != 1.0:
        processor.priority_weight = 1.0

    session.add(processor)
    await session.commit()
    await session.refresh(processor)
    return processor


async def list_routing_rules(session: AsyncSession) -> list[RoutingRule]:
    result = await session.execute(
        select(RoutingRule).order_by(RoutingRule.updated_at.desc(), RoutingRule.id.desc())
    )
    return result.scalars().all()


async def create_routing_rule(
    session: AsyncSession,
    payload: RouterRuleCreateRequest,
) -> RoutingRule:
    allow_gateways = _normalize_gateway_codes(payload.allow_gateways)
    deny_gateways = _normalize_gateway_codes(payload.deny_gateways)
    force_priority_order = _normalize_gateway_codes(payload.force_priority_order)
    operation = payload.operation.strip().lower()
    channel = _normalize_channel(payload.channel)

    _validate_rule_values(
        operation=operation,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        allow_gateways=allow_gateways,
        deny_gateways=deny_gateways,
    )

    rule = RoutingRule(
        name=payload.name.strip(),
        operation=operation,
        channel=channel,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        allow_gateways=allow_gateways,
        deny_gateways=deny_gateways,
        force_priority_order=force_priority_order,
        enabled=payload.enabled,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def update_routing_rule(
    session: AsyncSession,
    rule_id: int,
    payload: RouterRuleUpdateRequest,
) -> RoutingRule | None:
    result = await session.execute(
        select(RoutingRule).where(RoutingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        return None

    if payload.name is not None:
        rule.name = payload.name.strip()
    if payload.operation is not None:
        rule.operation = payload.operation.strip().lower()
    if payload.channel is not None:
        rule.channel = _normalize_channel(payload.channel)
    if payload.min_amount is not None:
        rule.min_amount = payload.min_amount
    if payload.max_amount is not None:
        rule.max_amount = payload.max_amount
    if payload.allow_gateways is not None:
        rule.allow_gateways = _normalize_gateway_codes(payload.allow_gateways)
    if payload.deny_gateways is not None:
        rule.deny_gateways = _normalize_gateway_codes(payload.deny_gateways)
    if payload.force_priority_order is not None:
        rule.force_priority_order = _normalize_gateway_codes(payload.force_priority_order)
    if payload.enabled is not None:
        rule.enabled = payload.enabled

    _validate_rule_values(
        operation=rule.operation,
        min_amount=rule.min_amount,
        max_amount=rule.max_amount,
        allow_gateways=list(rule.allow_gateways or []),
        deny_gateways=list(rule.deny_gateways or []),
    )

    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule

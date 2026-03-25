from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.RoutingRule import RoutingRule


@dataclass(slots=True)
class RoutingRuleContext:
    operation: str
    amount: float
    channel: str | None = None


@dataclass(slots=True)
class EffectiveRoutingRulePolicy:
    matched_rule_count: int
    allow_gateways: set[str] | None
    deny_gateways: set[str]
    force_priority_order: list[str]


def _matches_rule(rule: RoutingRule, context: RoutingRuleContext) -> bool:
    if rule.operation != context.operation:
        return False
    if rule.channel and rule.channel != context.channel:
        return False
    if rule.min_amount is not None and context.amount < float(rule.min_amount):
        return False
    if rule.max_amount is not None and context.amount > float(rule.max_amount):
        return False
    return True


async def resolve_routing_rule_policy(
    session: AsyncSession,
    *,
    operation: str,
    amount: float,
    channel: str | None = None,
) -> EffectiveRoutingRulePolicy:
    result = await session.execute(
        select(RoutingRule)
        .where(RoutingRule.enabled.is_(True))
        .order_by(RoutingRule.updated_at.asc(), RoutingRule.id.asc())
    )
    rules = result.scalars().all()
    context = RoutingRuleContext(
        operation=operation,
        amount=amount,
        channel=channel,
    )

    matched_rules = [rule for rule in rules if _matches_rule(rule, context)]

    allowlists = [
        set(rule.allow_gateways or [])
        for rule in matched_rules
        if rule.allow_gateways
    ]
    effective_allowlist: set[str] | None = None
    if allowlists:
        effective_allowlist = set.intersection(*allowlists)

    effective_denylist: set[str] = set()
    forced_priority_order: list[str] = []

    for rule in matched_rules:
        effective_denylist.update(rule.deny_gateways or [])
        if rule.force_priority_order:
            forced_priority_order = list(rule.force_priority_order)

    return EffectiveRoutingRulePolicy(
        matched_rule_count=len(matched_rules),
        allow_gateways=effective_allowlist,
        deny_gateways=effective_denylist,
        force_priority_order=forced_priority_order,
    )

from datetime import datetime, timedelta, timezone
from math import ceil

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.GatewayHealthSnapshot import GatewayHealthSnapshot
from database.models.Processor import Processor
from database.models.RoutingAttempt import RoutingAttempt
from external_services.adapters import get_adapter

BASELINE_SUCCESS_RATE = 85.0
BASELINE_LATENCY_MS = 1000.0
OPEN_SUCCESS_THRESHOLD = 70.0
DEGRADED_SUCCESS_THRESHOLD = 85.0
OPEN_TIMEOUT_THRESHOLD = 30.0
DEGRADED_TIMEOUT_THRESHOLD = 10.0
OPEN_LATENCY_THRESHOLD_MS = 2500.0
DEGRADED_LATENCY_THRESHOLD_MS = 1500.0


async def get_gateway_snapshots(session: AsyncSession) -> dict[str, GatewayHealthSnapshot]:
    result = await session.execute(select(GatewayHealthSnapshot))
    snapshots = result.scalars().all()

    latest_by_gateway: dict[str, GatewayHealthSnapshot] = {}
    for snapshot in snapshots:
        current = latest_by_gateway.get(snapshot.gateway_code)
        if not current or snapshot.last_checked_at >= current.last_checked_at:
            latest_by_gateway[snapshot.gateway_code] = snapshot

    return latest_by_gateway


def is_gateway_available(snapshot: GatewayHealthSnapshot | None) -> bool:
    if snapshot is None:
        return True

    return snapshot.circuit_state.lower() not in {"open", "maintenance", "down"}


def compute_latency_score(latency_ms: float | None) -> float:
    if latency_ms is None:
        return 60.0

    return max(0.0, 100.0 - (latency_ms / 50.0))


def _compute_success_rate(attempts: list[RoutingAttempt]) -> float:
    if not attempts:
        return BASELINE_SUCCESS_RATE

    successful = sum(1 for attempt in attempts if attempt.status == "success")
    return round((successful / len(attempts)) * 100.0, 2)


def _compute_timeout_rate(attempts: list[RoutingAttempt]) -> float:
    if not attempts:
        return 0.0

    timeout_attempts = sum(
        1
        for attempt in attempts
        if attempt.error_code == "timeout"
        or attempt.status == "timeout"
        or "timeout" in (attempt.error_message or "").lower()
    )
    return round((timeout_attempts / len(attempts)) * 100.0, 2)


def _compute_p95_latency_ms(attempts: list[RoutingAttempt]) -> float:
    latencies = sorted(
        attempt.latency_ms
        for attempt in attempts
        if attempt.latency_ms is not None
    )
    if not latencies:
        return BASELINE_LATENCY_MS

    percentile_index = max(0, ceil(len(latencies) * 0.95) - 1)
    return float(latencies[percentile_index])


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _compute_circuit_state(
    *,
    adapter_status: str,
    success_rate_5m: float,
    timeout_rate_5m: float,
    p95_latency_ms: float,
) -> str:
    normalized_adapter_status = adapter_status.lower()
    if normalized_adapter_status in {"maintenance", "down"}:
        return normalized_adapter_status

    if (
        success_rate_5m < OPEN_SUCCESS_THRESHOLD
        or timeout_rate_5m >= OPEN_TIMEOUT_THRESHOLD
        or p95_latency_ms >= OPEN_LATENCY_THRESHOLD_MS
    ):
        return "open"

    if (
        normalized_adapter_status == "degraded"
        or success_rate_5m < DEGRADED_SUCCESS_THRESHOLD
        or timeout_rate_5m >= DEGRADED_TIMEOUT_THRESHOLD
        or p95_latency_ms >= DEGRADED_LATENCY_THRESHOLD_MS
    ):
        return "degraded"

    return "closed"


async def refresh_gateway_health_snapshots(
    session: AsyncSession,
) -> dict[str, GatewayHealthSnapshot]:
    from services import routingService

    await routingService.ensure_processor_catalog(session)
    processors_result = await session.execute(select(Processor))
    processors = processors_result.scalars().all()

    now = datetime.now(timezone.utc)
    attempts_result = await session.execute(
        select(RoutingAttempt).where(
            RoutingAttempt.created_at >= now - timedelta(hours=1),
        )
    )
    recent_attempts = attempts_result.scalars().all()
    existing_snapshots = await get_gateway_snapshots(session)

    refreshed_snapshots: dict[str, GatewayHealthSnapshot] = {}

    for processor in processors:
        gateway_attempts = [
            attempt
            for attempt in recent_attempts
            if attempt.gateway_code == processor.code
        ]
        attempts_5m = [
            attempt
            for attempt in gateway_attempts
            if _normalize_timestamp(attempt.created_at) >= now - timedelta(minutes=5)
        ]

        try:
            health_hint = await get_adapter(processor.code).health_check()
            adapter_status = str(health_hint.get("status", "unknown"))
        except Exception:
            adapter_status = "unknown"

        snapshot = existing_snapshots.get(processor.code)
        if snapshot is None:
            snapshot = GatewayHealthSnapshot(gateway_code=processor.code)
            session.add(snapshot)

        snapshot.success_rate_5m = _compute_success_rate(attempts_5m)
        snapshot.success_rate_1h = _compute_success_rate(gateway_attempts)
        snapshot.timeout_rate_5m = _compute_timeout_rate(attempts_5m)
        snapshot.p95_latency_ms = _compute_p95_latency_ms(attempts_5m)
        snapshot.circuit_state = _compute_circuit_state(
            adapter_status=adapter_status,
            success_rate_5m=snapshot.success_rate_5m,
            timeout_rate_5m=snapshot.timeout_rate_5m,
            p95_latency_ms=snapshot.p95_latency_ms,
        )
        snapshot.last_checked_at = now
        refreshed_snapshots[processor.code] = snapshot

    await session.commit()

    for snapshot in refreshed_snapshots.values():
        await session.refresh(snapshot)

    return refreshed_snapshots

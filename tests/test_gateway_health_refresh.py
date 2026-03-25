from datetime import datetime, timedelta, timezone

import pytest

from database.models.Processor import Processor
from database.models.RoutingAttempt import RoutingAttempt
from services import gatewayHealthService


@pytest.mark.asyncio
class TestGatewayHealthRefresh:
    async def test_refresh_gateway_health_snapshots_persists_metrics_from_recent_attempts(
        self,
        async_session,
    ):
        now = datetime.now(timezone.utc)
        async_session.add(
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                is_active=True,
                supports_collections=True,
                supports_payouts=False,
                priority_weight=1.1,
            )
        )
        await async_session.commit()

        async_session.add_all(
            [
                RoutingAttempt(
                    transaction_id=1,
                    attempt_no=1,
                    gateway_code="fltw",
                    operation="collection",
                    status="success",
                    latency_ms=800,
                    created_at=now - timedelta(minutes=2),
                ),
                RoutingAttempt(
                    transaction_id=2,
                    attempt_no=1,
                    gateway_code="fltw",
                    operation="collection",
                    status="success",
                    latency_ms=900,
                    created_at=now - timedelta(minutes=4),
                ),
                RoutingAttempt(
                    transaction_id=3,
                    attempt_no=1,
                    gateway_code="fltw",
                    operation="collection",
                    status="failed",
                    latency_ms=2500,
                    error_code="timeout",
                    created_at=now - timedelta(minutes=1),
                ),
                RoutingAttempt(
                    transaction_id=4,
                    attempt_no=1,
                    gateway_code="fltw",
                    operation="collection",
                    status="success",
                    latency_ms=950,
                    created_at=now - timedelta(minutes=40),
                ),
            ]
        )
        await async_session.commit()

        snapshots = await gatewayHealthService.refresh_gateway_health_snapshots(async_session)
        snapshot = snapshots["fltw"]

        assert round(snapshot.success_rate_5m, 2) == 66.67
        assert round(snapshot.success_rate_1h, 2) == 75.0
        assert round(snapshot.timeout_rate_5m, 2) == 33.33
        assert snapshot.p95_latency_ms == 2500
        assert snapshot.circuit_state == "open"

    async def test_refresh_gateway_health_snapshots_uses_adapter_hint_without_recent_attempts(
        self,
        async_session,
    ):
        async_session.add(
            Processor(
                code="isw",
                name="Interswitch",
                charge=1.6,
                markup=0.0,
                is_active=False,
                supports_collections=False,
                supports_payouts=False,
                priority_weight=0.85,
            )
        )
        await async_session.commit()

        snapshots = await gatewayHealthService.refresh_gateway_health_snapshots(async_session)
        snapshot = snapshots["isw"]

        assert snapshot.circuit_state == "maintenance"
        assert snapshot.success_rate_5m == 85.0
        assert snapshot.success_rate_1h == 85.0

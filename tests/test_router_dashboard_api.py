from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from database.models.GatewayHealthSnapshot import GatewayHealthSnapshot
from database.models.Processor import Processor
from database.models.RoutingAttempt import RoutingAttempt
from database.models.RoutingDecisionAudit import RoutingDecisionAudit
from database.models.Transaction import Transaction
from main import app
import services.adminService as adminService
from database.models.Admin import Admin


def _override_admin() -> Admin:
    return Admin(id=1, email="admin@routex.test", name="Admin", password="x", is_active=True)


@pytest.mark.asyncio
class TestRouterDashboardApi:
    async def test_router_dashboard_requires_auth(self, client):
        response = await client.get("/analytics/router/dashboard")

        assert response.status_code in [401, 403]

    async def test_router_dashboard_returns_gateway_health_and_failovers(
        self,
        client,
        async_session,
        test_merchant,
        test_customer,
    ):
        processors = [
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                is_active=True,
                supports_collections=True,
                supports_payouts=False,
                priority_weight=1.1,
            ),
            Processor(
                code="kora",
                name="Korapay",
                charge=1.3,
                markup=0.0,
                is_active=True,
                supports_collections=True,
                supports_payouts=True,
                priority_weight=0.95,
            ),
        ]
        async_session.add_all(processors)
        await async_session.commit()

        async_session.add_all(
            [
                GatewayHealthSnapshot(
                    gateway_code="fltw",
                    success_rate_5m=97.5,
                    success_rate_1h=95.0,
                    timeout_rate_5m=1.0,
                    p95_latency_ms=850.0,
                    circuit_state="closed",
                ),
                GatewayHealthSnapshot(
                    gateway_code="kora",
                    success_rate_5m=91.0,
                    success_rate_1h=89.0,
                    timeout_rate_5m=2.5,
                    p95_latency_ms=1020.0,
                    circuit_state="degraded",
                ),
            ]
        )
        await async_session.commit()

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=5000.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="ROUTER_DASH_001",
            processor_reference="PROC_ROUTER_001",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add_all(
            [
                RoutingAttempt(
                    transaction_id=transaction.id,
                    attempt_no=1,
                    gateway_code="kora",
                    operation="collection",
                    status="failed",
                    gateway_reference="PROC_ROUTER_001",
                ),
                RoutingAttempt(
                    transaction_id=transaction.id,
                    attempt_no=2,
                    gateway_code="fltw",
                    operation="collection",
                    status="success",
                    gateway_reference="PROC_ROUTER_001",
                ),
                RoutingDecisionAudit(
                    transaction_id=transaction.id,
                    selected_gateway="fltw",
                    eligible_gateways=["fltw", "kora"],
                    rejected_gateways={},
                    reason="fallback after degraded primary",
                    score_breakdown={"fltw": 92.0, "kora": 84.5},
                    fallback_order=["fltw", "kora"],
                ),
            ]
        )
        await async_session.commit()

        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.get(
                "/analytics/router/dashboard",
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["gateway_health"][0]["gateway_code"] == "fltw"
        assert payload["recent_failovers"][0]["reference"] == "ROUTER_DASH_001"
        assert payload["summary"]["total_gateways"] == 4

    async def test_admin_can_update_gateway_state(
        self,
        client,
        async_session,
    ):
        processor = Processor(
            code="pstk",
            name="Paystack",
            charge=1.5,
            markup=0.0,
            is_active=True,
            supports_collections=True,
            supports_payouts=False,
            priority_weight=1.0,
        )
        async_session.add(processor)
        await async_session.commit()

        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.patch(
                "/admin/router/gateways/pstk",
                json={"is_active": False, "priority_weight": 1.4},
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        await async_session.refresh(processor)

        assert response.status_code == 200
        payload = response.json()
        assert payload["gateway_code"] == "pstk"
        assert payload["is_active"] is False
        assert payload["priority_weight"] == 1.4
        assert processor.is_active is False

    async def test_admin_can_refresh_gateway_health(
        self,
        client,
        async_session,
    ):
        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.post(
                "/admin/router/refresh-health",
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["summary"]["total_gateways"] == 4
        assert "last_checked_at" in payload["gateway_health"][0]

    async def test_admin_can_list_routing_rules(
        self,
        client,
    ):
        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.get(
                "/admin/router/rules",
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, list)

    async def test_admin_can_create_routing_rule(
        self,
        client,
    ):
        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.post(
                "/admin/router/rules",
                json={
                    "name": "High value card collections",
                    "operation": "collection",
                    "channel": "card",
                    "min_amount": 20000,
                    "allow_gateways": ["fltw", "pstk"],
                    "deny_gateways": ["kora"],
                    "force_priority_order": ["fltw", "pstk"],
                    "enabled": True,
                },
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["name"] == "High value card collections"
        assert payload["allow_gateways"] == ["fltw", "pstk"]
        assert payload["deny_gateways"] == ["kora"]
        assert payload["force_priority_order"] == ["fltw", "pstk"]

    async def test_admin_can_update_routing_rule(
        self,
        client,
        async_session,
    ):
        await async_session.execute(
            text(
                """
                INSERT INTO routing_rules
                (name, operation, channel, min_amount, max_amount, allow_gateways,
                 deny_gateways, force_priority_order, enabled, created_at, updated_at)
                VALUES
                (:name, :operation, :channel, :min_amount, :max_amount, :allow_gateways,
                 :deny_gateways, :force_priority_order, :enabled, :created_at, :updated_at)
                """
            ),
            {
                "name": "Fallback card traffic",
                "operation": "collection",
                "channel": "card",
                "min_amount": None,
                "max_amount": None,
                "allow_gateways": '["fltw","kora"]',
                "deny_gateways": "[]",
                "force_priority_order": '["kora","fltw"]',
                "enabled": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        await async_session.commit()

        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.patch(
                "/admin/router/rules/1",
                json={
                    "enabled": False,
                    "deny_gateways": ["isw"],
                },
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is False
        assert payload["deny_gateways"] == ["isw"]
        assert payload["allow_gateways"] == ["fltw", "kora"]
        assert payload["force_priority_order"] == ["kora", "fltw"]

    async def test_router_transaction_detail_returns_attempts_and_decision(
        self,
        client,
        async_session,
        test_merchant,
        test_customer,
    ):
        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=5000.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="ROUTER_DETAIL_001",
            processor_reference="PROC_ROUTER_DETAIL_001",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add_all(
            [
                RoutingAttempt(
                    transaction_id=transaction.id,
                    attempt_no=1,
                    gateway_code="kora",
                    operation="collection",
                    status="failed",
                    gateway_reference="PROC_ROUTER_DETAIL_001",
                    latency_ms=1240,
                ),
                RoutingAttempt(
                    transaction_id=transaction.id,
                    attempt_no=2,
                    gateway_code="fltw",
                    operation="collection",
                    status="success",
                    gateway_reference="PROC_ROUTER_DETAIL_001",
                    latency_ms=860,
                ),
                RoutingDecisionAudit(
                    transaction_id=transaction.id,
                    selected_gateway="fltw",
                    eligible_gateways=["fltw", "kora"],
                    rejected_gateways={"isw": "processor_inactive"},
                    reason="fallback after degraded primary",
                    score_breakdown={"fltw": 92.0, "kora": 84.5},
                    fallback_order=["fltw", "kora"],
                ),
            ]
        )
        await async_session.commit()

        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.get(
                "/analytics/router/transactions/ROUTER_DETAIL_001",
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["transaction"]["reference"] == "ROUTER_DETAIL_001"
        assert payload["transaction"]["gateway_reference"] == "PROC_ROUTER_DETAIL_001"
        assert payload["transaction"]["type"] == "credit"
        assert payload["routing_decision"]["reason"] == "fallback after degraded primary"
        assert payload["attempts"][0]["gateway"] == "kora"
        assert payload["attempts"][1]["gateway"] == "fltw"

    async def test_router_transaction_detail_uses_created_at_to_disambiguate_duplicate_references(
        self,
        client,
        async_session,
        test_merchant,
        test_customer,
    ):
        older_created_at = datetime(2026, 3, 24, 8, 0, 0, tzinfo=timezone.utc)
        newer_created_at = datetime(2026, 3, 24, 9, 0, 0, tzinfo=timezone.utc)

        older_transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=4100.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="kora",
            selected_gateway="kora",
            reference="ROUTER_DUP_001",
            processor_reference="PROC_ROUTER_DUP_OLD",
            created_at=older_created_at,
            updated_at=older_created_at,
        )
        newer_transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=7300.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="ROUTER_DUP_001",
            processor_reference="PROC_ROUTER_DUP_NEW",
            created_at=newer_created_at,
            updated_at=newer_created_at,
        )
        async_session.add_all([older_transaction, newer_transaction])
        await async_session.commit()

        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.get(
                "/analytics/router/transactions/ROUTER_DUP_001",
                params={"created_at": older_created_at.isoformat()},
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["transaction"]["gateway_reference"] == "PROC_ROUTER_DUP_OLD"
        assert payload["transaction"]["amount"] == 4100.0
        assert payload["transaction"]["selected_gateway"] == "kora"

    async def test_router_transaction_detail_returns_404_when_created_at_does_not_match(
        self,
        client,
        async_session,
        test_merchant,
        test_customer,
    ):
        exact_created_at = datetime(2026, 3, 24, 8, 0, 0, tzinfo=timezone.utc)

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=5100.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="ROUTER_MISS_001",
            processor_reference="PROC_ROUTER_MISS_001",
            created_at=exact_created_at,
            updated_at=exact_created_at,
        )
        async_session.add(transaction)
        await async_session.commit()

        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.get(
                "/analytics/router/transactions/ROUTER_MISS_001",
                params={"created_at": datetime(2026, 3, 24, 9, 0, 0, tzinfo=timezone.utc).isoformat()},
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 404

    async def test_router_transaction_detail_does_not_count_same_gateway_retry_as_failover(
        self,
        client,
        async_session,
        test_merchant,
        test_customer,
    ):
        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=3200.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="kora",
            selected_gateway="kora",
            reference="ROUTER_RETRY_001",
            processor_reference="PROC_ROUTER_RETRY_001",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add_all(
            [
                RoutingAttempt(
                    transaction_id=transaction.id,
                    attempt_no=1,
                    gateway_code="kora",
                    operation="collection",
                    status="failed",
                    gateway_reference="PROC_ROUTER_RETRY_001",
                    latency_ms=910,
                ),
                RoutingAttempt(
                    transaction_id=transaction.id,
                    attempt_no=2,
                    gateway_code="kora",
                    operation="collection",
                    status="success",
                    gateway_reference="PROC_ROUTER_RETRY_001",
                    latency_ms=780,
                ),
            ]
        )
        await async_session.commit()

        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.get(
                "/analytics/router/transactions/ROUTER_RETRY_001",
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["failover_summary"]["did_failover"] is False
        assert payload["failover_summary"]["failover_count"] == 0
        assert payload["failover_summary"]["recovered_after_failover"] is False

    async def test_router_transaction_detail_returns_404_for_unknown_reference(
        self,
        client,
    ):
        assert any(
            getattr(route, "path", None) == "/analytics/router/transactions/{reference}"
            for route in app.routes
        )
        app.dependency_overrides[adminService.get_current_admin] = _override_admin
        try:
            response = await client.get(
                "/analytics/router/transactions/UNKNOWN_REF",
                headers={"Authorization": "Bearer admin-token"},
            )
        finally:
            app.dependency_overrides.pop(adminService.get_current_admin, None)

        assert response.status_code == 404

import pytest
from sqlalchemy import text

from database.models.GatewayHealthSnapshot import GatewayHealthSnapshot
from database.models.Processor import Processor
from external_services.adapters import get_adapter
from services import routingService


@pytest.mark.asyncio
class TestRoutingService:
    async def test_builds_routing_decision_with_scores_and_rejections(
        self,
        async_session,
    ):
        processors = [
            Processor(
                code="pstk",
                name="Paystack",
                charge=1.5,
                markup=0.0,
                priority_weight=1.0,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                priority_weight=1.1,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="kora",
                name="Korapay",
                charge=1.3,
                markup=0.0,
                priority_weight=0.9,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="isw",
                name="Interswitch",
                charge=1.6,
                markup=0.0,
                priority_weight=0.8,
                supports_collections=True,
                supports_payouts=False,
                is_active=False,
            ),
        ]

        snapshots = [
            GatewayHealthSnapshot(
                gateway_code="pstk",
                success_rate_5m=92.0,
                success_rate_1h=89.0,
                timeout_rate_5m=2.0,
                p95_latency_ms=1200.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="fltw",
                success_rate_5m=97.0,
                success_rate_1h=95.0,
                timeout_rate_5m=1.0,
                p95_latency_ms=850.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="kora",
                success_rate_5m=90.0,
                success_rate_1h=88.0,
                timeout_rate_5m=3.5,
                p95_latency_ms=1400.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="isw",
                success_rate_5m=70.0,
                success_rate_1h=75.0,
                timeout_rate_5m=10.0,
                p95_latency_ms=2100.0,
                circuit_state="open",
            ),
        ]

        async_session.add_all(processors + snapshots)
        await async_session.commit()

        decision = await routingService.build_routing_decision(
            session=async_session,
            operation="collection",
            currency="NGN",
            amount=5000,
            merchant_id="m_123",
        )

        assert decision.selected_gateway == "fltw"
        assert decision.ranked_gateways == ["fltw", "pstk", "kora"]
        assert set(decision.score_breakdown) == {"fltw", "pstk", "kora"}
        assert decision.rejected_gateways["isw"] == "processor_inactive"

    async def test_routing_scores_ignore_priority_weight_bias_and_rank_by_health_then_latency(
        self,
        async_session,
    ):
        processors = [
            Processor(
                code="pstk",
                name="Paystack",
                charge=1.5,
                markup=0.0,
                priority_weight=5.0,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                priority_weight=0.1,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="kora",
                name="Korapay",
                charge=1.3,
                markup=0.0,
                priority_weight=1.0,
                supports_collections=True,
                supports_payouts=True,
                is_active=False,
            ),
            Processor(
                code="isw",
                name="Interswitch",
                charge=1.6,
                markup=0.0,
                priority_weight=1.0,
                supports_collections=True,
                supports_payouts=False,
                is_active=False,
            ),
        ]

        snapshots = [
            GatewayHealthSnapshot(
                gateway_code="pstk",
                success_rate_5m=93.0,
                success_rate_1h=91.0,
                timeout_rate_5m=1.5,
                p95_latency_ms=980.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="fltw",
                success_rate_5m=98.0,
                success_rate_1h=96.0,
                timeout_rate_5m=0.5,
                p95_latency_ms=760.0,
                circuit_state="closed",
            ),
        ]

        async_session.add_all(processors + snapshots)
        await async_session.commit()

        decision = await routingService.build_routing_decision(
            session=async_session,
            operation="collection",
            currency="NGN",
            amount=5000,
            merchant_id="m_123",
        )

        assert decision.selected_gateway == "fltw"
        assert decision.ranked_gateways == ["fltw", "pstk"]

    async def test_selects_highest_scoring_eligible_gateway(
        self,
        async_session,
    ):
        processors = [
            Processor(
                code="pstk",
                name="Paystack",
                charge=1.5,
                markup=0.0,
                priority_weight=1.0,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                priority_weight=1.1,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="kora",
                name="Korapay",
                charge=1.3,
                markup=0.0,
                priority_weight=0.9,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="isw",
                name="Interswitch",
                charge=1.6,
                markup=0.0,
                priority_weight=0.8,
                supports_collections=True,
                supports_payouts=False,
                is_active=False,
            ),
        ]

        snapshots = [
            GatewayHealthSnapshot(
                gateway_code="pstk",
                success_rate_5m=92.0,
                success_rate_1h=89.0,
                timeout_rate_5m=2.0,
                p95_latency_ms=1200.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="fltw",
                success_rate_5m=97.0,
                success_rate_1h=95.0,
                timeout_rate_5m=1.0,
                p95_latency_ms=850.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="kora",
                success_rate_5m=90.0,
                success_rate_1h=88.0,
                timeout_rate_5m=3.5,
                p95_latency_ms=1400.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="isw",
                success_rate_5m=70.0,
                success_rate_1h=75.0,
                timeout_rate_5m=10.0,
                p95_latency_ms=2100.0,
                circuit_state="open",
            ),
        ]

        async_session.add_all(processors + snapshots)
        await async_session.commit()

        selected, ranked = await routingService.select_gateway(
            session=async_session,
            operation="collection",
            currency="NGN",
            amount=5000,
            merchant_id="m_123",
        )

        assert selected == "fltw"
        assert ranked[0] == "fltw"
        assert ranked == ["fltw", "pstk", "kora"]

    async def test_returns_gateway_adapter_for_selected_processor(self):
        adapter = get_adapter("fltw")

        assert adapter.capability.code == "fltw"

    async def test_build_routing_decision_respects_rule_allowlist(
        self,
        async_session,
    ):
        processors = [
            Processor(
                code="pstk",
                name="Paystack",
                charge=1.5,
                markup=0.0,
                priority_weight=1.0,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                priority_weight=1.1,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="kora",
                name="Korapay",
                charge=1.3,
                markup=0.0,
                priority_weight=0.9,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
        ]
        snapshots = [
            GatewayHealthSnapshot(
                gateway_code="pstk",
                success_rate_5m=94.0,
                success_rate_1h=92.0,
                timeout_rate_5m=1.0,
                p95_latency_ms=980.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="fltw",
                success_rate_5m=97.0,
                success_rate_1h=95.0,
                timeout_rate_5m=1.0,
                p95_latency_ms=820.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="kora",
                success_rate_5m=91.0,
                success_rate_1h=89.0,
                timeout_rate_5m=2.5,
                p95_latency_ms=1100.0,
                circuit_state="closed",
            ),
        ]
        async_session.add_all(processors + snapshots)
        await async_session.commit()

        await async_session.execute(
            text(
                """
                INSERT INTO routing_rules
                (name, operation, channel, min_amount, max_amount, allow_gateways,
                 deny_gateways, force_priority_order, enabled, created_at, updated_at)
                VALUES
                (:name, :operation, :channel, :min_amount, :max_amount, :allow_gateways,
                 :deny_gateways, :force_priority_order, :enabled, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {
                "name": "High value card allowlist",
                "operation": "collection",
                "channel": "card",
                "min_amount": 20000,
                "max_amount": None,
                "allow_gateways": '["fltw","pstk"]',
                "deny_gateways": "[]",
                "force_priority_order": "[]",
                "enabled": True,
            },
        )
        await async_session.execute(
            text(
                """
                INSERT INTO routing_rules
                (name, operation, channel, min_amount, max_amount, allow_gateways,
                 deny_gateways, force_priority_order, enabled, created_at, updated_at)
                VALUES
                (:name, :operation, :channel, :min_amount, :max_amount, :allow_gateways,
                 :deny_gateways, :force_priority_order, :enabled, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {
                "name": "Ignore payout-only override",
                "operation": "payout",
                "channel": "bank_transfer",
                "min_amount": 1,
                "max_amount": 1000,
                "allow_gateways": '["kora"]',
                "deny_gateways": '["fltw","pstk"]',
                "force_priority_order": '["kora"]',
                "enabled": True,
            },
        )
        await async_session.commit()

        decision = await routingService.build_routing_decision(
            session=async_session,
            operation="collection",
            currency="NGN",
            amount=25000,
            merchant_id="m_123",
            channel="card",
        )

        assert set(decision.ranked_gateways) <= {"fltw", "pstk"}
        assert "kora" not in decision.ranked_gateways
        assert decision.ranked_gateways == ["fltw", "pstk"]

    async def test_build_routing_decision_applies_forced_priority_order(
        self,
        async_session,
    ):
        processors = [
            Processor(
                code="pstk",
                name="Paystack",
                charge=1.5,
                markup=0.0,
                priority_weight=1.0,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                priority_weight=1.1,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="kora",
                name="Korapay",
                charge=1.3,
                markup=0.0,
                priority_weight=0.9,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
        ]
        snapshots = [
            GatewayHealthSnapshot(
                gateway_code="pstk",
                success_rate_5m=94.0,
                success_rate_1h=92.0,
                timeout_rate_5m=1.0,
                p95_latency_ms=980.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="fltw",
                success_rate_5m=99.0,
                success_rate_1h=97.0,
                timeout_rate_5m=0.5,
                p95_latency_ms=760.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="kora",
                success_rate_5m=90.0,
                success_rate_1h=88.0,
                timeout_rate_5m=2.0,
                p95_latency_ms=1080.0,
                circuit_state="closed",
            ),
        ]
        async_session.add_all(processors + snapshots)
        await async_session.commit()

        await async_session.execute(
            text(
                """
                INSERT INTO routing_rules
                (name, operation, channel, min_amount, max_amount, allow_gateways,
                 deny_gateways, force_priority_order, enabled, created_at, updated_at)
                VALUES
                (:name, :operation, :channel, :min_amount, :max_amount, :allow_gateways,
                 :deny_gateways, :force_priority_order, :enabled, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {
                "name": "Priority override",
                "operation": "collection",
                "channel": "card",
                "min_amount": None,
                "max_amount": None,
                "allow_gateways": '["fltw","pstk","kora"]',
                "deny_gateways": "[]",
                "force_priority_order": '["kora","pstk"]',
                "enabled": True,
            },
        )
        await async_session.execute(
            text(
                """
                INSERT INTO routing_rules
                (name, operation, channel, min_amount, max_amount, allow_gateways,
                 deny_gateways, force_priority_order, enabled, created_at, updated_at)
                VALUES
                (:name, :operation, :channel, :min_amount, :max_amount, :allow_gateways,
                 :deny_gateways, :force_priority_order, :enabled, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {
                "name": "Ignore bank transfer ordering",
                "operation": "collection",
                "channel": "bank_transfer",
                "min_amount": None,
                "max_amount": None,
                "allow_gateways": '["fltw","pstk","kora"]',
                "deny_gateways": "[]",
                "force_priority_order": '["fltw"]',
                "enabled": True,
            },
        )
        await async_session.commit()

        decision = await routingService.build_routing_decision(
            session=async_session,
            operation="collection",
            currency="NGN",
            amount=5000,
            merchant_id="m_123",
            channel="card",
        )

        assert decision.ranked_gateways == ["kora", "pstk", "fltw"]

    async def test_build_routing_decision_fails_when_rules_remove_all_gateways(
        self,
        async_session,
    ):
        processors = [
            Processor(
                code="pstk",
                name="Paystack",
                charge=1.5,
                markup=0.0,
                priority_weight=1.0,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
            Processor(
                code="fltw",
                name="Flutterwave",
                charge=1.4,
                markup=0.0,
                priority_weight=1.1,
                supports_collections=True,
                supports_payouts=True,
                is_active=True,
            ),
        ]
        snapshots = [
            GatewayHealthSnapshot(
                gateway_code="pstk",
                success_rate_5m=94.0,
                success_rate_1h=92.0,
                timeout_rate_5m=1.0,
                p95_latency_ms=980.0,
                circuit_state="closed",
            ),
            GatewayHealthSnapshot(
                gateway_code="fltw",
                success_rate_5m=99.0,
                success_rate_1h=97.0,
                timeout_rate_5m=0.5,
                p95_latency_ms=760.0,
                circuit_state="closed",
            ),
        ]
        async_session.add_all(processors + snapshots)
        await async_session.commit()

        await async_session.execute(
            text(
                """
                INSERT INTO routing_rules
                (name, operation, channel, min_amount, max_amount, allow_gateways,
                 deny_gateways, force_priority_order, enabled, created_at, updated_at)
                VALUES
                (:name, :operation, :channel, :min_amount, :max_amount, :allow_gateways,
                 :deny_gateways, :force_priority_order, :enabled, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {
                "name": "Deny all card routes",
                "operation": "collection",
                "channel": "card",
                "min_amount": None,
                "max_amount": None,
                "allow_gateways": "[]",
                "deny_gateways": '["pstk","fltw","kora","isw"]',
                "force_priority_order": "[]",
                "enabled": True,
            },
        )
        await async_session.commit()

        with pytest.raises(
            ValueError,
            match="No eligible gateways available after applying routing rules.",
        ):
            await routingService.build_routing_decision(
                session=async_session,
                operation="collection",
                currency="NGN",
                amount=5000,
                merchant_id="m_123",
                channel="card",
            )

import pytest

from database.models.Processor import Processor
from database.models.Transaction import Transaction


@pytest.mark.asyncio
class TestRoutingModels:
    async def test_can_create_routing_attempt_record(
        self,
        async_session,
        test_merchant,
    ):
        from database.models.RoutingAttempt import RoutingAttempt

        processor = Processor(code="pstk", charge=1.5, markup=0.0)
        transaction = Transaction(
            type="credit",
            mode="test",
            processor="pstk",
            merchant_id=test_merchant.id,
            reference="ORD_ROUTE_1001",
            amount=5000.0,
            currency="NGN",
            status="pending",
        )

        async_session.add_all([processor, transaction])
        await async_session.commit()
        await async_session.refresh(transaction)

        attempt = RoutingAttempt(
            transaction_id=transaction.id,
            attempt_no=1,
            gateway_code="pstk",
            operation="collection",
            status="pending",
        )

        async_session.add(attempt)
        await async_session.commit()
        await async_session.refresh(attempt)

        assert attempt.id is not None
        assert attempt.transaction_id == transaction.id
        assert attempt.gateway_code == "pstk"

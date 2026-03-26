import pytest

from database.models.Transaction import Transaction
from enums.tokenEnums import TokenMode
from enums.transactionEnums import TransactionProcessor, TransactionStatus, TransactionType
from services import analyticsService


@pytest.mark.asyncio
class TestAnalyticsService:
    async def test_revenue_metrics_count_enum_backed_successful_credit_transactions(
        self,
        async_session,
        test_merchant,
        test_customer,
    ):
        async_session.add_all(
            [
                Transaction(
                    merchant_id=test_merchant.id,
                    customer_id=test_customer.id,
                    amount=2500.0,
                    charge=125.0,
                    currency="NGN",
                    type=TransactionType.CREDIT,
                    status=TransactionStatus.SUCCESS,
                    mode=TokenMode.TEST.value,
                    processor=TransactionProcessor.FLUTTERWAVE,
                    selected_gateway="fltw",
                    reference="ANALYTICS_SUCCESS_001",
                    processor_reference="ANALYTICS_PROC_001",
                ),
                Transaction(
                    merchant_id=test_merchant.id,
                    customer_id=test_customer.id,
                    amount=1800.0,
                    charge=90.0,
                    currency="NGN",
                    type=TransactionType.CREDIT,
                    status=TransactionStatus.PENDING,
                    mode=TokenMode.TEST.value,
                    processor=TransactionProcessor.FLUTTERWAVE,
                    selected_gateway="fltw",
                    reference="ANALYTICS_PENDING_001",
                    processor_reference="ANALYTICS_PROC_002",
                ),
            ]
        )
        await async_session.commit()

        metrics = await analyticsService.get_revenue_metrics(
            session=async_session,
            merchant_id=test_merchant.id,
            mode=TokenMode.TEST.value,
        )

        assert metrics["total_transactions"] == 2
        assert metrics["total_revenue"] == 2500.0
        assert metrics["total_charges"] == 125.0
        assert metrics["net_revenue"] == 2375.0
        assert metrics["average_transaction_value"] == 2500.0
        assert metrics["success_rate"] == 50.0

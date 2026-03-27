from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from database.models.PaymentLink import PaymentLink
from database.models.Transaction import Transaction
from enums.LinkEnums import AmountType, LinkMode, LinkType
from enums.transactionEnums import (
    TransactionCurrency,
    TransactionProcessor,
    TransactionStatus,
    TransactionType,
)
from schemas.linkSchema import PaymentLinkCreateRequest
from services import linkService


@pytest.mark.asyncio
class TestPaymentLinkGatewayOverride:
    async def test_create_payment_link_persists_gateway_override(
        self,
        async_session,
        test_merchant,
    ):
        request = PaymentLinkCreateRequest(
            merchant_id=test_merchant.id,
            title="Launch payment link",
            description="Pinned to Paystack",
            amount_type=AmountType.STATIC,
            mode=LinkMode.TEST,
            type=LinkType.RECURRING,
            currency=TransactionCurrency.NIGERIA,
            amount=2500,
            gateway_code="pstk",
        )

        link = await linkService.create_payment_link(
            session=async_session,
            merchant=test_merchant,
            data=request,
        )
        response = await linkService.get_payment_link_response(
            session=async_session,
            link_id=link.id,
        )

        assert link.gateway_code == "pstk"
        assert response.gateway_code == "pstk"

    @patch("api.views.linkView.get_adapter")
    @patch(
        "api.views.linkView.transactionService.get_transaction_by_merchant_and_reference",
        new_callable=AsyncMock,
    )
    @patch("api.views.linkView.transactionService.save_transaction", new_callable=AsyncMock)
    async def test_public_link_checkout_uses_pinned_gateway(
        self,
        mock_save_transaction,
        mock_get_transaction,
        mock_get_adapter,
        client,
        async_session,
        test_merchant,
        test_customer,
    ):
        persisted_transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=2500.0,
            currency=TransactionCurrency.NIGERIA.value,
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode=LinkMode.TEST.value,
            processor=TransactionProcessor.PAYSTACK.value,
            selected_gateway=TransactionProcessor.PAYSTACK.value,
            reference="plink-checkout-001",
            processor_reference="PROC_PLINK_001",
            redirect_url="https://merchant.example.com/return",
            notification_url="https://merchant.example.com/webhook",
        )
        mock_get_transaction.return_value = persisted_transaction
        mock_save_transaction.return_value = persisted_transaction

        adapter = AsyncMock()
        adapter.initialize_collection.return_value = (
            {"status": True, "message": "ok"},
            200,
            "https://checkout.paystack.test/plink-checkout-001",
        )
        mock_get_adapter.return_value = adapter

        link = PaymentLink(
            id="plink001",
            reference="LINK_001",
            title="Pinned gateway link",
            description="Use Paystack for this link",
            currency=TransactionCurrency.NIGERIA.value,
            amount_type=AmountType.STATIC.value,
            amount=2500,
            type=LinkType.RECURRING.value,
            mode=LinkMode.TEST.value,
            merchant_id=test_merchant.id,
            redirect_url="https://merchant.example.com/return",
            is_active=True,
            gateway_code="pstk",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        async_session.add(link)
        await async_session.commit()

        response = await client.post(
            f"/links/r/{link.reference}/checkout",
            json={
                "customer_email": test_customer.email,
                "currency": TransactionCurrency.NIGERIA.value,
                "amount": 2500,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["checkout_url"] == "https://checkout.paystack.test/plink-checkout-001"
        assert payload["selected_gateway"] == "pstk"
        mock_get_adapter.assert_called_once_with("pstk")

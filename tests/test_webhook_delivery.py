from unittest.mock import patch

import pytest
from sqlalchemy import select

from database.models.RoutingAttempt import RoutingAttempt
from database.models.Transaction import Transaction
from enums.eventEnums import EventType
from enums.transactionEnums import TransactionStatus, TransactionType


@pytest.mark.asyncio
class TestWebhookDelivery:
    @patch("api.v1.webhooks.FLTW_SECRET_HASH", "test-secret-hash")
    @patch("services.webhookService.dispatch")
    @patch("services.emailService.send_customer_receipt_email")
    @patch("services.emailService.send_merchant_receipt_email")
    async def test_flutterwave_success_webhook_dispatches_merchant_callback(
        self,
        mock_send_merchant_receipt,
        mock_send_customer_receipt,
        mock_dispatch,
        client,
        async_session,
        test_merchant,
        test_wallet,
        test_customer,
    ):
        del mock_send_merchant_receipt
        del mock_send_customer_receipt
        del test_wallet

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=2500.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="WEBHOOK_DELIVERY_FLTW_001",
            processor_reference="PROC_DELIVERY_FLTW_001",
            notification_url="https://merchant.example.com/webhook",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add(
            RoutingAttempt(
                transaction_id=transaction.id,
                attempt_no=1,
                gateway_code="fltw",
                operation="collection",
                status="pending",
                gateway_reference=transaction.processor_reference,
            )
        )
        await async_session.commit()

        response = await client.post(
            "/flutterwave/webhook/test",
            headers={
                "verif-hash": "test-secret-hash",
                "Content-Type": "application/json",
            },
            json={
                "event": "charge.completed",
                "data": {
                    "status": "successful",
                    "tx_ref": transaction.processor_reference,
                    "app_fee": 20.0,
                },
            },
        )

        assert response.status_code == 200

        await async_session.refresh(transaction)
        attempt = await async_session.scalar(
            select(RoutingAttempt).where(RoutingAttempt.transaction_id == transaction.id)
        )

        assert transaction.status == TransactionStatus.SUCCESS.value
        assert attempt.status == TransactionStatus.SUCCESS.value
        mock_dispatch.assert_called_once()
        assert mock_dispatch.call_args.kwargs["transaction"].id == transaction.id
        assert mock_dispatch.call_args.kwargs["event"] == EventType.CHARGE_SUCCESS

import json
from unittest.mock import patch

import pytest
from sqlalchemy import select
from cryptography.fernet import Fernet

from database.models.RoutingAttempt import RoutingAttempt
from database.models.Token import Token
from database.models.Transaction import Transaction
from enums.eventEnums import EventType
from enums.transactionEnums import TransactionStatus, TransactionType
from services import webhookService


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

    @patch("api.v1.webhooks.FLTW_SECRET_HASH", "test-secret-hash")
    @patch("services.webhookService.dispatch")
    @patch("services.webhookNormalizationService.flutterwaveService.verify_transaction")
    @patch("services.emailService.send_customer_receipt_email")
    @patch("services.emailService.send_merchant_receipt_email")
    async def test_flutterwave_success_webhook_recovers_reference_via_verify_and_dispatches_merchant_callback(
        self,
        mock_send_merchant_receipt,
        mock_send_customer_receipt,
        mock_verify_transaction,
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
            amount=3100.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="WEBHOOK_VERIFY_FLTW_001",
            processor_reference="PROC_VERIFY_FLTW_001",
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

        mock_verify_transaction.return_value = (
            {
                "status": "success",
                "data": {
                    "id": 918273,
                    "status": "successful",
                    "tx_ref": transaction.processor_reference,
                    "app_fee": 25.0,
                    "meta": {
                        "routex_reference": transaction.reference,
                        "routex_processor_reference": transaction.processor_reference,
                    },
                },
            },
            200,
        )

        response = await client.post(
            "/flutterwave/webhook/test",
            headers={
                "verif-hash": "test-secret-hash",
                "Content-Type": "application/json",
            },
            json={
                "event": "charge.successful",
                "data": {
                    "id": 918273,
                    "status": "successful",
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
        mock_verify_transaction.assert_awaited_once()
        mock_dispatch.assert_called_once()
        assert mock_dispatch.call_args.kwargs["transaction"].id == transaction.id
        assert mock_dispatch.call_args.kwargs["event"] == EventType.CHARGE_SUCCESS

    @patch("services.celeryService.send_webhook_task.apply_async")
    async def test_webhook_dispatch_queues_celery_delivery_with_aggregator_signature_only(
        self,
        mock_apply_async,
        async_session,
        test_merchant,
        test_customer,
        monkeypatch,
    ):
        agg_secret = "N9uM0cgA3-4W1hLqgNGVZy2lxwM21O08OZl5sB2h_OI="
        raw_secret = "test_webhook_secret_123"
        monkeypatch.setattr("settings.AGG_SECRET", agg_secret)

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=2500.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.SUCCESS.value,
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="WEBHOOK_QUEUE_001",
            processor_reference="PROC_WEBHOOK_QUEUE_001",
            notification_url="https://merchant.example.com/webhook",
            metadata_payload={"order_id": "WEBHOOK_QUEUE_001"},
        )
        async_session.add(transaction)
        token_obj = Token(
            merchant_id=test_merchant.id,
            secret_key=Fernet(agg_secret).encrypt(raw_secret.encode()).decode(),
            public_key=Fernet(agg_secret).encrypt(b"public_key").decode(),
            type="test",
            is_active=True,
        )
        async_session.add(token_obj)
        await async_session.commit()
        await async_session.refresh(transaction)

        webhookService.dispatch(
            transaction=transaction,
            event=EventType.CHARGE_SUCCESS,
            token=token_obj,
        )

        mock_apply_async.assert_called_once()
        kwargs = mock_apply_async.call_args.kwargs
        assert kwargs["queue"] == "webhook_queue"
        assert kwargs["routing_key"] == "webhook_queue"
        task_kwargs = kwargs["kwargs"]
        assert task_kwargs["url"] == "https://merchant.example.com/webhook"
        assert task_kwargs["event_type"] == EventType.CHARGE_SUCCESS.value
        assert set(task_kwargs["headers"]) == {"Content-Type", "X-AGGREGATOR-SIGNATURE"}

        payload = json.loads(task_kwargs["payload_str"])
        assert payload["event"] == EventType.CHARGE_SUCCESS.value
        assert payload["reference"] == "WEBHOOK_QUEUE_001"
        assert payload["data"]["customer"]["email"] == test_customer.email

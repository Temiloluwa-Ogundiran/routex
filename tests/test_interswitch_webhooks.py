import hashlib
import hmac
import json
from unittest.mock import patch

import pytest
from sqlalchemy import select

from database.models.RoutingAttempt import RoutingAttempt
from database.models.Transaction import Transaction
from enums.transactionEnums import TransactionStatus, TransactionType


def _signed_body(payload: dict, secret: str) -> tuple[bytes, str]:
    raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha512).hexdigest()
    return raw_body, signature


@pytest.mark.asyncio
class TestInterswitchWebhookEndpoints:
    async def test_interswitch_webhook_rejects_invalid_signature(
        self,
        client,
        monkeypatch,
    ):
        monkeypatch.setenv("INTERSWITCH_SECRET_KEY", "isw_test_secret")
        payload = {
            "event": "TRANSACTION.COMPLETED",
            "uuid": "evt_invalid_sig",
            "data": {
                "merchantReference": "ISW_PROC_INVALID_SIG",
                "responseCode": "00",
            },
        }
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        response = await client.post(
            "/interswitch/webhook/test",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Interswitch-Signature": "invalid-signature",
            },
        )

        assert response.status_code == 400

    @patch("services.emailService.send_customer_receipt_email")
    @patch("services.emailService.send_merchant_receipt_email")
    async def test_interswitch_webhook_accepts_signed_completed_event(
        self,
        mock_send_merchant_receipt,
        mock_send_customer_receipt,
        client,
        async_session,
        test_merchant,
        test_wallet,
        test_customer,
        monkeypatch,
    ):
        del mock_send_merchant_receipt
        del mock_send_customer_receipt

        monkeypatch.setenv("INTERSWITCH_SECRET_KEY", "isw_test_secret")

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            wallet_id=test_wallet.id,
            amount=1200.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="isw",
            selected_gateway="isw",
            reference="ISW_WEBHOOK_001",
            processor_reference="ISW_PROC_WEBHOOK_001",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add(
            RoutingAttempt(
                transaction_id=transaction.id,
                attempt_no=1,
                gateway_code="isw",
                operation="collection",
                status="pending",
                gateway_reference=transaction.processor_reference,
            )
        )
        await async_session.commit()

        payload = {
            "event": "TRANSACTION.COMPLETED",
            "uuid": "evt_valid_sig",
            "data": {
                "merchantReference": transaction.processor_reference,
                "paymentReference": "ISW_PAY_VALID_001",
                "responseCode": "00",
                "responseDescription": "Approved by Financial Institution",
                "amount": 120000,
            },
        }
        raw_body, signature = _signed_body(payload, "isw_test_secret")

        response = await client.post(
            "/interswitch/webhook/test",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Interswitch-Signature": signature,
            },
        )

        await async_session.refresh(transaction)
        await async_session.refresh(test_wallet)
        attempt = await async_session.scalar(
            select(RoutingAttempt).where(RoutingAttempt.transaction_id == transaction.id)
        )

        assert response.status_code == 200
        assert transaction.status == TransactionStatus.SUCCESS.value
        assert attempt.status == TransactionStatus.SUCCESS.value

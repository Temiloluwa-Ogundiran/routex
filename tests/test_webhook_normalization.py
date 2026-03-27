from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy import select

from database.models.RoutingAttempt import RoutingAttempt
from database.models.Transaction import Transaction
from enums.transactionEnums import TransactionStatus, TransactionType


@pytest.mark.asyncio
class TestWebhookNormalization:
    @patch("services.emailService.send_customer_receipt_email")
    @patch("services.emailService.send_merchant_receipt_email")
    async def test_duplicate_webhook_is_idempotent(
        self,
        mock_send_merchant_receipt,
        mock_send_customer_receipt,
        async_session,
        test_merchant,
        test_wallet,
        test_customer,
    ):
        del mock_send_merchant_receipt
        del mock_send_customer_receipt

        import services.webhookNormalizationService as webhookNormalizationService

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            wallet_id=test_wallet.id,
            amount=1000.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="kora",
            selected_gateway="kora",
            reference="WEBHOOK_DUPLICATE_001",
            processor_reference="PROC_DUPLICATE_001",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add(
            RoutingAttempt(
                transaction_id=transaction.id,
                attempt_no=1,
                gateway_code="kora",
                operation="collection",
                status="pending",
                gateway_reference=transaction.processor_reference,
            )
        )
        await async_session.commit()

        payload = {
            "event": "charge.success",
            "data": {
                "reference": transaction.processor_reference,
                "fee": 5.0,
            },
        }

        starting_balance = test_wallet.balance

        await webhookNormalizationService.handle_event("kora", payload, async_session)
        await async_session.refresh(transaction)
        await async_session.refresh(test_wallet)
        balance_after_first_delivery = test_wallet.balance

        await webhookNormalizationService.handle_event("kora", payload, async_session)
        await async_session.refresh(transaction)
        await async_session.refresh(test_wallet)

        attempt = await async_session.scalar(
            select(RoutingAttempt).where(RoutingAttempt.transaction_id == transaction.id)
        )

        assert transaction.status == TransactionStatus.SUCCESS.value
        assert balance_after_first_delivery > starting_balance
        assert test_wallet.balance == balance_after_first_delivery
        assert attempt.status == TransactionStatus.SUCCESS.value

    async def test_failed_webhook_marks_transaction_for_reconciliation(
        self,
        async_session,
        test_merchant,
        test_customer,
    ):
        import services.webhookNormalizationService as webhookNormalizationService

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=2000.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="WEBHOOK_FAILED_001",
            processor_reference="PROC_FAILED_001",
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

        payload = {
            "event": "charge.failed",
            "data": {
                "tx_ref": transaction.processor_reference,
                "status": "failed",
                "app_fee": 12.0,
            },
        }

        await webhookNormalizationService.handle_event("fltw", payload, async_session)
        await async_session.refresh(transaction)
        attempt = await async_session.scalar(
            select(RoutingAttempt).where(RoutingAttempt.transaction_id == transaction.id)
        )

        assert transaction.status == TransactionStatus.FAILED.value
        assert transaction.details["reconciliation_required"] is True
        assert attempt.status == TransactionStatus.FAILED.value

    @patch("services.emailService.send_customer_receipt_email")
    @patch("services.emailService.send_merchant_receipt_email")
    async def test_flutterwave_type_payload_with_reference_fallback_marks_success(
        self,
        mock_send_merchant_receipt,
        mock_send_customer_receipt,
        async_session,
        test_merchant,
        test_wallet,
        test_customer,
    ):
        del mock_send_merchant_receipt
        del mock_send_customer_receipt

        import services.webhookNormalizationService as webhookNormalizationService

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            wallet_id=test_wallet.id,
            amount=2200.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="WEBHOOK_FLTW_TYPE_001",
            processor_reference="PROC_FLTW_TYPE_001",
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

        starting_balance = test_wallet.balance
        payload = {
            "type": "charge.completed",
            "data": {
                "reference": transaction.processor_reference,
                "status": "succeeded",
                "app_fee": 15.0,
            },
        }

        normalized_event, updated_transaction = await webhookNormalizationService.handle_event(
            "fltw",
            payload,
            async_session,
        )
        await async_session.refresh(transaction)
        await async_session.refresh(test_wallet)

        attempt = await async_session.scalar(
            select(RoutingAttempt).where(RoutingAttempt.transaction_id == transaction.id)
        )

        assert normalized_event.event == "charge.completed"
        assert normalized_event.status == TransactionStatus.SUCCESS.value
        assert updated_transaction is not None
        assert transaction.status == TransactionStatus.SUCCESS.value
        assert test_wallet.balance > starting_balance
        assert attempt.status == TransactionStatus.SUCCESS.value

    @patch("services.emailService.send_customer_receipt_email")
    @patch("services.emailService.send_merchant_receipt_email")
    async def test_interswitch_completed_success_credits_wallet(
        self,
        mock_send_merchant_receipt,
        mock_send_customer_receipt,
        async_session,
        test_merchant,
        test_wallet,
        test_customer,
    ):
        del mock_send_merchant_receipt
        del mock_send_customer_receipt

        import services.webhookNormalizationService as webhookNormalizationService

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            wallet_id=test_wallet.id,
            amount=1500.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="isw",
            selected_gateway="isw",
            reference="WEBHOOK_ISW_SUCCESS_001",
            processor_reference="ISW_PROC_SUCCESS_001",
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

        starting_balance = test_wallet.balance
        payload = {
            "event": "TRANSACTION.COMPLETED",
            "uuid": "evt_isw_success_001",
            "data": {
                "merchantReference": transaction.processor_reference,
                "paymentReference": "ISW_PAYMENT_001",
                "responseCode": "00",
                "responseDescription": "Approved by Financial Institution",
                "amount": 150000,
            },
        }

        normalized_event, updated_transaction = await webhookNormalizationService.handle_event(
            "isw",
            payload,
            async_session,
        )
        await async_session.refresh(transaction)
        await async_session.refresh(test_wallet)

        attempt = await async_session.scalar(
            select(RoutingAttempt).where(RoutingAttempt.transaction_id == transaction.id)
        )

        assert normalized_event.status == TransactionStatus.SUCCESS.value
        assert updated_transaction is not None
        assert transaction.status == TransactionStatus.SUCCESS.value
        assert test_wallet.balance > starting_balance
        assert attempt.status == TransactionStatus.SUCCESS.value

    async def test_interswitch_updated_event_keeps_transaction_pending(
        self,
        async_session,
        test_merchant,
        test_wallet,
        test_customer,
    ):
        import services.webhookNormalizationService as webhookNormalizationService

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            wallet_id=test_wallet.id,
            amount=1800.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="isw",
            selected_gateway="isw",
            reference="WEBHOOK_ISW_PENDING_001",
            processor_reference="ISW_PROC_PENDING_001",
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

        starting_balance = test_wallet.balance
        payload = {
            "event": "TRANSACTION.UPDATED",
            "uuid": "evt_isw_pending_001",
            "data": {
                "merchantReference": transaction.processor_reference,
                "paymentReference": "ISW_PAYMENT_PENDING_001",
                "responseCode": "09",
                "responseDescription": "Processing",
                "amount": 180000,
            },
        }

        normalized_event, updated_transaction = await webhookNormalizationService.handle_event(
            "isw",
            payload,
            async_session,
        )
        await async_session.refresh(transaction)
        await async_session.refresh(test_wallet)

        attempt = await async_session.scalar(
            select(RoutingAttempt).where(RoutingAttempt.transaction_id == transaction.id)
        )

        assert normalized_event.status == TransactionStatus.PENDING.value
        assert updated_transaction is not None
        assert transaction.status == TransactionStatus.PENDING.value
        assert test_wallet.balance == starting_balance
        assert attempt.status == TransactionStatus.PENDING.value
        assert transaction.details["last_webhook_event"] == "TRANSACTION.UPDATED"

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import services.emailService as emailService
import services.reconciliationService as reconciliationService
import services.transactionService as transactionService
import services.walletService as walletService
from database.models.RoutingAttempt import RoutingAttempt
from database.models.Transaction import Transaction
from enums import tokenEnums, transactionEnums
from database.models.Merchant import Merchant


@dataclass(slots=True)
class NormalizedWebhookEvent:
    gateway: str
    event: str
    processor_reference: str | None
    operation: str
    status: str
    processor_fee: float = 0.0


def normalize_event(gateway: str, payload: dict) -> NormalizedWebhookEvent:
    data = payload.get("data", {})

    if gateway == "kora":
        raw_event = payload.get("event", "")
        event_map = {
            "charge.success": ("collection", transactionEnums.TransactionStatus.SUCCESS.value),
            "charge.failed": ("collection", transactionEnums.TransactionStatus.FAILED.value),
            "transfer.success": ("payout", transactionEnums.TransactionStatus.SUCCESS.value),
            "transfer.failed": ("payout", transactionEnums.TransactionStatus.FAILED.value),
        }
        operation, status = event_map.get(
            raw_event,
            ("collection", "ignored"),
        )
        return NormalizedWebhookEvent(
            gateway=gateway,
            event=raw_event,
            processor_reference=data.get("reference"),
            operation=operation,
            status=status,
            processor_fee=float(data.get("fee") or 0.0),
        )

    if gateway == "pstk":
        raw_event = payload.get("event", "")
        event_map = {
            "charge.success": ("collection", transactionEnums.TransactionStatus.SUCCESS.value),
            "charge.failed": ("collection", transactionEnums.TransactionStatus.FAILED.value),
        }
        operation, status = event_map.get(raw_event, ("collection", "ignored"))
        raw_fee = data.get("fees") or 0.0
        return NormalizedWebhookEvent(
            gateway=gateway,
            event=raw_event,
            processor_reference=data.get("reference"),
            operation=operation,
            status=status,
            processor_fee=float(raw_fee) / 100 if raw_fee else 0.0,
        )

    if gateway == "fltw":
        status_value = str(data.get("status", "")).lower()
        normalized_status = (
            transactionEnums.TransactionStatus.SUCCESS.value
            if status_value == "successful"
            else transactionEnums.TransactionStatus.FAILED.value
        )
        return NormalizedWebhookEvent(
            gateway=gateway,
            event=payload.get("event", f"charge.{status_value or 'failed'}"),
            processor_reference=data.get("tx_ref") or data.get("reference"),
            operation="collection",
            status=normalized_status,
            processor_fee=float(data.get("app_fee") or 0.0),
        )

    if gateway == "isw":
        raw_event = str(payload.get("event", "")).upper()
        response_code = str(data.get("responseCode") or "").strip()
        if raw_event == "TRANSACTION.COMPLETED":
            normalized_status = (
                transactionEnums.TransactionStatus.SUCCESS.value
                if response_code == "00"
                else transactionEnums.TransactionStatus.FAILED.value
            )
        elif raw_event in {"TRANSACTION.CREATED", "TRANSACTION.UPDATED"}:
            normalized_status = transactionEnums.TransactionStatus.PENDING.value
        else:
            normalized_status = "ignored"

        return NormalizedWebhookEvent(
            gateway=gateway,
            event=raw_event,
            processor_reference=data.get("merchantReference") or payload.get("uuid"),
            operation="collection",
            status=normalized_status,
            processor_fee=0.0,
        )

    raise ValueError(f"Unsupported webhook gateway: {gateway}")


async def _get_latest_routing_attempt(
    session: AsyncSession,
    transaction_id: int,
) -> RoutingAttempt | None:
    result = await session.execute(
        select(RoutingAttempt)
        .where(RoutingAttempt.transaction_id == transaction_id)
        .order_by(RoutingAttempt.attempt_no.desc())
    )
    return result.scalars().first()


async def _update_routing_attempt(
    session: AsyncSession,
    transaction: Transaction,
    normalized_event: NormalizedWebhookEvent,
) -> None:
    attempt = await _get_latest_routing_attempt(session, transaction.id)
    if not attempt:
        return

    attempt.status = normalized_event.status
    attempt.gateway_reference = transaction.processor_reference
    if normalized_event.status == transactionEnums.TransactionStatus.FAILED.value:
        attempt.error_message = normalized_event.event
    else:
        attempt.error_message = None

    session.add(attempt)
    await session.commit()


async def _mark_transaction_pending_update(
    session: AsyncSession,
    transaction: Transaction,
    normalized_event: NormalizedWebhookEvent,
) -> Transaction:
    details = transaction.details if isinstance(transaction.details, dict) else {}
    details.update(
        {
            "last_webhook_gateway": normalized_event.gateway,
            "last_webhook_event": normalized_event.event,
            "last_webhook_status": normalized_event.status,
        }
    )
    transaction.details = details
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


async def handle_collection_success(
    session: AsyncSession,
    transaction: Transaction,
    processor_fee: float = 0.0,
) -> Transaction:
    if transaction.status != transactionEnums.TransactionStatus.PENDING.value:
        return transaction

    merchant: Merchant = transaction.merchant

    wallet = await walletService.get_or_create_wallet(
        session=session,
        merchant=merchant,
        currency=transaction.currency,
        mode=transaction.mode,
    )

    amount_charged = await walletService.get_payin_charge(wallet=wallet, amount=transaction.amount)
    processed_amount = transaction.amount - amount_charged
    transaction.charge = amount_charged
    transaction.wallet_id = wallet.id

    await walletService.credit_wallet(
        session=session,
        wallet=wallet,
        amount=processed_amount,
    )

    transaction.status = transactionEnums.TransactionStatus.SUCCESS.value
    transaction.processor_charge = processor_fee
    await transactionService.save_transaction(transaction=transaction, session=session)

    emailService.send_customer_receipt_email(transaction.id)
    emailService.send_merchant_receipt_email(transaction.id)
    return transaction


async def handle_payout_success(
    session: AsyncSession,
    transaction: Transaction,
    processor_fee: float = 0.0,
) -> Transaction:
    if transaction.status != transactionEnums.TransactionStatus.PENDING.value:
        return transaction

    merchant: Merchant = transaction.merchant
    wallet = await walletService.get_wallet(
        session=session,
        merchant_id=merchant.id,
        currency=transaction.currency,
        mode=transaction.mode,
    )

    if wallet:
        amount_charged = await walletService.get_payout_charge(wallet=wallet, amount=transaction.amount)
        transaction.charge = amount_charged
        await walletService.debit_wallet(
            session=session,
            wallet=wallet,
            amount=transaction.amount + amount_charged,
        )

    transaction.status = transactionEnums.TransactionStatus.SUCCESS.value
    transaction.processor_charge = processor_fee
    await transactionService.save_transaction(transaction=transaction, session=session)
    return transaction


async def _mark_transaction_failed(
    session: AsyncSession,
    transaction: Transaction,
    normalized_event: NormalizedWebhookEvent,
) -> Transaction:
    if transaction.status != transactionEnums.TransactionStatus.PENDING.value:
        return transaction

    transaction.status = transactionEnums.TransactionStatus.FAILED.value
    transaction.processor_charge = normalized_event.processor_fee
    reconciliationService.mark_for_reconciliation(
        transaction,
        reason=f"{normalized_event.gateway}:{normalized_event.event}",
    )
    await transactionService.save_transaction(transaction=transaction, session=session)
    return transaction


async def handle_event(
    gateway: str,
    payload: dict,
    session: AsyncSession,
) -> tuple[NormalizedWebhookEvent, Transaction | None]:
    normalized_event = normalize_event(gateway, payload)

    if normalized_event.status == "ignored" or not normalized_event.processor_reference:
        return normalized_event, None

    transaction = await transactionService.get_transaction_by_processor_reference(
        processor_reference=normalized_event.processor_reference,
        session=session,
    )
    if not transaction:
        return normalized_event, None

    if normalized_event.status == transactionEnums.TransactionStatus.SUCCESS.value:
        if normalized_event.operation == "collection":
            transaction = await handle_collection_success(
                session=session,
                transaction=transaction,
                processor_fee=normalized_event.processor_fee,
            )
        else:
            transaction = await handle_payout_success(
                session=session,
                transaction=transaction,
                processor_fee=normalized_event.processor_fee,
            )
    elif normalized_event.status == transactionEnums.TransactionStatus.FAILED.value:
        transaction = await _mark_transaction_failed(
            session=session,
            transaction=transaction,
            normalized_event=normalized_event,
        )
    elif normalized_event.status == transactionEnums.TransactionStatus.PENDING.value:
        transaction = await _mark_transaction_pending_update(
            session=session,
            transaction=transaction,
            normalized_event=normalized_event,
        )

    await _update_routing_attempt(
        session=session,
        transaction=transaction,
        normalized_event=normalized_event,
    )
    return normalized_event, transaction

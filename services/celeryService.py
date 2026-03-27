from celery import Celery, group, chord
from asgiref.sync import async_to_sync
from kombu import Queue
from settings import REDIS_URL
import requests
from external_services import koraService
from services import merchantService, transactionService, twilioService, receiptService, bulkpayoutService, gatewayHealthService
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from settings import DB_URL

# NullPool prevents asyncpg from holding connections after asyncio.run() closes
# the event loop, eliminating "Event loop is closed" RuntimeError in Celery workers.
_celery_engine = create_async_engine(DB_URL, poolclass=NullPool)
async_session = async_sessionmaker(bind=_celery_engine, expire_on_commit=False, class_=AsyncSession)
from enums import transactionEnums, BulkPayoutEnums, tokenEnums
from enums.BulkPayoutEnums import BulkPayoutTransactionKeys, BulkPayoutStatusMessage
from database.models.Transaction import Transaction
from database.models.BulkPayout import BulkPayout
from lib import bank
import asyncio
import logging
from sqlalchemy import update, literal, func, cast
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)

# ==========================
# Celery setup
# ==========================
celery_app = Celery(
    "bulk_payouts",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.task_queues = (
    Queue("default"),
    Queue("expiry_queue"),
    Queue("payout_queue"),
    Queue("webhook_queue"),
)
celery_app.conf.task_routes = {
    "services.celeryService.expire_transaction": {"queue": "expiry_queue"},
    "services.celeryService.process_bulk_payout_batch": {"queue": "payout_queue"},
    "services.celeryService.schedule_bulk_payouts": {"queue": "payout_queue"},
    "services.celeryService.refresh_gateway_health_snapshots_task": {"queue": "default"},
    "services.celeryService.send_webhook_task": {"queue": "webhook_queue"},
}
celery_app.conf.task_default_queue = "default"
celery_app.conf.beat_schedule = {
    "refresh-gateway-health-snapshots": {
        "task": "services.celeryService.refresh_gateway_health_snapshots_task",
        "schedule": 60.0,
    },
}

_PAYOUT_BATCH_SIZE = 10  # process payouts in batches of 10 concurrently

# ==========================
# Bulk payout tasks
# ==========================


@celery_app.task(bind=True, max_retries=2)
def refresh_gateway_health_snapshots_task(self):
    try:
        asyncio.run(_refresh_gateway_health_snapshots())
    except Exception as exc:
        logger.exception("Failed to refresh gateway health snapshots")
        raise self.retry(exc=exc, countdown=30)


async def _refresh_gateway_health_snapshots():
    async with async_session() as session:
        snapshots = await gatewayHealthService.refresh_gateway_health_snapshots(session)
        logger.info("Refreshed %s gateway health snapshot(s)", len(snapshots))

@celery_app.task(bind=True, max_retries=3)
def schedule_bulk_payouts(self, merchant_id: str, records: list[dict], bulk_id: int = None, mode: str = None):
    """
    Splits records into batches of _PAYOUT_BATCH_SIZE and dispatches each batch
    as a single Celery task. Each batch task processes its records concurrently
    using asyncio.gather inside the worker.
    """
    logger.info(f"Scheduling {len(records)} payouts for merchant_id={merchant_id}, bulk_id={bulk_id}")
    try:
        batches = [
            records[i:i + _PAYOUT_BATCH_SIZE]
            for i in range(0, len(records), _PAYOUT_BATCH_SIZE)
        ]
        job = group(
            process_bulk_payout_batch.s(merchant_id, batch, bulk_id, mode)
            for batch in batches
        )
        job.apply_async()
        logger.info(f"Dispatched {len(batches)} batch(es) of up to {_PAYOUT_BATCH_SIZE} payouts each")
    except Exception as exc:
        logger.exception("Failed to schedule bulk payouts")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=2)
def process_bulk_payout_batch(self, merchant_id: str, records: list[dict], bulk_id: int = None, mode: str = None):
    """
    Processes a batch of payout records concurrently using asyncio.gather.
    All records in the batch run in parallel within this single worker task.
    """
    try:
        asyncio.run(_process_payout_batch(merchant_id, records, bulk_id, mode))
    except Exception as exc:
        logger.exception(f"Batch failed for bulk_id={bulk_id}, retrying")
        raise self.retry(exc=exc, countdown=30)


async def _process_payout_batch(merchant_id: str, records: list[dict], bulk_id: int = None, mode: str = None):
    """Runs all records in the batch concurrently, then updates bulk payout status."""
    await asyncio.gather(
        *[_process_single_payout(merchant_id, record, bulk_id, mode) for record in records],
        return_exceptions=True  # don't let one failure cancel the rest
    )

    if not bulk_id:
        return

    # After all payouts in this batch are done, recalculate and persist bulk payout status
    async with async_session() as session:
        bulk_payout = await bulkpayoutService.get_bulk_payout_by_id(session=session, payout_id=bulk_id)
        if bulk_payout:
            await bulkpayoutService.transaction_based_update(session=session, bulk_payout=bulk_payout)


async def _process_single_payout(merchant_id: str, record: dict, bulk_id: int = None, mode: str = None):
    """Async function that handles a single payout with notifications."""

    async with async_session() as session:
        merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
        if not merchant:
            logger.error(f"Merchant {merchant_id} not found")
            return

        if bulk_id:
            bulk_payout = await bulkpayoutService.get_bulk_payout_by_id(session=session, payout_id=bulk_id)
            if not bulk_payout:
                logger.error(f"Bulk payout {bulk_id} not found")
                return

        customer = record["customer"]
        bank_obj = bank.find_bank_by_slug(slug=customer["bank_slug"])
        reference = await transactionService.generate_processor_reference(session=session)

        logger.info(f"Payout: {customer['account_number']} ({bank_obj.name}) → {record['amount']}")

        # Perform the actual payout
        status, message, http_status, txn_id = await koraService.payout(
            session=session,
            merchant=merchant,
            acc_number=customer["account_number"],
            bank_code=bank_obj.code,
            reference=reference,
            amount=record["amount"],
            email=customer.get("email"),
            mode=tokenEnums.TokenMode.TEST if not mode else mode,
            currency=record.get("currency"),
            narration=record.get("narration") or f"{merchant.name} payout"
        )

        # Save transaction details into the bulk payout JSONB array atomically
        transaction_details = {
            BulkPayoutTransactionKeys.TXN_ID: txn_id,
            BulkPayoutTransactionKeys.STATUS: status,
            BulkPayoutTransactionKeys.MESSAGE: message,
            BulkPayoutTransactionKeys.HTTP_STATUS: http_status,
            BulkPayoutTransactionKeys.TXN_STATUS: transactionEnums.TransactionStatus.SUCCESS.value if http_status == 200 else transactionEnums.TransactionStatus.FAILED.value,
            BulkPayoutTransactionKeys.TXN_MESSAGE: BulkPayoutStatusMessage.SUCCESS if http_status == 200 else BulkPayoutStatusMessage.FAILED
        }

        await session.execute(
            update(BulkPayout)
            .where(BulkPayout.id == bulk_id)
            .values(
                transaction_details=(
                    func.coalesce(BulkPayout.transaction_details, cast([], JSONB))
                    + cast([transaction_details], JSONB)
                )
            )
        )
        await session.commit()

        # Link the transaction to the bulk payout
        await bulkpayoutService.add_transaction_to_payout(session=session, payout=bulk_payout, transaction_id=txn_id)

        # Notifications
        phone_number = customer.get("phone_number")
        try:
            if phone_number:
                txn = await transactionService.get_transaction_by_id_loaded(session=session, id=txn_id)
                sms_text = receiptService.generate_customer_receipt_text(transaction=txn)
                twilioService.send_sms(phone_number=phone_number, text=sms_text)
        except Exception as e:
            logger.warning(f"Notification failed for txn {txn_id}: {e}")

        logger.info(f"Payout processed: txn_id={txn_id} status={status}")


# ==========================
# Transaction expiry task
# ==========================
@celery_app.task(bind=True, max_retries=3)
def expire_transaction(self, tx_id: str):
    try:
        asyncio.run(_expire_transaction(tx_id))
    except Exception as exc:
        self.retry(exc=exc, countdown=10)


async def _expire_transaction(tx_id: str):
    async with async_session() as session:
        tx = await session.get(Transaction, tx_id)
        if not tx:
            logger.warning(f"Transaction {tx_id} not found for expiry")
            return
        if tx.status not in [transactionEnums.TransactionStatus.SUCCESS, transactionEnums.TransactionStatus.FAILED]:
            tx.status = transactionEnums.TransactionStatus.ABANDONED
            await session.commit()
            logger.info(f"Transaction {tx_id} marked as abandoned")
        else:
            logger.info(f"Transaction {tx_id} already {tx.status}, skipping expiry")


# ==========================
# Webhook delivery task (DEPRECATED — moved to asyncio.create_task in webhookService.py)
# ==========================
# _WEBHOOK_RETRY_COUNTDOWNS = [0, 300, 900]  # immediately, 5min, 15min
#
# @celery_app.task(bind=True, max_retries=2)
# def send_webhook_task(self, url: str, payload_str: str, headers: dict, event_type: str):
#     try:
#         response = requests.post(url, data=payload_str.encode("utf-8"), headers=headers, timeout=10)
#         if response.status_code < 200 or response.status_code >= 300:
#             raise ValueError(f"Non-2xx response: {response.status_code}")
#         logger.info("Webhook delivered: event=%s url=%s status=%s", event_type, url, response.status_code)
#     except Exception as exc:
#         attempt = self.request.retries
#         next_retry = attempt + 1
#         if next_retry <= self.max_retries:
#             countdown = _WEBHOOK_RETRY_COUNTDOWNS[next_retry]
#             logger.warning("Webhook failed (attempt %s/%s), retrying in %ss: %s",
#                            attempt + 1, self.max_retries + 1, countdown, exc)
#             raise self.retry(exc=exc, countdown=countdown)
#         logger.error("Webhook permanently failed after %s attempts: event=%s url=%s",
#                      self.max_retries + 1, event_type, url)

_WEBHOOK_RETRY_COUNTDOWNS = [0, 5, 15]


@celery_app.task(bind=True, max_retries=2)
def send_webhook_task(self, url: str, payload_str: str, headers: dict, event_type: str):
    try:
        response = requests.post(
            url,
            data=payload_str.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise ValueError(f"Non-2xx response: {response.status_code}")

        logger.info(
            "Webhook delivered: event=%s url=%s status=%s",
            event_type,
            url,
            response.status_code,
        )
    except Exception as exc:
        attempt = self.request.retries
        next_retry = attempt + 1
        if next_retry <= self.max_retries:
            countdown = _WEBHOOK_RETRY_COUNTDOWNS[next_retry]
            logger.warning(
                "Webhook failed (attempt %s/%s), retrying in %ss: %s",
                attempt + 1,
                self.max_retries + 1,
                countdown,
                exc,
            )
            raise self.retry(exc=exc, countdown=countdown)

        logger.error(
            "Webhook permanently failed after %s attempts: event=%s url=%s",
            self.max_retries + 1,
            event_type,
            url,
        )

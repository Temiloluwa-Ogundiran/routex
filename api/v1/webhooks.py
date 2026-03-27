from fastapi import FastAPI, Request, HTTPException, status, APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import hmac
import hashlib
import logging
import os
from settings import KORA_SECRET, PAYSTACK_SECRET, FLTW_SECRET_KEY, FLTW_SECRET_HASH, BASQET_LIVE_SECRET, BASQET_SECRET, INTERSWITCH_SECRET_KEY
from services import transactionService, merchantService, tokenService, bulkpayoutService, walletService, emailService, webhookService
import services.webhookNormalizationService as webhookNormalizationService
from enums import transactionEnums, tokenEnums, eventEnums
from enums.BulkPayoutEnums import BulkPayoutTransactionKeys
from database.models.Merchant import *
from database.models.Transaction import *
from database.models.BulkPayout import *
import decimal
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from websocket.broadcast import broadcast

webhook_router = APIRouter()
webhook_util_router = APIRouter()
logger = logging.getLogger(__name__)


def _get_interswitch_secret() -> str | None:
    return os.getenv("INTERSWITCH_SECRET_KEY") or INTERSWITCH_SECRET_KEY


async def _dispatch_merchant_webhook(
    session: AsyncSession,
    transaction: Transaction | None,
    normalized_event,
) -> None:
    if not transaction:
        logger.warning(
            "Skipping merchant webhook dispatch: gateway=%s event=%s reason=no_transaction",
            normalized_event.gateway,
            normalized_event.event,
        )
        return

    if not transaction.notification_url:
        logger.info(
            "Skipping merchant webhook dispatch: ref=%s reason=no_notification_url",
            transaction.reference,
        )
        return

    if normalized_event.status == transactionEnums.TransactionStatus.SUCCESS.value:
        outgoing_event = eventEnums.EventType.CHARGE_SUCCESS
    elif normalized_event.status == transactionEnums.TransactionStatus.FAILED.value:
        outgoing_event = eventEnums.EventType.CHARGE_FAILED
    else:
        logger.info(
            "Skipping merchant webhook dispatch: ref=%s status=%s",
            transaction.reference,
            normalized_event.status,
        )
        return

    token_obj = await tokenService.get_token_obj(
        session=session,
        merchant=transaction.merchant,
        mode=transaction.mode,
    )
    webhookService.dispatch(
        transaction=transaction,
        event=outgoing_event,
        token=token_obj,
    )
    logger.info(
        "Merchant webhook queued: gateway=%s ref=%s event=%s",
        normalized_event.gateway,
        transaction.reference,
        outgoing_event.value,
    )


async def _handle_interswitch_webhook(
    request: Request,
    session: AsyncSession,
) -> Response:
    secret = _get_interswitch_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="Interswitch webhook secret is not configured")

    signature = request.headers.get("X-Interswitch-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    raw_body = await request.body()
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    normalized_event, transaction = await webhookNormalizationService.handle_event(
        gateway="isw",
        payload=payload,
        session=session,
    )

    await _dispatch_merchant_webhook(
        session=session,
        transaction=transaction,
        normalized_event=normalized_event,
    )

    return Response(status_code=200)


# ── Merchant webhook verification test ───────────────────────────────────────

class WebhookTestRequest(BaseModel):
    secret_key: str  # full secret token e.g. aggsk_test_<SECRET>_<MERCHANT_ID>
    payload: dict | None = None  # optional custom payload; uses sample charge.completed if omitted

def _extract_raw_secret(full_token: str) -> str:
    """
    Parses the raw HMAC secret from the full token string.
    Format: aggsk_{mode}_{raw_secret}_{merchant_id}
    The raw_secret is everything between the second and last underscore segments.
    """
    parts = full_token.split("_")
    # parts: ['aggsk', 'test'|'live', '<secret>', '<merchant_id>']
    # merchant_id itself may contain hyphens but not underscores; secret is a 64-char hex
    if len(parts) < 4:
        raise ValueError("Invalid token format")
    # raw secret is parts[2], merchant_id is parts[3]
    return parts[2]

@webhook_util_router.post("/webhook/test-signature", tags=["Webhooks"])
async def test_webhook_signature(body: WebhookTestRequest):
    """
    Generate a signed webhook payload using your full secret key and verify it —
    exactly as your merchant server should do.

    Pass your full secret token (e.g. aggsk_test_xxxxx_merchant_id).
    The raw HMAC secret is extracted automatically.

    Returns the payload string, the signature to expect in X-AGGREGATOR-SIGNATURE,
    and a tamper test confirming a wrong secret is rejected.
    """
    import hmac as _hmac
    import hashlib as _hashlib

    try:
        raw_secret = _extract_raw_secret(body.secret_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sample_payload = body.payload or {
        "event": "charge.completed",
        "reference": "TXN-TEST-001",
        "data": {
            "customer": {"email": "test@example.com"},
            "amount": 5000.0,
            "reference": "TXN-TEST-001",
            "currency": "NGN",
            "metadata": None,
        },
    }

    payload_str = json.dumps(sample_payload, separators=(",", ":"), sort_keys=True)
    raw_body = payload_str.encode()

    signature = _hmac.new(raw_secret.encode(), raw_body, _hashlib.sha256).hexdigest()

    # Tamper check: a wrong secret must produce a different signature
    tampered_sig = _hmac.new(b"wrong-secret", raw_body, _hashlib.sha256).hexdigest()
    tamper_rejected = not _hmac.compare_digest(tampered_sig, signature)

    return {
        "payload_str": payload_str,
        "signature": signature,
        "headers": {
            "X-AGGREGATOR-SIGNATURE": signature,
        },
        "tamper_test_rejected": tamper_rejected,
        "merchant_verification_code": (
            "import hmac, hashlib\n"
            "raw_body = request.get_data()  # raw bytes before calling request.json\n"
            f"secret = \"{raw_secret}\"\n"
            "expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()\n"
            "is_valid = hmac.compare_digest(expected, request.headers['X-AGGREGATOR-SIGNATURE'])"
        ),
    }

@webhook_router.post("/kora/webhook/test")
async def kora_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    # Signature Verification
    sig_header = request.headers.get("X-KORAPAY-SIGNATURE")
    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header")

    try:
        raw_body = await request.body()
        payload_dict = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    data_bytes = json.dumps(payload_dict.get("data", {}), separators=(",", ":")).encode("utf-8")
    expected_sig = hmac.new(KORA_SECRET.encode(), data_bytes, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig_header, expected_sig):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    normalized_event, transaction = await webhookNormalizationService.handle_event(
        gateway="kora",
        payload=payload_dict,
        session=session,
    )
    if not transaction:
        return {"status": "ignored"}

    token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)

    if transaction.bulk_payout_id:
        bulk_payout:BulkPayout = await bulkpayoutService.get_bulk_payout_by_id(transaction.bulk_payout_id, session= session)
        transaction_details: list= bulk_payout.transaction_details
        transaction_index = next((i for i, item in enumerate(transaction_details) if item[BulkPayoutTransactionKeys.TXN_ID] == transaction.id), -1)
        
    if normalized_event.operation == "collection" and normalized_event.status == transactionEnums.TransactionStatus.SUCCESS.value:
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

    elif normalized_event.operation == "collection" and normalized_event.status == transactionEnums.TransactionStatus.FAILED.value:
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_FAILED, token=token_obj)

    elif normalized_event.operation == "payout" and normalized_event.status == transactionEnums.TransactionStatus.SUCCESS.value:
        if transaction.bulk_payout_id:
            txn_detail: dict=  transaction_details[transaction_index]
            txn_detail[BulkPayoutTransactionKeys.TXN_STATUS] = TransactionStatus.SUCCESS
            txn_detail[BulkPayoutTransactionKeys.TXN_MESSAGE] = "Successful transfer"
            transaction_details[transaction_index] = txn_detail
            bulk_payout.transaction_details = transaction_details
            await bulkpayoutService.save_bulk_payout_obj(bulk_payout= bulk_payout, session= session)

        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.TRANSFER_SUCCESS, token=token_obj)

    elif normalized_event.operation == "payout" and normalized_event.status == transactionEnums.TransactionStatus.FAILED.value:
        if transaction.bulk_payout_id:
            txn_detail: dict=  transaction_details[transaction_index]
            txn_detail[BulkPayoutTransactionKeys.TXN_STATUS] = TransactionStatus.FAILED
            txn_detail[BulkPayoutTransactionKeys.TXN_MESSAGE] = "Failed transfer"
            transaction_details[transaction_index] = txn_detail
            bulk_payout.transaction_details = transaction_details
            await bulkpayoutService.save_bulk_payout_obj(bulk_payout= bulk_payout, session= session)

        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.TRANSFER_FAILED, token=token_obj)

    if transaction.bulk_payout_id:
        statuses = [item[BulkPayoutTransactionKeys.TXN_STATUS] for item in transaction_details]

        if all(status == TransactionStatus.SUCCESS for status in statuses):
            bulk_payout.status = BulkPayoutStatus.SUCCESSFUL
        elif all(status == TransactionStatus.FAILED for status in statuses):
            bulk_payout.status = BulkPayoutStatus.FAILED
        else:
            bulk_payout.status = BulkPayoutStatus.PARTIAL
            
        await bulkpayoutService.save_bulk_payout_obj(bulk_payout=bulk_payout, session=session)
        
    return {"status": "success"}

@webhook_router.post("/kora/webhook/live")
async def kora_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    # Signature Verification
    sig_header = request.headers.get("X-KORAPAY-SIGNATURE")
    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header")

    try:
        raw_body = await request.body()
        payload_dict = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    data_bytes = json.dumps(payload_dict.get("data", {}), separators=(",", ":")).encode("utf-8")
    expected_sig = hmac.new(KORA_SECRET.encode(), data_bytes, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig_header, expected_sig):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    normalized_event, transaction = await webhookNormalizationService.handle_event(
        gateway="kora",
        payload=payload_dict,
        session=session,
    )
    if not transaction:
        return {"status": "ignored"}

    token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)

    if transaction.bulk_payout_id:
        bulk_payout:BulkPayout = await bulkpayoutService.get_bulk_payout_by_id(transaction.bulk_payout_id, session= session)
        transaction_details: list= bulk_payout.transaction_details
        transaction_index = next((i for i, item in enumerate(transaction_details) if item[BulkPayoutTransactionKeys.TXN_ID] == transaction.id), -1)

    if normalized_event.operation == "collection" and normalized_event.status == transactionEnums.TransactionStatus.SUCCESS.value:
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

    elif normalized_event.operation == "collection" and normalized_event.status == transactionEnums.TransactionStatus.FAILED.value:
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_FAILED, token=token_obj)

    elif normalized_event.operation == "payout" and normalized_event.status == transactionEnums.TransactionStatus.SUCCESS.value:
        if transaction.bulk_payout_id:
            txn_detail: dict=  transaction_details[transaction_index]
            txn_detail[BulkPayoutTransactionKeys.TXN_STATUS] = TransactionStatus.SUCCESS
            txn_detail[BulkPayoutTransactionKeys.TXN_MESSAGE] = "Successful transfer"
            transaction_details[transaction_index] = txn_detail
            bulk_payout.transaction_details = transaction_details
            await bulkpayoutService.save_bulk_payout_obj(bulk_payout= bulk_payout, session= session)

        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.TRANSFER_SUCCESS, token=token_obj)

    elif normalized_event.operation == "payout" and normalized_event.status == transactionEnums.TransactionStatus.FAILED.value:
        if transaction.bulk_payout_id:
            txn_detail: dict=  transaction_details[transaction_index]
            txn_detail[BulkPayoutTransactionKeys.TXN_STATUS] = TransactionStatus.FAILED
            txn_detail[BulkPayoutTransactionKeys.TXN_MESSAGE] = "Failed transfer"
            transaction_details[transaction_index] = txn_detail
            bulk_payout.transaction_details = transaction_details
            await bulkpayoutService.save_bulk_payout_obj(bulk_payout= bulk_payout, session= session)

        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.TRANSFER_FAILED, token=token_obj)

    if transaction.bulk_payout_id:
        statuses = [item[BulkPayoutTransactionKeys.TXN_STATUS] for item in transaction_details]

        if all(status == TransactionStatus.SUCCESS for status in statuses):
            bulk_payout.status = BulkPayoutStatus.SUCCESSFUL
        elif all(status == TransactionStatus.FAILED for status in statuses):
            bulk_payout.status = BulkPayoutStatus.FAILED
        else:
            bulk_payout.status = BulkPayoutStatus.PARTIAL
            
        await bulkpayoutService.save_bulk_payout_obj(bulk_payout=bulk_payout, session=session)

    return {"status": "success"}

@webhook_router.post("/paystack/webhook/test")
async def paystack_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    sig_header = request.headers.get('X-Paystack-Signature')
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature header")

    body = await request.body()
    computed_sig = hmac.new(PAYSTACK_SECRET.encode(), body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(sig_header, computed_sig):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body)
    normalized_event, transaction = await webhookNormalizationService.handle_event(
        gateway="pstk",
        payload=payload,
        session=session,
    )
    await _dispatch_merchant_webhook(
        session=session,
        transaction=transaction,
        normalized_event=normalized_event,
    )

    return {"status": "success"}


@webhook_router.post("/flutterwave/webhook/test")
async def flutterwave_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    signature = request.headers.get("verif-hash")
    if not signature or signature != FLTW_SECRET_HASH:
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = await request.body()
    payload = json.loads(body)
    normalized_event, transaction = await webhookNormalizationService.handle_event(
        gateway="fltw",
        payload=payload,
        session=session,
    )

    await _dispatch_merchant_webhook(
        session=session,
        transaction=transaction,
        normalized_event=normalized_event,
    )

    return {"status": "success"}


@webhook_router.post("/interswitch/webhook/test")
async def interswitch_webhook_test(request: Request, session: AsyncSession = Depends(get_async_session)):
    return await _handle_interswitch_webhook(request=request, session=session)


@webhook_router.post("/interswitch/webhook/live")
async def interswitch_webhook_live(request: Request, session: AsyncSession = Depends(get_async_session)):
    return await _handle_interswitch_webhook(request=request, session=session)


@webhook_router.post("/basqet/webhook/test")
async def basqet_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    payload = await request.json()

    # Compute HMAC SHA512
    computed_hash = hmac.new(BASQET_SECRET.encode(), json.dumps(payload).encode(), hashlib.sha512).hexdigest()

    basqet_signature = request.headers.get("basqetSignature")
    if not basqet_signature:
        raise HTTPException(status_code=400, detail="Missing basqetSignature header")
    
    # Compare signatures
    # if not computed_hash == basqet_signature:
    #     raise HTTPException(status_code=401, detail="Invalid signature")
    
    if not payload['event'] == "payment.recieved":
        return {"status": "ok"}
    
    basqet_reference = payload['data']['reference']
    transaction = await transactionService.get_transaction_by_processor_reference(processor_reference= basqet_reference, session=session)

    
    await payin_success_handler(transaction= transaction, session=session)
    if transaction.notification_url:
        token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

@webhook_router.post("/basqet/webhook/live")
async def basqet_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    payload = await request.json()

    # Compute HMAC SHA512
    computed_hash = hmac.new(BASQET_LIVE_SECRET.encode(), json.dumps(payload).encode(), hashlib.sha512).hexdigest()

    basqet_signature = request.headers.get("basqetSignature")
    if not basqet_signature:
        raise HTTPException(status_code=400, detail="Missing basqetSignature header")
    
    # Compare signatures
    if not computed_hash == basqet_signature:
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    if not payload['event'] == "payment.recieved":
        return {"status": "ok"}
    
    basqet_reference = payload['data']['reference']
    transaction = await transactionService.get_transaction_by_processor_reference(processor_reference= basqet_reference, session=session)

    
    await payin_success_handler(transaction= transaction, session=session)
    if transaction.notification_url:
        token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

        
async def payin_success_handler(session: AsyncSession, transaction:Transaction, processor_fee: float = 0):
    return await webhookNormalizationService.handle_collection_success(
        session=session,
        transaction=transaction,
        processor_fee=processor_fee,
    )

async def payout_success_handler(session: AsyncSession, processor_reference:str, processor_fee: float, mode:str = tokenEnums.TokenMode.TEST):
    transaction: Transaction = await transactionService.get_transaction_by_processor_reference(processor_reference= processor_reference, session= session)
    if not transaction:
        return
    return await webhookNormalizationService.handle_payout_success(
        session=session,
        transaction=transaction,
        processor_fee=processor_fee,
    )
# await handle_


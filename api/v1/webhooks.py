from fastapi import FastAPI, Request, HTTPException, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import hmac
import hashlib
from settings import KORA_SECRET, PAYSTACK_SECRET, FLTW_SECRET_KEY, FLTW_SECRET_HASH, KORA_LIVE_SECRET_KEY, BASQET_LIVE_SECRET, BASQET_SECRET
from services import transactionService, merchantService, tokenService, bulkpayoutService, walletService, emailService, webhookService
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
            "X-XOROPAY-SIGNATURE": signature,
        },
        "tamper_test_rejected": tamper_rejected,
        "merchant_verification_code": (
            "import hmac, hashlib\n"
            "raw_body = request.get_data()  # raw bytes before calling request.json\n"
            f"secret = \"{raw_secret}\"\n"
            "expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()\n"
            "# check either header:\n"
            "is_valid = hmac.compare_digest(expected, request.headers.get('X-XOROPAY-SIGNATURE') or request.headers.get('X-AGGREGATOR-SIGNATURE'))"
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

    # Handle Event
    event = payload_dict.get("event")
    print("✅ Kora webhook received!")
    print("Event:", event)
    print("Payload:", payload_dict)

    reference = payload_dict.get("data", {}).get("reference")
    processor_charge =  payload_dict.get("data", {}).get("fee")
    transaction = await transactionService.get_transaction_by_processor_reference(processor_reference=reference, session=session)
    token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)

    if transaction.bulk_payout_id:
        bulk_payout:BulkPayout = await bulkpayoutService.get_bulk_payout_by_id(transaction.bulk_payout_id, session= session)
        transaction_details: list= bulk_payout.transaction_details
        transaction_index = next((i for i, item in enumerate(transaction_details) if item[BulkPayoutTransactionKeys.TXN_ID] == transaction.id), -1)
        
    # Switch based on event type
    if event == "charge.success":
        await payin_success_handler(transaction= transaction, session=session, processor_fee= processor_charge)
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

    elif event == "charge.failed":
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_FAILED, token=token_obj)

    elif event == "transfer.success":
        if transaction.bulk_payout_id:
            txn_detail: dict=  transaction_details[transaction_index]
            txn_detail[BulkPayoutTransactionKeys.TXN_STATUS] = TransactionStatus.SUCCESS
            txn_detail[BulkPayoutTransactionKeys.TXN_MESSAGE] = "Successful transfer"
            transaction_details[transaction_index] = txn_detail
            bulk_payout.transaction_details = transaction_details
            await bulkpayoutService.save_bulk_payout_obj(bulk_payout= bulk_payout, session= session)

        await payout_success_handler(processor_reference=reference, session=session, processor_fee= processor_charge)
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.TRANSFER_SUCCESS, token=token_obj)

    elif event == "transfer.failed":
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
    expected_sig = hmac.new(KORA_LIVE_SECRET_KEY.encode(), data_bytes, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig_header, expected_sig):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    # Handle Event
    event = payload_dict.get("event")
    print("✅ Kora webhook received!")
    print("Event:", event)
    print("Payload:", payload_dict)

    reference = payload_dict.get("data", {}).get("reference")
    processor_charge =  payload_dict.get("data", {}).get("fee")

    transaction = await transactionService.get_transaction_by_processor_reference(processor_reference=reference, session=session)
    token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)
    # Switch based on event type
    #TODO: save transaction  dtatus for failed events

    if transaction.bulk_payout_id:
        bulk_payout:BulkPayout = await bulkpayoutService.get_bulk_payout_by_id(transaction.bulk_payout_id, session= session)
        transaction_details: list= bulk_payout.transaction_details
        transaction_index = next((i for i, item in enumerate(transaction_details) if item[BulkPayoutTransactionKeys.TXN_ID] == transaction.id), -1)

    if event == "charge.success":
        await payin_success_handler(transaction= transaction, session=session, processor_fee= processor_charge)
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

    elif event == "charge.failed":
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_FAILED, token=token_obj)

    elif event == "transfer.success":
        if transaction.bulk_payout_id:
            txn_detail: dict=  transaction_details[transaction_index]
            txn_detail[BulkPayoutTransactionKeys.TXN_STATUS] = TransactionStatus.SUCCESS
            txn_detail[BulkPayoutTransactionKeys.TXN_MESSAGE] = "Successful transfer"
            transaction_details[transaction_index] = txn_detail
            bulk_payout.transaction_details = transaction_details
            await bulkpayoutService.save_bulk_payout_obj(bulk_payout= bulk_payout, session= session)

        await payout_success_handler(processor_reference=reference, session=session, processor_fee= processor_charge)
        webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.TRANSFER_SUCCESS, token=token_obj)

    elif event == "transfer.failed":
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
    event = payload.get("event")
    reference = payload.get("data", {}).get("reference")
    processor_charge =  payload.get("data", {}).get("fees")
    processor_charge = float(processor_charge) / 100 #change to local currency

    print(payload)
    print(f"paystack reference: {reference}")

    print(f"✅ Paystack webhook received! Event: {event} Ref: {reference}")
    transaction = await transactionService.get_transaction_by_processor_reference(processor_reference=reference, session=session)

    if event == "charge.success":
        await payin_success_handler(transaction= transaction, session=session, processor_fee= processor_charge)

        if transaction.notification_url:
            token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)

            webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

    return {"status": "success"}


@webhook_router.post("/flutterwave/webhook/test")
async def flutterwave_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    signature = request.headers.get("verif-hash")
    if not signature or signature != FLTW_SECRET_HASH:
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = await request.body()
    payload = json.loads(body)
    data = payload.get("data", {})
    reference = data.get("tx_ref")
    processor_charge =  payload.get("data", {}).get("app_fee")

    print(f"✅ Flutterwave webhook received! Ref: {reference}")

    if data.get("status", "").lower() == "successful":

        transaction = await transactionService.get_transaction_by_processor_reference(processor_reference= reference, session=session)
        await payin_success_handler(transaction= transaction, session=session, processor_fee= processor_charge)

        if transaction.notification_url:
            token_obj = await tokenService.get_token_obj(session= session, merchant= transaction.merchant, mode= transaction.mode)

            webhookService.dispatch(transaction=transaction, event=eventEnums.EventType.CHARGE_SUCCESS, token=token_obj)

    return {"status": "success"}


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

    if not transaction.status == transactionEnums.TransactionStatus.PENDING.value: #indempotence
        return
    merchant: Merchant = transaction.merchant
    mode = transaction.mode

    # Get or create wallet for this transaction
    wallet = await walletService.get_or_create_wallet(
        session=session,
        merchant=merchant,
        currency=transaction.currency,
        mode=mode
    )

    # Calculate charge using wallet's charge configuration
    amount_charged = await walletService.get_payin_charge(wallet=wallet, amount=transaction.amount)
    processed_amount = transaction.amount - amount_charged
    transaction.charge = amount_charged
    transaction.wallet_id = wallet.id  # Link transaction to wallet

    # Credit wallet with processed amount
    await walletService.credit_wallet(
        session=session,
        wallet=wallet,
        amount=processed_amount
    )

    transaction.status = transactionEnums.TransactionStatus.SUCCESS.value
    transaction.processor_charge = processor_fee
    await transactionService.save_transaction(transaction= transaction, session= session)

    try:
        print("Starting broadcast")
        # await broadcast.publish(
        #     channel=f"merchant_{merchant.id}",
        #     message= await transactionService.get_transaction_socket_data(
        #         merchant= merchant,
        #         transaction= transaction
        #     )
        # )
        emailService.send_customer_receipt_email(transaction.id)
        emailService.send_merchant_receipt_email(transaction.id)
    except Exception as e:
        print(f"Error occurred when sending broadcast: {e}")

    return
    print("Mmerchant and transaction updated")

async def payout_success_handler(session: AsyncSession, processor_reference:str, processor_fee: float, mode:str = tokenEnums.TokenMode.TEST):
    transaction: Transaction = await transactionService.get_transaction_by_processor_reference(processor_reference= processor_reference, session= session)
    if not transaction.status == transactionEnums.TransactionStatus.PENDING.value: #indempotence
        return
    merchant: Merchant = transaction.merchant

    # Get wallet for this transaction
    wallet = await walletService.get_wallet(
        session=session,
        merchant_id=merchant.id,
        currency=transaction.currency,
        mode=transaction.mode
    )

    if wallet:
        # Calculate payout charge using wallet's charge configuration
        amount_charged = await walletService.get_payout_charge(wallet=wallet, amount=transaction.amount)
        transaction.charge = amount_charged

        # Debit wallet with total amount (transaction amount + charge)
        total_debit = transaction.amount + amount_charged
        await walletService.debit_wallet(session=session, wallet=wallet, amount=total_debit)

    transaction.status = transactionEnums.TransactionStatus.SUCCESS.value
    await transactionService.save_transaction(transaction= transaction, session= session)

    try:
        # await broadcast.publish(
        #     channel=f"merchant_{merchant.id}",
        #     message= await transactionService.get_transaction_socket_data(
        #         merchant= merchant,
        #         transaction= transaction
        #     )
        # )
        pass
    except:
        pass

    return
# await handle_


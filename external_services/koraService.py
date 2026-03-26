from settings import KORA_SECRET, SERVER_URL, PROXY_URL, PROXY_USERNAME, PROXY_PASSWORD, logging, AGG_EMAIL, FRONTEND_BASE_URL
from services.httpRequestService import post_request
from enums.transactionEnums import *
from services import transactionService, merchantService, customerService, bulkpayoutService, celeryService, walletService, emailService
from enums.transactionEnums import TransactionCurrency
from database.models.Merchant import Merchant
from database.models.Transaction import Transaction
from database.models.BulkPayout import BulkPayout
from enums.BulkPayoutEnums import BulkPayoutTransactionKeys, BulkPayoutStatus, BulkPayoutStatusMessage
from sqlalchemy.ext.asyncio import AsyncSession
from lib.bank import Bank
from lib import bank
from enums import tokenEnums, transactionEnums
import json
from websocket.broadcast import broadcast
from datetime import datetime, timezone

BASE_URL = 'https://api.korapay.com/merchant/api/v1/'
DEFAULT_HEADERS = {
    'Authorization': f'Bearer {KORA_SECRET}',
    'Content-Type': 'application/json'
}

# TRANSACTION_MODE_TO_KORA_CHANNEL_MAP = {
#     TransactionMode.CARD.value: 'card',
#     TransactionMode.TRANSFER.value: 'bank_transfer'
# }

async def _get_wallet_payin_charge(session: AsyncSession, merchant: Merchant, currency: str, mode: str, amount: float) -> float:
    """Helper function to get payin charge from wallet."""
    wallet = await walletService.get_or_create_wallet(
        session=session,
        merchant=merchant,
        currency=currency,
        mode=mode
    )
    return await walletService.get_payin_charge(wallet=wallet, amount=amount)

async def resolve_account(acc_number: str, bank: Bank, currency: str = None) -> tuple[bool, str]:
    url = BASE_URL + 'misc/banks/resolve'
    currency = currency or "NGN"
    local_headers = DEFAULT_HEADERS.copy()
    data = {"account": acc_number, 'bank': bank.code, 'currency': currency}
    print(f"Resolve account payload: {json.dumps(data, indent=2)}")

    response, status = await post_request(url=url, data=json.dumps(data), headers= local_headers)
    if status == 200:
        return True, response.get('data', {}).get('account_name')
    elif status != 500:
        return False, response.get("message")
    else:
        return False, "Internal server error"

async def initialize(session: AsyncSession, email: str, amount: float, merchant: Merchant, mode: str, reference: str,
                     currency: str = TransactionCurrency.NIGERIA.value, redirect_url: str | None = None,
                     notification_url: str | None = None, merchant_bears_cost: bool = True,
                     narration: str | None = None, metadata: dict | None = None) -> tuple[dict, int, str | None]:
    url = BASE_URL + 'charges/initialize'
    local_headers = DEFAULT_HEADERS.copy()

    customer, _ = await customerService.add_get_or_create_customer(session=session, email=email, merchant= merchant)
    transaction = await transactionService.create_transaction(
        session=session,
        merchant=merchant,
        processor=TransactionProcessor.KORA.value,
        amount=amount,
        customer=customer,
        currency=currency,
        reference=reference,
    )

    transaction.mode = mode
    transaction.type = TransactionType.CREDIT.value
    transaction.redirect_url = redirect_url
    transaction.notification_url = notification_url
    transaction.metadata_payload = json.dumps(metadata) if metadata else None
    # transaction.narration = narration or f"Aggregator Pay in through {TransactionProcessor.KORA.value}"

    await transactionService.save_transaction(session=session, transaction=transaction)
    if mode == tokenEnums.TokenMode.TEST:
        notification_url = SERVER_URL + "/kora/webhook/test"
    else:
        notification_url = SERVER_URL + "/kora/webhook/live"

    data = {
        'currency': currency,
        'amount': amount,
        'reference': transaction.processor_reference,
        "customer": {"email": email},
        "notification_url": notification_url,
    }
    if redirect_url:
        data['redirect_url'] = redirect_url 
    print(f"Sending to Kora:\n{json.dumps(data, indent=2)}")
    print(f"\n\nHeaders: {local_headers}\n\n")
    response_data, response_status = await post_request(url=url, headers=local_headers, data=json.dumps(data))

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

    if response_status != 200:
        logging.error(f"Error initializing transaction: {response_data}")

    charge_url = response_data.get("data", {}).get("checkout_url")

    seconds_until_expiry = 60 * 60 #1hr
    celeryService.expire_transaction.apply_async(args=[transaction.id], countdown=(seconds_until_expiry + 20))

    return response_data, response_status, charge_url

async def payout(session: AsyncSession, merchant: Merchant, acc_number: str, bank_code: str, amount: float,
                 email: str, reference: str, mode: str, currency: str, metadata: dict = None,
                 narration: str = None) -> tuple[bool, str, int]:
    """Returns in order: \n
        Transaction status: bool,
        transaction_message: string,
        http_status: int,
        transaction_id: int
    """
    url = BASE_URL + "transactions/disburse"
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_URL}"
    local_headers = DEFAULT_HEADERS.copy()

    # Get wallet for balance check and charge calculation
    wallet = await walletService.get_wallet(
        session=session,
        merchant_id=merchant.id,
        currency=currency,
        mode=mode
    )

    if not wallet:
        return False, f"Wallet not found for {currency} in {mode} mode", 400, 0

    # Calculate charge using wallet's charge configuration
    amount_charged = await walletService.get_payout_charge(wallet=wallet, amount=amount)

    if wallet.balance < amount + amount_charged:
        return False, "Insufficient balance", 400, 0

    narration = narration or "Aggregator payout"
    processor_reference = await transactionService.generate_processor_reference(session=session)

    payload = {
        "reference": processor_reference,
        "destination": {
            "type": "bank_account",
            "amount": amount,
            "currency": currency,
            "narration": narration,
            "bank_account": {
                "bank": bank_code,
                "account": acc_number
            },
            "customer": {"email": email}
        }
    }

    logging.debug(f"Kora payout payload:\n{json.dumps(payload, indent=2)}")

    customer, _ = await customerService.add_get_or_create_customer(session=session, email=email, merchant=merchant)

    transaction = await transactionService.create_transaction(
        session=session,
        merchant=merchant,
        processor=TransactionProcessor.KORA.value,
        amount=amount,
        customer=customer,
        currency=currency,
        reference=reference,
        mode=mode,
        type=TransactionType.DEBIT.value,
        narration= narration
    )
    bank_obj = bank.find_bank_by_code(bank_code)
    transaction.metadata_payload = json.dumps(metadata) if metadata else None
    transaction.narration = narration
    _, customer_name = await resolve_account(
            acc_number= acc_number,
            bank= bank_obj,
            currency= currency,
        )
    transaction.details = {
        "account_number": acc_number,
        "bank": bank_obj.name,
        "customer_name": customer_name
    }
    transaction.wallet_id = wallet.id  # Link transaction to wallet
    transaction = await transactionService.save_transaction(session=session, transaction=transaction)
    
    res, status = await post_request(url=url, data=json.dumps(payload), headers=local_headers, proxy_url=proxy_url)
   
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
    
    if status == 500:
        
        logging.error(f"Kora payout failed: {res}")
        transaction.status = TransactionStatus.FAILED.value
        await transactionService.save_transaction(session=session, transaction=transaction)
        return False, "Transfer failed", status, transaction.id

    if status != 200:
        transaction.status = TransactionStatus.FAILED.value
        await transactionService.save_transaction(session=session, transaction=transaction)
        return False, res.get("message"), status, transaction.id

    # Debit wallet with total amount (transaction amount + charge)
    total_amount = amount_charged + amount
    await walletService.debit_wallet(session=session, wallet=wallet, amount=total_amount)

    transaction.status = TransactionStatus.SUCCESS.value
    transaction.charge = amount_charged
    await transactionService.save_transaction(session=session, transaction=transaction)
    
    emailService.send_customer_receipt_email(transaction.id)
    emailService.send_merchant_receipt_email(transaction.id)

    return True, "Transfer successfully initiated", status, transaction.id

async def charge_bank_transfer(session: AsyncSession, merchant: Merchant, tx: Transaction, customer_email: str) -> dict:
    """Returns dict link this:  {
            "status": True,
            "reference": ...,
            "currency": ...,
            "amount": ...,
            "fee": ...,
            "bank_account": {
                "account_name": ...,
                "account_number": ...,
                "bank_name": ...,
                "bank_code": ...,
                "expiry_date": ...
            }
        }
        if successful else: {"status": False}
        """
    url = BASE_URL + "charges/bank-transfer"
    headers = DEFAULT_HEADERS.copy()
    tx
    if tx.mode == tokenEnums.TokenMode.LIVE:
        notification_url = SERVER_URL + "/kora/webhook/live"
    else:
        notification_url = SERVER_URL + "/kora/webhook/test"
    
    data = {
        "account_name": f"{merchant.name} account",
        "amount": float(tx.amount),
        "currency": tx.currency,
        "reference": tx.processor_reference,
        "auto_complete": True,
        "customer": {
            "email": AGG_EMAIL
        },
        "notification_url": notification_url,
        "narration": f"Payment on {merchant.name}"
    }

    response_data, response_status = await post_request(url=url, headers=headers, data=json.dumps(data))

    if response_status == 200:
        bank_account = response_data['data']['bank_account']

        expiry_dt = datetime.fromisoformat(bank_account["expiry_date_in_utc"]).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        seconds_until_expiry = (expiry_dt - now).total_seconds()
        # Make sure it's positive
        seconds_until_expiry = max(0, seconds_until_expiry)
        celeryService.expire_transaction.apply_async(args=[tx.id], countdown=(seconds_until_expiry + 20))


        data= {
            "status": True,
            "reference": tx.reference,
            "seconds_until_expiry": seconds_until_expiry,
            "merchant_id": tx.merchant_id,
            "processor_reference": tx.processor_reference,
            "currency": tx.currency,
            "customer_email": customer_email,
            "amount": tx.amount,
            "fee": await _get_wallet_payin_charge(session, merchant, tx.currency, tx.mode, tx.amount),
            "bank_account": {
                "account_name": bank_account['account_name'],
                "account_number": bank_account["account_number"],
                "bank_name": bank_account["bank_name"],
                "bank_code": bank_account["bank_code"],
                "expiry_date": bank_account["expiry_date_in_utc"]
            },
        }

        if tx.redirect_url:
            data["redirect_url"]= tx.redirect_url
            
        return data

    return {"status": False}
    
async def charge_with_card(session: AsyncSession, merchant: Merchant, amount: float, tx: Transaction , customer_email: str, link = None) ->dict:
    url = BASE_URL + "charges/initialize"
    headers = DEFAULT_HEADERS.copy()

    if tx.mode == tokenEnums.TokenMode.LIVE:
        notification_url = SERVER_URL + "/kora/webhook/live"
    else:
        notification_url = SERVER_URL + "/kora/webhook/test"
    
    data = {
        "amount": float(amount),
        "currency": tx.currency,
        "reference": tx.processor_reference,
        "channels": ["card"],
        "default_channel": "card",
        "customer": {
            "email": AGG_EMAIL
        },
        "notification_url": notification_url,
        "narration": f"Payment on {merchant.name}",
        "redirect_url": f"https://checkout.xoropay.com/pay/{link.reference}?email={customer_email}"
    }
    
    # if tx.redirect_url:
    #     data[ "redirect_url"] = tx.redirect_url

    response_data, response_status = await post_request(url=url, headers=headers, data=json.dumps(data))

    if response_status == 200: 
        data= {
            "status": True,
            "reference": tx.reference,
            "processor_reference": tx.processor_reference,
            "merchant_id": tx.merchant_id,
            "currency": tx.currency,
            "customer_email": customer_email,
            "amount": amount,
            "fee": await _get_wallet_payin_charge(session, merchant, tx.currency, tx.mode, amount),
            "checkout_url": response_data['data']['checkout_url'],
        }
        
        if tx.redirect_url:
            data['redirect_url'] = tx.redirect_url

        seconds_until_expiry = 60 * 60 #1hr
        celeryService.expire_transaction.apply_async(args=[tx.id], countdown=(seconds_until_expiry + 20))

        return data
    
    return {"status": False}

async def charge_mobile_money(merchant: Merchant, tx: Transaction, customer_email: str, mobile_money_number: str)-> dict:
    url= BASE_URL + "charges/mobile-money"
    headers = DEFAULT_HEADERS.copy()
    tx
    if tx.mode == tokenEnums.TokenMode.LIVE:
        notification_url = SERVER_URL + "/kora/webhook/live"
    else:
        notification_url = SERVER_URL + "/kora/webhook/test"
    
    data = {
        "reference": tx.processor_reference,
        "amount": tx.amount,
        "currency": tx.currency,
        "customer": { "email": "info@xoropay.com" },
        "mobile_money": {"number": mobile_money_number},
        "notification_url": notification_url,
    }
    response_data, response_status = await post_request(url=url, headers=headers, data=json.dumps(data))

    if response_status == 200:
        auth_type = response_data.get("data").get("auth_model")
        message = f"Please enter the token that was sent to {mobile_money_number}" if auth_type == "OTP" else f"A pin prompt has been set to your mobile number: {mobile_money_number}. Kindly enter your wallet pin to authorize this payment"

        if response_data.get('status') == True:
            data = {
                "status": True,
                "auth_required": True,
                "auth_type": auth_type,
                "message": message,
                "reference": tx.processor_reference
            }
        else:
            data = {
                "status": False,
                "detail": f"An error occurred while processing transaction",
                "data": response_data
            }
    else:
        data = {
            "status": False,
            "detail": f"An error occurred while processing transaction",
            "data": response_data
        }
    return data

async def authorize_mobile_money_otp(tx: Transaction, token: str):
    url= BASE_URL + "charges/mobile-money/authorize"
    headers = DEFAULT_HEADERS.copy()

    data = {
        "reference": tx.processor_reference,
        "token": token
    }
    response_data, response_status = await post_request(url=url, headers=headers, data=json.dumps(data))

    if response_status == 200:

        auth_type = response_data.get("data").get("auth_model")
        message =  f"A pin prompt has been set to the mobile number you provided. Kindly enter your wallet pin to authorize this payment"
        if response_data.get("status") == True:
            data = {
                "status": True,
                "auth_required": True,
                "auth_type": auth_type,
                "message": message,
                "reference": tx.processor_reference
            }
        else:
            data = {
            "status": False,
            "detail": f"Invalid otp provided",
            "data": response_data
        }
    else:
        data = {
            "status": False,
            "detail": f"An error occurred while processing transaction",
            "data": response_data
        }
    return data

from settings import PAYSTACK_SECRET, FLTW_SECRET_KEY
from services.httpRequestService import post_request
from settings import logging, FRONTEND_BASE_URL, AGG_EMAIL
import uuid
from enums.transactionEnums import *
from services import transactionService, merchantService, customerService
from enums.transactionEnums import TransactionCurrency
from database.models.Merchant import Merchant
from database.models.Transaction import Transaction
import json
from sqlalchemy.ext.asyncio import AsyncSession
from enums import tokenEnums
from websocket.broadcast import broadcast
from settings import SERVER_URL, BASQET_LIVE_SECRET, BASQET_SECRET
from lib import crypto

BASE_URL = 'https://api.basqet.com/v1/'
DEFAULT_HEADERS = {
    'Authorization': f'Bearer {BASQET_SECRET}',
    'Content-Type': 'application/json'
}


async def charge_with_crypto(
        session: AsyncSession, customer_email: str, amount: float, txn: Transaction, merchant: Merchant = None
):
    url = "https://api.basqet.com/v1/transaction"
    
    local_headers = DEFAULT_HEADERS.copy()
    notification_url = SERVER_URL + "/basqet/webhook/test"

    if txn.mode == tokenEnums.TokenMode.LIVE.value:
        local_headers["Authorization"] = f"Bearer {BASQET_LIVE_SECRET}"
        notification_url = SERVER_URL + "/basqet/webhook/live"


    data = {
        "customer": {"email": AGG_EMAIL, "name": "XOROPAY"},
        "amount": str(amount), #charging 0.5%, TODO: MOVE TO DB
        "currency": TransactionCurrency.NIGERIA,
    }
    print(f"Sending to basqet:\n{json.dumps(data, indent=2)}")
    print(f"Headers: {local_headers}")
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

    if response_status not in [200, 201]:
        logging.error(f"Error initializing transaction: {response_data}")
        return
    basqet_txn_reference = response_data['data']['reference']
    basqet_txn_id = response_data['data']['id']
    txn.processor_reference = basqet_txn_reference

    txn = await transactionService.save_transaction(session, txn)

    initiate_url = BASE_URL + f"transaction/{basqet_txn_id}/pay"
    crypto_obj = crypto.find_crypto_by_symbol(txn.currency)

    if not crypto_obj:
        raise ValueError("Error in crypto slug")
    
    data = {
        "currency_id": crypto_obj.get_basqet_id()
    }

    response_data, response_status = await post_request(url= initiate_url, headers=local_headers, data=json.dumps(data))

    if response_status not in [200, 201]:
        logging.error(f"Error initiating transaction: {response_data}")
        return
    
    data = response_data['data']
    qr_uri = crypto_obj.generate_qr_uri(
        address= data['payment_address'], amount= data["payment_amount"]
    )
    return_data = {
        "status": True,
        "reference": txn.reference,
        "merchant_id": txn.merchant_id,
        "currency": txn.currency,
        "customer_email": customer_email,
        "amount": amount,
        "fee": txn.charge,
        "payment_address": data['payment_address'],
        "standard": crypto_obj.standard,
        "blockchain": crypto_obj.blockchain,
        "amount": data["payment_amount"],
        "payment_currency": txn.currency,
        "qr_code": data['qrCode'],
        "qr_uri": qr_uri 
    }    
    return return_data
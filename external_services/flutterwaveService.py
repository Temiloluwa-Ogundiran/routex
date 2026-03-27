from settings import FLTW_SECRET_KEY
from services.httpRequestService import get_request, post_request
from settings import logging, FRONTEND_BASE_URL
from enums.transactionEnums import *
from services import transactionService, merchantService, customerService
from enums.transactionEnums import TransactionCurrency
from database.models.Merchant import Merchant
from database.models.Transaction import Transaction
import json
from sqlalchemy.ext.asyncio import AsyncSession
from enums import tokenEnums
from websocket.broadcast import broadcast

BASE_URL = "https://api.flutterwave.com/v3/payments"
VERIFY_URL_BASE = "https://api.flutterwave.com/v3/transactions"
HEADERS = {
    'Authorization' : f'Bearer {FLTW_SECRET_KEY}',
    'Content-Type' : 'application/json'
}


async def verify_transaction(transaction_id: str | int) -> tuple[dict, int]:
    url = f"{VERIFY_URL_BASE}/{transaction_id}/verify"
    return await get_request(url=url, headers=HEADERS)

async def initialize(session: AsyncSession, email:str, amount: float, merchant: Merchant, mode:str,
                     reference:str, currency: str = TransactionCurrency.NIGERIA.value, 
                     redirect_url: str|None=None, notification_url:str|None = None,
                     narration: str|None = None, metadata:dict|None = None) ->tuple[dict, int, str|None]:
    customer, _ = await customerService.add_get_or_create_customer(session=session, email=email, merchant= merchant)

    transaction: Transaction = await transactionService.create_transaction(
        session= session,
        merchant= merchant,
        processor= TransactionProcessor.FLUTTERWAVE.value,
        amount= amount,
        customer= customer,
        currency= currency,
        reference= reference,        
        mode= mode,
        type= TransactionType.CREDIT.value,
        narration= narration
    )
    
    url = BASE_URL 
    data = {
        "amount" : amount,
        "customer": {"email": email},
        "currency": currency,
        "redirect_url": redirect_url or FRONTEND_BASE_URL,
        "tx_ref": transaction.processor_reference,
    }
    payload_metadata = dict(metadata or {})
    payload_metadata.update(
        {
            "routex_reference": transaction.reference,
            "routex_processor_reference": transaction.processor_reference,
        }
    )
    data["meta"] = payload_metadata

    if redirect_url:
        # data['redirect_url'] = redirect_url
        transaction.redirect_url = redirect_url
    if notification_url:
        transaction.notification_url = notification_url
    
    transaction.metadata_payload = payload_metadata

    if mode == tokenEnums.TokenMode.LIVE.value:
        #TODO: SWITCH TO LIVE HEADER
        pass
    transaction.narration = narration if narration else f"Aggregator Pay in through {TransactionProcessor.FLUTTERWAVE.value}"
    transaction = await transactionService.save_transaction(session= session, transaction= transaction)
    response_data, response_status = await post_request(url= url, headers= HEADERS, data= json.dumps(data))
    
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
        logging.error(f"An error occured while initializing transaction: {response_data}")
    charge_url = response_data.get("data").get("link") if  response_data.get("data") else None
    return response_data, response_status, charge_url

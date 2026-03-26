from settings import PAYSTACK_SECRET
from services.httpRequestService import post_request
from settings import logging
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

BASE_URL = "https://api.paystack.co/transaction"
HEADERS = {
    'Authorization' : f'Bearer {PAYSTACK_SECRET}',
    'Content-Type' : 'application/json'
}

async def initialize(session: AsyncSession, email:str, amount: float, merchant: Merchant, mode: str,
                     reference:str, currency: str = TransactionCurrency.NIGERIA.value, 
                     redirect_url: str|None=None, notification_url:str|None = None,
                     narration: str|None = None, metadata:dict|None = None) ->tuple[dict, int, str|None]:
    local_headers = HEADERS.copy()
    customer, _ = await customerService.add_get_or_create_customer(session=session, email=email, merchant= merchant)

    transaction: Transaction = await transactionService.create_transaction(
        session= session,
        merchant= merchant,
        processor= TransactionProcessor.PAYSTACK.value,
        amount= amount,
        customer= customer,
        currency= currency,
        reference= reference,
        mode= mode,
        type= TransactionType.CREDIT.value,
        narration= narration
    )
    url = BASE_URL + "/initialize"

    data = {
        "amount" : amount * 100,
        "email": email,
        "currency": currency,
        "reference": transaction.processor_reference,
    }
    if redirect_url:
        data["callback_url"] = redirect_url
    if redirect_url:
        transaction.redirect_url = redirect_url
    if notification_url:
        transaction.notification_url = notification_url
    
    if metadata:
        transaction.metadata_payload = json.dumps(metadata)
    # transaction.narration = narration if narration else f"Aggregator Pay in through {TransactionProcessor.PAYSTACK.value}"
    await transactionService.save_transaction(session= session, transaction= transaction)
    response_data, response_status = await post_request(url= url, headers= local_headers, data= json.dumps(data))

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
        logging.error(f"An error occured while initializing transaction with Paystack: {response_data}")
    charge_url = response_data.get("data").get("authorization_url") if  response_data.get("data") else None
    return response_data, response_status, charge_url

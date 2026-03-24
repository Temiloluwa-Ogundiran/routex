from services import httpRequestService
from database.models.Merchant import Merchant
from settings import RELAY_TOKEN
from enums.eventEnums import EventType
from enums import eventEnums
import hmac
import hashlib
import base64
import json
from cryptography.fernet import Fernet
from database.models.Merchant import Merchant
from database.models.Transaction import Transaction
from database.models.Token import Token
from sqlalchemy.ext.asyncio import AsyncSession
import settings

HEADERS = {
    'Authorization' : f'Bearer {RELAY_TOKEN}',
    'Content-Type' : 'application/json'
}
BASE_URL = "https://relay-backend-production.up.railway.app/api/v1/"

async def create_merchant_application(merchant: Merchant):
    url = BASE_URL + "app"
    payload = {
        "appId": merchant.id,
        "name": merchant.name
    }
    print(f"payload: {payload}")
    data, status = await httpRequestService.post_request(url= url, headers= HEADERS, data= json.dumps(payload))
    if status in [200, 201]:
        print(data)
        print("\n\n")
        return True
    print(f"Error creating merchant with relay service: {data.get('message')}")
    return

async def queue_merchant_webhook(merchant: Merchant, payload: dict, event_type: EventType, token: Token, notification_url: str):
    url = BASE_URL + f"app/{merchant.id}/msg"
    headers = {
        'Content-Type' : 'application/json', 
        "X-AGGREGATOR-SIGNATURE": await generate_webhook_signature(payload= payload, secret_token_encrypted= token.secret_key),
        "X-AGGREGATOR-SIGNATURE-TYPE": token.type
        }
    payload = {
      "eventType": event_type.value,
      "payload": payload,
      "headers": headers,
    #   "payloadAsString": str(payload),
    #   "headersAsString": str(headers),
      "url": notification_url
    }

    print(f"payload: {payload}")
    data, status = await httpRequestService.post_request(url= url, headers= HEADERS, data= json.dumps(payload))
    if status == 200:
        print(data)
        print("\n\n")
        return True
    print(f"Error creating merchant with relay service: {data.get('message')}")
    return



async def generate_webhook_signature(payload: dict, secret_token_encrypted: str) -> str:
    secret_key = Fernet(settings.AGG_SECRET).decrypt(secret_token_encrypted.encode()).decode()
    message = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
    return hmac.new(secret_key.encode(), message, hashlib.sha256).hexdigest()

async def send_relay_webhook(transaction: Transaction, event: eventEnums.EventType, token: Token, session: AsyncSession):
    payload = {
        "event": event.value,
        "reference": transaction.reference,
        "data": {
            "customer": {"email": transaction.customer.email},
            "amount": transaction.amount,
            "reference": transaction.reference,
            "currency": transaction.currency,
            "metadata": transaction.metadata_payload
        }
    }
    if transaction.notification_url:
        await queue_merchant_webhook(
            merchant=transaction.merchant,
            payload=payload,
            event_type=event,
            token=token,
            notification_url=transaction.notification_url
        )

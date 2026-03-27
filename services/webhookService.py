"""
Queue normalized merchant webhooks with an HMAC-SHA256 signature.

Merchant verification:
    import hmac, hashlib
    raw_body = request.body()
    secret = "<merchant secret token>"
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    is_valid = hmac.compare_digest(expected, request.headers["X-AGGREGATOR-SIGNATURE"])
"""

import hashlib
import hmac
import json
import logging

from cryptography.fernet import Fernet

from database.models.Token import Token
from database.models.Transaction import Transaction
from enums.eventEnums import EventType
from services.celeryService import send_webhook_task
import settings

logger = logging.getLogger(__name__)


def _build_payload(transaction: Transaction, event: EventType) -> dict:
    customer_email = None
    if getattr(transaction, "customer", None) is not None:
        customer_email = transaction.customer.email

    return {
        "event": event.value,
        "reference": transaction.reference,
        "data": {
            "customer": {"email": customer_email},
            "amount": transaction.amount,
            "reference": transaction.reference,
            "currency": transaction.currency,
            "metadata": transaction.metadata_payload,
        },
    }


def _sign_payload(payload_str: str, secret_token_encrypted: str) -> str:
    plain_secret = Fernet(settings.AGG_SECRET).decrypt(
        secret_token_encrypted.encode()
    ).decode()
    return hmac.new(
        plain_secret.encode(),
        payload_str.encode(),
        hashlib.sha256,
    ).hexdigest()


def dispatch(transaction: Transaction, event: EventType, token: Token) -> None:
    if not transaction.notification_url:
        return

    payload = _build_payload(transaction, event)
    payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = _sign_payload(payload_str, token.secret_key)
    headers = {
        "Content-Type": "application/json",
        "X-AGGREGATOR-SIGNATURE": signature,
    }

    send_webhook_task.apply_async(
        kwargs={
            "url": transaction.notification_url,
            "payload_str": payload_str,
            "headers": headers,
            "event_type": event.value,
        },
        queue="webhook_queue",
        routing_key="webhook_queue",
    )
    logger.info(
        "Webhook queued: ref=%s event=%s url=%s",
        transaction.reference,
        event.value,
        transaction.notification_url,
    )

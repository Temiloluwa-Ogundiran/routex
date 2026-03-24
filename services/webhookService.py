"""
webhookService.py

Builds the outbound webhook payload + HMAC-SHA256 hex signature and dispatches
it as a fire-and-forget asyncio task with inline retries.

Merchant verification (on their server):
    import hmac, hashlib
    raw_body = request.body()          # raw bytes of the POST body
    secret   = "<their secret key>"    # plain-text secret key
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    is_valid = hmac.compare_digest(expected, request.headers["X-AGGREGATOR-SIGNATURE"])

Retry schedule:
    attempt 1 — immediately
    attempt 2 — 5 seconds  later
    attempt 3 — 15 seconds later

# ── OLD Celery-based delivery (kept for reference) ────────────────────────
# Retry schedule was: immediately → 5 min → 15 min (handled in celeryService)
#
# def dispatch(transaction, event, token):
#     if not transaction.notification_url:
#         return
#     from services.celeryService import send_webhook_task
#     payload = _build_payload(transaction, event)
#     payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
#     signature = _sign_payload(payload_str, token.secret_key)
#     headers = {"Content-Type": "application/json", "X-AGGREGATOR-SIGNATURE": signature}
#     send_webhook_task.delay(url=transaction.notification_url, payload_str=payload_str,
#                             headers=headers, event_type=event.value)
#     logger.info("Webhook queued: ref=%s event=%s url=%s", ...)
# ─────────────────────────────────────────────────────────────────────────
"""

import hmac
import hashlib
import json
import asyncio
import logging

import httpx
from cryptography.fernet import Fernet

from database.models.Transaction import Transaction
from database.models.Token import Token
from enums.eventEnums import EventType
import settings

logger = logging.getLogger(__name__)

_RETRY_DELAYS = [0, 5, 15]  # seconds: immediate, 5s, 15s


def _build_payload(transaction: Transaction, event: EventType) -> dict:
    return {
        "event": event.value,
        "reference": transaction.reference,
        "data": {
            "customer": {"email": transaction.customer.email},
            "amount": transaction.amount,
            "reference": transaction.reference,
            "currency": transaction.currency,
            "metadata": transaction.metadata_payload,
        },
    }


def _sign_payload(payload_str: str, secret_token_encrypted: str) -> str:
    plain_secret = Fernet(settings.AGG_SECRET).decrypt(secret_token_encrypted.encode()).decode()
    return hmac.new(plain_secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()


async def _deliver(url: str, payload_str: str, headers: dict, event_type: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
            if delay:
                await asyncio.sleep(delay)
            try:
                response = await client.post(url, content=payload_str.encode("utf-8"), headers=headers)
                if response.status_code < 300:
                    logger.info("Webhook delivered: event=%s url=%s status=%s", event_type, url, response.status_code)
                    return
                raise ValueError(f"Non-2xx response: {response.status_code}")
            except Exception as exc:
                if attempt < len(_RETRY_DELAYS):
                    logger.warning("Webhook attempt %s/%s failed, retrying in %ss: %s", attempt, len(_RETRY_DELAYS), _RETRY_DELAYS[attempt], exc)
                else:
                    logger.error("Webhook permanently failed after %s attempts: event=%s url=%s err=%s", attempt, event_type, url, exc)


def dispatch(transaction: Transaction, event: EventType, token: Token) -> None:
    """
    Build the webhook payload and schedule delivery as a non-blocking background coroutine.
    Returns immediately. No-ops silently if the transaction has no notification_url.
    """
    if not transaction.notification_url:
        return

    payload = _build_payload(transaction, event)
    payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = _sign_payload(payload_str, token.secret_key)

    headers = {
        "Content-Type": "application/json",
        "X-AGGREGATOR-SIGNATURE": signature,
        "X-XOROPAY-SIGNATURE": signature,
    }

    asyncio.create_task(
        _deliver(
            url=transaction.notification_url,
            payload_str=payload_str,
            headers=headers,
            event_type=event.value,
        )
    )
    logger.info("Webhook scheduled: ref=%s event=%s url=%s", transaction.reference, event.value, transaction.notification_url)

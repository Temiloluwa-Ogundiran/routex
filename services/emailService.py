import asyncio
import base64
import json
import logging
import os
from functools import partial

import requests

import settings
from database.session import async_session
from services import receiptService, transactionService
from services.tokenService import RESET_URL_TTL_IN_SECONDS

logger = logging.getLogger(__name__)

OTP_TEMPLATE_PATH = os.path.join(os.getcwd(), "templates", "otp.html")
RESEND_API_URL = "https://api.resend.com/emails"


def _send_sync(payload: dict) -> None:
    if not settings.RESEND_API_KEY:
        raise RuntimeError("Resend API key is not configured")

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Resend request failed: {exc}") from exc

    if response.status_code not in (200, 202):
        raise RuntimeError(f"Resend error {response.status_code}: {response.text}")

    logger.info("Email sent via Resend (status %s)", response.status_code)


async def _send_async(payload: dict) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(_send_sync, payload))


def _fire(coro) -> None:
    asyncio.create_task(coro)


def _pdf_attachment(pdf_bytes: bytes, filename: str = "receipt.pdf") -> dict:
    encoded = base64.b64encode(pdf_bytes).decode()
    return {
        "filename": filename,
        "content": encoded,
    }


def _build_message(
    *,
    from_email: str,
    to_email: str,
    subject: str,
    html_content: str | None = None,
    plain_text_content: str | None = None,
    attachments: list[dict] | None = None,
) -> dict:
    payload: dict[str, object] = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
    }
    if html_content is not None:
        payload["html"] = html_content
    if plain_text_content is not None:
        payload["text"] = plain_text_content
    if attachments:
        payload["attachments"] = attachments
    return payload


def _load_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _render_otp_html(otp: str) -> str:
    return _load_template(OTP_TEMPLATE_PATH).replace("{{OTP_CODE}}", str(otp))


async def _send_otp_email(email: str, otp: str) -> None:
    html_body = _render_otp_html(otp)

    payload = _build_message(
        from_email=settings.AUTH_EMAIL,
        to_email=email,
        subject="Your RouteX verification code",
        html_content=html_body,
    )
    await _send_async(payload)


async def _send_reset_url(email: str, url: str) -> None:
    body = (
        f"Your reset url is: {url}. "
        f"Please note that the url is valid for {RESET_URL_TTL_IN_SECONDS // 60} minutes"
    )
    payload = _build_message(
        from_email=settings.AUTH_EMAIL,
        to_email=email,
        subject="Reset your RouteX password",
        plain_text_content=body,
    )
    await _send_async(payload)


async def _send_receipt_email(
    email: str,
    html_content: str,
    pdf_bytes: bytes,
    pdf_filename: str = "receipt.pdf",
    subject: str = "Your RouteX receipt",
) -> None:
    payload = _build_message(
        from_email=settings.RECEIPT_EMAIL,
        to_email=email,
        subject=subject,
        html_content=html_content,
        attachments=[_pdf_attachment(pdf_bytes, pdf_filename)],
    )
    await _send_async(payload)


async def _send_customer_receipt_email(txn_id: str) -> None:
    async with async_session() as session:
        txn = await transactionService.get_transaction_by_id_loaded(
            session=session, id=int(txn_id)
        )
        if not txn:
            logger.warning("Transaction %s not found - skipping customer receipt", txn_id)
            return

        html_content = receiptService.generate_customer_receipt_html(transaction=txn)
        pdf_bytes = receiptService.getenerate_customer_receipt_pdf_bytes(transaction=txn)

        await _send_receipt_email(
            email=txn.customer.email,
            html_content=html_content,
            pdf_bytes=pdf_bytes,
        )


async def _send_merchant_receipt_email(txn_id: str) -> None:
    async with async_session() as session:
        txn = await transactionService.get_transaction_by_id_loaded(
            session=session, id=int(txn_id)
        )
        if not txn:
            logger.warning("Transaction %s not found - skipping merchant receipt", txn_id)
            return

        html_content = receiptService.generate_receipt_html(transaction=txn)
        pdf_bytes = receiptService.generate_receipt_pdf_bytes(transaction=txn)

        await _send_receipt_email(
            email=txn.merchant.email,
            html_content=html_content,
            pdf_bytes=pdf_bytes,
        )


async def send_otp_email(email: str, otp: str) -> None:
    await _send_otp_email(email, otp)


async def send_reset_url(email: str, url: str) -> None:
    await _send_reset_url(email, url)


def send_customer_receipt_email(txn_id: str) -> None:
    _fire(_send_customer_receipt_email(txn_id))


def send_merchant_receipt_email(txn_id: str) -> None:
    _fire(_send_merchant_receipt_email(txn_id))

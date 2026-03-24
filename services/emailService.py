import asyncio
import base64
import logging
import os  # still needed for OTP_TEMPLATE_PATH
from functools import partial

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)

import settings
from services.otpService import OTP_EXPIRY_IN_SECONDS
from services.tokenService import RESET_URL_TTL_IN_SECONDS
from services import receiptService, transactionService
from database.session import async_session

logger = logging.getLogger(__name__)

OTP_TEMPLATE_PATH = os.path.join(os.getcwd(), "templates", "otp.html")

_sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _send_sync(message: Mail) -> None:
    """Synchronous SendGrid send — run in a thread so we don't block the loop."""
    response = _sg.send(message)
    if response.status_code not in (200, 202):
        logger.error("SendGrid error %s: %s", response.status_code, response.body)
    else:
        logger.info("Email sent via SendGrid (status %s)", response.status_code)


async def _send_async(message: Mail) -> None:
    """Offload the blocking SDK call to a thread pool."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(_send_sync, message))


def _fire(coro) -> None:
    """Schedule a coroutine as a fire-and-forget asyncio task."""
    asyncio.create_task(coro)


def _pdf_attachment(pdf_bytes: bytes, filename: str = "receipt.pdf") -> Attachment:
    encoded = base64.b64encode(pdf_bytes).decode()
    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    attachment.file_type = FileType("application/pdf")
    attachment.file_name = FileName(filename)
    attachment.disposition = Disposition("attachment")
    return attachment


# ─────────────────────────────────────────────
# Auth emails  (from: AUTH_FROM_EMAIL)
# ─────────────────────────────────────────────

async def _send_otp_email(email: str, otp: str) -> None:
    with open(OTP_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_body = f.read().replace("{{OTP_CODE}}", str(otp))

    message = Mail(
        from_email=settings.AUTH_EMAIL,
        to_emails=email,
        subject="Your OTP Code",
        html_content=html_body,
    )
    await _send_async(message)


async def _send_reset_url(email: str, url: str) -> None:
    body = (
        f"Your reset url is: {url}. "
        f"Please note that the url is valid for {RESET_URL_TTL_IN_SECONDS // 60} minutes"
    )
    message = Mail(
        from_email=settings.AUTH_EMAIL,
        to_emails=email,
        subject="Password Reset",
        plain_text_content=body,
    )
    await _send_async(message)


# ─────────────────────────────────────────────
# Receipt emails  (from: RECEIPT_FROM_EMAIL)
# ─────────────────────────────────────────────

async def _send_receipt_email(
    email: str,
    html_content: str,
    pdf_bytes: bytes,
    pdf_filename: str = "receipt.pdf",
    subject: str = "Your Transaction Receipt",
) -> None:
    message = Mail(
        from_email=settings.RECEIPT_EMAIL,
        to_emails=email,
        subject=subject,
        html_content=html_content,
    )
    message.attachment = _pdf_attachment(pdf_bytes, pdf_filename)
    await _send_async(message)


async def _send_customer_receipt_email(txn_id: str) -> None:
    async with async_session() as session:
        txn = await transactionService.get_transaction_by_id_loaded(
            session=session, id=int(txn_id)
        )
        if not txn:
            logger.warning("Transaction %s not found — skipping customer receipt", txn_id)
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
            logger.warning("Transaction %s not found — skipping merchant receipt", txn_id)
            return

        html_content = receiptService.generate_receipt_html(transaction=txn)
        pdf_bytes = receiptService.generate_receipt_pdf_bytes(transaction=txn)

        await _send_receipt_email(
            email=txn.merchant.email,
            html_content=html_content,
            pdf_bytes=pdf_bytes,
        )


# ─────────────────────────────────────────────
# Public API — fire-and-forget (non-blocking)
# ─────────────────────────────────────────────

def send_otp_email(email: str, otp: str) -> None:
    """Schedule OTP email; returns immediately."""
    _fire(_send_otp_email(email, otp))


def send_reset_url(email: str, url: str) -> None:
    """Schedule password-reset email; returns immediately."""
    _fire(_send_reset_url(email, url))


def send_customer_receipt_email(txn_id: str) -> None:
    """Schedule customer receipt email; returns immediately."""
    _fire(_send_customer_receipt_email(txn_id))


def send_merchant_receipt_email(txn_id: str) -> None:
    """Schedule merchant receipt email; returns immediately."""
    _fire(_send_merchant_receipt_email(txn_id))

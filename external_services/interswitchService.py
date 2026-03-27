import base64
from html import escape
import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.Merchant import Merchant
from database.models.Transaction import Transaction
from enums import tokenEnums
from enums.transactionEnums import (
    TransactionCurrency,
    TransactionProcessor,
    TransactionStatus,
    TransactionType,
)
from services import customerService, transactionService
from services.httpRequestService import get_request
from settings import (
    FRONTEND_BASE_URL,
    INTERSWITCH_CLIENT_ID,
    INTERSWITCH_MERCHANT_CODE,
    INTERSWITCH_PAY_ITEM_ID,
    INTERSWITCH_SECRET_KEY,
    SERVER_URL,
)

INTERSWITCH_QA_CHECKOUT_URL = "https://newwebpay.qa.interswitchng.com/collections/w/pay"
INTERSWITCH_LIVE_CHECKOUT_URL = "https://newwebpay.interswitchng.com/collections/w/pay"
INTERSWITCH_QA_TOKEN_URL = "https://passport.k8.isw.la/passport/oauth/token?grant_type=client_credentials"
INTERSWITCH_LIVE_TOKEN_URL = "https://passport.interswitchng.com/passport/oauth/token?grant_type=client_credentials"
INTERSWITCH_QA_PAYBILL_URL = "https://qa.interswitchng.com/paymentgateway/api/v1/paybill"
INTERSWITCH_LIVE_PAYBILL_URL = "https://webpay.interswitchng.com/paymentgateway/api/v1/paybill"
INTERSWITCH_QA_VERIFY_URL = "https://qa.interswitchng.com/collections/api/v1/gettransaction.json"
INTERSWITCH_LIVE_VERIFY_URL = "https://webpay.interswitchng.com/collections/api/v1/gettransaction.json"
NGN_NUMERIC_CURRENCY = "566"


def has_required_checkout_config() -> bool:
    return bool(INTERSWITCH_MERCHANT_CODE and INTERSWITCH_PAY_ITEM_ID)


def has_required_verify_config() -> bool:
    return bool(INTERSWITCH_MERCHANT_CODE)


def has_full_credentials() -> bool:
    return bool(
        INTERSWITCH_MERCHANT_CODE
        and INTERSWITCH_PAY_ITEM_ID
        and INTERSWITCH_CLIENT_ID
        and INTERSWITCH_SECRET_KEY
    )


def amount_to_minor(amount: float) -> int:
    return int(round(float(amount) * 100))


def get_hosted_checkout_url(mode: str) -> str:
    if mode == tokenEnums.TokenMode.LIVE.value:
        return INTERSWITCH_LIVE_CHECKOUT_URL
    return INTERSWITCH_QA_CHECKOUT_URL


def get_verify_url(mode: str) -> str:
    if mode == tokenEnums.TokenMode.LIVE.value:
        return INTERSWITCH_LIVE_VERIFY_URL
    return INTERSWITCH_QA_VERIFY_URL


def get_access_token_url(mode: str) -> str:
    if mode == tokenEnums.TokenMode.LIVE.value:
        return INTERSWITCH_LIVE_TOKEN_URL
    return INTERSWITCH_QA_TOKEN_URL


def get_paybill_url(mode: str) -> str:
    if mode == tokenEnums.TokenMode.LIVE.value:
        return INTERSWITCH_LIVE_PAYBILL_URL
    return INTERSWITCH_QA_PAYBILL_URL


def get_checkout_bridge_url(processor_reference: str, server_base_url: str | None = None) -> str:
    base_url = (server_base_url or SERVER_URL or FRONTEND_BASE_URL or "").rstrip("/")
    if not base_url:
        raise ValueError("RouteX server base URL is required to build the Interswitch checkout URL.")
    return f"{base_url}/api/v1/checkout/interswitch/{processor_reference}"


def get_redirect_url(redirect_url: str | None = None) -> str:
    return redirect_url or FRONTEND_BASE_URL


def get_return_url(server_base_url: str | None = None) -> str:
    base_url = (server_base_url or SERVER_URL or FRONTEND_BASE_URL or "").rstrip("/")
    if not base_url:
        raise ValueError("RouteX server base URL is required to build the Interswitch return URL.")
    return f"{base_url}/api/v1/checkout/interswitch/return"


def get_payment_status_url(
    reference: str,
    status: str,
    selected_gateway: str,
    gateway_reference: str,
    next_url: str | None = None,
) -> str:
    base_url = (FRONTEND_BASE_URL or SERVER_URL or "").rstrip("/")
    if not base_url:
        raise ValueError("RouteX frontend base URL is required to build the payment status URL.")

    params = {
        "reference": reference,
        "status": status,
        "selected_gateway": selected_gateway,
        "gateway_reference": gateway_reference,
    }
    if next_url:
        params["next"] = next_url
    return f"{base_url}/pay/status?{urlencode(params)}"


def get_post_payment_redirect_url(
    redirect_url: str,
    reference: str,
    status: str,
    selected_gateway: str,
    gateway_reference: str,
) -> str:
    parsed_url = urlparse(redirect_url)
    existing_query = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    existing_query.update(
        {
            "reference": reference,
            "status": status,
            "selected_gateway": selected_gateway,
            "gateway_reference": gateway_reference,
        }
    )
    return urlunparse(parsed_url._replace(query=urlencode(existing_query)))


def _get_transaction_server_base_url(transaction: Transaction) -> str | None:
    details = transaction.details if isinstance(transaction.details, dict) else {}
    return details.get("routex_server_base_url")


def build_checkout_form_fields(
    transaction: Transaction,
    customer_email: str | None = None,
    server_base_url: str | None = None,
) -> dict[str, str]:
    return {
        "merchant_code": str(INTERSWITCH_MERCHANT_CODE),
        "pay_item_id": str(INTERSWITCH_PAY_ITEM_ID),
        "site_redirect_url": get_return_url(
            server_base_url=server_base_url or _get_transaction_server_base_url(transaction)
        ),
        "txn_ref": str(transaction.processor_reference),
        "amount": str(amount_to_minor(transaction.amount)),
        "currency": NGN_NUMERIC_CURRENCY,
        "cust_email": customer_email or "",
        "pay_item_name": transaction.narration or "RouteX payment",
    }


def build_bridge_html(form_action: str, form_fields: dict[str, str]) -> str:
    hidden_inputs = "\n".join(
        f'<input type="hidden" name="{escape(key)}" value="{escape(value)}" />'
        for key, value in form_fields.items()
        if value
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Redirecting to Interswitch</title>
</head>
<body>
  <main>
    <p>Redirecting to Interswitch checkout...</p>
    <form id="interswitch-checkout-form" method="post" action="{escape(form_action)}">
      {hidden_inputs}
      <noscript>
        <button type="submit">Continue to payment</button>
      </noscript>
    </form>
  </main>
  <script>
    document.getElementById("interswitch-checkout-form").submit();
  </script>
</body>
</html>"""


def build_verify_query(transaction: Transaction) -> str:
    details = transaction.details if isinstance(transaction.details, dict) else {}
    verify_reference = (
        details.get("interswitch_reference")
        or transaction.processor_reference
    )
    return urlencode(
        {
            "merchantcode": INTERSWITCH_MERCHANT_CODE,
            "transactionreference": verify_reference,
            "amount": amount_to_minor(transaction.amount),
        }
    )


def _build_basic_authorization_header() -> str:
    credentials = f"{INTERSWITCH_CLIENT_ID}:{INTERSWITCH_SECRET_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded_credentials}"


async def _request_access_token(mode: str) -> str:
    headers = {
        "accept": "application/json",
        "Authorization": _build_basic_authorization_header(),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(get_access_token_url(mode), headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ValueError(
            f"Interswitch access token request failed: {exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise ValueError("Interswitch access token request failed.") from exc

    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise ValueError("Interswitch did not return an access token.")
    return access_token


async def _create_paybill_checkout(mode: str, access_token: str, payload: dict[str, str]) -> dict[str, Any]:
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                get_paybill_url(mode),
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ValueError(
            f"Interswitch paybill request failed: {exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise ValueError("Interswitch paybill request failed.") from exc
    return response.json()


def extract_payment_url(response_data: dict[str, Any]) -> str | None:
    nested_data = response_data.get("data") if isinstance(response_data.get("data"), dict) else {}
    return (
        response_data.get("paymentUrl")
        or response_data.get("payment_url")
        or response_data.get("checkout_url")
        or response_data.get("url")
        or nested_data.get("paymentUrl")
        or nested_data.get("payment_url")
        or nested_data.get("checkout_url")
        or nested_data.get("url")
    )


async def initialize(
    session: AsyncSession,
    email: str,
    amount: float,
    merchant: Merchant,
    mode: str,
    reference: str,
    currency: str = TransactionCurrency.NIGERIA.value,
    redirect_url: str | None = None,
    notification_url: str | None = None,
    narration: str | None = None,
    metadata: dict | None = None,
    server_base_url: str | None = None,
) -> tuple[dict[str, Any], int, str | None]:
    if currency != TransactionCurrency.NIGERIA.value:
        raise ValueError("Interswitch collections currently support NGN only.")
    if not has_full_credentials():
        raise ValueError("Interswitch integration credentials are not configured.")

    customer, _ = await customerService.add_get_or_create_customer(
        session=session,
        email=email,
        merchant=merchant,
    )
    transaction = await transactionService.create_transaction(
        session=session,
        merchant=merchant,
        processor=TransactionProcessor.INTERSWITCH.value,
        amount=amount,
        customer=customer,
        currency=currency,
        reference=reference,
        mode=mode,
        type=TransactionType.CREDIT.value,
        narration=narration,
    )

    transaction.redirect_url = get_redirect_url(redirect_url)
    transaction.notification_url = notification_url
    transaction.metadata_payload = json.dumps(metadata) if metadata else None
    transaction.details = {
        "routex_server_base_url": (server_base_url or SERVER_URL or FRONTEND_BASE_URL or "").rstrip("/")
    }
    transaction = await transactionService.save_transaction(session=session, transaction=transaction)

    access_token = await _request_access_token(mode)
    paybill_payload = {
        "merchantCode": str(INTERSWITCH_MERCHANT_CODE),
        "payableCode": str(INTERSWITCH_PAY_ITEM_ID),
        "amount": str(amount_to_minor(transaction.amount)),
        "transactionReference": str(transaction.reference),
        "redirectUrl": str(transaction.redirect_url),
        "customerId": customer.email,
        "currencyCode": NGN_NUMERIC_CURRENCY,
        "customerEmail": customer.email,
    }
    response_data = await _create_paybill_checkout(
        mode=mode,
        access_token=access_token,
        payload=paybill_payload,
    )
    checkout_url = extract_payment_url(response_data)
    if not checkout_url:
        raise ValueError("Interswitch did not return a checkout URL.")

    details = dict(transaction.details) if isinstance(transaction.details, dict) else {}
    details.update(
        {
            "interswitch_payment_url": checkout_url,
            "interswitch_reference": response_data.get("reference"),
        }
    )
    transaction.details = details
    await transactionService.save_transaction(session=session, transaction=transaction)

    response_data = {
        "status": True,
        "message": "Charge created successfully",
        "data": response_data,
    }
    return response_data, 200, checkout_url


async def verify_transaction(
    session: AsyncSession,
    transaction: Transaction,
) -> tuple[dict[str, Any], int]:
    if not has_required_verify_config():
        raise ValueError("Interswitch integration credentials are not configured.")

    verify_url = f"{get_verify_url(transaction.mode)}?{build_verify_query(transaction)}"
    return await get_request(url=verify_url)


def normalize_verify_status(
    response_data: dict[str, Any],
    current_status: str,
) -> str:
    response_code = str(response_data.get("ResponseCode") or "").strip()
    if response_code == "00":
        return TransactionStatus.SUCCESS.value
    if response_code:
        return TransactionStatus.FAILED.value
    return current_status

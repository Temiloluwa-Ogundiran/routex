from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select

from database.models.Transaction import Transaction
from enums.transactionEnums import TransactionProcessor, TransactionStatus, TransactionType
from external_services import interswitchService
from services import transactionService


class _FakeHttpxResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://qa.interswitchng.com/paymentgateway/api/v1/paybill")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_initialize_returns_provider_payment_url(
    mock_post,
    async_session,
    test_merchant,
    monkeypatch,
):
    monkeypatch.setattr(interswitchService, "INTERSWITCH_MERCHANT_CODE", "MX123")
    monkeypatch.setattr(interswitchService, "INTERSWITCH_PAY_ITEM_ID", "9405967")
    monkeypatch.setattr(interswitchService, "INTERSWITCH_CLIENT_ID", "CLIENT123")
    monkeypatch.setattr(interswitchService, "INTERSWITCH_SECRET_KEY", "SECRET456")
    monkeypatch.setattr(interswitchService, "FRONTEND_BASE_URL", "https://routex.dev")

    mock_post.side_effect = [
        _FakeHttpxResponse({"access_token": "test-access-token"}),
        _FakeHttpxResponse(
            {
                "reference": "ISW_BILL_REF_001",
                "paymentUrl": "https://newwebpay.qa.interswitchng.com/pay/ISW_BILL_REF_001",
                "code": "200",
            }
        ),
    ]

    response_data, status, checkout_url = await interswitchService.initialize(
        session=async_session,
        email="customer@test.com",
        amount=5000.0,
        merchant=test_merchant,
        mode="test",
        reference="ISW_INIT_001",
        currency="NGN",
        redirect_url="https://merchant.example.com/callback",
    )

    assert status == 200
    assert checkout_url == "https://newwebpay.qa.interswitchng.com/pay/ISW_BILL_REF_001"
    assert response_data["data"]["paymentUrl"] == checkout_url

    token_call = mock_post.await_args_list[0]
    assert token_call.kwargs["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    assert token_call.kwargs["headers"]["Authorization"].startswith("Basic ")

    paybill_call = mock_post.await_args_list[1]
    assert paybill_call.kwargs["headers"]["Authorization"] == "Bearer test-access-token"
    assert paybill_call.kwargs["json"]["merchantCode"] == "MX123"
    assert paybill_call.kwargs["json"]["payableCode"] == "9405967"
    assert paybill_call.kwargs["json"]["amount"] == "500000"
    assert paybill_call.kwargs["json"]["redirectUrl"] == "https://merchant.example.com/callback"
    assert paybill_call.kwargs["json"]["customerId"] == "customer@test.com"
    assert paybill_call.kwargs["json"]["customerEmail"] == "customer@test.com"
    assert paybill_call.kwargs["json"]["currencyCode"] == "566"

    transaction = await async_session.scalar(
        select(Transaction).where(Transaction.reference == "ISW_INIT_001")
    )
    assert transaction is not None
    assert paybill_call.kwargs["json"]["transactionReference"] == transaction.reference
    assert transaction.processor == TransactionProcessor.INTERSWITCH.value
    assert transaction.status == TransactionStatus.PENDING.value
    assert transaction.details["interswitch_reference"] == "ISW_BILL_REF_001"
    assert transaction.details["interswitch_payment_url"] == checkout_url


def test_build_verify_query_prefers_interswitch_reference():
    transaction = Transaction(
        amount=2500.0,
        processor_reference="ISW_PROC_004",
        details={"interswitch_reference": "ISW_BILL_REF_004"},
    )

    query = interswitchService.build_verify_query(transaction)

    assert "transactionreference=ISW_BILL_REF_004" in query
    assert "amount=250000" in query


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_verify_nin_identity_uses_marketplace_defaults_and_payload(
    mock_post,
    monkeypatch,
):
    monkeypatch.setattr(interswitchService, "INTERSWITCH_CLIENT_ID", "CLIENT123")
    monkeypatch.setattr(interswitchService, "INTERSWITCH_SECRET_KEY", "SECRET456")
    monkeypatch.setattr(interswitchService, "INTERSWITCH_IDENTITY_VERIFY_URL", None)

    mock_post.side_effect = [
        _FakeHttpxResponse({"access_token": "test-access-token"}),
        _FakeHttpxResponse(
            {
                "status": "VERIFIED",
                "reference": "ISW|KYC|NIN|20260327|ABC123",
                "firstName": "Ada",
                "lastName": "Lovelace",
            }
        ),
    ]

    response = await interswitchService.verify_nin_identity(
        nin="12345678901",
        first_name="Ada",
        last_name="Lovelace",
        phone="+2348012345678",
        birth_date=date(1990, 12, 10),
        mode="test",
    )

    assert response["status"] == "VERIFIED"
    token_call = mock_post.await_args_list[0]
    assert (
        token_call.args[0]
        == "https://qa.interswitchng.com/passport/oauth/token"
    )
    assert token_call.kwargs["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    assert token_call.kwargs["data"] == {
        "scope": "profile",
        "grant_type": "client_credentials",
    }

    verify_call = mock_post.await_args_list[1]
    assert (
        verify_call.args[0]
        == "https://api-marketplace-routing.k8.isw.la/marketplace-routing/api/v1/verify/identity/nin"
    )
    assert verify_call.kwargs["json"] == {
        "firstName": "Ada",
        "lastName": "Lovelace",
        "nin": "12345678901",
    }


@pytest.mark.asyncio
async def test_interswitch_bridge_checkout_renders_form(
    client,
    async_session,
    test_merchant,
    test_customer,
    monkeypatch,
):
    monkeypatch.setattr(interswitchService, "INTERSWITCH_MERCHANT_CODE", "MX123")
    monkeypatch.setattr(interswitchService, "INTERSWITCH_PAY_ITEM_ID", "9405967")
    monkeypatch.setattr(interswitchService, "FRONTEND_BASE_URL", "https://routex.dev")

    transaction = Transaction(
        merchant_id=test_merchant.id,
        customer_id=test_customer.id,
        amount=2500.0,
        charge=0.0,
        currency="NGN",
        type=TransactionType.CREDIT.value,
        status=TransactionStatus.PENDING.value,
        mode="test",
        processor=TransactionProcessor.INTERSWITCH.value,
        selected_gateway="isw",
        reference="ISW_BRIDGE_001",
        processor_reference="ISW_PROC_001",
        redirect_url="https://merchant.example.com/callback",
    )
    async_session.add(transaction)
    await async_session.commit()

    response = await client.get("/api/v1/checkout/interswitch/ISW_PROC_001")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'action="https://newwebpay.qa.interswitchng.com/collections/w/pay"' in response.text
    assert 'name="merchant_code" value="MX123"' in response.text
    assert 'name="pay_item_id" value="9405967"' in response.text
    assert 'name="txn_ref" value="ISW_PROC_001"' in response.text
    assert 'name="amount" value="250000"' in response.text
    assert 'name="site_redirect_url" value="http://test/api/v1/checkout/interswitch/return"' in response.text

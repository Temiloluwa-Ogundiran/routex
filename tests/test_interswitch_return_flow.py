from urllib.parse import parse_qs, urlparse

import pytest
from unittest.mock import AsyncMock, patch

from database.models.Transaction import Transaction
from enums.transactionEnums import TransactionProcessor, TransactionStatus, TransactionType


@pytest.mark.asyncio
@patch("external_services.interswitchService.get_request", new_callable=AsyncMock)
async def test_interswitch_return_redirects_to_status_page(
    mock_get_request,
    client,
    async_session,
    test_merchant,
    test_customer,
    monkeypatch,
):
    mock_get_request.return_value = (
        {
            "ResponseCode": "00",
            "PaymentReference": "ISW_PAY_001",
        },
        200,
    )
    monkeypatch.setattr("external_services.interswitchService.INTERSWITCH_MERCHANT_CODE", "MX123")
    monkeypatch.setattr("external_services.interswitchService.FRONTEND_BASE_URL", "https://routex.app")

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
        reference="ISW_RETURN_001",
        processor_reference="ISW_PROC_001",
        redirect_url="https://merchant.example.com/callback",
    )
    async_session.add(transaction)
    await async_session.commit()

    response = await client.post(
        "/api/v1/checkout/interswitch/return",
        data={"txnref": "ISW_PROC_001"},
    )

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://routex.app/pay/status?")
    params = parse_qs(urlparse(location).query)
    assert params["reference"] == ["ISW_RETURN_001"]
    assert params["status"] == ["success"]
    assert params["selected_gateway"] == ["isw"]
    assert params["gateway_reference"] == ["ISW_PROC_001"]
    assert params["next"] == ["https://merchant.example.com/callback"]


@pytest.mark.asyncio
@patch("external_services.interswitchService.get_request", new_callable=AsyncMock)
async def test_interswitch_return_marks_pending_when_verify_unavailable(
    mock_get_request,
    client,
    async_session,
    test_merchant,
    test_customer,
    monkeypatch,
):
    mock_get_request.side_effect = RuntimeError("verify unavailable")
    monkeypatch.setattr("external_services.interswitchService.INTERSWITCH_MERCHANT_CODE", "MX123")
    monkeypatch.setattr("external_services.interswitchService.FRONTEND_BASE_URL", "https://routex.app")

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
        reference="ISW_RETURN_002",
        processor_reference="ISW_PROC_002",
    )
    async_session.add(transaction)
    await async_session.commit()

    response = await client.post(
        "/api/v1/checkout/interswitch/return",
        data={"txnref": "ISW_PROC_002"},
    )

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://routex.app/pay/status?")
    params = parse_qs(urlparse(location).query)
    assert params["reference"] == ["ISW_RETURN_002"]
    assert params["status"] == ["pending"]
    assert params["selected_gateway"] == ["isw"]

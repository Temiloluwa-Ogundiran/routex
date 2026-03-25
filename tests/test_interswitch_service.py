import pytest
from sqlalchemy import select

from database.models.Transaction import Transaction
from enums.transactionEnums import TransactionProcessor, TransactionStatus, TransactionType
from external_services import interswitchService
from services import transactionService


@pytest.mark.asyncio
async def test_initialize_returns_bridge_checkout_url(
    async_session,
    test_merchant,
    monkeypatch,
):
    monkeypatch.setattr(interswitchService, "INTERSWITCH_MERCHANT_CODE", "MX123")
    monkeypatch.setattr(interswitchService, "INTERSWITCH_PAY_ITEM_ID", "9405967")
    monkeypatch.setattr(interswitchService, "FRONTEND_BASE_URL", "https://routex.dev")

    response_data, status, checkout_url = await interswitchService.initialize(
        session=async_session,
        email="customer@test.com",
        amount=5000.0,
        merchant=test_merchant,
        mode="test",
        reference="ISW_INIT_001",
        currency="NGN",
        redirect_url="https://merchant.example.com/callback",
        server_base_url="http://test",
    )

    assert status == 200
    assert checkout_url is not None
    assert checkout_url.startswith("http://test/api/v1/checkout/interswitch/")
    assert response_data["data"]["form_fields"]["merchant_code"] == "MX123"
    assert response_data["data"]["form_fields"]["pay_item_id"] == "9405967"
    assert response_data["data"]["form_fields"]["currency"] == "566"
    assert response_data["data"]["form_fields"]["amount"] == "500000"
    assert (
        response_data["data"]["form_fields"]["site_redirect_url"]
        == "http://test/api/v1/checkout/interswitch/return"
    )

    transaction = await async_session.scalar(
        select(Transaction).where(Transaction.reference == "ISW_INIT_001")
    )
    assert transaction is not None
    assert transaction.processor == TransactionProcessor.INTERSWITCH.value
    assert transaction.status == TransactionStatus.PENDING.value


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

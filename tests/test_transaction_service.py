import pytest

from enums.transactionEnums import TransactionStatus, TransactionType
from services import transactionService


@pytest.mark.asyncio
async def test_create_transaction_persists_pending_status_value(
    async_session,
    test_merchant,
    test_customer,
):
    transaction = await transactionService.create_transaction(
        session=async_session,
        merchant=test_merchant,
        processor="pstk",
        amount=2500.0,
        customer=test_customer,
        reference="TXN_PENDING_001",
        type=TransactionType.CREDIT.value,
        currency="NGN",
        mode="test",
    )

    assert transaction.status == TransactionStatus.PENDING.value
    assert transaction.type == TransactionType.CREDIT


@pytest.mark.asyncio
async def test_save_transaction_normalizes_string_enum_values(
    async_session,
    test_merchant,
    test_customer,
):
    transaction = await transactionService.create_transaction(
        session=async_session,
        merchant=test_merchant,
        processor="pstk",
        amount=1500.0,
        customer=test_customer,
        reference="TXN_PENDING_002",
        type="credit",
        currency="NGN",
        mode="test",
    )

    transaction.status = "success"
    transaction.type = "credit"
    transaction.processor = "pstk"

    transaction = await transactionService.save_transaction(
        session=async_session,
        transaction=transaction,
    )

    assert transaction.status == TransactionStatus.SUCCESS
    assert transaction.type == TransactionType.CREDIT

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

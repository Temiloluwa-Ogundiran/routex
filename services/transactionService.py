from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound
from database.models.Transaction import Transaction
from database.models.Merchant import Merchant
from database.models.Customer import Customer
from database.models.PaymentLink import PaymentLink
from enums.transactionEnums import *
from enums.tokenEnums import *
from typing import Union, Optional, List, Dict
import uuid
from schemas.transactionSchema import TransactionResponse
import json

PROCESSOR_CHOICES = ['fltw', 'pstk', 'kora', 'isw']
PROCESSOR_CHARGE_PRIORITY = ['kora', 'pstk', 'fltw', 'isw']

async def save_transaction(session:AsyncSession, transaction: Transaction)->Transaction:
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction

async def get_total_transactions(session: AsyncSession, merchant_id, mode: str):
    count_stmt = select(func.count()).select_from(Transaction).where(Transaction.merchant_id == merchant_id, Transaction.mode == mode)
    total_result = await session.execute(count_stmt)
    total_items = total_result.scalar() or 0
    return total_items

async def get_paginated_transactions(merchant_id: str, mode: str, page: int, page_size: int, session: AsyncSession):
    offset = (page - 1) * page_size

    stmt = (
        select(Transaction)
        .where(Transaction.merchant_id == merchant_id, Transaction.mode == mode)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(
            selectinload(Transaction.customer),
            selectinload(Transaction.merchant)
        )
    )

    result = await session.execute(stmt)
    transactions = result.scalars().all()
    return transactions

async def generate_processor_reference(session:AsyncSession):
    while True:
        processor_reference = uuid.uuid4().hex[:7]
        txn = await session.execute(select(Transaction).where(Transaction.processor_reference == processor_reference))
        if not txn.scalar_one_or_none():
            return processor_reference
        
async def create_transaction(session: AsyncSession, merchant: Merchant, processor: str, amount: float, customer: Customer, reference: str, type: Optional[str] = None, currency: str = TransactionCurrency.NIGERIA, mode: Optional[str] = None, link: PaymentLink = None, narration: str = None, metadata_payload: Union[List, Dict] = None, redirect_url: str = None, notification_url: str = None) -> Transaction:

    if not TransactionProcessor.is_valid(value=processor) and processor is not None:
        raise Exception("Invalid transaction processor")
    if not TransactionCurrency.is_valid(value=currency) and currency is not None:
        raise Exception("Invalid transaction currency")
    if not TokenMode.is_valid(value=mode) and mode is not None:
        raise Exception("Invalid transaction mode")

    transaction = Transaction(
        type=type,
        processor=processor,
        merchant_id=merchant.id,
        customer_id=customer.id,
        currency=currency,
        mode=mode,
        amount=amount,
        reference=reference,
        processor_reference = await generate_processor_reference(session= session),
        payment_link = link,
        narration = narration,
        metadata_payload = metadata_payload,
        redirect_url= redirect_url,
        notification_url= notification_url,
        status=TransactionStatus.PENDING.value,
    )
    
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction

async def get_transaction_by_id(session: AsyncSession, id: int) -> Transaction:
    stmt = select(Transaction).where(Transaction.id == id)
    result = await session.execute(stmt)
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise NoResultFound
    return transaction

async def get_transaction_by_id_loaded(session: AsyncSession, id: str):
    stmt = select(Transaction).where(Transaction.id == id).options(selectinload(Transaction.merchant), selectinload(Transaction.customer))
    result = await session.execute(stmt)
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise NoResultFound
    return transaction


async def get_transaction_by_processor(session: AsyncSession, processor: str):
    if processor not in PROCESSOR_CHOICES:
        raise ValueError("Invalid processor")
    stmt = select(Transaction).where(Transaction.processor == processor)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_last_transaction_by_processor(session: AsyncSession, processor: str):
    if processor not in PROCESSOR_CHOICES:
        raise ValueError("Invalid processor")
    stmt = select(Transaction).where(Transaction.processor == processor).order_by(Transaction.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().first()

async def get_transaction_by_merchant_and_reference(session: AsyncSession, merchant: Merchant, reference: str) -> Optional[Transaction]:
    stmt = select(Transaction).options(selectinload(Transaction.customer)).where(Transaction.merchant_id == merchant.id, Transaction.reference == reference)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_transaction_by_processor_reference(session: AsyncSession, processor_reference: str) -> Optional[Transaction]:
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.merchant), selectinload(Transaction.customer))
        .where(Transaction.processor_reference == processor_reference)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_transaction_by_reference_and_datetime(session: AsyncSession, reference: str, datetime_str: str) -> Optional[Transaction]:
    """
    Get transaction by reference and datetime string.

    Args:
        session: Database session
        reference: Transaction reference
        datetime_str: ISO format datetime string (e.g., '2024-01-15T10:30:45.123456')

    Returns:
        Transaction object if found, None otherwise
    """
    from datetime import datetime

    try:
        # Parse the datetime string
        created_at = datetime.fromisoformat(datetime_str)

        stmt = (
            select(Transaction)
            .options(selectinload(Transaction.merchant), selectinload(Transaction.customer))
            .where(
                Transaction.reference == reference,
                Transaction.created_at == created_at
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    except (ValueError, AttributeError) as e:
        # Invalid datetime format
        return None

async def select_best_processor(session: AsyncSession, priority: list[str], charges: Optional[bool] = None):
    for processor in priority:
        if processor not in PROCESSOR_CHOICES:
            raise ValueError("Invalid processor in priority list")

    processors = priority
    if charges:
        processors = [p for p in priority if p in PROCESSOR_CHOICES]

    for processor in processors:
        transaction = await get_last_transaction_by_processor(session, processor)
        if transaction and transaction.status != TransactionStatus.PENDING.value:
            return processor
    return PROCESSOR_CHARGE_PRIORITY[0]

async def generate_receipt(transaction: Transaction):
    if not transaction.type == TransactionType.DEBIT or not transaction.details:
        return None
    
async def get_transaction_socket_data(transaction: Transaction, merchant: Merchant, session: AsyncSession = None)->str:
    """Get transaction socket data with wallet balances."""
    from services import walletService

    # Get wallet balances for NGN currency (default)
    test_balance = 0
    live_balance = 0

    if session:
        test_balance = await walletService.get_wallet_balance(session, merchant.id, "NGN", "test")
        live_balance = await walletService.get_wallet_balance(session, merchant.id, "NGN", "live")

    return json.dumps({
        "merchant_live_balance": live_balance,
        "merchant_test_balance": test_balance,
        "transaction_data": TransactionResponse.model_validate(transaction).model_dump(mode= 'json')
    })

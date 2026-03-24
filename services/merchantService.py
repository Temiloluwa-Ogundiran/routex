from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from typing import Optional
from database.models.Merchant import Merchant
from database.models.Customer import Customer
from database.models.User import User
from services import tokenService
from settings import PREFIX
import uuid
from sqlalchemy import func
from database.models.Transaction import Transaction
from services import walletService
from enums import tokenEnums, transactionEnums

async def save_merchant(session: AsyncSession, merchant: Merchant)->Merchant:
    session.add(merchant)
    await session.commit()
    await session.refresh(merchant)
    return merchant

async def generate_merchant_id(session: AsyncSession):
    while True:
        merchant_id = f'{PREFIX}-{str(uuid.uuid4())[:5]}'
        merchant = await session.execute(select(Merchant).where(Merchant.id == merchant_id))
        if not merchant.scalar_one_or_none():
            return merchant_id
        
async def create_merchant(name: str, email: str, session: AsyncSession) -> Optional[Merchant]:
    """Return a new merchant if it does not exist else return None"""
    result = await session.execute(select(Merchant).where(Merchant.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        return None

    merchant = Merchant(name=name, email=email, id= await generate_merchant_id(session))
    session.add(merchant)
    await session.commit()
    await session.refresh(merchant)
    await tokenService.create_merchant_token(merchant=merchant, session= session)
    
    #create default merchant ngn wallet
    await walletService.get_or_create_wallet(session= session, merchant= merchant, currency="NGN", mode= "test")
    return merchant

async def get_by_id_or_email(session: AsyncSession, id: Optional[int] = None, email: Optional[str] = None) -> Optional[Merchant]:
    """Return merchant if found else None"""
    if not id and not email:
        return None

    stmt = select(Merchant)
    
    if email:
        stmt = stmt.where(Merchant.email == email)
    elif id:
        stmt = stmt.where(Merchant.id == id)

    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_customers(session: AsyncSession, merchant: Merchant) -> list[Customer]:
    await session.refresh(merchant)  # Ensure relationships are loaded
    return merchant.customers

async def get_users(session: AsyncSession, merchant: Merchant) -> list[User]:
    await session.refresh(merchant)
    return merchant.users

async def get_charge(amount: float, merchant: Merchant) -> float:
    return merchant.flat_charge + (merchant.percentage_charge * amount) / 100

async def get_payout_charge(amount: float, merchant: Merchant)-> float:
    return merchant.payout_flat_charge + (merchant.payout_percentage_charge * amount) / 100

async def get_merchant_revenue(session: AsyncSession, merchant: Merchant, mode: str = tokenEnums.TokenMode.TEST):
    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.merchant_id == merchant.id,
        Transaction.type == transactionEnums.TransactionType.CREDIT,
        Transaction.mode == mode
    )
    result = await session.execute(stmt)
    total = result.scalar_one()
    return total

async def activate_merchant_live_account(session: AsyncSession, merchant: Merchant)->Merchant:
    merchant.is_verified = True
    session.add(merchant)
    await session.commit()
    await tokenService.create_merchant_token(session= session, merchant= merchant, type= tokenEnums.TokenMode.LIVE)
    return merchant

async def deactivate_merchant_live_account(session: AsyncSession, merchant: Merchant):
    if  merchant.is_verified:
        merchant.is_verified = False
        #dectivate the merchant
        session.add(merchant)
        await session.commit()

        await tokenService.delete_token(session= session, merchant= merchant, type= tokenEnums.TokenMode.LIVE)

    return merchant

async def get_merchant_periodic_revenue(session: AsyncSession,  merchant: Merchant, mode = tokenEnums.TokenMode.TEST, start_date = None, end_date= None, group_by: transactionEnums.GroupBy = None):

    trunc_period = func.date_trunc(group_by.value, Transaction.created_at).label("period")
    stmt = (
        select(func.coalesce(func.sum(Transaction.amount), 0).label("revenue"), trunc_period)
        .where(Transaction.merchant_id == merchant.id)
        .where(Transaction.type == transactionEnums.TransactionType.CREDIT)
        .where(Transaction.mode == mode)
    )

    if start_date:
        stmt = stmt.where(Transaction.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.created_at <= end_date)

    stmt = stmt.group_by(trunc_period).order_by(trunc_period)

    results = await session.execute(stmt)

    revenue_breakdown = [
        {"period": row.period.strftime("%Y-%m-%d"), "revenue": row.revenue}
        for row in results
    ]
    return revenue_breakdown
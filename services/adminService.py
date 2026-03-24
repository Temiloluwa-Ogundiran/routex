from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import NoResultFound
from database.models.Admin import Admin
from database.models.Transaction import Transaction
from database.models.UserMerchant import UserMerchant
from database.models.Merchant import Merchant
from database.models.Wallet import Wallet
from services import bcryptService
from enums.userEnums import UserRole
from typing import Optional, Union
from settings import PREFIX, ALGORITHM, AUTH_SECRET
import uuid
from sqlalchemy.orm import selectinload
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from services import userService
from database.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from enums.transactionEnums import TransactionStatus
from enums.tokenEnums import TokenMode
import os

security = HTTPBearer()

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):

    token = credentials.credentials

    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[ALGORITHM], options={"verify_exp": True})
        print(f"jwt payload: {payload}")
        admin_id = payload.get("sub")

        if admin_id is None:
            raise HTTPException(status_code=403, detail="Invalid token")
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    except Exception as e:
        raise HTTPException(status_code=403, detail= f"Error occurred with token validation : {e}")

    admin = await get_admin_by_id(session=session, admin_id = int(admin_id))

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    if not admin.is_active:
        raise HTTPException(status_code=401, detail="Admin not accessible")
    
    return admin

async def check_password(admin: Admin, password: str) -> bool:
    return await bcryptService.check_password(password=password, encrypted=admin.password)

async def update_password(session: AsyncSession, admin:Admin, raw_password):
    admin.password = await bcryptService.make_password(raw_password)
    session.add(admin)
    await session.commit()
    return admin
    
async def get_admin_by_id(session: AsyncSession, admin_id: str) -> Optional[Admin]:
    stmt = select(Admin).where(Admin.id == admin_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_admin_by_email(session: AsyncSession, email: str) -> Optional[Admin]:
    stmt = select(Admin).where(Admin.email == email)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()
    print(f"admin: {admin}")
    return admin


async def create_admin(session: AsyncSession, email: str, name: str, raw_password: str) -> Optional[Admin]:

    encrypted_password = await bcryptService.make_password(password_string=raw_password)
    admin = Admin(email=email, name=name, password=encrypted_password)
    
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin

async def soft_delete_admin(session: AsyncSession, admin_id: str) -> Admin:
    stmt = select(Admin).where(Admin.id == admin_id)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()
    if not admin:
        raise NoResultFound
    
    admin.is_active = False
    await session.commit()
    return admin

async def get_merchants(session: AsyncSession) -> list[Merchant]:
    stmt = select(Merchant).join(UserMerchant)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_total_charges(session: AsyncSession, mode: str, currency: Optional[str] = None):
    """Sum of charge for successful transactions, optionally filtered by currency."""
    charge_stmt = select(func.coalesce(func.sum(Transaction.charge), 0)).where(
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.mode == mode
    )
    if currency:
        charge_stmt = charge_stmt.where(Transaction.currency == currency)

    charge_result = await session.execute(charge_stmt)
    total_charge = charge_result.scalar()

    return total_charge

async def get_total_processor_charges(session: AsyncSession, mode: str, currency: Optional[str] = None):
    """Sum of processor_charge for successful transactions, optionally filtered by currency."""
    processor_stmt = select(func.coalesce(func.sum(Transaction.processor_charge), 0)).where(
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.mode == mode
    )
    if currency:
        processor_stmt = processor_stmt.where(Transaction.currency == currency)

    processor_result = await session.execute(processor_stmt)
    total_processor_charge = processor_result.scalar()

    return total_processor_charge

async def get_merchant_total_charges(session: AsyncSession, mode: str, merchant: Merchant, currency: Optional[str] = None):
    """Sum of charge for successful transactions for a merchant, optionally filtered by currency."""
    charge_stmt = select(func.coalesce(func.sum(Transaction.charge), 0)).where(
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.mode == mode,
        Transaction.merchant_id == merchant.id
    )
    if currency:
        charge_stmt = charge_stmt.where(Transaction.currency == currency)

    charge_result = await session.execute(charge_stmt)
    total_charge = charge_result.scalar()

    return total_charge

async def get_merchant_total_processor_charges(session: AsyncSession, mode: str, merchant: Merchant, currency: Optional[str] = None):
    """Sum of processor_charge for successful transactions for a merchant, optionally filtered by currency."""
    processor_stmt = select(func.coalesce(func.sum(Transaction.processor_charge), 0)).where(
        Transaction.status == TransactionStatus.SUCCESS,
        Transaction.mode == mode,
        Transaction.merchant_id == merchant.id
    )
    if currency:
        processor_stmt = processor_stmt.where(Transaction.currency == currency)

    processor_result = await session.execute(processor_stmt)
    total_processor_charge = processor_result.scalar()

    return total_processor_charge

async def get_total_merchant_balance(session: AsyncSession, mode: str = TokenMode.TEST, currency: Optional[str] = None):
    """Get total balance across all wallets for a specific mode, optionally filtered by currency."""
    stmt = select(func.coalesce(func.sum(Wallet.balance), 0)).where(Wallet.mode == mode)
    if currency:
        stmt = stmt.where(Wallet.currency == currency)

    result = await session.execute(stmt)
    total = result.scalar_one()
    return total

async def get_system_balance(session: AsyncSession, mode: str, currency: Optional[str] = None):
    """Get system balance for a mode, optionally filtered by currency."""
    total_merchant_balace = await get_total_merchant_balance(session, mode, currency)
    total_processor_charges = await get_total_processor_charges(session, mode, currency)
    total_system_charges = await get_total_charges(session, mode, currency)
    return total_merchant_balace + total_system_charges - total_processor_charges

async def get_balances_by_currency(session: AsyncSession, mode: str) -> dict[str, float]:
    """Get wallet balances grouped by currency for a specific mode."""
    stmt = (
        select(
            Wallet.currency,
            func.sum(Wallet.balance).label('total_balance')
        )
        .where(Wallet.mode == mode)
        .group_by(Wallet.currency)
    )
    result = await session.execute(stmt)

    balances = {}
    for row in result:
        balances[row.currency] = float(row.total_balance)

    return balances

async def get_charges_by_currency(session: AsyncSession, mode: str) -> dict[str, dict]:
    """Get system charges and processor charges grouped by currency."""
    # System charges by currency
    system_charges_stmt = (
        select(
            Transaction.currency,
            func.coalesce(func.sum(Transaction.charge), 0).label('total_charge')
        )
        .where(
            Transaction.status == TransactionStatus.SUCCESS,
            Transaction.mode == mode
        )
        .group_by(Transaction.currency)
    )
    system_result = await session.execute(system_charges_stmt)

    # Processor charges by currency
    processor_charges_stmt = (
        select(
            Transaction.currency,
            func.coalesce(func.sum(Transaction.processor_charge), 0).label('total_processor_charge')
        )
        .where(
            Transaction.status == TransactionStatus.SUCCESS,
            Transaction.mode == mode
        )
        .group_by(Transaction.currency)
    )
    processor_result = await session.execute(processor_charges_stmt)

    # Build results
    charges_by_currency = {}

    for row in system_result:
        currency = row.currency
        if currency not in charges_by_currency:
            charges_by_currency[currency] = {
                'system_charges': 0.0,
                'processor_charges': 0.0,
                'profit': 0.0
            }
        charges_by_currency[currency]['system_charges'] = float(row.total_charge)

    for row in processor_result:
        currency = row.currency
        if currency not in charges_by_currency:
            charges_by_currency[currency] = {
                'system_charges': 0.0,
                'processor_charges': 0.0,
                'profit': 0.0
            }
        charges_by_currency[currency]['processor_charges'] = float(row.total_processor_charge)

    # Calculate profit for each currency
    for currency in charges_by_currency:
        system = charges_by_currency[currency]['system_charges']
        processor = charges_by_currency[currency]['processor_charges']
        charges_by_currency[currency]['profit'] = system - processor

    return charges_by_currency

async def get_system_balance_by_currency(session: AsyncSession, mode: str) -> dict[str, float]:
    """Get system balance (merchant balance + profit) grouped by currency."""
    balances = await get_balances_by_currency(session, mode)
    charges = await get_charges_by_currency(session, mode)

    system_balances = {}

    # Get all currencies from both balances and charges
    all_currencies = set(balances.keys()) | set(charges.keys())

    for currency in all_currencies:
        merchant_balance = balances.get(currency, 0.0)
        charge_data = charges.get(currency, {'profit': 0.0})
        profit = charge_data['profit']

        system_balances[currency] = merchant_balance + profit

    return system_balances
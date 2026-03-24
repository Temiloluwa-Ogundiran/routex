from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models.Wallet import Wallet
from database.models.Merchant import Merchant
from enums.tokenEnums import TokenMode
from typing import Optional, List

async def get_or_create_wallet(
    session: AsyncSession,
    merchant: Merchant,
    currency: str,
    mode: str
) -> Wallet:
    """Get or create a wallet for a merchant with specific currency and mode."""
    stmt = select(Wallet).where(
        Wallet.merchant_id == merchant.id,
        Wallet.currency == currency,
        Wallet.mode == mode
    )
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        wallet = Wallet(
            merchant_id=merchant.id,
            currency=currency,
            mode=mode,
            balance=0.0,
            is_active=True
        )
        #give test wallet 5m
        if mode == "test":
            wallet.balance = 50000000

        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)

    return wallet


async def get_wallet(
    session: AsyncSession,
    merchant_id: str,
    currency: str,
    mode: str
) -> Optional[Wallet]:
    """Get a specific wallet for a merchant."""
    stmt = select(Wallet).where(
        Wallet.merchant_id == merchant_id,
        Wallet.currency == currency,
        Wallet.mode == mode
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_merchant_wallets(
    session: AsyncSession,
    merchant_id: str,
    mode: Optional[str] = None
) -> List[Wallet]:
    """Get all wallets for a merchant, optionally filtered by mode."""
    stmt = select(Wallet).where(Wallet.merchant_id == merchant_id)

    if mode:
        stmt = stmt.where(Wallet.mode == mode)

    stmt = stmt.order_by(Wallet.currency, Wallet.mode)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def credit_wallet(
    session: AsyncSession,
    wallet: Wallet,
    amount: float
) -> Wallet:
    """Credit a wallet with a specific amount."""
    wallet.balance += amount
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def debit_wallet(
    session: AsyncSession,
    wallet: Wallet,
    amount: float
) -> Wallet:
    """Debit a wallet with a specific amount."""
    if wallet.balance < amount:
        raise ValueError(f"Insufficient balance. Available: {wallet.balance}, Required: {amount}")

    wallet.balance -= amount
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def get_wallet_balance(
    session: AsyncSession,
    merchant_id: str,
    currency: str,
    mode: str
) -> float:
    """Get the balance of a specific wallet."""
    wallet = await get_wallet(session, merchant_id, currency, mode)
    return wallet.balance if wallet else 0.0


async def transfer_between_wallets(
    session: AsyncSession,
    from_wallet: Wallet,
    to_wallet: Wallet,
    amount: float
) -> tuple[Wallet, Wallet]:
    """Transfer amount from one wallet to another."""
    if from_wallet.balance < amount:
        raise ValueError(f"Insufficient balance in source wallet. Available: {from_wallet.balance}, Required: {amount}")

    from_wallet.balance -= amount
    to_wallet.balance += amount

    await session.commit()
    await session.refresh(from_wallet)
    await session.refresh(to_wallet)

    return from_wallet, to_wallet


async def update_wallet_balance(
    session: AsyncSession,
    wallet: Wallet,
    new_balance: float
) -> Wallet:
    """Set a wallet's balance to a specific value (use with caution)."""
    wallet.balance = new_balance
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def get_total_balance_by_mode(
    session: AsyncSession,
    merchant_id: str,
    mode: str
) -> dict[str, float]:
    """Get total balances across all currencies for a specific mode."""
    wallets = await get_merchant_wallets(session, merchant_id, mode)
    balances = {}

    for wallet in wallets:
        balances[wallet.currency] = wallet.balance

    return balances


async def get_payin_charge(wallet: Wallet, amount: float) -> float:
    """Calculate payin charge based on wallet's charge configuration."""
    return wallet.flat_charge + (wallet.percentage_charge * float(amount)) / 100


async def get_payout_charge(wallet: Wallet, amount: float) -> float:
    """Calculate payout charge based on wallet's charge configuration."""
    return wallet.payout_flat_charge + (wallet.payout_percentage_charge * float(amount)) / 100

"""
Script to top up all test NGN wallets by 5,000,000.

Usage:
    python scripts/topup_test_ngn_wallets.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from settings import DB_URL
from database.models.Wallet import Wallet
# Import all related models to satisfy SQLAlchemy relationship resolution
import database.models.Merchant
import database.models.PaymentLink
import database.models.Customer
import database.models.Transaction
import database.models.BulkPayout
import database.models.User
import database.models.UserMerchant
import database.models.Processor
import database.models.Token
import database.models.Admin

TOPUP_AMOUNT = 5_000_000

engine = create_async_engine(DB_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def topup_test_ngn_wallets():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Wallet).where(
                Wallet.currency == "NGN",
                Wallet.mode == "test"
            )
        )
        wallets = result.scalars().all()

        print(f"Found {len(wallets)} test NGN wallets")

        for wallet in wallets:
            old_balance = wallet.balance
            wallet.balance = old_balance + TOPUP_AMOUNT
            print(f"  merchant={wallet.merchant_id}  {old_balance:,.2f} -> {wallet.balance:,.2f}")

        await session.commit()
        print(f"\nDone. Topped up {len(wallets)} wallets by N{TOPUP_AMOUNT:,} each.")


async def main():
    try:
        await topup_test_ngn_wallets()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

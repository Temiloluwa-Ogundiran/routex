"""
Data migration script to move merchant balances to wallet model.

This script:
1. Creates NGN test and live wallets for all existing merchants
2. Transfers test_balance and live_balance to respective wallets
3. Links existing transactions to appropriate wallets based on currency and mode

Usage:
    python scripts/migrate_balances_to_wallets.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from settings import DB_URL
from database.models.Merchant import Merchant
from database.models.Wallet import Wallet
from database.models.Transaction import Transaction
from database.models.PaymentLink import PaymentLink  # Import all referenced models
from database.models.BulkPayout import BulkPayout
from database.models.Customer import Customer
from enums.tokenEnums import TokenMode

# Create async engine
engine = create_async_engine(DB_URL, echo=True)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def migrate_merchant_balances_to_wallets():
    """Migrate all merchant balances to wallet model."""
    print("=" * 80)
    print("STARTING MERCHANT BALANCE TO WALLET MIGRATION")
    print("=" * 80)

    async with async_session_maker() as session:
        # Fetch all merchants
        result = await session.execute(select(Merchant))
        merchants = result.scalars().all()

        print(f"\nFound {len(merchants)} merchants to migrate")

        wallets_created = 0
        balances_migrated = 0

        for merchant in merchants:
            print(f"\n Processing merchant: {merchant.id} ({merchant.name})")

            # Create or update NGN test wallet
            test_wallet_stmt = select(Wallet).where(
                Wallet.merchant_id == merchant.id,
                Wallet.currency == "NGN",
                Wallet.mode == TokenMode.TEST
            )
            test_wallet_result = await session.execute(test_wallet_stmt)
            test_wallet = test_wallet_result.scalar_one_or_none()

            if not test_wallet:
                test_wallet = Wallet(
                    merchant_id=merchant.id,
                    currency="NGN",
                    mode=TokenMode.TEST,
                    balance=merchant.test_balance or 0.0,
                    percentage_charge=merchant.percentage_charge or 1.5,
                    flat_charge=merchant.flat_charge or 0.0,
                    payout_percentage_charge=merchant.payout_percentage_charge or 0.0,
                    payout_flat_charge=merchant.payout_flat_charge or 50.0,
                    is_active=True
                )
                session.add(test_wallet)
                wallets_created += 1
                print(f"  Created NGN test wallet with balance: N{merchant.test_balance or 0.0}")
                print(f"    Charges: {test_wallet.percentage_charge}% + N{test_wallet.flat_charge}")
            else:
                test_wallet.balance = merchant.test_balance or 0.0
                test_wallet.percentage_charge = merchant.percentage_charge or 1.5
                test_wallet.flat_charge = merchant.flat_charge or 0.0
                test_wallet.payout_percentage_charge = merchant.payout_percentage_charge or 0.0
                test_wallet.payout_flat_charge = merchant.payout_flat_charge or 50.0
                print(f"  Updated NGN test wallet balance: N{merchant.test_balance or 0.0}")

            balances_migrated += 1

            # Create or update NGN live wallet
            live_wallet_stmt = select(Wallet).where(
                Wallet.merchant_id == merchant.id,
                Wallet.currency == "NGN",
                Wallet.mode == TokenMode.LIVE
            )
            live_wallet_result = await session.execute(live_wallet_stmt)
            live_wallet = live_wallet_result.scalar_one_or_none()

            if not live_wallet:
                live_wallet = Wallet(
                    merchant_id=merchant.id,
                    currency="NGN",
                    mode=TokenMode.LIVE,
                    balance=merchant.live_balance or 0.0,
                    percentage_charge=merchant.percentage_charge or 1.5,
                    flat_charge=merchant.flat_charge or 0.0,
                    payout_percentage_charge=merchant.payout_percentage_charge or 0.0,
                    payout_flat_charge=merchant.payout_flat_charge or 50.0,
                    is_active=True
                )
                session.add(live_wallet)
                wallets_created += 1
                print(f"  Created NGN live wallet with balance: N{merchant.live_balance or 0.0}")
                print(f"    Charges: {live_wallet.percentage_charge}% + N{live_wallet.flat_charge}")
            else:
                live_wallet.balance = merchant.live_balance or 0.0
                live_wallet.percentage_charge = merchant.percentage_charge or 1.5
                live_wallet.flat_charge = merchant.flat_charge or 0.0
                live_wallet.payout_percentage_charge = merchant.payout_percentage_charge or 0.0
                live_wallet.payout_flat_charge = merchant.payout_flat_charge or 50.0
                print(f"  Updated NGN live wallet balance: N{merchant.live_balance or 0.0}")

            balances_migrated += 1

        # Commit wallet creation
        await session.commit()

        print(f"\n{'=' * 80}")
        print(f"WALLET CREATION COMPLETE")
        print(f"  - Wallets created: {wallets_created}")
        print(f"  - Balances migrated: {balances_migrated}")
        print(f"{'=' * 80}")


async def link_transactions_to_wallets():
    """Link existing transactions to appropriate wallets based on currency and mode."""
    print("\n" + "=" * 80)
    print("STARTING TRANSACTION TO WALLET LINKING")
    print("=" * 80)

    async with async_session_maker() as session:
        # Fetch all transactions without wallet_id
        result = await session.execute(
            select(Transaction).where(Transaction.wallet_id.is_(None))
        )
        transactions = result.scalars().all()

        print(f"\nFound {len(transactions)} transactions to link")

        linked_count = 0
        not_linked_count = 0

        for i, txn in enumerate(transactions, 1):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(transactions)}")

            # Skip transactions without mode or currency (invalid data)
            if not txn.mode or not txn.currency:
                not_linked_count += 1
                print(f"  WARNING: Skipping txn {txn.id} - missing mode or currency")
                continue

            # Find the appropriate wallet
            wallet_stmt = select(Wallet).where(
                Wallet.merchant_id == txn.merchant_id,
                Wallet.currency == txn.currency,
                Wallet.mode == txn.mode
            )
            wallet_result = await session.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()

            if wallet:
                txn.wallet_id = wallet.id
                linked_count += 1
            else:
                # Create wallet for this currency-mode combination if it doesn't exist
                # Get merchant to copy charge configuration
                merchant_stmt = select(Merchant).where(Merchant.id == txn.merchant_id)
                merchant_result = await session.execute(merchant_stmt)
                merchant = merchant_result.scalar_one_or_none()

                wallet = Wallet(
                    merchant_id=txn.merchant_id,
                    currency=txn.currency,
                    mode=txn.mode,
                    balance=0.0,  # Will be calculated based on transactions
                    percentage_charge=merchant.percentage_charge if merchant else 1.5,
                    flat_charge=merchant.flat_charge if merchant else 0.0,
                    payout_percentage_charge=merchant.payout_percentage_charge if merchant else 0.0,
                    payout_flat_charge=merchant.payout_flat_charge if merchant else 50.0,
                    is_active=True
                )
                session.add(wallet)
                await session.flush()  # Get the wallet ID

                txn.wallet_id = wallet.id
                linked_count += 1
                print(f"  WARNING: Created new wallet for {txn.merchant_id} - {txn.currency} ({txn.mode})")

        await session.commit()

        print(f"\n{'=' * 80}")
        print(f"TRANSACTION LINKING COMPLETE")
        print(f"  - Transactions linked: {linked_count}")
        print(f"  - Transactions not linked: {not_linked_count}")
        print(f"{'=' * 80}")


async def verify_migration():
    """Verify the migration was successful."""
    print("\n" + "=" * 80)
    print("VERIFYING MIGRATION")
    print("=" * 80)

    async with async_session_maker() as session:
        # Count wallets
        wallet_count_result = await session.execute(select(Wallet))
        wallet_count = len(wallet_count_result.scalars().all())

        # Count transactions without wallet_id
        unlinked_txn_result = await session.execute(
            select(Transaction).where(Transaction.wallet_id.is_(None))
        )
        unlinked_count = len(unlinked_txn_result.scalars().all())

        # Count merchants
        merchant_result = await session.execute(select(Merchant))
        merchant_count = len(merchant_result.scalars().all())

        print(f"\nVerification Results:")
        print(f"  - Total merchants: {merchant_count}")
        print(f"  - Total wallets created: {wallet_count}")
        print(f"  - Expected minimum wallets (2 per merchant): {merchant_count * 2}")
        print(f"  - Transactions without wallet link: {unlinked_count}")

        if unlinked_count == 0:
            print(f"\nMIGRATION SUCCESSFUL - All transactions linked to wallets")
        else:
            print(f"\nWARNING - {unlinked_count} transactions still unlinked")

        print("=" * 80)


async def main():
    """Run all migration steps."""
    try:
        # Step 1: Migrate balances to wallets
        await migrate_merchant_balances_to_wallets()

        # Step 2: Link transactions to wallets
        await link_transactions_to_wallets()

        # Step 3: Verify migration
        await verify_migration()

        print("\n" + "=" * 80)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review the migration results above")
        print("2. Test the application with wallet-based operations")
        print("3. Once verified, you can remove test_balance and live_balance")
        print("   columns from the merchant table in a future migration")

    except Exception as e:
        print(f"\nERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

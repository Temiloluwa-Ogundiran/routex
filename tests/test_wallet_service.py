"""
Unit tests for wallet service functions
"""
import pytest
from services import walletService
from database.models.Wallet import Wallet


@pytest.mark.asyncio
class TestWalletService:
    """Test wallet service functions"""

    async def test_get_payin_charge(self, test_wallet):
        """Test payin charge calculation"""
        amount = 1000.0
        charge = await walletService.get_payin_charge(test_wallet, amount)

        # Expected: flat_charge + (percentage_charge * amount) / 100
        # 100 + (1.5 * 1000) / 100 = 100 + 15 = 115
        assert charge == 115.0

    async def test_get_payout_charge(self, test_wallet):
        """Test payout charge calculation"""
        amount = 1000.0
        charge = await walletService.get_payout_charge(test_wallet, amount)

        # Expected: payout_flat_charge + (payout_percentage_charge * amount) / 100
        # 50 + (1.0 * 1000) / 100 = 50 + 10 = 60
        assert charge == 60.0

    async def test_get_or_create_wallet_existing(self, async_session, test_merchant, test_wallet):
        """Test get_or_create_wallet with existing wallet"""
        wallet = await walletService.get_or_create_wallet(
            session=async_session,
            merchant=test_merchant,
            currency="NGN",
            mode="test"
        )

        assert wallet.id == test_wallet.id
        assert wallet.currency == "NGN"
        assert wallet.mode == "test"

    async def test_get_or_create_wallet_new(self, async_session, test_merchant):
        """Test get_or_create_wallet creating new wallet"""
        wallet = await walletService.get_or_create_wallet(
            session=async_session,
            merchant=test_merchant,
            currency="USD",
            mode="live"
        )

        assert wallet.id is not None
        assert wallet.currency == "USD"
        assert wallet.mode == "live"
        assert wallet.balance == 0.0

    async def test_credit_wallet(self, async_session, test_wallet):
        """Test crediting a wallet"""
        initial_balance = test_wallet.balance
        credit_amount = 500.0

        updated_wallet = await walletService.credit_wallet(
            session=async_session,
            wallet=test_wallet,
            amount=credit_amount
        )

        assert updated_wallet.balance == initial_balance + credit_amount

    async def test_debit_wallet_success(self, async_session, test_wallet):
        """Test debiting a wallet with sufficient balance"""
        initial_balance = test_wallet.balance
        debit_amount = 500.0

        updated_wallet = await walletService.debit_wallet(
            session=async_session,
            wallet=test_wallet,
            amount=debit_amount
        )

        assert updated_wallet.balance == initial_balance - debit_amount

    async def test_debit_wallet_insufficient_balance(self, async_session, test_wallet):
        """Test debiting a wallet with insufficient balance"""
        debit_amount = test_wallet.balance + 1000.0

        with pytest.raises(ValueError, match="Insufficient balance"):
            await walletService.debit_wallet(
                session=async_session,
                wallet=test_wallet,
                amount=debit_amount
            )

    async def test_get_wallet(self, async_session, test_merchant, test_wallet):
        """Test getting a specific wallet"""
        wallet = await walletService.get_wallet(
            session=async_session,
            merchant_id=test_merchant.id,
            currency="NGN",
            mode="test"
        )

        assert wallet is not None
        assert wallet.id == test_wallet.id

    async def test_get_wallet_nonexistent(self, async_session, test_merchant):
        """Test getting a non-existent wallet"""
        wallet = await walletService.get_wallet(
            session=async_session,
            merchant_id=test_merchant.id,
            currency="EUR",
            mode="test"
        )

        assert wallet is None

    async def test_get_merchant_wallets(self, async_session, test_merchant, test_wallet):
        """Test getting all merchant wallets"""
        # Create additional wallet
        wallet2 = Wallet(
            merchant_id=test_merchant.id,
            currency="USD",
            mode="test",
            balance=5000.0,
            is_active=True
        )
        async_session.add(wallet2)
        await async_session.commit()

        wallets = await walletService.get_merchant_wallets(
            session=async_session,
            merchant_id=test_merchant.id
        )

        assert len(wallets) == 2

    async def test_get_wallet_balance(self, async_session, test_merchant, test_wallet):
        """Test getting wallet balance"""
        balance = await walletService.get_wallet_balance(
            session=async_session,
            merchant_id=test_merchant.id,
            currency="NGN",
            mode="test"
        )

        assert balance == test_wallet.balance

    async def test_transfer_between_wallets(self, async_session, test_merchant):
        """Test transferring funds between wallets"""
        # Create two wallets
        wallet1 = Wallet(
            merchant_id=test_merchant.id,
            currency="NGN",
            mode="test",
            balance=10000.0,
            is_active=True
        )
        wallet2 = Wallet(
            merchant_id=test_merchant.id,
            currency="NGN",
            mode="live",
            balance=5000.0,
            is_active=True
        )
        async_session.add_all([wallet1, wallet2])
        await async_session.commit()
        await async_session.refresh(wallet1)
        await async_session.refresh(wallet2)

        transfer_amount = 2000.0
        updated_wallet1, updated_wallet2 = await walletService.transfer_between_wallets(
            session=async_session,
            from_wallet=wallet1,
            to_wallet=wallet2,
            amount=transfer_amount
        )

        assert updated_wallet1.balance == 8000.0
        assert updated_wallet2.balance == 7000.0

    async def test_transfer_insufficient_balance(self, async_session, test_merchant):
        """Test transferring with insufficient balance"""
        wallet1 = Wallet(
            merchant_id=test_merchant.id,
            currency="NGN",
            mode="test",
            balance=1000.0,
            is_active=True
        )
        wallet2 = Wallet(
            merchant_id=test_merchant.id,
            currency="NGN",
            mode="live",
            balance=5000.0,
            is_active=True
        )
        async_session.add_all([wallet1, wallet2])
        await async_session.commit()
        await async_session.refresh(wallet1)
        await async_session.refresh(wallet2)

        with pytest.raises(ValueError, match="Insufficient balance"):
            await walletService.transfer_between_wallets(
                session=async_session,
                from_wallet=wallet1,
                to_wallet=wallet2,
                amount=2000.0
            )

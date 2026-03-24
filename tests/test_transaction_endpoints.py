"""
Unit tests for transaction endpoints with wallet integration
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from database.models.Transaction import Transaction
from datetime import datetime


@pytest.mark.asyncio
class TestWalletTransactionEndpoints:
    """Test wallet-specific transaction endpoints"""

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_wallet_transactions(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        async_session,
        test_user,
        test_merchant,
        test_wallet,
        test_customer
    ):
        """Test GET /wallet-transactions endpoint"""
        # Create test transactions
        txn1 = Transaction(
            merchant_id=test_merchant.id,
            wallet_id=test_wallet.id,
            customer_id=test_customer.id,
            amount=1000.0,
            charge=115.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="kora",
            reference="TEST_001",
            processor_reference="PROC_001"
        )
        async_session.add(txn1)
        await async_session.commit()

        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(
            f"/wallet-transactions?wallet_id={test_wallet.id}&page=1&page_size=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "wallet_info" in data
        assert data["wallet_info"]["wallet_id"] == test_wallet.id

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_wallet_transaction_stats(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        async_session,
        test_user,
        test_merchant,
        test_wallet,
        test_customer
    ):
        """Test GET /wallet-transaction-stats endpoint"""
        # Create test transactions
        credit_txn = Transaction(
            merchant_id=test_merchant.id,
            wallet_id=test_wallet.id,
            customer_id=test_customer.id,
            amount=1000.0,
            charge=115.0,
            currency="NGN",
            type="credit",
            status="success",
            mode="test",
            processor="kora",
            reference="CREDIT_001",
            processor_reference="PROC_CREDIT_001"
        )
        debit_txn = Transaction(
            merchant_id=test_merchant.id,
            wallet_id=test_wallet.id,
            customer_id=test_customer.id,
            amount=500.0,
            charge=60.0,
            currency="NGN",
            type="debit",
            status="success",
            mode="test",
            processor="kora",
            reference="DEBIT_001",
            processor_reference="PROC_DEBIT_001"
        )
        async_session.add_all([credit_txn, debit_txn])
        await async_session.commit()

        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(f"/wallet-transaction-stats?wallet_id={test_wallet.id}")

        assert response.status_code == 200
        data = response.json()
        assert "wallet_info" in data
        assert "transaction_summary" in data
        assert "credits" in data
        assert "debits" in data
        assert "charges" in data

        # Verify stats
        assert data["credits"]["count"] >= 1
        assert data["debits"]["count"] >= 1
        assert data["charges"]["payin_percentage"] == test_wallet.percentage_charge
        assert data["charges"]["payout_percentage"] == test_wallet.payout_percentage_charge

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_merchant_transactions_by_wallet(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test GET /merchant-transactions-by-wallet endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(
            f"/merchant-transactions-by-wallet?merchant_id={test_merchant.id}&mode=test"
        )

        assert response.status_code == 200
        data = response.json()
        assert "merchant_id" in data
        assert "wallets" in data
        assert "summary" in data
        assert isinstance(data["wallets"], list)

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_merchant_transactions_with_wallet_filter(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test GET /merchant-transactions with wallet_id filter"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(
            f"/merchant-transactions?merchant_id={test_merchant.id}&mode=test&wallet_id={test_wallet.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "filters" in data
        assert data["filters"]["wallet_id"] == test_wallet.id


@pytest.mark.asyncio
class TestPayoutWithWallet:
    """Test payout endpoints with wallet integration"""

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    @patch('services.walletService.get_wallet')
    @patch('services.walletService.get_payout_charge')
    @patch('external_services.koraService.payout')
    async def test_payout_success(
        self,
        mock_kora_payout,
        mock_get_payout_charge,
        mock_get_wallet,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test successful payout with wallet"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True
        mock_get_wallet.return_value = test_wallet
        mock_get_payout_charge.return_value = 60.0
        mock_kora_payout.return_value = (True, "Success", 200, 1)

        payout_data = {
            "amount": 1000.0,
            "currency": "NGN",
            "customer": {
                "account_number": "0123456789",
                "bank_code": "058"
            },
            "email": "customer@test.com"
        }

        response = await client.post(
            f"/payout?merchant_id={test_merchant.id}",
            json=payout_data
        )

        assert response.status_code in [200, 201]
        # Verify wallet was used for charge calculation
        mock_get_payout_charge.assert_called_once()

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    @patch('services.walletService.get_wallet')
    async def test_payout_wallet_not_found(
        self,
        mock_get_wallet,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant
    ):
        """Test payout when wallet doesn't exist"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True
        mock_get_wallet.return_value = None

        payout_data = {
            "amount": 1000.0,
            "currency": "EUR",  # Non-existent wallet
            "customer": {
                "account_number": "0123456789",
                "bank_code": "058"
            },
            "email": "customer@test.com"
        }

        response = await client.post(
            f"/payout?merchant_id={test_merchant.id}",
            json=payout_data
        )

        assert response.status_code == 400
        assert "Wallet not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestWebhookWalletIntegration:
    """Test webhook handlers with wallet integration"""

    async def test_payin_success_handler_uses_wallet(
        self,
        async_session,
        test_merchant,
        test_wallet,
        test_customer
    ):
        """Test payin success handler uses wallet charges"""
        from api.v1.webhooks import payin_success_handler

        # Create pending transaction
        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=1000.0,
            currency="NGN",
            type="credit",
            status="pending",
            mode="test",
            processor="kora",
            reference="WEBHOOK_TEST_001",
            processor_reference="PROC_WEBHOOK_001"
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        # Call handler
        await payin_success_handler(
            session=async_session,
            transaction=transaction,
            processor_fee=5.0
        )

        # Refresh transaction
        await async_session.refresh(transaction)

        # Verify wallet was used
        assert transaction.status == "success"
        assert transaction.charge > 0  # Charge was calculated from wallet
        assert transaction.wallet_id == test_wallet.id  # Transaction linked to wallet

        # Verify wallet was credited
        await async_session.refresh(test_wallet)
        # Balance should be increased by (amount - charge)
        # Initial: 10000, Amount: 1000, Charge: 115, New: 10885
        assert test_wallet.balance > 10000.0

    async def test_payout_success_handler_uses_wallet(
        self,
        async_session,
        test_merchant,
        test_wallet,
        test_customer
    ):
        """Test payout success handler uses wallet charges"""
        from api.v1.webhooks import payout_success_handler

        initial_balance = test_wallet.balance

        # Create pending payout transaction
        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            wallet_id=test_wallet.id,
            amount=500.0,
            currency="NGN",
            type="debit",
            status="pending",
            mode="test",
            processor="kora",
            reference="PAYOUT_WEBHOOK_001",
            processor_reference="PROC_PAYOUT_001"
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        # Call handler
        await payout_success_handler(
            session=async_session,
            processor_reference="PROC_PAYOUT_001",
            processor_fee=3.0,
            mode="test"
        )

        # Refresh transaction and wallet
        await async_session.refresh(transaction)
        await async_session.refresh(test_wallet)

        # Verify
        assert transaction.status == "success"
        assert transaction.charge > 0  # Charge was calculated from wallet
        # Wallet should be debited by (amount + charge)
        assert test_wallet.balance < initial_balance

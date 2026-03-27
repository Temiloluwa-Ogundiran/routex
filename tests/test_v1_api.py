"""
Unit tests for V1 API endpoints
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
class TestV1PayoutEndpoint:
    """Test V1 payout API endpoint"""

    @patch('services.tokenService.verify_token')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.walletService.get_wallet')
    @patch('services.walletService.get_payout_charge')
    async def test_payout_success(
        self,
        mock_get_payout_charge,
        mock_get_wallet,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant,
        test_wallet
    ):
        """Test successful payout simulation deducts merchant balance internally."""
        # Setup mocks
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_get_wallet.return_value = test_wallet
        mock_get_payout_charge.return_value = 60.0

        payout_data = {
            "reference": "TEST_REF_001",
            "amount": 1000.0,
            "currency": "NGN",
            "destination": {
                "account_number": "0123456789",
                "bank_code": "058"
            },
            "customer": {
                "email": "customer@test.com"
            },
            "narration": "Test payout"
        }

        response = await client.post(
            "/api/v1/payout",
            json=payout_data,
            headers={"Authorization": f"Bearer aggsk_test_{test_merchant.id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == True
        assert data["message"] == "Payout simulated successfully"
        assert data["reference"] == "TEST_REF_001"
        assert "selected_gateway" not in data
        assert "gateway_reference" not in data
        assert data["data"]["balance_before"] == 10000.0
        assert data["data"]["balance_after"] == 8940.0
        assert data["data"]["total_deducted"] == 1060.0

    @patch('services.tokenService.verify_token')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.walletService.get_wallet')
    async def test_payout_insufficient_balance(
        self,
        mock_get_wallet,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant
    ):
        """Test payout with insufficient balance"""
        from database.models.Wallet import Wallet

        # Mock wallet with low balance
        low_balance_wallet = Wallet(
            merchant_id=test_merchant.id,
            currency="NGN",
            mode="test",
            balance=100.0,  # Low balance
            payout_percentage_charge=1.0,
            payout_flat_charge=50.0
        )

        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_get_wallet.return_value = low_balance_wallet

        payout_data = {
            "reference": "TEST_REF_002",
            "amount": 1000.0,
            "currency": "NGN",
            "destination": {
                "account_number": "0123456789",
                "bank_code": "058"
            },
            "customer": {
                "email": "customer@test.com"
            }
        }

        response = await client.post(
            "/api/v1/payout",
            json=payout_data,
            headers={"Authorization": f"Bearer aggsk_test_{test_merchant.id}"}
        )

        assert response.status_code == 400
        assert "Insufficient balance" in response.json()["detail"]

    @patch('services.tokenService.verify_token')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.walletService.get_wallet')
    async def test_payout_wallet_not_found(
        self,
        mock_get_wallet,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant
    ):
        """Test payout when wallet doesn't exist"""
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_get_wallet.return_value = None

        payout_data = {
            "reference": "TEST_REF_003",
            "amount": 1000.0,
            "currency": "USD",
            "destination": {
                "account_number": "0123456789",
                "bank_code": "058"
            },
            "customer": {
                "email": "customer@test.com"
            }
        }

        response = await client.post(
            "/api/v1/payout",
            json=payout_data,
            headers={"Authorization": f"Bearer aggsk_test_{test_merchant.id}"}
        )

        assert response.status_code == 400
        assert "Wallet not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestV1InitializeEndpoint:
    """Test V1 initialize transaction endpoint"""

    @patch('services.tokenService.verify_token')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('external_services.flutterwaveService.post_request')
    async def test_initialize_success(
        self,
        mock_post_request,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant,
        test_customer
    ):
        """Test successful transaction initialization"""
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_post_request.return_value = (
            {"data": {"link": "https://checkout.example.com/xyz"}},
            200,
        )

        init_data = {
            "reference": "TEST_INIT_001",
            "amount": 5000.0,
            "currency": "NGN",
            "customer": {
                "email": "customer@test.com"
            },
            "redirect_url": "https://example.com/callback"
        }

        response = await client.post(
            "/api/v1/initiate",
            json=init_data,
            headers={"Authorization": f"Bearer aggsk_test_{test_merchant.id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == True
        assert "checkout_url" in data
        assert data["selected_gateway"] == "fltw"

    @patch('services.tokenService.verify_token')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.transactionService.get_transaction_by_merchant_and_reference')
    async def test_initialize_duplicate_reference(
        self,
        mock_get_txn,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant
    ):
        """Test initialization with duplicate reference"""
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_get_txn.return_value = MagicMock()  # Existing transaction

        init_data = {
            "reference": "DUPLICATE_REF",
            "amount": 5000.0,
            "currency": "NGN",
            "customer": {
                "email": "customer@test.com"
            }
        }

        response = await client.post(
            "/api/v1/initiate",
            json=init_data,
            headers={"Authorization": f"Bearer aggsk_test_{test_merchant.id}"}
        )

        assert response.status_code == 400
        assert "not unique" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestV1VerifyEndpoint:
    """Test V1 verify transaction endpoint"""

    @patch('services.tokenService.verify_token')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.transactionService.get_transaction_by_merchant_and_reference')
    async def test_verify_success(
        self,
        mock_get_txn,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant,
        test_customer
    ):
        """Test successful transaction verification"""
        from database.models.Transaction import Transaction
        from datetime import datetime

        # Mock transaction
        mock_transaction = MagicMock(spec=Transaction)
        mock_transaction.id = 1
        mock_transaction.mode = "test"
        mock_transaction.type = "credit"
        mock_transaction.amount = 5000.0
        mock_transaction.charge = 115.0
        mock_transaction.currency = "NGN"
        mock_transaction.reference = "TEST_REF_001"
        mock_transaction.status = "success"
        mock_transaction.selected_gateway = "fltw"
        mock_transaction.processor_reference = "FLTW_PROC_001"
        mock_transaction.narration = "Test payment"
        mock_transaction.metadata_payload = {}
        mock_transaction.created_at = datetime.now()
        mock_transaction.updated_at = datetime.now()
        mock_transaction.customer = test_customer

        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_get_txn.return_value = mock_transaction

        response = await client.get(
            "/api/v1/transactions/verify?reference=TEST_REF_001",
            headers={"Authorization": f"Bearer aggsk_test_{test_merchant.id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == True
        assert "data" in data
        assert data["data"]["selected_gateway"] == "fltw"

    @patch('services.tokenService.verify_token')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.transactionService.get_transaction_by_merchant_and_reference')
    async def test_verify_not_found(
        self,
        mock_get_txn,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant
    ):
        """Test verification of non-existent transaction"""
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_get_txn.return_value = None

        response = await client.get(
            "/api/v1/transactions/verify?reference=NONEXISTENT",
            headers={"Authorization": f"Bearer aggsk_test_{test_merchant.id}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

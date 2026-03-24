"""
Unit tests for wallet API endpoints
"""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
class TestWalletEndpoints:
    """Test wallet API endpoints"""

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_merchant_wallets(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test GET /wallets endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(
            f"/wallets?merchant_id={test_merchant.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["currency"] == "NGN"

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_wallets_by_criteria(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test GET /wallets/by-criteria endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(
            f"/wallets/by-criteria?merchant_id={test_merchant.id}&currencies=NGN,USD&mode=test"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_wallet_by_id(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test GET /wallets/{wallet_id} endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(f"/wallets/{test_wallet.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_wallet.id
        assert data["currency"] == "NGN"
        assert data["balance"] == test_wallet.balance

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_create_wallet(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant
    ):
        """Test POST /wallets/create endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        wallet_data = {
            "merchant_id": test_merchant.id,
            "currency": "USD",
            "mode": "live",
            "percentage_charge": 2.0,
            "flat_charge": 150.0,
            "payout_percentage_charge": 1.5,
            "payout_flat_charge": 75.0
        }

        response = await client.post("/wallets/create", json=wallet_data)

        assert response.status_code == 201
        data = response.json()
        assert data["currency"] == "USD"
        assert data["mode"] == "live"
        assert data["percentage_charge"] == 2.0

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_update_wallet_charges(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test PATCH /wallets/{wallet_id}/charges endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        update_data = {
            "percentage_charge": 2.5,
            "flat_charge": 200.0
        }

        response = await client.patch(
            f"/wallets/{test_wallet.id}/charges",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["percentage_charge"] == 2.5
        assert data["flat_charge"] == 200.0

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_toggle_wallet_active(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test PATCH /wallets/{wallet_id}/toggle-active endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        initial_status = test_wallet.is_active

        response = await client.patch(f"/wallets/{test_wallet.id}/toggle-active")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] != initial_status

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_get_wallet_balance_summary(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_merchant,
        test_wallet
    ):
        """Test GET /wallets/balance/summary endpoint"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = True

        response = await client.get(
            f"/wallets/balance/summary?merchant_id={test_merchant.id}&mode=test"
        )

        assert response.status_code == 200
        data = response.json()
        assert "wallets" in data
        assert "total_balances_by_currency" in data

    @patch('services.userService.get_current_user')
    @patch('services.userService.user_in_merchant')
    async def test_unauthorized_access(
        self,
        mock_user_in_merchant,
        mock_get_current_user,
        client,
        test_user,
        test_wallet
    ):
        """Test unauthorized access to wallet"""
        mock_get_current_user.return_value = test_user
        mock_user_in_merchant.return_value = False

        response = await client.get(f"/wallets/{test_wallet.id}")

        assert response.status_code == 401

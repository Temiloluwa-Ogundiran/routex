"""
Unit tests for admin endpoints with currency-sensitive functionality
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from database.models.Admin import Admin
from database.models.Wallet import Wallet
from database.models.Transaction import Transaction


@pytest.fixture
async def test_admin(async_session):
    """Create a test admin user"""
    admin = Admin(
        email="admin@test.com",
        name="Test Admin",
        password="$2b$12$hashed_password",  # Hashed password
        is_active=True
    )
    async_session.add(admin)
    await async_session.commit()
    await async_session.refresh(admin)
    return admin


@pytest.mark.asyncio
class TestAdminAuthentication:
    """Test admin authentication endpoints"""

    @patch('services.adminService.get_admin_by_email')
    @patch('services.adminService.check_password')
    @patch('services.tokenService.create_access_token')
    async def test_admin_login_success(
        self,
        mock_create_token,
        mock_check_password,
        mock_get_admin,
        client,
        test_admin
    ):
        """Test successful admin login"""
        mock_get_admin.return_value = test_admin
        mock_check_password.return_value = True
        mock_create_token.return_value = "test_token_123"

        login_data = {
            "email": "admin@test.com",
            "password": "password123"
        }

        response = await client.post("/admin/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == True
        assert data["message"] == "Login successful"
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["data"]["email"] == test_admin.email

    @patch('services.adminService.get_admin_by_email')
    async def test_admin_login_not_found(
        self,
        mock_get_admin,
        client
    ):
        """Test login with non-existent admin"""
        mock_get_admin.return_value = None

        login_data = {
            "email": "nonexistent@test.com",
            "password": "password123"
        }

        response = await client.post("/admin/login", json=login_data)

        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"].lower()

    @patch('services.adminService.get_admin_by_email')
    @patch('services.adminService.check_password')
    async def test_admin_login_wrong_password(
        self,
        mock_check_password,
        mock_get_admin,
        client,
        test_admin
    ):
        """Test login with wrong password"""
        mock_get_admin.return_value = test_admin
        mock_check_password.return_value = False

        login_data = {
            "email": "admin@test.com",
            "password": "wrongpassword"
        }

        response = await client.post("/admin/login", json=login_data)

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestAdminBalanceEndpoints:
    """Test admin balance endpoints with currency support"""

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_system_balance')
    async def test_get_total_balance_all_currencies(
        self,
        mock_get_system_balance,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get total balance without currency filter"""
        mock_get_current_admin.return_value = test_admin
        mock_get_system_balance.side_effect = [50000.0, 100000.0]  # test, live

        response = await client.get("/admin/total-balance")

        assert response.status_code == 200
        data = response.json()
        assert data["test_balance"] == 50000.0
        assert data["live_balance"] == 100000.0

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_system_balance')
    async def test_get_total_balance_with_currency(
        self,
        mock_get_system_balance,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get total balance filtered by currency"""
        mock_get_current_admin.return_value = test_admin
        mock_get_system_balance.side_effect = [30000.0, 60000.0]  # test, live for NGN

        response = await client.get("/admin/total-balance?currency=NGN")

        assert response.status_code == 200
        data = response.json()
        assert data["test_balance"] == 30000.0
        assert data["live_balance"] == 60000.0
        # Verify currency parameter was passed
        assert mock_get_system_balance.call_count == 2

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_balances_by_currency')
    async def test_get_balances_by_currency(
        self,
        mock_get_balances,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get balances grouped by currency"""
        mock_get_current_admin.return_value = test_admin
        mock_get_balances.return_value = {
            "NGN": 30000.0,
            "USD": 15000.0,
            "GHS": 5000.0
        }

        response = await client.get("/admin/balances-by-currency?mode=test")

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "test"
        assert data["total_currencies"] == 3
        assert data["balances"]["NGN"] == 30000.0
        assert data["balances"]["USD"] == 15000.0
        assert data["balances"]["GHS"] == 5000.0

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_total_merchant_balance')
    async def test_get_merchant_balance(
        self,
        mock_get_merchant_balance,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get total merchant wallet balances"""
        mock_get_current_admin.return_value = test_admin
        mock_get_merchant_balance.side_effect = [25000.0, 50000.0]  # test, live

        response = await client.get("/admin/merchant-balance")

        assert response.status_code == 200
        data = response.json()
        assert data["test_balance"] == 25000.0
        assert data["live_balance"] == 50000.0


@pytest.mark.asyncio
class TestAdminChargesEndpoints:
    """Test admin charges endpoints with currency support"""

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_total_processor_charges')
    @patch('services.adminService.get_total_charges')
    async def test_get_total_amounts_all_currencies(
        self,
        mock_get_total_charges,
        mock_get_processor_charges,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get total amounts without currency filter"""
        mock_get_current_admin.return_value = test_admin
        mock_get_processor_charges.return_value = 500.0
        mock_get_total_charges.return_value = 2000.0

        response = await client.get("/admin/total-amounts?mode=test")

        assert response.status_code == 200
        data = response.json()
        assert data["processor_charges"] == 500.0
        assert data["system_charges"] == 2000.0
        assert data["profit"] == 1500.0

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_total_processor_charges')
    @patch('services.adminService.get_total_charges')
    async def test_get_total_amounts_with_currency(
        self,
        mock_get_total_charges,
        mock_get_processor_charges,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get total amounts filtered by currency"""
        mock_get_current_admin.return_value = test_admin
        mock_get_processor_charges.return_value = 300.0
        mock_get_total_charges.return_value = 1200.0

        response = await client.get("/admin/total-amounts?mode=test&currency=NGN")

        assert response.status_code == 200
        data = response.json()
        assert data["processor_charges"] == 300.0
        assert data["system_charges"] == 1200.0
        assert data["profit"] == 900.0

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_charges_by_currency')
    async def test_get_charges_by_currency(
        self,
        mock_get_charges,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get charges grouped by currency"""
        mock_get_current_admin.return_value = test_admin
        mock_get_charges.return_value = {
            "NGN": {
                "system_charges": 1200.0,
                "processor_charges": 300.0,
                "profit": 900.0
            },
            "USD": {
                "system_charges": 800.0,
                "processor_charges": 200.0,
                "profit": 600.0
            }
        }

        response = await client.get("/admin/charges-by-currency?mode=test")

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "test"
        assert data["total_currencies"] == 2
        assert data["charges"]["NGN"]["profit"] == 900.0
        assert data["charges"]["USD"]["profit"] == 600.0

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_system_balance_by_currency')
    async def test_get_system_balance_by_currency(
        self,
        mock_get_system_balance,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get system balance grouped by currency"""
        mock_get_current_admin.return_value = test_admin
        mock_get_system_balance.return_value = {
            "NGN": 31200.0,
            "USD": 15800.0,
            "GHS": 5000.0
        }

        response = await client.get("/admin/system-balance-by-currency?mode=test")

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "test"
        assert data["total_currencies"] == 3
        assert data["grand_total"] == 52000.0
        assert data["balances"]["NGN"] == 31200.0
        assert data["balances"]["USD"] == 15800.0


@pytest.mark.asyncio
class TestAdminMerchantEndpoints:
    """Test admin merchant management endpoints"""

    @patch('services.adminService.get_current_admin')
    @patch('services.adminService.get_merchants')
    async def test_get_all_merchants(
        self,
        mock_get_merchants,
        mock_get_current_admin,
        client,
        test_admin,
        test_merchant
    ):
        """Test get all merchants"""
        mock_get_current_admin.return_value = test_admin
        mock_get_merchants.return_value = [test_merchant]

        response = await client.get("/admin/merchants")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @patch('services.adminService.get_current_admin')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.adminService.get_merchant_total_processor_charges')
    @patch('services.adminService.get_merchant_total_charges')
    async def test_get_merchant_amounts(
        self,
        mock_get_merchant_charges,
        mock_get_processor_charges,
        mock_get_merchant,
        mock_get_current_admin,
        client,
        test_admin,
        test_merchant
    ):
        """Test get merchant amounts without currency filter"""
        mock_get_current_admin.return_value = test_admin
        mock_get_merchant.return_value = test_merchant
        mock_get_processor_charges.return_value = 200.0
        mock_get_merchant_charges.return_value = 800.0

        response = await client.get(
            f"/admin/merchant-amounts?merchant_id={test_merchant.id}&mode=test"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["merchant_processor_charges"] == 200.0
        assert data["merchant_system_charges"] == 800.0
        assert data["profit"] == 600.0

    @patch('services.adminService.get_current_admin')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.adminService.get_merchant_total_processor_charges')
    @patch('services.adminService.get_merchant_total_charges')
    async def test_get_merchant_amounts_with_currency(
        self,
        mock_get_merchant_charges,
        mock_get_processor_charges,
        mock_get_merchant,
        mock_get_current_admin,
        client,
        test_admin,
        test_merchant
    ):
        """Test get merchant amounts filtered by currency"""
        mock_get_current_admin.return_value = test_admin
        mock_get_merchant.return_value = test_merchant
        mock_get_processor_charges.return_value = 150.0
        mock_get_merchant_charges.return_value = 600.0

        response = await client.get(
            f"/admin/merchant-amounts?merchant_id={test_merchant.id}&mode=test&currency=NGN"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["merchant_processor_charges"] == 150.0
        assert data["merchant_system_charges"] == 600.0
        assert data["profit"] == 450.0

    @patch('services.adminService.get_current_admin')
    async def test_get_merchant_amounts_missing_identifier(
        self,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get merchant amounts without merchant identifier"""
        mock_get_current_admin.return_value = test_admin

        response = await client.get("/admin/merchant-amounts?mode=test")

        assert response.status_code == 422
        assert "merchant email or id must be provided" in response.json()["detail"].lower()

    @patch('services.adminService.get_current_admin')
    @patch('services.merchantService.get_by_id_or_email')
    async def test_get_merchant_amounts_not_found(
        self,
        mock_get_merchant,
        mock_get_current_admin,
        client,
        test_admin
    ):
        """Test get merchant amounts for non-existent merchant"""
        mock_get_current_admin.return_value = test_admin
        mock_get_merchant.return_value = None

        response = await client.get(
            "/admin/merchant-amounts?merchant_id=nonexistent&mode=test"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('services.adminService.get_current_admin')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.merchantService.activate_merchant_live_account')
    async def test_activate_merchant(
        self,
        mock_activate,
        mock_get_merchant,
        mock_get_current_admin,
        client,
        test_admin,
        test_merchant
    ):
        """Test activate merchant live account"""
        test_merchant.is_verified = False
        mock_get_current_admin.return_value = test_admin
        mock_get_merchant.return_value = test_merchant

        activated_merchant = MagicMock()
        activated_merchant.is_verified = True
        mock_activate.return_value = activated_merchant

        activate_data = {
            "merchant_id": test_merchant.id
        }

        response = await client.post("/admin/activate-merchant", json=activate_data)

        assert response.status_code == 200
        mock_activate.assert_called_once()

    @patch('services.adminService.get_current_admin')
    @patch('services.merchantService.get_by_id_or_email')
    @patch('services.merchantService.deactivate_merchant_live_account')
    async def test_deactivate_merchant(
        self,
        mock_deactivate,
        mock_get_merchant,
        mock_get_current_admin,
        client,
        test_admin,
        test_merchant
    ):
        """Test deactivate merchant live account"""
        test_merchant.is_verified = True
        mock_get_current_admin.return_value = test_admin
        mock_get_merchant.return_value = test_merchant

        deactivate_data = {
            "merchant_id": test_merchant.id
        }

        response = await client.post("/admin/deactivate-merchant", json=deactivate_data)

        assert response.status_code == 200
        mock_deactivate.assert_called_once()


@pytest.mark.asyncio
class TestAdminAuthorizationChecks:
    """Test admin authorization and access control"""

    async def test_unauthorized_access_no_token(self, client):
        """Test accessing admin endpoint without token"""
        response = await client.get("/admin/merchants")

        assert response.status_code in [401, 403]

    @patch('services.adminService.get_current_admin')
    async def test_unauthorized_access_invalid_admin(
        self,
        mock_get_current_admin,
        client
    ):
        """Test accessing admin endpoint with invalid admin"""
        mock_get_current_admin.side_effect = HTTPException(status_code=404, detail="Admin not found")

        response = await client.get("/admin/merchants")

        assert response.status_code == 404

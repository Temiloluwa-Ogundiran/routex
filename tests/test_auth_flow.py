"""
Tests for auth delivery hardening and identity bootstrap endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace
from datetime import datetime, timezone

from database.models.Admin import Admin
from services.tokenService import create_access_token


@pytest.fixture
async def test_admin(async_session):
    admin = Admin(
        email="admin@test.com",
        name="Test Admin",
        password="$2b$12$hashed_password",
        is_active=True,
    )
    async_session.add(admin)
    await async_session.commit()
    await async_session.refresh(admin)
    return admin


@pytest.mark.asyncio
class TestAuthOtpDelivery:
    @patch("services.emailService.send_otp_email", new_callable=AsyncMock)
    @patch("services.otpService.store_otp", new_callable=AsyncMock)
    @patch("services.userService.check_password", new_callable=AsyncMock)
    @patch("services.userService.get_user_by_email", new_callable=AsyncMock)
    async def test_login_does_not_return_raw_otp(
        self,
        mock_get_user,
        mock_check_password,
        mock_store_otp,
        mock_send_otp_email,
        client,
        test_user,
    ):
        mock_get_user.return_value = test_user
        mock_check_password.return_value = True
        mock_store_otp.return_value = None
        mock_send_otp_email.return_value = None

        response = await client.post(
            "/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] is True
        assert "otp" not in payload

    @patch("services.emailService.send_otp_email", new_callable=AsyncMock)
    @patch("services.otpService.store_otp", new_callable=AsyncMock)
    @patch("services.userService.get_user_by_email", new_callable=AsyncMock)
    async def test_signup_does_not_return_raw_otp(
        self,
        mock_get_user,
        mock_store_otp,
        mock_send_otp_email,
        client,
    ):
        mock_get_user.return_value = None
        mock_store_otp.return_value = None
        mock_send_otp_email.return_value = None

        response = await client.post(
            "/auth/signup",
            json={
                "name": "New User",
                "email": "newuser@test.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] is True
        assert "otp" not in payload

    async def test_signup_requires_name_field(self, client):
        response = await client.post(
            "/auth/signup",
            json={
                "email": "newuser@test.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 422

    @patch("api.views.authView.create_access_token")
    @patch("services.adminService.get_admin_by_email", new_callable=AsyncMock)
    @patch("services.otpService.delete_otp", new_callable=AsyncMock)
    @patch("services.otpService.get_otp", new_callable=AsyncMock)
    @patch("services.userService.check_password", new_callable=AsyncMock)
    @patch("services.userService.get_user_by_email", new_callable=AsyncMock)
    async def test_login_otp_awaits_admin_lookup_for_regular_users(
        self,
        mock_get_user,
        mock_check_password,
        mock_get_otp,
        mock_delete_otp,
        mock_get_admin,
        mock_create_access_token,
        client,
    ):
        fake_user = SimpleNamespace(
            id="u_test001",
            email="test@user.com",
            name="Test User",
            is_verified=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            merchants=[],
        )

        mock_get_user.return_value = fake_user
        mock_check_password.return_value = True
        mock_get_otp.return_value = "123456"
        mock_delete_otp.return_value = None
        mock_get_admin.return_value = None
        mock_create_access_token.return_value = "user-token"

        response = await client.post(
            "/auth/login/verify-otp",
            json={
                "email": fake_user.email,
                "password": "testpassword123",
                "otp": "123456",
            },
        )

        assert response.status_code == 200
        assert mock_get_admin.await_count == 1
        assert mock_get_admin.await_args.kwargs["email"] == fake_user.email
        mock_create_access_token.assert_called_once_with({"sub": fake_user.id})
        assert response.json()["access_token"] == "user-token"


@pytest.mark.asyncio
class TestAuthIdentityEndpoints:
    async def test_auth_me_returns_minimal_identity_fields(self, client, test_user):
        token = create_access_token({"sub": test_user.id})

        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] is True
        assert payload["data"]["id"] == test_user.id
        assert payload["data"]["email"] == test_user.email
        assert payload["data"]["name"] == test_user.name
        assert payload["data"]["is_verified"] is False
        assert "password" not in payload["data"]

    async def test_admin_me_returns_minimal_identity_fields(self, client, test_admin):
        token = create_access_token({"sub": str(test_admin.id)}, is_admin=True)

        response = await client.get(
            "/admin/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] is True
        assert payload["data"]["id"] == test_admin.id
        assert payload["data"]["email"] == test_admin.email
        assert payload["data"]["name"] == test_admin.name
        assert payload["data"]["role"] == "admin"
        assert "password" not in payload["data"]

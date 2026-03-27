from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from database.models.UserMerchant import UserMerchant
from main import app
from services import userService


@pytest.mark.asyncio
class TestMerchantNinVerification:
    @patch("external_services.interswitchService.verify_nin_identity", new_callable=AsyncMock)
    async def test_merchant_can_submit_optional_nin_verification(
        self,
        mock_verify_nin_identity,
        client,
        async_session,
        test_merchant,
        test_user,
    ):
        async_session.add(
            UserMerchant(
                user_id=test_user.id,
                merchant_id=test_merchant.id,
                role="owner",
            )
        )
        await async_session.commit()

        mock_verify_nin_identity.return_value = {
            "status": "VERIFIED",
            "reference": "ISW|KYC|NIN|20260327|A1B2C3",
            "full_name": "Ada Lovelace",
            "provider_response": {
                "verificationResponses": [
                    {
                        "type": "NIN",
                        "status": "VERIFIED",
                        "identityNumber": "12345678901",
                        "firstName": "Ada",
                        "lastName": "Lovelace",
                    }
                ]
            },
        }

        app.dependency_overrides[userService.get_current_user] = lambda: test_user
        try:
            response = await client.post(
                "/merchant/verify-nin",
                json={
                    "merchant_id": test_merchant.id,
                    "nin": "12345678901",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "phone": "+2348012345678",
                    "birth_date": "1990-12-10",
                },
            )
        finally:
            app.dependency_overrides.pop(userService.get_current_user, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] is True
        assert payload["nin_status"] == "verified"
        assert payload["nin_last4"] == "8901"
        assert payload["nin_reference"] == "ISW|KYC|NIN|20260327|A1B2C3"
        assert payload["nin_verified_name"] == "Ada Lovelace"

        await async_session.refresh(test_merchant)
        assert test_merchant.nin_status == "verified"
        assert test_merchant.nin_last4 == "8901"
        assert test_merchant.nin_reference == "ISW|KYC|NIN|20260327|A1B2C3"
        assert test_merchant.nin_verified_name == "Ada Lovelace"
        assert test_merchant.nin_submitted_at is not None
        assert test_merchant.nin_verified_at is not None


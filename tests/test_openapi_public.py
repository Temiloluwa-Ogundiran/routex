import pytest


@pytest.mark.asyncio
class TestPublicOpenApi:
    async def test_public_openapi_hides_private_dashboard_routes(self, client):
        response = await client.get("/public/openapi.json")

        assert response.status_code == 200

        paths = response.json()["paths"]
        assert "/api/v1/initiate" in paths
        assert "/api/v1/payout" in paths
        assert "/api/v1/transactions/verify" in paths
        assert "/public/openapi.json" not in paths
        assert "/api/v2/initiate" not in paths
        assert "/webhook/test-signature" not in paths
        assert "/admin/login" not in paths
        assert "/analytics/router/dashboard" not in paths

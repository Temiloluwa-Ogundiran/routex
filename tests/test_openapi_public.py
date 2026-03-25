import pytest


@pytest.mark.asyncio
class TestPublicOpenApi:
    async def test_public_openapi_hides_private_dashboard_routes(self, client):
        response = await client.get("/public/openapi.json")

        assert response.status_code == 200

        paths = response.json()["paths"]
        assert "/api/v1/initiate" in paths
        assert "/api/v1/payout" in paths
        assert "/admin/login" not in paths
        assert "/analytics/router/dashboard" not in paths

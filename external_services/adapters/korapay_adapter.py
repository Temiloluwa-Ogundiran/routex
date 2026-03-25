from external_services import koraService

from .base import GatewayCapability


class KorapayAdapter:
    capability = GatewayCapability(
        code="kora",
        display_name="Korapay",
        supports_collections=True,
        supports_payouts=True,
    )

    async def initialize_collection(self, **kwargs):
        return await koraService.initialize(**kwargs)

    async def initiate_payout(self, **kwargs):
        return await koraService.payout(**kwargs)

    async def verify_transaction(self, **kwargs):
        raise NotImplementedError("Korapay verify adapter is not implemented yet.")

    async def health_check(self):
        return {"status": "healthy", "gateway": self.capability.code}

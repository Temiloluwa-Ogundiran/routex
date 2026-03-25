from external_services import interswitchService

from .base import GatewayCapability


class InterswitchAdapter:
    capability = GatewayCapability(
        code="isw",
        display_name="Interswitch",
        supports_collections=True,
        supports_payouts=False,
    )

    async def initialize_collection(self, **kwargs):
        return await interswitchService.initialize(**kwargs)

    async def initiate_payout(self, **kwargs):
        raise NotImplementedError("Interswitch payout adapter is not implemented yet.")

    async def verify_transaction(self, **kwargs):
        return await interswitchService.verify_transaction(**kwargs)

    async def health_check(self):
        status = "healthy" if interswitchService.has_required_checkout_config() else "maintenance"
        return {"status": status, "gateway": self.capability.code}

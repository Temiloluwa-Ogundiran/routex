from external_services import flutterwaveService

from .base import GatewayCapability


class FlutterwaveAdapter:
    capability = GatewayCapability(
        code="fltw",
        display_name="Flutterwave",
        supports_collections=True,
        supports_payouts=False,
    )

    async def initialize_collection(self, **kwargs):
        return await flutterwaveService.initialize(**kwargs)

    async def initiate_payout(self, **kwargs):
        raise NotImplementedError("Flutterwave payout adapter is not implemented yet.")

    async def verify_transaction(self, **kwargs):
        raise NotImplementedError("Flutterwave verify adapter is not implemented yet.")

    async def health_check(self):
        return {"status": "healthy", "gateway": self.capability.code}

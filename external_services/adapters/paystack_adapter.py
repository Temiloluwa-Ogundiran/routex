from external_services import paystackService

from .base import GatewayCapability


class PaystackAdapter:
    capability = GatewayCapability(
        code="pstk",
        display_name="Paystack",
        supports_collections=True,
        supports_payouts=False,
    )

    async def initialize_collection(self, **kwargs):
        return await paystackService.initialize(**kwargs)

    async def initiate_payout(self, **kwargs):
        raise NotImplementedError("Paystack payout adapter is not implemented yet.")

    async def verify_transaction(self, **kwargs):
        raise NotImplementedError("Paystack verify adapter is not implemented yet.")

    async def health_check(self):
        return {"status": "healthy", "gateway": self.capability.code}

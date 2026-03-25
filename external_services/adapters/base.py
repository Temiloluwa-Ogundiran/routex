from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class GatewayCapability:
    code: str
    display_name: str
    supports_collections: bool = True
    supports_payouts: bool = False


class GatewayAdapter(Protocol):
    capability: GatewayCapability

    async def initialize_collection(self, **kwargs: Any) -> Any:
        ...

    async def initiate_payout(self, **kwargs: Any) -> Any:
        ...

    async def verify_transaction(self, **kwargs: Any) -> Any:
        ...

    async def health_check(self) -> dict[str, Any]:
        ...

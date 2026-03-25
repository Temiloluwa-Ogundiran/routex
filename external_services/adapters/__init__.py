from .flutterwave_adapter import FlutterwaveAdapter
from .interswitch_adapter import InterswitchAdapter
from .korapay_adapter import KorapayAdapter
from .paystack_adapter import PaystackAdapter

ADAPTER_REGISTRY = {
    "fltw": FlutterwaveAdapter(),
    "isw": InterswitchAdapter(),
    "kora": KorapayAdapter(),
    "pstk": PaystackAdapter(),
}


def get_adapter(gateway_code: str):
    adapter = ADAPTER_REGISTRY.get(gateway_code)
    if adapter is None:
        raise ValueError(f"Unsupported gateway adapter: {gateway_code}")
    return adapter

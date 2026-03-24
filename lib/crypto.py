import json
import os
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "cryptos.json")


with open(file_path, 'r') as file:
    crypto_list = json.load(file)

BASQET_ID_MAP = {
    "USDT": 3,
    "BTC": 4,
    "ETH": 6
}
class Crypto:
    def __init__(self, id, name, slug, blockchain, standard, symbol):
        self.id = id
        self.name = name
        self.slug = slug
        self.blockchain = blockchain
        self.standard = standard
        self.symbol = symbol

    def __repr__(self):
        return f"Crypto(name={self.name}, slug={self.slug}, blockchain={self.blockchain}, symbol={self.symbol})"

    def generate_qr_uri(self, address: str, amount: float = None) -> str:
        """Return a URI like bitcoin:addr?amount=0.01"""
        uri = f"{self.blockchain}:{address}"
        if amount:
            uri += f"?amount={amount}"
        return uri
    
    
    def get_basqet_id(self):
        if self.symbol not in BASQET_ID_MAP:
            raise ValueError(f"No id mapped for {self.symbol}")
        return BASQET_ID_MAP[self.symbol]


def find_crypto_by_slug(slug):
    crypto = next((c for c in crypto_list if c['slug'] == slug), None)
    return Crypto(**crypto) if crypto else None


def find_crypto_by_id(id):
    crypto = next((c for c in crypto_list if c['id'] == str(id)), None)
    return Crypto(**crypto) if crypto else None

def find_crypto_by_symbol(symbol: str):
    crypto = next((c for c in crypto_list if c['symbol'] == symbol), None)
    return Crypto(**crypto) if crypto else None

def get_all_cryptos():
    return [Crypto(**crypto) for crypto in crypto_list]


# === Validators ===
def is_valid_btc_address(value: str) -> bool:
    return re.fullmatch(r"(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}", value) is not None

def is_valid_eth_address(value: str) -> bool:
    return re.fullmatch(r"0x[a-fA-F0-9]{40}", value) is not None

def is_valid_tron_address(value: str) -> bool:
    return re.fullmatch(r"T[a-zA-HJ-NP-Z1-9]{33}", value) is not None

def is_valid_sol_address(value: str) -> bool:
    return re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", value) is not None

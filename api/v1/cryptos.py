from lib.crypto import get_all_cryptos
from fastapi import APIRouter
from pydantic import BaseModel, Field

crypto_router = APIRouter()
class CryptoDetail(BaseModel):
    id: str = Field(..., example="1", description="Unique identifier for the cryptocurrency")
    name: str = Field(..., example="Bitcoin", description="The name of the cryptocurrency")
    slug: str = Field(..., example="btc", description="A short identifier for the cryptocurrency")
    blockchain: str = Field(..., example="bitcoin", description="The blockchain network it belongs to")
    standard: str = Field(..., example="native", description="Token standard (e.g., ERC20, native)")
    symbol: str = Field(..., example="BTC", description="The symbol of the cryptocurrency")

@crypto_router.get("/cryptos", response_model= list[CryptoDetail])
async def get_cryptos():
    return get_all_cryptos()



from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WalletResponse(BaseModel):
    id: int
    merchant_id: str
    currency: str
    balance: float
    mode: str
    percentage_charge: float
    flat_charge: float
    payout_percentage_charge: float
    payout_flat_charge: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletCreateRequest(BaseModel):
    merchant_id: str
    currency: str = Field(..., examples=["NGN", "USD", "GHS", "KES"])
    mode: str = Field(..., examples=["test", "live"])
    percentage_charge: Optional[float] = Field(default=1.5, ge=0, description="Payin percentage charge")
    flat_charge: Optional[float] = Field(default=0.0, ge=0, description="Payin flat charge")
    payout_percentage_charge: Optional[float] = Field(default=0.0, ge=0, description="Payout percentage charge")
    payout_flat_charge: Optional[float] = Field(default=50.0, ge=0, description="Payout flat charge")


class WalletUpdateChargesRequest(BaseModel):
    percentage_charge: Optional[float] = Field(None, ge=0, description="Payin percentage charge")
    flat_charge: Optional[float] = Field(None, ge=0, description="Payin flat charge")
    payout_percentage_charge: Optional[float] = Field(None, ge=0, description="Payout percentage charge")
    payout_flat_charge: Optional[float] = Field(None, ge=0, description="Payout flat charge")


class WalletBalanceResponse(BaseModel):
    merchant_id: str
    wallets: list[WalletResponse]
    total_balances_by_currency: dict[str, float]


class WalletTransferRequest(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: float = Field(..., gt=0, description="Amount to transfer")


class WalletGetRequest(BaseModel):
    merchant_id: str
    currency: Optional[str] = None
    mode: Optional[str] = None

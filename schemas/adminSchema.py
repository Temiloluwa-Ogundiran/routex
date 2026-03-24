from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime
from schemas.merchantSchema import MerchantResponse
# ------------------------------
# Request Schemas
# ------------------------------

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


# ------------------------------
# Response Schemas
# ------------------------------

class AdminResponse(BaseModel):
    name: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    status: bool
    message: str
    data: AdminResponse
    access_token: str
    token_type: str


class TotalBalanceResponse(BaseModel):
    test_balance: float
    live_balance: float


class TotalAmountsResponse(BaseModel):
    processor_charges: float
    system_charges: float
    profit: float


class MerchantAmountsResponse(BaseModel):
    # Import MerchantResponse from merchantSchema when using
    merchant: MerchantResponse   # you'll replace this with MerchantResponse once imported
    merchant_processor_charges: float
    merchant_system_charges: float
    profit: float


class CurrencyBalanceData(BaseModel):
    """Balance data for a single currency"""
    currency: str
    balance: float


class BalancesByCurrencyResponse(BaseModel):
    """Response for wallet balances grouped by currency"""
    mode: str
    balances: dict[str, float]  # {'NGN': 10000.0, 'USD': 5000.0}
    total_currencies: int


class CurrencyChargeData(BaseModel):
    """Charge data for a single currency"""
    currency: str
    system_charges: float
    processor_charges: float
    profit: float


class ChargesByCurrencyResponse(BaseModel):
    """Response for charges grouped by currency"""
    mode: str
    charges: dict[str, dict]  # {'NGN': {'system_charges': ..., 'processor_charges': ..., 'profit': ...}}
    total_currencies: int


class SystemBalanceByCurrencyResponse(BaseModel):
    """Response for system balance grouped by currency"""
    mode: str
    balances: dict[str, float]  # {'NGN': merchant_balance + profit, 'USD': ...}
    total_currencies: int
    grand_total: float


class MerchantBalancesByCurrencyResponse(BaseModel):
    """Response for merchant balances grouped by currency"""
    merchant_id: str
    mode: str
    balances: dict[str, float]
    total_currencies: int

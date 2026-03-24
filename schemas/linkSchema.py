from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
import datetime
from schemas.merchantSchema import MerchantResponse
from enums import LinkEnums  # define LinkMode, AmountType enums
from schemas.transactionSchema import TransactionResponse
from enums.transactionEnums import TransactionCurrency, TransactionChannel


# -----------------------------
# BASE SCHEMA
# -----------------------------
class PaymentLinkBase(BaseModel):
    title: str = Field(..., example="Support My Project")
    description: Optional[str] = Field(None, example="Donation link for open source work")
    amount_type: LinkEnums.AmountType = Field(..., example="static")
    mode: LinkEnums.LinkMode = Field(..., example="test")
    type: LinkEnums.LinkType = Field(..., example="recurring")
    currency: TransactionCurrency = Field(..., example= TransactionCurrency.NIGERIA.value)
    amount: Optional[float] = Field(None, example=1000.0)
    max_uses: Optional[int] = Field(None, example=10)
    redirect_url: Optional[str] = Field(None, example="https://example.com/thank-you")
    expires_at: Optional[datetime.datetime] = None
    metadata: Optional[str] = Field(None, example="campaign=donation2025")


# -----------------------------
# REQUEST SCHEMAS
# -----------------------------
class PaymentLinkCreateRequest(PaymentLinkBase):
    merchant_id: str = Field(..., example="merchant_123")


class PaymentLinkUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    max_uses: Optional[int] = None
    redirect_url: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None
    metadata: Optional[str] = None
    is_active: Optional[bool] = None


# -----------------------------
# RESPONSE SCHEMAS
# -----------------------------
class PaymentLinkResponse(BaseModel):
    id: str
    reference: str
    title: str
    merchant_id: str
    url: str
    description: Optional[str]
    amount_type: LinkEnums.AmountType
    mode: LinkEnums.LinkMode
    type: LinkEnums.LinkType
    currency: TransactionCurrency
    amount: Optional[float]
    max_uses: Optional[int]
    current_uses: int
    redirect_url: Optional[str]
    expires_at: Optional[datetime.datetime]
    _metadata: Optional[str]
    is_active: bool
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    class Config:
        from_attributes = True


class PaymentLinkDetailResponse(PaymentLinkResponse):
    """Detailed view including transactions"""
    transactions: List[TransactionResponse] = []
    class Config:
        from_attributes = True

# -----------------------------
# TRANSACTION RESPONSE FOR LINKS
# -----------------------------
class LinkTransactionResponse(BaseModel):
    id: str
    amount: float
    status: str
    customer_id: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class CheckoutRequest(BaseModel):
    amount: Optional[float] = None
    # customer_id: Optional[int] = None
    # customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    currency: Optional[str] = TransactionCurrency.NIGERIA
    narration: Optional[str] = None
    channel: Optional[TransactionChannel] = None

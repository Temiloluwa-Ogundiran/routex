from pydantic import BaseModel
from enums import transactionEnums
from typing import Optional

class CompleteTransactionRequest(BaseModel):
    reference: str
    datetime: str  # ISO format datetime string
    channel: transactionEnums.TransactionChannel
    mobile_money_number: Optional[str] = None

class AuthroizeMmRequest(BaseModel):
    reference: str
    datetime: str  # ISO format datetime string
    otp: str
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from enums import transactionEnums

class Customer(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class InitializeTransactionRequest(BaseModel):
    customer: Customer
    amount: float
    currency: transactionEnums.TransactionCurrency = Field(description="Currency in lower case")
    reference: str
    redirect_url: Optional[str] = None
    notification_url: Optional[str] = None
    narration: Optional[str] = None
    mode: Optional[transactionEnums.TransactionChannel] = None
    metadata: Optional[dict] = None
    channels: Optional[List] = None
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enums.transactionEnums import TransactionChannel, TransactionStatus, TransactionType, TransactionCurrency, TransactionProcessor
from enums.BulkPayoutEnums import BulkPayoutStatus
from schemas.customerSchema import CustomerModel, CustomerResponse
from enums.tokenEnums import TokenMode

class TransactionResponse(BaseModel):
    id: int
    type: Optional[TransactionType]
    mode: Optional[str]
    reference: str
    status: TransactionStatus
    currency: TransactionCurrency
    amount: float
    charge: float
    processor_reference: Optional[str] = None
    customer: CustomerModel
    details: Optional[dict]
    created_at: datetime
    class Config:
        from_attributes = True

class BulkPayoutResponse(BaseModel):
    id: int
    merchant_id: str
    name: str
    reference: str
    status: BulkPayoutStatus
    transaction_details: list
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BulkPayoutDetailResponse(BulkPayoutResponse):
    transactions: list[TransactionResponse]

class PayoutCustomerDetails(BaseModel):
    account_number: str
    bank_code: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class PayoutRequest(BaseModel):
    merchant_id: str
    reference: Optional[str] = None
    amount: float
    currency:  TransactionCurrency = TransactionCurrency.NIGERIA.value
    customer: PayoutCustomerDetails
    mode: TokenMode = TokenMode.TEST
    narration: Optional[str] = None

class BulkPayoutCustomerDetails(BaseModel):
    account_number: str
    bank_slug: str 
    email: Optional[EmailStr] = None
    whatsapp_number: Optional[str] = Field(None, examples=['+2348012345678'])
    phone_number: Optional[str] = Field(None, examples=['+2348012345678'])

class BulkPayoutCategoryItem(BaseModel):
    beneficiary_id: int
    amount: Optional[float]

class BulkPayoutItem(PayoutRequest):
    merchant_id: Optional[str] = None
    customer: BulkPayoutCustomerDetails

class BulkPayoutRequest(BaseModel):
    merchant_id: str
    mode: TokenMode = TokenMode.TEST
    name: Optional[str] = Field(None, examples=["Farmer's market employee payroll"])
    data: Optional[list[BulkPayoutItem]] = None
    category_ids: Optional[list[int]] = None
    beneficiary_ids: Optional[list[int]] = None
    # category_data : Optional[list[BulkPayoutCategoryItem]] = None

class PaymentLinkRequest(PayoutRequest):
    customer: CustomerResponse
    processor: TransactionProcessor
    mode: TokenMode

class GenerateReceiptRequest(BaseModel):
    merchant_id: str
    reference: str


class PayoutCategoryBase(BaseModel):
    name: str = Field(..., examples=["Vendors", "Employees", "Freelancers"])
    description: Optional[str] = None

class PayoutCategoryCreate(PayoutCategoryBase):
    merchant_id: str

class PayoutCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PayoutCategoryResponse(PayoutCategoryBase):
    id: int
    merchant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --------------------------
# Payout Beneficiary Schemas
# --------------------------

class PayoutBeneficiaryBase(BaseModel):
    name: str
    bank_code: str
    account_number: str
    email: EmailStr
    merchant_id: str 
    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    default_amount: Optional[float] = None
    narration: Optional[str] = None


class PayoutBeneficiaryCreate(PayoutBeneficiaryBase):
    category_id: Optional[int] = None

class PayoutBeneficiaryUpdate(BaseModel):
    name: Optional[str] = None
    bank_code: Optional[str] = None
    account_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    default_amount: Optional[float] = None
    narration: Optional[str] = None
    # is_active: Optional[bool] = None
    category_id: Optional[int] = None

class PayoutBeneficiaryResponse(PayoutBeneficiaryBase):
    id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------------------
# Payout Execution Schemas
# ----------------------------

class CategoryPayoutRequest(BaseModel):
    merchant_id: str
    category_id: int
    mode: TokenMode = TokenMode.TEST
    currency: TransactionCurrency = TransactionCurrency.NIGERIA.value
    narration: Optional[str] = Field(None, examples=["Monthly payroll", "Vendor settlement"])


class CategoryPayoutResponse(BaseModel):
    bulk_payout_id: int
    category_id: int
    merchant_id: str
    status: BulkPayoutStatus
    total_beneficiaries: int
    total_amount: float
    created_at: datetime

    class Config:
        from_attributes = True

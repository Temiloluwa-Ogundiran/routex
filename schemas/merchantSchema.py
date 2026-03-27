from pydantic import BaseModel, EmailStr, model_validator, Field
from typing import List, Optional
import datetime
from schemas.customerSchema import CustomerResponse
class MerchantCreateRequest(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str]= None

class MerchantGetRequest(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None

   

class MerchantResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    is_verified: bool
    is_active: bool
    joined_at: datetime.datetime
    test_balance: float
    live_balance: float
    percentage_charge: float
    flat_charge: float
    role: Optional[str] = None
    nin_status: Optional[str] = None
    nin_last4: Optional[str] = None
    nin_reference: Optional[str] = None
    nin_verified_name: Optional[str] = None
    nin_submitted_at: Optional[datetime.datetime] = None
    nin_verified_at: Optional[datetime.datetime] = None
    
    
    class Config:
        from_attributes = True  # ORM mode for Tortoise ORM


class UserResponse(BaseModel):
    id: str
    email: EmailStr

class MerchantDetailResponse(MerchantResponse):
    customers: Optional[List[CustomerResponse]] 
    users: Optional[List[UserResponse]]

class ActivateMerchantRequest(BaseModel):
    merchant_id: str 


class MerchantNinVerificationRequest(BaseModel):
    merchant_id: str
    nin: str = Field(min_length=11, max_length=11)
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    phone: str
    birth_date: datetime.date
    mode: Optional[str] = "test"


class MerchantNinVerificationResponse(BaseModel):
    status: bool
    message: str
    nin_status: str
    nin_last4: str
    nin_reference: str
    nin_verified_name: str
    nin_submitted_at: datetime.datetime
    nin_verified_at: Optional[datetime.datetime] = None

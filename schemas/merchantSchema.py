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
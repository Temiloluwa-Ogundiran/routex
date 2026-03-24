from pydantic import BaseModel, EmailStr, model_validator, Field
from typing import List, Optional
import datetime
from schemas.merchantSchema import MerchantDetailResponse, MerchantResponse
from enums import userEnums

class UserResponse(BaseModel):
    id : str
    name: str
    email : EmailStr
    created_at : datetime.datetime
    updated_at : datetime.datetime
    is_verified : bool
    merchants : Optional[List[MerchantResponse]]
    class Config:
        from_attributes = True

class UserCreateRequest(BaseModel):
    email: EmailStr
    name : str
    password: str
    merchant_id: str

class UserAddRequest(BaseModel):
    email: EmailStr
    merchant_id: str
    role: userEnums.UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
 
class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
   
class VerifyLoginOtpRequest(LoginRequest):
    otp: str

class VerifySignupOtpRequest(SignUpRequest):
    otp: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyForgotPasswordRequest(ForgotPasswordRequest):
    new_password: str
    token: str

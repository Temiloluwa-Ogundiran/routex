from pydantic import BaseModel, EmailStr, model_validator, Field
from typing import Optional

class CustomerResponse(BaseModel):
    name: Optional[str] = None
    email: EmailStr | str

class CustomerModel(CustomerResponse):
    class Config:
        from_attributes = True 
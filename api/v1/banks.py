from lib.bank import get_all_banks
from fastapi import APIRouter, HTTPException, Depends, Security, Request, Response, Query
from pydantic import BaseModel, Field
bank_router = APIRouter()

class Bank(BaseModel):
    name: str = Field(..., example="Access Bank Nigeria", description="The name of the bank")
    slug: str = Field(..., example="access", description="A short identifier for the bank")
    code: str = Field(..., example="044", description="The bank code")
    nibss_bank_code: str = Field(..., example="000014", description="NIBSS bank code")
    country: str = Field(..., example="NG", description="Country code in ISO format")

@bank_router.get("/banks")
async def get_banks():
    return get_all_banks()



from fastapi import APIRouter, HTTPException, Depends, Security, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services import merchantService, tokenService, userService
from external_services import koraService
from schemas.merchantSchema import MerchantCreateRequest, MerchantResponse, MerchantDetailResponse, MerchantGetRequest
from tortoise.exceptions import DoesNotExist
import json
from fastapi.responses import JSONResponse
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from database.models.User import User
from enums import tokenEnums, transactionEnums
from datetime import date
from typing import Optional

merchant_router = APIRouter()

@merchant_router.post("/create-merchant", status_code=201)
async def create_merchant(request: MerchantCreateRequest, session: AsyncSession = Depends(get_async_session), user: User = Depends(userService.get_current_user)):
    if await merchantService.get_by_id_or_email(email= request.email, session= session):
        raise HTTPException(status_code=400, detail="Merchant with this email already exists")
    
    merchant = await merchantService.create_merchant(name=request.name, email=request.email, session= session)
    await userService.add_user_to_merchant(session= session, user= user, merchant= merchant, role= request.role)
    return MerchantResponse.model_validate(merchant)

@merchant_router.post("/get-token", status_code=200)
async def get_merchant_tokens(request: MerchantGetRequest, session: AsyncSession = Depends(get_async_session), user: User = Depends(userService.get_current_user)):
    
    merchant = await merchantService.get_by_id_or_email(
        id=request.id if request.id else None,
        email = request.email if request.email else None,
        session= session
    )
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    if not await userService.user_in_merchant(user= user, merchant= merchant, session= session):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "user not allowed to view merchant details")
    
    token_dict = await tokenService.get_merchant_tokens(merchant=merchant, session= session)

    if not token_dict:
        raise HTTPException(status_code=500, detail="Failed to retrieve tokens for merchant")

    # Add merchant ID to payload
    token_dict["merchant_id"] = merchant.id
    return token_dict

@merchant_router.get("/get-merchant")
async def get_merchant(email: str = Query(..., description="Merchant email"), session: AsyncSession = Depends(get_async_session), user: User = Depends(userService.get_current_user)):
    merchant = await merchantService.get_by_id_or_email(email=email, session= session)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    response = MerchantResponse.model_validate(merchant)

    if not await userService.user_in_merchant(user= user, merchant= merchant, session= session):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "user not allowed to view merchant details")
    
    response.role = await userService.get_user_role(session= session, user= user, merchant= merchant)
    return response

@merchant_router.get("/merchant/revenue")
async def get_merchant_revenue(id: str = Query(..., description="Merchant ID"), mode: tokenEnums.TokenMode = Query(..., description="Merchant ID"), session: AsyncSession = Depends(get_async_session), user: User = Depends(userService.get_current_user)):
    merchant = await merchantService.get_by_id_or_email(id= id, session= session)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    if not await userService.user_in_merchant(user= user, merchant= merchant, session= session):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "user not allowed to view merchant details")
    total_revenue = await merchantService.get_merchant_revenue(session= session, merchant= merchant, mode= mode)
    return {"total_revenue": total_revenue}

@merchant_router.get("/merchant/periodic-revenue")
async def get_merchant_periodic_revenue(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
    id: str = Query(..., description="Mrchant's Id"),
    mode: tokenEnums.TokenMode = Query(default=tokenEnums.TokenMode.TEST, description= "live or test"),
    group_by: transactionEnums.GroupBy = Query(transactionEnums.GroupBy.MONTH, description="Group by 'day', 'week' or 'month'"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    merchant = await merchantService.get_by_id_or_email(id= id, session= session)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    if not await userService.user_in_merchant(user= user, merchant= merchant, session= session):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "user not allowed to view merchant details")
    
    revenue_breakdown = await merchantService.get_merchant_periodic_revenue(
        session= session, merchant= merchant,
        start_date= start_date, end_date= end_date,
        group_by= group_by, mode= mode
    )
    return {
        "merchant_id": id,
        "mode": mode,
        "revenue_breakdown": revenue_breakdown,
        "total_revenue": await merchantService.get_merchant_revenue(session= session, merchant= merchant, mode= mode)
    }

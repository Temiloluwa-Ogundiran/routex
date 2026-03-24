from settings import app
from fastapi import APIRouter, Query, HTTPException, status, Request, Depends
from services import userService, merchantService
from schemas import userSchema
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from database.models.User import User
user_router = APIRouter()

@user_router.get("/get-user")
async def get_user(user: User = Depends(userService.get_current_user), session: AsyncSession = Depends(get_async_session)):
    return userSchema.UserResponse.model_validate(user)

@user_router.post("/add-user")
async def add_user(request: userSchema.UserAddRequest, session: AsyncSession = Depends(get_async_session), user: User= Depends(userService.get_current_user)):
    merchant = await merchantService.get_by_id_or_email(id= request.merchant_id, session= session)
    added_user = await userService.get_user_by_email(email= request.email, session= session)

    if not user:
        raise HTTPException(status_code= 404, detail= "User to be added not found")
    
    if not merchant:
        raise HTTPException(status_code= 404, detail= "Merchant not found")
    
    if not user:
        raise HTTPException(status_code= 404, detail= "User not found")
    
    if await userService.user_in_merchant(user= added_user, merchant= merchant, session= session):
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "User already in merchant")
    
    user = await userService.add_user_to_merchant(
        user = added_user,
        merchant= merchant, 
        session= session,
        role= request.role
    )
    
    return userSchema.UserResponse.model_validate(user)

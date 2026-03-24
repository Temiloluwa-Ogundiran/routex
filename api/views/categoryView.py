from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math
from lib import bank
from database.session import get_async_session
from database.models.User import User
from database.models.Merchant import Merchant
from schemas.transactionSchema import (
    PayoutCategoryCreate, PayoutCategoryResponse, 
    PayoutBeneficiaryCreate, PayoutBeneficiaryResponse, PayoutBeneficiaryUpdate
)
from services import merchantService, userService, bulkpayoutService
from external_services import koraService
from enums.transactionEnums import TransactionCurrency

category_router = APIRouter(prefix="/payout-category")
beneficiary_router = APIRouter(prefix="/payout-beneficiary")


# -------------------------
# CATEGORY CRUD
# -------------------------

@category_router.post("", response_model=PayoutCategoryResponse)
async def create_category(
    data: PayoutCategoryCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session, id=data.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if await bulkpayoutService.get_category_by_name(session = session, category_name= data.name):
        raise HTTPException(
            status_code= 400,
            detail= "Category name already exist"
        )
    
    category = await bulkpayoutService.create_payout_category(
        session= session,
        merchant_id= data.merchant_id,
        name = data.name,
        description= data.description
    )
    return PayoutCategoryResponse.model_validate(category)

@category_router.get("", response_model=list[PayoutCategoryResponse])
async def list_categories(
    merchant_id: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    merchant = await merchantService.get_by_id_or_email(session, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(user, merchant, session):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await bulkpayoutService.get_all_categories(session, merchant.id)

@category_router.get("/{category_id}")
async def get_category(
    category_id: int,
    merchant_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")
    
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    category = await bulkpayoutService.get_category_by_id(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    count = await bulkpayoutService.get_beneficiary_count_by_category(category_id, session)
    total_amount = await bulkpayoutService.get_total_default_amount_by_category(category_id, session)

    return {
        **PayoutCategoryResponse.model_validate(category).model_dump(),
        "beneficiary_count": count,
        "total_default_amount": total_amount,
    }


@category_router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    merchant_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")
    
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    deleted = await bulkpayoutService.soft_delete_category(session, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

@category_router.get("/{category_id}/beneficiaries", response_model= List[PayoutBeneficiaryResponse])
async def fetch_beneficiaries(category_id: int,merchant_id:str,  session: AsyncSession = Depends(get_async_session), user: User = Depends(userService.get_current_user)):
    merchant = await merchantService.get_by_id_or_email(session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")
    
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    beneficiaries = await bulkpayoutService.get_beneficiaries_by_category(session = session, category_id= category_id)
    return beneficiaries
# -------------------------
# BENEFICIARY CRUD
# -------------------------

@beneficiary_router.post("", response_model=PayoutBeneficiaryResponse)
async def create_beneficiary(
    data: PayoutBeneficiaryCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session, id=data.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    bank_obj = bank.find_bank_by_code(code= data.bank_code) 

    if bank_obj is None:
        raise HTTPException(status_code= 400, detail= "Invalid bank code provided")
    
    if data.category_id:
        category = await bulkpayoutService.get_category_by_id(session= session, category_id= data.category_id)
        print(category)
        if not category:

            raise HTTPException(status_code= 404, detail= "Category not found")

    _, message = await koraService.resolve_account(
        acc_number= data.account_number, bank= bank_obj,
        currency= TransactionCurrency.NIGERIA
    )
    if _ is False:
        raise HTTPException(status_code= 400, detail="Invalid account details")
    
    beneficiary = await bulkpayoutService.create_beneficiary(session, data)
    return PayoutBeneficiaryResponse.model_validate(beneficiary)


@beneficiary_router.get("/{beneficiary_id}", response_model=PayoutBeneficiaryResponse)
async def get_beneficiary(
    beneficiary_id: int,
    merchant_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")
    
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    beneficiary = await bulkpayoutService.get_beneficiary_by_id(session, beneficiary_id)
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    return PayoutBeneficiaryResponse.model_validate(beneficiary)

@beneficiary_router.get("")
async def list_beneficiaries(
    merchant_id: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(10, le=100),
    category_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    merchant = await merchantService.get_by_id_or_email(session, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(user, merchant, session):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await bulkpayoutService.get_all_beneficiaries(
        session=session,
        merchant_id=merchant.id,
        page=page,
        size=size,
        category_id=category_id,
    )


@beneficiary_router.put("/{beneficiary_id}", response_model=PayoutBeneficiaryResponse)
async def update_beneficiary(
    beneficiary_id: int,
    merchant_id: str,
    data: PayoutBeneficiaryUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")
    
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    beneficiary = await bulkpayoutService.update_beneficiary(session, beneficiary_id, data)
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    return PayoutBeneficiaryResponse.model_validate(beneficiary)


@beneficiary_router.delete("/{beneficiary_id}")
async def delete_beneficiary(
    beneficiary_id: int,
    merchant_id:str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    merchant = await merchantService.get_by_id_or_email(session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")
    
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="Unauthorized")
    deleted = await bulkpayoutService.soft_delete_beneficiary(session, beneficiary_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    return {"message": "Beneficiary deleted successfully"}

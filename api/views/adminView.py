from fastapi import APIRouter, Query, HTTPException, status, Request, Depends
from services import userService, merchantService, adminService, tokenService, transactionService
from schemas import userSchema, adminSchema, merchantSchema
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from database.models.Admin import Admin
from enums import tokenEnums
from typing import List, Optional

admin_router = APIRouter()

@admin_router.post("/admin/login", response_model=adminSchema.LoginResponse)
async def admin_login(
    data: adminSchema.AdminLoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    admin = await adminService.get_admin_by_email(session=session, email=data.email)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin does not exist")
    if not await adminService.check_password(admin=admin, password=data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = tokenService.create_access_token(data={'sub': str(admin.id)})
    return {
        "status": True,
        "message": "Login successful",
        "data": adminSchema.AdminResponse.model_validate(admin),
        "access_token": token,
        "token_type": "bearer"
    }


@admin_router.get("/admin/merchants", response_model=List[merchantSchema.MerchantResponse])    
async def get_all_merchants(
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    merchants = await adminService.get_merchants(session=session)
    return [merchantSchema.MerchantResponse.model_validate(merchant) for merchant in merchants]


@admin_router.get("/admin/total-balance", response_model=adminSchema.TotalBalanceResponse)
async def get_total_balance(
    currency: Optional[str] = Query(None, description="Filter by currency (e.g., NGN, USD)"),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    """Get total system balance, optionally filtered by currency"""
    test_balance = await adminService.get_system_balance(session=session, mode=tokenEnums.TokenMode.TEST, currency=currency)
    live_balance = await adminService.get_system_balance(session=session, mode=tokenEnums.TokenMode.LIVE, currency=currency)
    return {
        "test_balance": test_balance,
        "live_balance": live_balance
    }


@admin_router.get("/admin/total-amounts", response_model=adminSchema.TotalAmountsResponse)
async def get_total_amounts(
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    currency: Optional[str] = Query(None, description="Filter by currency (e.g., NGN, USD)"),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    """Get total charges and profit, optionally filtered by currency"""
    processor_charges = await adminService.get_total_processor_charges(session=session, mode=mode, currency=currency)
    system_charges = await adminService.get_total_charges(session=session, mode=mode, currency=currency)
    return {
        "processor_charges": processor_charges,
        "system_charges": system_charges,
        "profit": system_charges - processor_charges
    }


@admin_router.post("/admin/activate-merchant", response_model=merchantSchema.MerchantResponse)
async def activatate_merchant(
    data: merchantSchema.ActivateMerchantRequest,
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    merchant = await merchantService.get_by_id_or_email(session=session, id=data.merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    
    if not merchant.is_verified:
        merchant = await merchantService.activate_merchant_live_account(session=session, merchant=merchant)
    return merchantSchema.MerchantResponse.model_validate(merchant)


@admin_router.post("/admin/deactivate-merchant", response_model=merchantSchema.MerchantResponse)
async def deactivatate_merchant(
    data: merchantSchema.ActivateMerchantRequest,
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    merchant = await merchantService.get_by_id_or_email(session=session, id=data.merchant_id)

    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    
    if merchant.is_verified:
        await merchantService.deactivate_merchant_live_account(session=session, merchant=merchant)

    return merchantSchema.MerchantResponse.model_validate(merchant)


@admin_router.get("/admin/merchant-amounts", response_model=adminSchema.MerchantAmountsResponse)
async def get_merchant_total_amounts(
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    merchant_id: Optional[str] = Query(None, description="Merchant ID"),
    merchant_email: Optional[str] = Query(None, description="Merchant email"),
    currency: Optional[str] = Query(None, description="Filter by currency (e.g., NGN, USD)"),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    """Get merchant charges and profit, optionally filtered by currency"""
    if not merchant_email and not merchant_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Merchant email or Id must be provided"
        )

    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id, email=merchant_email)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    processor_charges = await adminService.get_merchant_total_processor_charges(session=session, mode=mode, merchant=merchant, currency=currency)
    system_charges = await adminService.get_merchant_total_charges(session=session, mode=mode, merchant=merchant, currency=currency)

    return {
        "merchant": merchantSchema.MerchantResponse.model_validate(merchant),
        "merchant_processor_charges": processor_charges,
        "merchant_system_charges": system_charges,
        "profit": system_charges - processor_charges
    }


@admin_router.get("/admin/balances-by-currency", response_model=adminSchema.BalancesByCurrencyResponse)
async def get_balances_by_currency(
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    """Get wallet balances grouped by currency for a specific mode"""
    balances = await adminService.get_balances_by_currency(session=session, mode=mode)
    return {
        "mode": mode,
        "balances": balances,
        "total_currencies": len(balances)
    }


@admin_router.get("/admin/charges-by-currency", response_model=adminSchema.ChargesByCurrencyResponse)
async def get_charges_by_currency(
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    """Get system charges and processor charges grouped by currency"""
    charges = await adminService.get_charges_by_currency(session=session, mode=mode)
    return {
        "mode": mode,
        "charges": charges,
        "total_currencies": len(charges)
    }


@admin_router.get("/admin/system-balance-by-currency", response_model=adminSchema.SystemBalanceByCurrencyResponse)
async def get_system_balance_by_currency(
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    """Get system balance (merchant balance + profit) grouped by currency"""
    balances = await adminService.get_system_balance_by_currency(session=session, mode=mode)
    grand_total = sum(balances.values())
    return {
        "mode": mode,
        "balances": balances,
        "total_currencies": len(balances),
        "grand_total": grand_total
    }


@admin_router.get("/admin/merchant-balance", response_model=adminSchema.TotalBalanceResponse)
async def get_total_merchant_balance(
    currency: Optional[str] = Query(None, description="Filter by currency (e.g., NGN, USD)"),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin)
):
    """Get total merchant wallet balances across all merchants, optionally filtered by currency"""
    test_balance = await adminService.get_total_merchant_balance(session=session, mode=tokenEnums.TokenMode.TEST, currency=currency)
    live_balance = await adminService.get_total_merchant_balance(session=session, mode=tokenEnums.TokenMode.LIVE, currency=currency)
    return {
        "test_balance": test_balance,
        "live_balance": live_balance
    }

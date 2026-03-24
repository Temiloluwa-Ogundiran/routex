from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from services import walletService, merchantService, userService
from schemas.walletSchema import (
    WalletResponse,
    WalletCreateRequest,
    WalletUpdateChargesRequest,
    WalletBalanceResponse,
    WalletTransferRequest,
    WalletGetRequest
)
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from database.models.User import User
from database.models.Wallet import Wallet
from typing import List, Optional

wallet_router = APIRouter()


@wallet_router.post("/wallets/create", status_code=201, response_model=WalletResponse)
async def create_wallet(
    request: WalletCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Create a new wallet for a merchant with specific currency and mode."""
    merchant = await merchantService.get_by_id_or_email(id=request.merchant_id, session=session)

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to manage this merchant's wallets"
        )

    # Check if wallet already exists
    existing_wallet = await walletService.get_wallet(
        session=session,
        merchant_id=request.merchant_id,
        currency=request.currency,
        mode=request.mode
    )

    if existing_wallet:
        raise HTTPException(
            status_code=400,
            detail=f"Wallet already exists for {request.currency} in {request.mode} mode"
        )

    # Create new wallet
    wallet = Wallet(
        merchant_id=request.merchant_id,
        currency=request.currency,
        mode=request.mode,
        balance=0.0,
        percentage_charge=request.percentage_charge,
        flat_charge=request.flat_charge,
        payout_percentage_charge=request.payout_percentage_charge,
        payout_flat_charge=request.payout_flat_charge,
        is_active=True
    )

    session.add(wallet)
    await session.commit()
    await session.refresh(wallet)

    return WalletResponse.model_validate(wallet)


@wallet_router.get("/wallets", response_model=List[WalletResponse])
async def get_merchant_wallets(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: Optional[str] = Query(None, description="Filter by mode: test or live"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get all wallets for a merchant, optionally filtered by mode."""
    merchant = await merchantService.get_by_id_or_email(id=merchant_id, session=session)

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to view this merchant's wallets"
        )

    wallets = await walletService.get_merchant_wallets(
        session=session,
        merchant_id=merchant_id,
        mode=mode
    )

    return [WalletResponse.model_validate(w) for w in wallets]


@wallet_router.get("/wallets/by-criteria", response_model=List[WalletResponse])
async def get_wallets_by_criteria(
    merchant_id: str = Query(..., description="Merchant ID"),
    currencies: Optional[str] = Query(None, description="Comma-separated list of currencies (e.g., 'NGN,USD,GHS')"),
    mode: Optional[str] = Query(None, description="Filter by mode: test or live"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get wallets by merchant, currencies (multiple), and optional mode."""
    from sqlalchemy import select

    merchant = await merchantService.get_by_id_or_email(id=merchant_id, session=session)

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to view this merchant's wallets"
        )

    # Build query
    query = select(Wallet).where(Wallet.merchant_id == merchant_id)

    if mode:
        query = query.where(Wallet.mode == mode)

    if currencies:
        # Parse comma-separated currencies
        currency_list = [c.strip().upper() for c in currencies.split(',')]
        query = query.where(Wallet.currency.in_(currency_list))

    query = query.order_by(Wallet.currency, Wallet.mode)

    result = await session.execute(query)
    wallets = list(result.scalars().all())

    return [WalletResponse.model_validate(w) for w in wallets]


@wallet_router.get("/wallets/{wallet_id}", response_model=WalletResponse)
async def get_wallet_by_id(
    wallet_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get a specific wallet by ID."""
    from sqlalchemy import select

    stmt = select(Wallet).where(Wallet.id == wallet_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Check if user has access to this merchant
    merchant = await merchantService.get_by_id_or_email(id=wallet.merchant_id, session=session)

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to view this wallet"
        )

    return WalletResponse.model_validate(wallet)


@wallet_router.get("/wallets/balance/summary", response_model=WalletBalanceResponse)
async def get_wallet_balance_summary(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: Optional[str] = Query(None, description="Filter by mode: test or live"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get balance summary for all merchant wallets."""
    merchant = await merchantService.get_by_id_or_email(id=merchant_id, session=session)

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to view this merchant's wallets"
        )

    wallets = await walletService.get_merchant_wallets(
        session=session,
        merchant_id=merchant_id,
        mode=mode
    )

    # Calculate total balances by currency
    total_balances = {}
    for wallet in wallets:
        currency_key = f"{wallet.currency}_{wallet.mode}"
        if currency_key not in total_balances:
            total_balances[currency_key] = 0.0
        total_balances[currency_key] += wallet.balance

    return WalletBalanceResponse(
        merchant_id=merchant_id,
        wallets=[WalletResponse.model_validate(w) for w in wallets],
        total_balances_by_currency=total_balances
    )


@wallet_router.patch("/wallets/{wallet_id}/charges", response_model=WalletResponse)
async def update_wallet_charges(
    wallet_id: int,
    request: WalletUpdateChargesRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Update charge configuration for a wallet."""
    from sqlalchemy import select

    stmt = select(Wallet).where(Wallet.id == wallet_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Check if user has access to this merchant
    merchant = await merchantService.get_by_id_or_email(id=wallet.merchant_id, session=session)

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to update this wallet"
        )

    # Update charges
    if request.percentage_charge is not None:
        wallet.percentage_charge = request.percentage_charge
    if request.flat_charge is not None:
        wallet.flat_charge = request.flat_charge
    if request.payout_percentage_charge is not None:
        wallet.payout_percentage_charge = request.payout_percentage_charge
    if request.payout_flat_charge is not None:
        wallet.payout_flat_charge = request.payout_flat_charge

    await session.commit()
    await session.refresh(wallet)

    return WalletResponse.model_validate(wallet)


@wallet_router.patch("/wallets/{wallet_id}/toggle-active", response_model=WalletResponse)
async def toggle_wallet_active(
    wallet_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Toggle wallet active status."""
    from sqlalchemy import select

    stmt = select(Wallet).where(Wallet.id == wallet_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Check if user has access to this merchant
    merchant = await merchantService.get_by_id_or_email(id=wallet.merchant_id, session=session)

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to update this wallet"
        )

    wallet.is_active = not wallet.is_active
    await session.commit()
    await session.refresh(wallet)

    return WalletResponse.model_validate(wallet)


@wallet_router.post("/wallets/transfer")
async def transfer_between_wallets(
    request: WalletTransferRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Transfer funds between two wallets (must belong to same merchant)."""
    from sqlalchemy import select

    # Get both wallets
    stmt = select(Wallet).where(Wallet.id.in_([request.from_wallet_id, request.to_wallet_id]))
    result = await session.execute(stmt)
    wallets = list(result.scalars().all())

    if len(wallets) != 2:
        raise HTTPException(status_code=404, detail="One or both wallets not found")

    from_wallet = next((w for w in wallets if w.id == request.from_wallet_id), None)
    to_wallet = next((w for w in wallets if w.id == request.to_wallet_id), None)

    if not from_wallet or not to_wallet:
        raise HTTPException(status_code=404, detail="Wallet configuration error")

    # Check if both wallets belong to same merchant
    if from_wallet.merchant_id != to_wallet.merchant_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot transfer between wallets of different merchants"
        )

    # Check user authorization
    merchant = await merchantService.get_by_id_or_email(id=from_wallet.merchant_id, session=session)

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to transfer funds for this merchant"
        )

    # Perform transfer
    try:
        from_wallet, to_wallet = await walletService.transfer_between_wallets(
            session=session,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            amount=request.amount
        )

        return {
            "success": True,
            "message": f"Transferred {request.amount} from wallet {from_wallet.id} to {to_wallet.id}",
            "from_wallet": WalletResponse.model_validate(from_wallet),
            "to_wallet": WalletResponse.model_validate(to_wallet)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@wallet_router.delete("/wallets/{wallet_id}")
async def delete_wallet(
    wallet_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Delete a wallet (only if balance is zero)."""
    from sqlalchemy import select, delete

    stmt = select(Wallet).where(Wallet.id == wallet_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Check if user has access to this merchant
    merchant = await merchantService.get_by_id_or_email(id=wallet.merchant_id, session=session)

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authorized to delete this wallet"
        )

    # Check if balance is zero
    if wallet.balance != 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete wallet with non-zero balance: {wallet.balance}"
        )

    # Delete wallet
    stmt = delete(Wallet).where(Wallet.id == wallet_id)
    await session.execute(stmt)
    await session.commit()

    return {"success": True, "message": f"Wallet {wallet_id} deleted successfully"}

from fastapi import APIRouter, HTTPException, Query, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from services import transactionService, merchantService, userService, customerService, celeryService, bulkpayoutService, receiptService, walletService
from database.models.Transaction import Transaction
from database.models.BulkPayout import BulkPayout
from schemas.transactionSchema import TransactionResponse, PayoutRequest, PaymentLinkRequest, BulkPayoutRequest, BulkPayoutResponse, BulkPayoutDetailResponse, GenerateReceiptRequest
from schemas.customerSchema import CustomerResponse
from external_services import koraService, paystackService, flutterwaveService
from database.session import get_async_session
import math
from enums import transactionEnums, tokenEnums, BulkPayoutEnums
from database.models.User import User
from lib import bank
from settings import TEMP_PAYOUT_FEE
import os
from websocket.broadcast import broadcast
from enums.BulkPayoutEnums import BulkPayoutStatus
transaction_router = APIRouter()

@transaction_router.get("/merchant-transactions")
async def get_merchant_transactions(
    merchant_id: str = Query(..., description="Merchant ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    mode: tokenEnums.TokenMode = tokenEnums.TokenMode.TEST,
    wallet_id: int = Query(None, description="Filter by wallet ID"),
    currency: str = Query(None, description="Filter by currency"),
    transaction_type: transactionEnums.TransactionType = Query(None, description="Filter by transaction type"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get merchant transactions with optional filters for wallet, currency, and type."""
    from sqlalchemy import func, desc

    merchant = await merchantService.get_by_id_or_email(session= session, id= merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail= "Merchant does not exist")

    if not await userService.user_in_merchant(user = user, merchant= merchant, session= session):
        raise HTTPException(status_code=401, detail= "User unauthorized to view merchant's transactions")

    # Build query with filters
    count_query = select(func.count()).select_from(Transaction).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode.value
    )

    if wallet_id:
        count_query = count_query.where(Transaction.wallet_id == wallet_id)
    if currency:
        count_query = count_query.where(Transaction.currency == currency)
    if transaction_type:
        count_query = count_query.where(Transaction.type == transaction_type)

    result = await session.execute(count_query)
    total_items = result.scalar_one()

    if total_items == 0:
        return {
            "transactions": [],
            "total_items": 0,
            "total_pages": 0,
            "current_page": page,
            "page_size": page_size,
            "filters": {
                "wallet_id": wallet_id,
                "currency": currency,
                "transaction_type": transaction_type.value if transaction_type else None
            }
        }

    total_pages = math.ceil(total_items / page_size)

    # Get paginated transactions with filters - eagerly load customer relationship
    txn_query = select(Transaction).options(
        selectinload(Transaction.customer)
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode.value
    )

    if wallet_id:
        txn_query = txn_query.where(Transaction.wallet_id == wallet_id)
    if currency:
        txn_query = txn_query.where(Transaction.currency == currency)
    if transaction_type:
        txn_query = txn_query.where(Transaction.type == transaction_type)

    txn_query = txn_query.order_by(desc(Transaction.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(txn_query)
    transactions = list(result.scalars().all())

    return {
        "transactions": [TransactionResponse.model_validate(t) for t in transactions],
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "filters": {
            "wallet_id": wallet_id,
            "currency": currency,
            "transaction_type": transaction_type.value if transaction_type else None
        }
    }

@transaction_router.get("/checkout-reference", response_model= TransactionResponse)
async def get_checkout_reference(
    reference: str,
    datetime: str,
    session = Depends(get_async_session)
):
    """
    Get transaction by reference and datetime
    """
    tx = await transactionService.get_transaction_by_reference_and_datetime(
        session=session,
        reference=reference,
        datetime_str=datetime
    )
    if not tx:
        raise HTTPException(detail="Checkout transaction not found", status_code=404)

    return tx

@transaction_router.post("/payout")
async def payout(
    data: PayoutRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    if data.amount < 200:
        raise HTTPException(status_code= status.HTTP_422_UNPROCESSABLE_ENTITY, detail= "Amount must be greater than 200")
    
    merchant = await merchantService.get_by_id_or_email(session= session, id= data.merchant_id)
    bank_obj = bank.find_bank_by_code(code= data.customer.bank_code)

    if bank_obj is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= f"Bank with code '{data.customer.bank_code}' does not exist")
    
    if merchant is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Merchant does not exist")
    
    if not await userService.user_in_merchant(session= session, merchant= merchant, user= user):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "User does not belong to merchant")
    
    if not merchant.is_verified :
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Merchant not authorized for this operation")

    # Get wallet for balance check and charge calculation
    wallet = await walletService.get_wallet(
        session=session,
        merchant_id=merchant.id,
        currency=data.currency,
        mode=tokenEnums.TokenMode.LIVE.value
    )

    if not wallet:
        raise HTTPException(status_code=400, detail=f"Wallet not found for {data.currency} in LIVE mode")

    # Calculate charge using wallet's charge configuration
    transaction_charge = await walletService.get_payout_charge(wallet=wallet, amount=data.amount)

    if wallet.balance < data.amount + transaction_charge:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Insufficient balance")
    
    trans_status, message, httpstatus, txn_id = await koraService.payout(
        session= session,
        merchant= merchant,
        acc_number= data.customer.account_number,
        bank_code= data.customer.bank_code,
        amount= data.amount,
        email= merchant.email,
        reference= await transactionService.generate_processor_reference(session= session),
        mode = tokenEnums.TokenMode.LIVE.value,
        narration= data.narration,
        currency= data.currency
    )
    
    return JSONResponse(content= {
        "status": trans_status,
        "message": message
    }, status_code= httpstatus)
    
@transaction_router.post("/bulk-payout")
async def bulk_payout(
    data: BulkPayoutRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)    
):
    errors = []
    categories = []
    beneficiaries = []
    total_amount = 0

    merchant = await merchantService.get_by_id_or_email(session= session, id=data.merchant_id)
    if not merchant:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    
    if not await userService.user_in_merchant(session= session, merchant= merchant, user= user):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "User does not belong to merchant")
    
    if data.category_ids and data.beneficiary_ids:
        raise HTTPException(status_code= 400, detail= "You can't pass category Id's and Beneficiary Id's, Select one")
    
    if not data.data and not (data.category_ids or data.beneficiary_ids):
         raise HTTPException(status_code= 400, detail= "Either payout category, payout beneficiary  or payout data must be passed")
    
    if  data.data and  (data.category_ids or data.beneficiary_ids):
         raise HTTPException(status_code= 400, detail= "Only one of payout category, payout beneficiary  or payout data must be passed")

    if data.category_ids:
        for category_id in data.category_ids:
            category = await bulkpayoutService.get_category_by_id(
                session= session,
                category_id= category_id
            )
            if category is None:
                raise HTTPException(status_code= 404, detail= f"Category ID: {category_id} not found")
            categories.append(category)
            
        payout_data = await bulkpayoutService.get_category_payout_data(
            session = session,
            cats= categories
        )
    elif data.beneficiary_ids:
        for ben_id in data.beneficiary_ids:
            beneficiary = await bulkpayoutService.get_beneficiary_by_id(
                session= session,
                beneficiary_id= ben_id
            )
            if beneficiary is None:    
                raise HTTPException(status_code= 404, detail= f"Beneficiary  ID: {ben_id} not found")
            beneficiaries.append(beneficiary)
            payout_data = await bulkpayoutService.get_beneficiary_payout_data(bnfs= beneficiaries)
    
    if not data.data:
        data.data = payout_data

    for index, item in enumerate(data.data):
        bank_obj = bank.find_bank_by_slug(slug=item.customer.bank_slug)
        if not bank_obj:
            errors.append({
                "row": index + 1,
                "message": f"Invalid bank slug: '{item.customer.bank_slug}'"
                })
        if not bank.is_valid_account_number(item.customer.account_number):
            errors.append({
                "row": index + 1,
                "message": f"Invalid account number: '{item.customer.account_number}'"
                })
        if not bank.is_valid_amount(item.amount):
            errors.append({
                "row": index + 1,
                "message": f"Invalid amount: '{item.amount}'"
                })
        total_amount += (item.amount + TEMP_PAYOUT_FEE)

    if data.mode == tokenEnums.TokenMode.LIVE:
        if not merchant.is_verified:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Merchant is not authorized to use live mode"
            )

    # Determine currency from first item or default to NGN
    currency = data.data[0].currency if data.data and len(data.data) > 0 else "NGN"

    # Get wallet for balance check
    wallet = await walletService.get_wallet(
        session=session,
        merchant_id=merchant.id,
        currency=currency,
        mode=data.mode.value
    )

    if not wallet:
        raise HTTPException(status_code=400, detail=f"Wallet not found for {currency} in {data.mode.value} mode")

    if wallet.balance < total_amount:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )    


    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail= errors
        )
    
    # ✅ Send task to Celery
    payout_queue = data.model_dump()
    bulk_payout = await bulkpayoutService.create_bulk_payout(session=session, merchant=merchant, name=data.name)
    celeryService.schedule_bulk_payouts.apply_async((merchant.id, payout_queue['data'], bulk_payout.id, data.mode))

    return {
        "status": "queued",
        "total": len(data.data),
        "message": "Payout task has been queued for processing."
    }

@transaction_router.post("/generate-payment-link")
async def generate_payment_url(
    data: PaymentLinkRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session= session, id=data.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    if not await userService.user_in_merchant(session= session, merchant= merchant, user= user):
            raise HTTPException(status_code= 401, detail= "User does not belong to merchant")
    
    if data.mode == tokenEnums.TokenMode.LIVE:
        if not merchant.is_verified:
            raise HTTPException(status_code=404, detail="Merchant cannot process live transactions")
        
        if data.processor == transactionEnums.TransactionProcessor.FLUTTERWAVE:
            #TODO: get fltw secret keys and take this off
            raise HTTPException(status_code= 400, detail= "Flutterwave service has no support for live transactions yet")

    await customerService.add_get_or_create_customer(email= data.customer.email, merchant= merchant, session= session)
    reference = await transactionService.generate_processor_reference(session= session)
    try:
        if data.processor == transactionEnums.TransactionProcessor.KORA.value:
        
            response, status, charge_url = await koraService.initialize(
                session= session,
                email= data.customer.email,
                amount= data.amount,
                reference= reference,
                merchant=merchant,
                currency=str(data.currency),
                mode = data.mode,
                narration= data.narration
            )
            
        elif data.processor == transactionEnums.TransactionProcessor.PAYSTACK.value:
            response, status, charge_url = await paystackService.initialize(
                session= session,
                email= data.customer.email,
                amount= data.amount,
                reference= reference,
                merchant=merchant,
                currency=str(data.currency),
                mode = data.mode,
                narration= data.narration
            )
        elif data.processor == transactionEnums.TransactionProcessor.FLUTTERWAVE.value:

            response, status, charge_url = await flutterwaveService.initialize(
                session= session,
                email= data.customer.email,
                amount= data.amount,
                reference= reference,
                merchant=merchant,
                currency=str(data.currency),
                mode = data.mode,
                narration= data.narration
            )
        if status == 200:
            data = {
                'status': True,
                'message': "Charge created successfully",
                "reference": reference,
                "checkout_url": charge_url,
                "processor": data.processor
            }
        else:
            data = {
                'status': False,
                'message': response.get("message"),
            }
        
        return JSONResponse(content=data, status_code=status)
    except Exception as e:
        return JSONResponse(content= {'details': f'{e}'}, status_code= 400)

@transaction_router.get("/bulk-payouts")
async def get_merchant_transactions(
    merchant_id: str = Query(..., description="Merchant ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    mode: tokenEnums.TokenMode = tokenEnums.TokenMode.TEST,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session= session, id= merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail= "Merchant does not exist")
    
    if not await userService.user_in_merchant(user = user, merchant= merchant, session= session):
        raise HTTPException(status_code=401, detail= "User unauthorized to view merchant's transactions")
        
    total_items = await bulkpayoutService.get_total_bp(session= session, merchant_id=  merchant_id, mode= mode.value)

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No bulk payouts found for this merchant.")

    total_pages = math.ceil(total_items / page_size)

    # Paginated query
    payouts = await bulkpayoutService.get_paginated_bulk_payout(
        merchant_id= merchant_id,
        mode= mode.value,
        page= page,
        page_size= page_size,
        session= session
    )
    if payouts is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Bulk payout not found")
    
    pending_count = await bulkpayoutService.bp_count_by_status(
            session= session,
            merchant_id= merchant_id,
            status= BulkPayoutStatus.PENDING.value
        )
    failed_count = await bulkpayoutService.bp_count_by_status(
            session= session,
            merchant_id= merchant_id,
            status= BulkPayoutStatus.FAILED.value
        )
    success_count = await bulkpayoutService.bp_count_by_status(
            session= session,
            merchant_id= merchant_id,
            status= BulkPayoutStatus.SUCCESSFUL.value
        )
    partial_count = await bulkpayoutService.bp_count_by_status(
            session= session,
            merchant_id= merchant_id,
            status= BulkPayoutStatus.PARTIAL.value
        )
    total_completed = success_count + partial_count + failed_count
    success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0.0

    return {
        "payouts": [BulkPayoutResponse.model_validate(t) for t in payouts],
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "pending_count": pending_count,
        "success_count": success_count,
        "partial_count": partial_count,
        "failed_count": failed_count,
        "success_rate": success_rate
    }

@transaction_router.get("/bulk-payout/{reference}")
async def get_bulk_payout_detail(
    reference: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    payout: BulkPayout = await bulkpayoutService.get_bulk_payout_by_reference(
        session= session,
        reference= reference
    )
    if payout is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Bulk payout not found")
    
    if not await userService.user_in_merchant(user= user, merchant= payout.merchant, session= session):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "User unauthorized to view merchant's transactions")
    
    return BulkPayoutDetailResponse.model_validate(payout)
    
@transaction_router.post("/generate-receipt")
async def generate_receipt(
    data: GenerateReceiptRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    merchant = await merchantService.get_by_id_or_email(session= session, id= data.merchant_id)

    if not merchant:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Merchant does not exists")
    
    if not await userService.user_in_merchant(user= user, merchant= merchant, session= session):
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "User not authorized to view merchant's receipts")
    
    transaction = await transactionService.get_transaction_by_merchant_and_reference(
        session= session,
        merchant= merchant,
        reference= data.reference
    )

    if not transaction:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Transaction not found")
    
    if  transaction.type != transactionEnums.TransactionType.DEBIT:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Receipts can only be generated for debit transactions")
     
    try:
        output_path = receiptService.generate_receipt_pdf(transaction)
        background_tasks.add_task(os.remove, output_path)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="receipt.pdf"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@transaction_router.get("/wallet-transactions")
async def get_wallet_transactions(
    wallet_id: int = Query(..., description="Wallet ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    transaction_type: transactionEnums.TransactionType = Query(None, description="Filter by transaction type"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get all transactions for a specific wallet with pagination."""
    from database.models.Wallet import Wallet
    from sqlalchemy import func, desc

    # Get wallet and verify access
    stmt = select(Wallet).where(Wallet.id == wallet_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Verify user has access to this merchant
    merchant = await merchantService.get_by_id_or_email(session=session, id=wallet.merchant_id)
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="User unauthorized to view this wallet's transactions")

    # Build query for transactions
    query = select(func.count()).select_from(Transaction).where(Transaction.wallet_id == wallet_id)
    if transaction_type:
        query = query.where(Transaction.type == transaction_type)

    result = await session.execute(query)
    total_items = result.scalar_one()

    if total_items == 0:
        return {
            "transactions": [],
            "total_items": 0,
            "total_pages": 0,
            "current_page": page,
            "page_size": page_size,
            "wallet_info": {
                "wallet_id": wallet.id,
                "currency": wallet.currency,
                "mode": wallet.mode,
                "balance": wallet.balance
            }
        }

    total_pages = math.ceil(total_items / page_size)

    # Get paginated transactions
    query = select(Transaction).where(Transaction.wallet_id == wallet_id)
    if transaction_type:
        query = query.where(Transaction.type == transaction_type)

    query = query.order_by(desc(Transaction.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    transactions = list(result.scalars().all())

    return {
        "transactions": [TransactionResponse.model_validate(t) for t in transactions],
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "wallet_info": {
            "wallet_id": wallet.id,
            "currency": wallet.currency,
            "mode": wallet.mode,
            "balance": wallet.balance
        }
    }


@transaction_router.get("/wallet-transaction-stats")
async def get_wallet_transaction_statistics(
    wallet_id: int = Query(..., description="Wallet ID"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get transaction statistics for a specific wallet."""
    from database.models.Wallet import Wallet
    from sqlalchemy import func

    # Get wallet and verify access
    stmt = select(Wallet).where(Wallet.id == wallet_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Verify user has access to this merchant
    merchant = await merchantService.get_by_id_or_email(session=session, id=wallet.merchant_id)
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="User unauthorized to view this wallet's statistics")

    # Get transaction statistics
    # Total transactions
    total_txn_stmt = select(func.count()).select_from(Transaction).where(Transaction.wallet_id == wallet_id)
    total_txn_result = await session.execute(total_txn_stmt)
    total_transactions = total_txn_result.scalar_one()

    # Credit transactions (pay-ins)
    credit_stmt = select(
        func.count(Transaction.id).label('count'),
        func.coalesce(func.sum(Transaction.amount), 0).label('total_amount'),
        func.coalesce(func.sum(Transaction.charge), 0).label('total_charges')
    ).where(
        Transaction.wallet_id == wallet_id,
        Transaction.type == transactionEnums.TransactionType.CREDIT,
        Transaction.status == transactionEnums.TransactionStatus.SUCCESS
    )
    credit_result = await session.execute(credit_stmt)
    credit_stats = credit_result.one()

    # Debit transactions (pay-outs)
    debit_stmt = select(
        func.count(Transaction.id).label('count'),
        func.coalesce(func.sum(Transaction.amount), 0).label('total_amount'),
        func.coalesce(func.sum(Transaction.charge), 0).label('total_charges')
    ).where(
        Transaction.wallet_id == wallet_id,
        Transaction.type == transactionEnums.TransactionType.DEBIT,
        Transaction.status == transactionEnums.TransactionStatus.SUCCESS
    )
    debit_result = await session.execute(debit_stmt)
    debit_stats = debit_result.one()

    # Pending transactions
    pending_stmt = select(func.count()).select_from(Transaction).where(
        Transaction.wallet_id == wallet_id,
        Transaction.status == transactionEnums.TransactionStatus.PENDING
    )
    pending_result = await session.execute(pending_stmt)
    pending_count = pending_result.scalar_one()

    # Failed transactions
    failed_stmt = select(func.count()).select_from(Transaction).where(
        Transaction.wallet_id == wallet_id,
        Transaction.status == transactionEnums.TransactionStatus.FAILED
    )
    failed_result = await session.execute(failed_stmt)
    failed_count = failed_result.scalar_one()

    # Success rate
    success_count = credit_stats.count + debit_stats.count
    total_completed = success_count + failed_count
    success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0

    return {
        "wallet_info": {
            "wallet_id": wallet.id,
            "merchant_id": wallet.merchant_id,
            "currency": wallet.currency,
            "mode": wallet.mode,
            "current_balance": wallet.balance
        },
        "transaction_summary": {
            "total_transactions": total_transactions,
            "pending_transactions": pending_count,
            "failed_transactions": failed_count,
            "success_rate": round(success_rate, 2)
        },
        "credits": {
            "count": credit_stats.count,
            "total_amount": float(credit_stats.total_amount),
            "total_charges": float(credit_stats.total_charges),
            "net_amount": float(credit_stats.total_amount - credit_stats.total_charges)
        },
        "debits": {
            "count": debit_stats.count,
            "total_amount": float(debit_stats.total_amount),
            "total_charges": float(debit_stats.total_charges),
            "total_with_charges": float(debit_stats.total_amount + debit_stats.total_charges)
        },
        "charges": {
            "payin_percentage": wallet.percentage_charge,
            "payin_flat": wallet.flat_charge,
            "payout_percentage": wallet.payout_percentage_charge,
            "payout_flat": wallet.payout_flat_charge
        }
    }


@transaction_router.get("/merchant-transactions-by-wallet")
async def get_merchant_transactions_grouped_by_wallet(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(..., description="Mode: test or live"),
    currency: str = Query(None, description="Filter by currency"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get merchant transactions grouped by wallet."""
    from database.models.Wallet import Wallet
    from sqlalchemy import func

    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant does not exist")

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="User unauthorized to view merchant's transactions")

    # Get wallets for the merchant
    wallets_query = select(Wallet).where(
        Wallet.merchant_id == merchant_id,
        Wallet.mode == mode.value
    )
    if currency:
        wallets_query = wallets_query.where(Wallet.currency == currency)

    wallets_result = await session.execute(wallets_query)
    wallets = list(wallets_result.scalars().all())

    if not wallets:
        raise HTTPException(status_code=404, detail="No wallets found for this merchant")

    wallet_summaries = []

    for wallet in wallets:
        # Get transaction counts by type
        credit_count_stmt = select(func.count()).select_from(Transaction).where(
            Transaction.wallet_id == wallet.id,
            Transaction.type == transactionEnums.TransactionType.CREDIT
        )
        credit_count_result = await session.execute(credit_count_stmt)
        credit_count = credit_count_result.scalar_one()

        debit_count_stmt = select(func.count()).select_from(Transaction).where(
            Transaction.wallet_id == wallet.id,
            Transaction.type == transactionEnums.TransactionType.DEBIT
        )
        debit_count_result = await session.execute(debit_count_stmt)
        debit_count = debit_count_result.scalar_one()

        # Get total amounts
        credit_amount_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.wallet_id == wallet.id,
            Transaction.type == transactionEnums.TransactionType.CREDIT,
            Transaction.status == transactionEnums.TransactionStatus.SUCCESS
        )
        credit_amount_result = await session.execute(credit_amount_stmt)
        total_credit = credit_amount_result.scalar_one()

        debit_amount_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.wallet_id == wallet.id,
            Transaction.type == transactionEnums.TransactionType.DEBIT,
            Transaction.status == transactionEnums.TransactionStatus.SUCCESS
        )
        debit_amount_result = await session.execute(debit_amount_stmt)
        total_debit = debit_amount_result.scalar_one()

        wallet_summaries.append({
            "wallet_id": wallet.id,
            "currency": wallet.currency,
            "mode": wallet.mode,
            "balance": wallet.balance,
            "transaction_counts": {
                "credits": credit_count,
                "debits": debit_count,
                "total": credit_count + debit_count
            },
            "amounts": {
                "total_credits": float(total_credit),
                "total_debits": float(total_debit),
                "net_flow": float(total_credit - total_debit)
            }
        })

    return {
        "merchant_id": merchant_id,
        "mode": mode.value,
        "wallets": wallet_summaries,
        "summary": {
            "total_wallets": len(wallets),
            "total_balance": sum(w.balance for w in wallets)
        }
    }


@transaction_router.get("/wallet-revenue-trends")
async def get_wallet_revenue_trends(
    wallet_id: int = Query(..., description="Wallet ID"),
    group_by: transactionEnums.GroupBy = Query(transactionEnums.GroupBy.DAY, description="Group by: day, week, month, year"),
    start_date: str = Query(None, description="Start date (ISO format)"),
    end_date: str = Query(None, description="End date (ISO format)"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """Get revenue trends for a wallet over time, grouped by day/week/month/year."""
    from database.models.Wallet import Wallet
    from sqlalchemy import func
    from datetime import datetime

    # Get wallet and verify access
    stmt = select(Wallet).where(Wallet.id == wallet_id)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Verify user has access to this merchant
    merchant = await merchantService.get_by_id_or_email(session=session, id=wallet.merchant_id)
    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        raise HTTPException(status_code=401, detail="User unauthorized to view this wallet's revenue trends")

    # Build query for credit transactions (pay-ins)
    trunc_period = func.date_trunc(group_by.value, Transaction.created_at).label("period")
    credits_stmt = (
        select(
            trunc_period,
            func.count(Transaction.id).label("transaction_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("gross_revenue"),
            func.coalesce(func.sum(Transaction.charge), 0).label("charges"),
            func.coalesce(func.sum(Transaction.processor_charge), 0).label("processor_charges")
        )
        .where(
            Transaction.wallet_id == wallet_id,
            Transaction.type == transactionEnums.TransactionType.CREDIT,
            Transaction.status == transactionEnums.TransactionStatus.SUCCESS
        )
        .group_by(trunc_period)
        .order_by(trunc_period)
    )

    # Apply date filters if provided
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            credits_stmt = credits_stmt.where(Transaction.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DD)")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            credits_stmt = credits_stmt.where(Transaction.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DD)")

    credits_result = await session.execute(credits_stmt)

    # Build query for debit transactions (pay-outs)
    debits_stmt = (
        select(
            trunc_period,
            func.count(Transaction.id).label("transaction_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.coalesce(func.sum(Transaction.charge), 0).label("charges")
        )
        .where(
            Transaction.wallet_id == wallet_id,
            Transaction.type == transactionEnums.TransactionType.DEBIT,
            Transaction.status == transactionEnums.TransactionStatus.SUCCESS
        )
        .group_by(trunc_period)
        .order_by(trunc_period)
    )

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            debits_stmt = debits_stmt.where(Transaction.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            debits_stmt = debits_stmt.where(Transaction.created_at <= end_dt)
        except ValueError:
            pass

    debits_result = await session.execute(debits_stmt)

    # Format results
    credit_trends = [
        {
            "period": row.period.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_count": row.transaction_count,
            "gross_revenue": float(row.gross_revenue),
            "charges": float(row.charges),
            "processor_charges": float(row.processor_charges),
            "net_revenue": float(row.gross_revenue - row.charges)
        }
        for row in credits_result
    ]

    debit_trends = [
        {
            "period": row.period.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_count": row.transaction_count,
            "total_amount": float(row.total_amount),
            "charges": float(row.charges),
            "total_with_charges": float(row.total_amount + row.charges)
        }
        for row in debits_result
    ]

    return {
        "wallet_info": {
            "wallet_id": wallet.id,
            "currency": wallet.currency,
            "mode": wallet.mode,
            "current_balance": wallet.balance
        },
        "group_by": group_by.value,
        "date_range": {
            "start_date": start_date,
            "end_date": end_date
        },
        "credit_trends": credit_trends,
        "debit_trends": debit_trends,
        "summary": {
            "total_periods": max(len(credit_trends), len(debit_trends)),
            "total_credits": sum(t["gross_revenue"] for t in credit_trends),
            "total_debits": sum(t["total_amount"] for t in debit_trends),
            "total_charges_collected": sum(t["charges"] for t in credit_trends) + sum(t["charges"] for t in debit_trends)
        }
    }
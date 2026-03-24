from fastapi import APIRouter, HTTPException, Depends, Security, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services import merchantService, tokenService, transactionService, customerService, walletService
from external_services import koraService, paystackService, flutterwaveService
from schemas.merchantSchema import MerchantCreateRequest, MerchantResponse, MerchantDetailResponse, MerchantGetRequest
from tortoise.exceptions import DoesNotExist
import json
from fastapi.responses import JSONResponse
from schemas.v1Schema import *
from enums import transactionEnums, tokenEnums
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from lib import bank
from database.models.Transaction import Transaction
payout_router = APIRouter()
security = HTTPBearer()  # this enables the "Authorize" button 

@payout_router.post(
    "/api/v1/payout",
    response_model=PayoutResponse,
    responses={
        400: {
            "model": PayoutErrorResponse,
            "description": "Bad request, e.g., insufficient balance or duplicate reference",
            "content": {
                "application/json": {
                    "examples": {
                        "insufficient_balance": {
                            "summary": "Insufficient balance",
                            "value": {"detail": "Insufficient balance"}
                        },
                        "duplicate_reference": {
                            "summary": "Duplicate reference",
                            "value": { "detail": "Transaction reference not unique for merchant"}
                        }
                    }
                }
            }
        },
        403: {
            "model": PayoutErrorResponse,
            "description": "Invalid token or bank code",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {"detail": "Invalid payment secret key"}
                        },
                        "invalid_bank_code": {
                            "summary": "Invalid bank code",
                            "value": { "detail": "Invalid bank code provided"}
                        }
                    }
                }
            }
        },
        404: {
            "model": PayoutErrorResponse,
            "description": "Merchant not found",
            "content": {
                "application/json": {
                    "examples": {
                        "merchant_not_found": {
                            "summary": "Merchant not found",
                            "value": {"detail": "Merchant not found"}
                        }
                    }
                }
            }
        },
        409: {
            "description": "Conflict - invalid account",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_account": {
                            "summary": "Invalid account conflict",
                            "value": {
                                "status": False,
                                "message": "Invalid account.",
                                "data": {
                                    "amount": 5000,
                                    "fee": 50,
                                    "reference": "PAYOUT_12346",
                                    "customer": {
                                        "email": "user@example.com",
                                        "name": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        422: {
            "model": PayoutErrorResponse,
            "description": "Invalid request, e.g., amount less than minimum 200",
            "content": {
                "application/json": {
                    "examples": {
                        "amount_too_low": {
                            "summary": "Amount less than minimum",
                            "value": {"detail": "Amount must be greater than 200"}
                        }
                    }
                }
            }
        }
    }
)

async def payout(
    payload: PayoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    token = credentials.credentials  # clean token string (no "Bearer " prefix)
    if payload.amount < 200:
        raise HTTPException(status_code= status.HTTP_422_UNPROCESSABLE_ENTITY, detail= "Amount must be greater than 200")
    
    merchant_id = token.split('_')[-1]
    mode = token.split('_')[1]
    
    merchant = await merchantService.get_by_id_or_email(session= session, id=merchant_id)
    bank_obj = bank.find_bank_by_code(code= payload.destination.bank_code)

    if not bank_obj:
        raise HTTPException(status_code=403, detail="Invalid bank code provided")

    if not await tokenService.verify_token(session= session, provided_token=token):
        raise HTTPException(status_code=403, detail="Invalid payment secret key")
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    if await transactionService.get_transaction_by_merchant_and_reference(merchant= merchant, reference= payload.reference, session= session):
        raise HTTPException(status_code = 400, detail = "Transaction reference not unique for merchant")

    # Get wallet for balance check and charge calculation
    wallet = await walletService.get_wallet(
        session=session,
        merchant_id=merchant.id,
        currency=payload.currency,
        mode=mode
    )

    if not wallet:
        raise HTTPException(status_code=400, detail=f"Wallet not found for {payload.currency} in {mode} mode")

    # Calculate charge using wallet's charge configuration
    amount_charged = await walletService.get_payout_charge(wallet=wallet, amount=payload.amount)

    if wallet.balance < amount_charged + payload.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")    
        
    _, message, status_code, txn_id = await koraService.payout(
        session= session, merchant= merchant, acc_number= payload.destination.account_number, 
        bank_code= payload.destination.bank_code, amount = payload.amount, email= payload.customer.email,
        reference = payload.reference, currency = payload.currency, 
        metadata= payload.metadata, narration= payload.narration, mode= mode
    )

    transaction: Transaction = await transactionService.get_transaction_by_merchant_and_reference(session= session, merchant= merchant, reference= payload.reference)

    if _ == True and status_code == 200:
        total_amount = amount_charged + payload.amount

        # if mode == tokenEnums.TokenMode.TEST.value:
        #     merchant.test_balance -= total_amount

        # if mode == tokenEnums.TokenMode.LIVE.value:
        #     merchant.live_balance -= total_amount

        transaction.status = transactionEnums.TransactionStatus.SUCCESS.value 

    else:
        transaction.status = transactionEnums.TransactionStatus.FAILED.value
    await merchantService.save_merchant(session= session, merchant= merchant)
    await transactionService.save_transaction(session= session, transaction= transaction)
    
    is_valid, customer_name = await koraService.resolve_account(acc_number=payload.destination.account_number, bank= bank_obj, currency= payload.currency)

    return JSONResponse(content= {
        'status' : _,
        'message': message,
        'data': {
            'amount': payload.amount,
            'fee': amount_charged,
            'reference': payload.reference,
            'customer':{
                'email': payload.customer.email,
                'name': payload.customer.name if payload.customer.name else customer_name
            }
        }
    }, status_code= status_code)
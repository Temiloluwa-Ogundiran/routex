from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services import merchantService, tokenService, transactionService, customerService, walletService
from fastapi.responses import JSONResponse
from schemas.v1Schema import *
from enums import tokenEnums
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from lib import bank
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
    token = credentials.credentials
    if payload.amount < 200:
        raise HTTPException(status_code= status.HTTP_422_UNPROCESSABLE_ENTITY, detail= "Amount must be greater than 200")

    if not await tokenService.verify_token(session= session, provided_token=token):
        raise HTTPException(status_code=403, detail="Invalid payment secret key")

    merchant_id = token.split('_')[-1]
    mode = token.split('_')[1]

    merchant = await merchantService.get_by_id_or_email(session= session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    bank_obj = bank.find_bank_by_code(code= payload.destination.bank_code)
    if not bank_obj:
        raise HTTPException(status_code=403, detail="Invalid bank code provided")

    if await transactionService.get_transaction_by_merchant_and_reference(merchant= merchant, reference= payload.reference, session= session):
        raise HTTPException(status_code = 400, detail = "Transaction reference not unique for merchant")

    wallet = await walletService.get_wallet(
        session=session,
        merchant_id=merchant.id,
        currency=payload.currency,
        mode=mode
    )

    if not wallet:
        raise HTTPException(status_code=400, detail=f"Wallet not found for {payload.currency} in {mode} mode")

    payout_fee = await walletService.get_payout_charge(wallet=wallet, amount=payload.amount)
    total_deducted = payout_fee + payload.amount
    if wallet.balance < total_deducted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    customer, _ = await customerService.add_get_or_create_customer(
        session=session,
        email=payload.customer.email,
        merchant=merchant,
    )

    if payload.customer.name:
        customer.name = payload.customer.name

    _, balance_before, balance_after = await transactionService.create_simulated_payout(
        session=session,
        merchant=merchant,
        wallet=wallet,
        amount=payload.amount,
        charge=payout_fee,
        reference=payload.reference,
        currency=payload.currency,
        mode=mode,
        destination_account_number=payload.destination.account_number,
        destination_bank_code=payload.destination.bank_code,
        destination_bank_name=bank_obj.name,
        customer=customer,
        customer_name=payload.customer.name,
        narration=payload.narration,
        metadata_payload=payload.metadata,
    )

    return JSONResponse(content= {
        'status' : True,
        'message': "Payout simulated successfully",
        'reference': payload.reference,
        'data': {
            'amount': payload.amount,
            'currency': payload.currency,
            'fee': payout_fee,
            'total_deducted': total_deducted,
            'balance_before': balance_before,
            'balance_after': balance_after,
            'reference': payload.reference,
            'customer':{
                'email': payload.customer.email,
                'name': payload.customer.name or customer.name or "Recipient"
            },
            'destination': {
                'bank_code': payload.destination.bank_code,
                'bank_name': bank_obj.name,
                'account_number': payload.destination.account_number,
            },
        }
    }, status_code= status.HTTP_200_OK)

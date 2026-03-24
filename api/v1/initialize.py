from fastapi import APIRouter, HTTPException, Depends, Security, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services import merchantService, tokenService, transactionService, customerService
from external_services import koraService, paystackService, flutterwaveService
from schemas.merchantSchema import MerchantCreateRequest, MerchantResponse, MerchantDetailResponse, MerchantGetRequest
from tortoise.exceptions import DoesNotExist
import json
from fastapi.responses import JSONResponse
from schemas.v1Schema import *
from enums import transactionEnums, tokenEnums
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from settings import CHECKOUT_URL

initialize_router = APIRouter()

security = HTTPBearer()  # this enables the "Authorize" button 

@initialize_router.post(
    "/api/v1/initiate",
    response_model=InitializeTransactionResponse,
    responses={
        400: {
            "model": InitializeErrorResponse,
            "description": "Bad request, e.g., duplicate transaction reference",
            "content": {
                "application/json": {
                    "examples": {
                        "duplicate_reference": {
                            "summary": "Duplicate reference",
                            "value": {"detail": "Transaction reference not unique for merchant"}
                        }
                    }
                }
            }
        },
        403: {
            "model": InitializeErrorResponse,
            "description": "Invalid payment secret key",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": { "detail": "Invalid payment secret key provided"}
                        }
                    }
                }
            }
        },
        404: {
            "model": InitializeErrorResponse,
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
        }
    }
)
async def initiate_checkout(
    payload: InitializeTransactionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    token = credentials.credentials  # clean token string (no "Bearer " prefix)
    merchant_id = token.split('_')[-1]
    mode = token.split('_')[1]
    merchant = await merchantService.get_by_id_or_email(session= session, id=merchant_id)

    if not await tokenService.verify_token(session= session, provided_token=token):
        raise HTTPException(status_code=403, detail="Invalid payment secret key")
    

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # if 
    if await transactionService.get_transaction_by_merchant_and_reference(merchant= merchant, reference= payload.reference, session= session):
        raise HTTPException(status_code = 400, detail = "Transaction reference not unique for merchant")
    
    await customerService.add_get_or_create_customer(email= payload.customer.email, merchant= merchant, session= session)
    try:

        response, status, charge_url = await koraService.initialize(
            session= session,
            email=payload.customer.email,
            amount=payload.amount,
            merchant=merchant,
            currency=str(payload.currency),
            reference = payload.reference,
            redirect_url=payload.redirect_url,
            notification_url=payload.notification_url,
            metadata=payload.metadata,
            mode = mode
        )
            
        if status == 200:
            data = {
                'status': True,
                'message': "Charge created successfully",
                "reference": payload.reference,
                "checkout_url": charge_url,
            }
        else:
            data = {
                'status': False,
                'message': response.get("message"),
            }
        return JSONResponse(content=data, status_code=status)
    except Exception as e:
        print(f"Exception occured here!!")
        return JSONResponse(content= {'details': f'{e}'}, status_code= 400)
    
@initialize_router.post(
    "/api/v2/initiate",
    response_model=InitializeTransactionResponse,
    responses={
        400: {
            "model": InitializeErrorResponse,
            "description": "Bad request, e.g., duplicate transaction reference",
            "content": {
                "application/json": {
                    "examples": {
                        "duplicate_reference": {
                            "summary": "Duplicate reference",
                            "value": {"detail": "Transaction reference not unique for merchant"}
                        }
                    }
                }
            }
        },
        403: {
            "model": InitializeErrorResponse,
            "description": "Invalid payment secret key",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": { "detail": "Invalid payment secret key provided"}
                        }
                    }
                }
            }
        },
        404: {
            "model": InitializeErrorResponse,
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
        }
    }
)
async def initiate_checkout_V2(
    payload: InitializeTransactionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    token = credentials.credentials  # clean token string (no "Bearer " prefix)
    merchant_id = token.split('_')[-1]
    mode = token.split('_')[1]
    merchant = await merchantService.get_by_id_or_email(session= session, id=merchant_id)

    if not await tokenService.verify_token(session= session, provided_token=token):
        raise HTTPException(status_code=403, detail="Invalid payment secret key")
    

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    if await transactionService.get_transaction_by_merchant_and_reference(merchant= merchant, reference= payload.reference, session= session):
        raise HTTPException(status_code = 400, detail = "Transaction reference not unique for merchant")
    
    customer, created = await customerService.add_get_or_create_customer(email= payload.customer.email, merchant= merchant, session= session)
    try:
        transaction  = await transactionService.create_transaction(
            session= session,
            merchant= merchant,
            processor= transactionEnums.TransactionProcessor.KORA,
            amount= payload.amount,
            currency= payload.currency,
            reference= payload.reference,
            customer= customer,
            type= transactionEnums.TransactionType.CREDIT,
            mode= mode,
            metadata_payload= payload.metadata,
            redirect_url= payload.redirect_url,
            notification_url= payload.notification_url
        )
        date_value = transaction.created_at.isoformat()
        data = {
            'status': True,
            'message': "Charge created successfully",
            "reference": payload.reference,
            "checkout_url": f"{CHECKOUT_URL}/{transaction.reference}/{date_value}",
        }
        return JSONResponse(content=data, status_code=200)

    except Exception as e:
        return JSONResponse(content= {'details': f'{e}'}, status_code= 400)

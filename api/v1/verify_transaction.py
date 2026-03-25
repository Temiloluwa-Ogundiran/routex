from fastapi import APIRouter, HTTPException, Depends, Security, Request, Response, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services import merchantService, tokenService, transactionService, customerService
from external_services import koraService, paystackService, flutterwaveService
from schemas.merchantSchema import MerchantCreateRequest, MerchantResponse, MerchantDetailResponse, MerchantGetRequest
from tortoise.exceptions import DoesNotExist
import json
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from schemas.v1Schema import *
from enums import transactionEnums, tokenEnums
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.session import get_async_session
from database.models.RoutingAttempt import RoutingAttempt
from database.models.RoutingDecisionAudit import RoutingDecisionAudit
from external_services.adapters import get_adapter

verify_router = APIRouter()

security = HTTPBearer()  # this enables the "Authorize" button 
@verify_router.get(
    "/api/v1/transactions/verify",
    response_model=VerifyTransactionResponse,
    responses={
        400: {
            "model": VerifyErrorResponse,
            "description": "Bad request or verification failed",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_ref": {
                            "summary": "Invalid reference format",
                            "value": {"detail": "Verification failed: invalid reference format"}
                        }
                    }
                }
            }
        },
        403: {
            "model": VerifyErrorResponse,
            "description": "Invalid payment secret key",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {"detail": "Invalid payment secret key provided"}
                        }
                    }
                }
            }
        },
        404: {
            "model": VerifyErrorResponse,
            "description": "Merchant or transaction not found",
            "content": {
                "application/json": {
                    "examples": {
                        "merchant_not_found": {
                            "summary": "Merchant not found",
                            "value": {"detail": "Merchant not found"}
                        },
                        "transaction_not_found": {
                            "summary": "Transaction not found",
                            "value": {"detail": "Transaction not found"}
                        },
                        "test_mode_error": {
                            "summary": "Test mode cannot see live transaction",
                            "value": {"detail": "Test domain can only see transactions in test mode"}
                        }
                    }
                }
            }
        }
    }
)
async def verify(
    reference: str = Query(..., description="Transaction reference"),
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
    
    transaction= await transactionService.get_transaction_by_merchant_and_reference(session= session, merchant= merchant, reference= reference)

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if mode == tokenEnums.TokenMode.TEST.value and transaction.mode == tokenEnums.TokenMode.LIVE.value:
        raise HTTPException(status_code=404, detail="Test domain can only see transactions in test mode")

    try:
        selected_gateway = transaction.selected_gateway or transaction.processor
        if selected_gateway == transactionEnums.TransactionProcessor.INTERSWITCH.value:
            adapter = get_adapter(selected_gateway)
            verify_response, verify_status = await adapter.verify_transaction(
                session=session,
                transaction=transaction,
            )
            if verify_status == 200:
                from external_services import interswitchService

                transaction.status = interswitchService.normalize_verify_status(
                    verify_response,
                    transaction.status,
                )
                transaction.details = {
                    "gateway": selected_gateway,
                    "verify_response": verify_response,
                }
                session.add(transaction)
                await session.commit()
                await session.refresh(transaction)

        attempts_result = await session.execute(
            select(RoutingAttempt)
            .where(RoutingAttempt.transaction_id == transaction.id)
            .order_by(RoutingAttempt.attempt_no.asc())
        )
        attempts = attempts_result.scalars().all()
        decisions_result = await session.execute(
            select(RoutingDecisionAudit)
            .where(RoutingDecisionAudit.transaction_id == transaction.id)
            .order_by(RoutingDecisionAudit.created_at.desc())
        )
        latest_decision = decisions_result.scalars().first()

        data = {
            "status": True,
            "message": "verification successful",
            "data": {
                "reference": transaction.reference,
                "status": transaction.status,
                "domain": transaction.mode,
                "type": transaction.type,
                "amount": transaction.amount,
                "fee": transaction.charge,
                "currency": transaction.currency,
                "narration": transaction.narration,
                "metadata": transaction.metadata_payload,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at,
                "selected_gateway": selected_gateway or getattr(latest_decision, "selected_gateway", None),
                "gateway_reference": transaction.processor_reference,
                "attempts": [
                    {
                        "attempt_no": attempt.attempt_no,
                        "gateway": attempt.gateway_code,
                        "status": attempt.status,
                        "gateway_reference": attempt.gateway_reference,
                        "latency_ms": attempt.latency_ms,
                    }
                    for attempt in attempts
                ],
                "customer": {"email": transaction.customer.email} 
            }
        }
        status = 200
    except Exception as e:
        data = {"status": False, 'message': f"{e}"}
        status = 400
    print(f"verification data: {data}")
    
    return JSONResponse(content= jsonable_encoder(data), status_code= status)
   

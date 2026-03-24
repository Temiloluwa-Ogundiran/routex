from schemas.apiCheckoutSchema import CompleteTransactionRequest, AuthroizeMmRequest
from fastapi import Request, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from services import transactionService, merchantService, customerService
from database.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from enums.transactionEnums import TransactionCurrency, TransactionStatus, TransactionChannel
from external_services import koraService, basqetService

checkout_router = APIRouter()

@checkout_router.post(
        "/api/v2/complete"
)
async def complete_checkout_v2(
    request_data: CompleteTransactionRequest,
    session: AsyncSession = Depends(get_async_session)
):
    transaction = await transactionService.get_transaction_by_reference_and_datetime(
        session=session,
        reference=request_data.reference,
        datetime_str=request_data.datetime
    )
    if not transaction:
        raise HTTPException(detail="Transaction not found", status_code=404)

    customer = await customerService.get_by_id_or_email(session=session, id=transaction.customer_id)

    if transaction.status != TransactionStatus.PENDING:
        raise HTTPException(detail="Transaction already completed/expired", status_code=400)

    # Regenerate processor_reference for uniqueness before sending to payment processor
    new_processor_reference = await transactionService.generate_processor_reference(session=session)
    transaction.processor_reference = new_processor_reference
    await session.commit()
    await session.refresh(transaction)

    if transaction.currency in [TransactionCurrency.BITCOIN, TransactionCurrency.ETHEREUM, TransactionCurrency.TETHER, TransactionCurrency.SOLANA]:
        merchant = await merchantService.get_by_id_or_email(session= session, id= transaction.merchant_id)
        response_data = await basqetService.charge_with_crypto(
            session= session,
            customer_email= customer.email,
            amount= transaction.amount,
            txn= transaction,
            merchant= merchant
        )
        return JSONResponse(content= response_data, status_code= 200 if response_data.get('status') == True else 400)
    if transaction.currency == TransactionCurrency.NIGERIA:
        if request_data.channel not in [TransactionChannel.CARD, TransactionChannel.TRANSFER]:
            raise HTTPException(detail= "Ngn transactions can only be processed through Card or Transfer", status_code= 400)

        if request_data.channel == TransactionChannel.TRANSFER:
            merchant = await merchantService.get_by_id_or_email(session= session, id= transaction.merchant_id)
            result = await koraService.charge_bank_transfer(
                session=session,
                merchant= merchant,
                tx= transaction,
                customer_email= customer.email
            )
            return JSONResponse(content= result, status_code= 200 if result.get('status') == True else 400)
        else:
            raise HTTPException(detail= "Card transactions not available for now", status_code= 400)
    else:
        if request_data.channel != TransactionChannel.MOBILE_MONEY:
            raise HTTPException(detail= f"Mobile money channel required for {transaction.currency} transaction", status_code= 400)
        
        if not request_data.mobile_money_number:
            raise HTTPException(detail= "Mobile money number expected", status_code= 400)
        
        #Pan-African currencies - Mobile money
        merchant = await merchantService.get_by_id_or_email(session= session, id= transaction.merchant_id)
        result = await koraService.charge_mobile_money(
            merchant= merchant,
            tx= transaction,
            customer_email= customer.email,
            mobile_money_number= request_data.mobile_money_number
        )
        return JSONResponse(content= result, status_code= 200 if result.get('status') == True else 400)


@checkout_router.post("/api/v2/complete/authorize")
async def authorize_mobile_money_checkout(
    request: AuthroizeMmRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authorize mobile money transaction with OTP/PIN
    This endpoint is called after the initial mobile money charge has been initiated
    and the user has received an OTP or PIN prompt
    """
    tx = await transactionService.get_transaction_by_reference_and_datetime(
        session=session,
        reference=request.reference,
        datetime_str=request.datetime
    )

    if not tx:
        raise HTTPException(detail="Transaction not found", status_code=404)

    # Verify transaction is pending and requires authorization
    if tx.status != TransactionStatus.PENDING:
        raise HTTPException(detail="Transaction already completed or expired", status_code=400)

    # Verify this is a mobile money transaction
    if tx.currency in [TransactionCurrency.NIGERIA, TransactionCurrency.BITCOIN, TransactionCurrency.ETHEREUM, TransactionCurrency.TETHER, TransactionCurrency.SOLANA]:
        raise HTTPException(detail="This endpoint is only for mobile money transactions", status_code=400)

    # Call koraService to authorize the mobile money transaction with OTP
    result = await koraService.authorize_mobile_money_otp(tx=tx, token=request.otp)

    # Return the result from the payment processor
    status_code = 200 if result.get('status') == True else 400
    return JSONResponse(content=result, status_code=status_code)
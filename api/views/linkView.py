# views/link_view.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from database.models.User import User
from services import userService, merchantService, linkService, transactionService, linkService, customerService, celeryService
from schemas import linkSchema, transactionSchema
from typing import Optional
from datetime import datetime, timezone
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from enums import transactionEnums, LinkEnums
from enums.transactionEnums import TransactionCurrency
from database.models.Transaction import Transaction
from external_services import basqetService
from external_services.adapters import get_adapter
from services import routingService

link_router = APIRouter(prefix="/links", tags=["payment_links"])


# -------------------------
# Merchant creates a link
# -------------------------
# views/link_view.py

@link_router.post("/", response_model=linkSchema.PaymentLinkResponse)
async def create_link(
    data: linkSchema.PaymentLinkCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    try:
        
        
        merchant = await merchantService.get_by_id_or_email(id=data.merchant_id, session=session)
        if not merchant:
            raise HTTPException(status_code=404, detail="Merchant not found")

        # Authorization
        if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
            raise HTTPException(status_code=403, detail="Not authorized")

        link = await linkService.create_payment_link(
            session=session,
            merchant=merchant,
            data=data
        )
        return await linkService.get_payment_link_response(
            session= session,
            link_id= link.id
        )
    except ValueError as e:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f"{e}")


# -------------------------
# Merchant lists links
# -------------------------
@link_router.get("/merchant/{merchant_id}", response_model=list[linkSchema.PaymentLinkResponse])
async def list_links(
    merchant_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    try:
        

        merchant = await merchantService.get_by_id_or_email(id=merchant_id, session=session)
        if not merchant:
            raise HTTPException(status_code=404, detail="Merchant not found")
        
        

        links = await linkService.get_links_by_merchant(session=session, merchant=merchant)
        responses = [
            await linkService.get_payment_link_response(session, link.id)
            for link in links
        ]
        return responses
    
    except ValueError as e:
       raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f"{e}")


# -------------------------
# Public: view link by reference (before checkout)
# -------------------------
@link_router.get("/r/{reference}", response_model=linkSchema.PaymentLinkResponse)
async def public_fetch_by_reference(reference: str, session: AsyncSession = Depends(get_async_session)):
    try:
        link = await linkService.get_payment_link_by_reference(session=session, reference=reference)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        # return minimal view (frontend decides to show amount input for dynamic)
        return await linkService.get_payment_link_response(
            session= session,
            link_id= link.id
        )
    except ValueError as e:
       raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f"{e}")

# -------------------------
# Public: initialize checkout for a link (creates pending tx and returns checkout URL)
# -------------------------
class CheckoutRequest(BaseModel):
    amount: Optional[float] = None
    # customer_id: Optional[int] = None
    # customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    currency: Optional[str] = transactionEnums.TransactionCurrency.NIGERIA
    narration: Optional[str] = None
    channel: Optional[str] = None

@link_router.post("/r/{reference}/checkout")
async def init_checkout(
    reference: str,
    body: CheckoutRequest,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        if body.currency in [TransactionCurrency.GHANA, TransactionCurrency.KENYA]:
            #TODO: Enable cross-border
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= "Only Naira/Crypto transactions can be performed for now"
            )

        link = await linkService.validate_link(session=session, reference=reference, amount=body.amount)

        if link.amount_type == LinkEnums.AmountType.DYNAMIC:
            if not body.amount:
                raise HTTPException(status_code= status.HTTP_422_UNPROCESSABLE_ENTITY, detail= "Dynamic links require amount to be specified")
            amount = float(body.amount)
        else:
            amount = float(link.amount)

        merchant = await merchantService.get_by_id_or_email(
            session= session,
            id= link.merchant_id
        )
        customer, _= await customerService.add_get_or_create_customer(session= session, email= body.customer_email, merchant= merchant)
        if body.channel == transactionEnums.TransactionChannel.CRYPTO:
            #TODO: Crypto channel
            if body.currency in [TransactionCurrency.NIGERIA, TransactionCurrency.GHANA, TransactionCurrency.KENYA]:
                raise HTTPException(
                    status_code= status.HTTP_400_BAD_REQUEST,
                    detail= "Crypto currency value expected"
                )

            data = await basqetService.charge_with_crypto(
                session= session, customer_email= body.customer_email, amount= amount,
                txn= tx, merchant= None
            )
            return data

        if link.gateway_code:
            decision = await routingService.build_manual_routing_decision(
                session=session,
                operation="collection",
                currency=str(body.currency),
                amount=amount,
                merchant_id=merchant.id,
                gateway_code=link.gateway_code,
                channel=body.channel,
            )
        else:
            decision = await routingService.build_routing_decision(
                session=session,
                operation="collection",
                currency=str(body.currency),
                amount=amount,
                merchant_id=merchant.id,
                channel=body.channel,
            )

        adapter = get_adapter(decision.selected_gateway)
        transaction_reference = f"plink_{await transactionService.generate_processor_reference(session=session)}"
        response, response_status, charge_url = await adapter.initialize_collection(
            session=session,
            email=body.customer_email,
            amount=amount,
            merchant=merchant,
            currency=str(body.currency),
            reference=transaction_reference,
            redirect_url=link.redirect_url,
            notification_url=merchant.live_webhook_url if link.mode == LinkEnums.LinkMode.LIVE else merchant.test_webhook_url,
            metadata={"payment_link_reference": link.reference},
            narration=body.narration,
            mode=link.mode,
        )

        transaction = await transactionService.get_transaction_by_merchant_and_reference(
            session=session,
            merchant=merchant,
            reference=transaction_reference,
        )
        if transaction:
            transaction.payment_link = link
            transaction.selected_gateway = decision.selected_gateway
            transaction.redirect_url = link.redirect_url
            await transactionService.save_transaction(session=session, transaction=transaction)

        data = {
            "status": response_status == 200,
            "message": response.get("message", "Checkout created successfully"),
            "reference": transaction_reference,
            "checkout_url": charge_url,
            "selected_gateway": decision.selected_gateway,
        }
        if transaction:
            data["gateway_reference"] = transaction.processor_reference
        return JSONResponse(content=data, status_code=response_status)

    except Exception as e:
       raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f"{e}")


# -------------------------
# Merchant get link detail
# -------------------------
@link_router.get("/{link_id}", response_model=linkSchema.PaymentLinkDetailResponse)
async def get_link_detail(
    link_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    try:   
        
        link = await linkService.get_payment_link_by_id_txn(session=session, link_id=link_id)

        if not link:
            raise HTTPException(status_code=404, detail="Link not found")

        if not await userService.user_in_merchant(user=user, merchant=link.merchant, session=session):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return link
    
    except ValueError as e:
       raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f"{e}")


# -------------------------
# Merchant update link
# -------------------------
@link_router.put("/{link_id}", response_model=linkSchema.PaymentLinkResponse)
async def update_link(
    link_id: str,
    request: linkSchema.PaymentLinkUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    try: 
        
        
        link = await linkService.get_payment_link_by_id(session=session, link_id=link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        if not await userService.user_in_merchant(user=user, merchant=link.merchant, session=session):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if not link.is_valid():
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Payment link is not active or has expired/used up")
        
        

        updated = await linkService.update_payment_link(
            session=session,
            link=link,
            title=request.title,
            amount=request.amount,
            max_uses=request.max_uses,
            gateway_code=request.gateway_code,
            description=request.description,
            redirect_url=str(request.redirect_url) if request.redirect_url else None,
            expires_at=request.expires_at,
            metadata=request.metadata,
            is_active=request.is_active
        )
        return await linkService.get_payment_link_response(
            session= session,
            link_id= updated.id
        )
    except ValueError as e:
       raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f"{e}")

# -------------------------
# Merchant deactivate link
# -------------------------
@link_router.delete("/{link_id}", response_model=linkSchema.PaymentLinkResponse)
async def deactivate_link(
    link_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user),
):
    try:        
        link = await linkService.get_payment_link_by_id(session=session, link_id=link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        if not await userService.user_in_merchant(user=user, merchant=link.merchant, session=session):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        deactivated = await linkService.soft_delete_payment_link(session=session, link=link)
        return await linkService.get_payment_link_response(
            session= session,
            link_id= deactivated.id
        )
    except ValueError as e:
       raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= f"{e}")



class VerifyTransactionRequest(BaseModel):
    reference: str
    customer_email: str
    merchant_id: str

@link_router.post("/verify-transaction", response_model=transactionSchema.TransactionResponse)
async def verify_transaction(
    body: VerifyTransactionRequest,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        merchant = await merchantService.get_by_id_or_email(session= session, id= body.merchant_id)
        
        if not merchant:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Merchant does not exist")
        
        # Fetch transaction by reference

        tx: Transaction = await transactionService.get_transaction_by_merchant_and_reference(
            session=session,
            reference=body.reference,
            merchant= merchant
        )

        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Validate customer email
        if not tx.customer or tx.customer.email.lower() != body.customer_email.lower():
            raise HTTPException(status_code=403, detail="Customer email does not match transaction")

        # Return serialized transaction
        return transactionSchema.TransactionResponse.model_validate(tx)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")


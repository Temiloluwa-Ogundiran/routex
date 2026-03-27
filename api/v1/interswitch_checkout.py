from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import parse_qs

from database.session import get_async_session
from enums.transactionEnums import TransactionProcessor, TransactionStatus
from external_services import interswitchService
from services import transactionService
from settings import SERVER_URL

interswitch_checkout_router = APIRouter()


async def _read_interswitch_return_fields(request: Request) -> dict[str, str]:
    try:
        form_data = await request.form()
        return {
            key: str(value)
            for key, value in form_data.items()
        }
    except AssertionError:
        raw_body = await request.body()
        parsed_body = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        return {
            key: values[-1]
            for key, values in parsed_body.items()
            if values
        }


@interswitch_checkout_router.get(
    "/api/v1/checkout/interswitch/{processor_reference}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def interswitch_checkout_bridge(
    processor_reference: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    transaction = await transactionService.get_transaction_by_processor_reference(
        session=session,
        processor_reference=processor_reference,
    )
    if not transaction or transaction.processor != TransactionProcessor.INTERSWITCH.value:
        raise HTTPException(status_code=404, detail="Transaction not found")

    customer_email = transaction.customer.email if transaction.customer else None
    form_fields = interswitchService.build_checkout_form_fields(
        transaction=transaction,
        customer_email=customer_email,
        server_base_url=(SERVER_URL or str(request.base_url)).rstrip("/"),
    )
    return HTMLResponse(
        content=interswitchService.build_bridge_html(
            form_action=interswitchService.get_hosted_checkout_url(transaction.mode),
            form_fields=form_fields,
        )
    )


@interswitch_checkout_router.post(
    "/api/v1/checkout/interswitch/return",
    include_in_schema=False,
)
async def interswitch_checkout_return(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    form_data = await _read_interswitch_return_fields(request)
    processor_reference = (
        form_data.get("txnref")
        or form_data.get("txn_ref")
        or form_data.get("transactionReference")
    )
    if not processor_reference:
        raise HTTPException(status_code=400, detail="Transaction reference is required")

    transaction = await transactionService.get_transaction_by_processor_reference(
        session=session,
        processor_reference=str(processor_reference),
    )
    if not transaction or transaction.processor != TransactionProcessor.INTERSWITCH.value:
        raise HTTPException(status_code=404, detail="Transaction not found")

    normalized_status = transaction.status or TransactionStatus.PENDING.value

    try:
        verify_response, verify_status = await interswitchService.verify_transaction(
            session=session,
            transaction=transaction,
        )
        if verify_status == 200:
            normalized_status = interswitchService.normalize_verify_status(
                verify_response,
                normalized_status,
            )
            transaction.status = normalized_status
            transaction.details = {
                "gateway": TransactionProcessor.INTERSWITCH.value,
                "verify_response": verify_response,
            }
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
        else:
            normalized_status = TransactionStatus.PENDING.value
    except Exception:
        normalized_status = TransactionStatus.PENDING.value

    status_page_url = interswitchService.get_payment_status_url(
        reference=transaction.reference,
        status=normalized_status,
        selected_gateway=transaction.selected_gateway or TransactionProcessor.INTERSWITCH.value,
        gateway_reference=transaction.processor_reference,
        next_url=transaction.redirect_url,
    )
    if transaction.redirect_url:
        merchant_redirect_url = interswitchService.get_post_payment_redirect_url(
            redirect_url=transaction.redirect_url,
            reference=transaction.reference,
            status=normalized_status,
            selected_gateway=transaction.selected_gateway or TransactionProcessor.INTERSWITCH.value,
            gateway_reference=transaction.processor_reference,
        )
        return RedirectResponse(url=merchant_redirect_url, status_code=307)

    return RedirectResponse(url=status_page_url, status_code=307)

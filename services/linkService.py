# services/paymentLinkService.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound
from database.models.PaymentLink import PaymentLink
from database.models.Transaction import Transaction
from database.models.Merchant import Merchant
from datetime import datetime, timezone
import uuid
from typing import Optional, List
import urllib.parse
from settings import SERVER_URL
from schemas.linkSchema import PaymentLinkCreateRequest
from enums import LinkEnums
from datetime import datetime, timezone
from enums.transactionEnums import TransactionStatus
from enums.transactionEnums import TransactionProcessor
from schemas.linkSchema import PaymentLinkResponse

# DOMAIN_URL = "https://yourpay.com/pay"  # Change to your front-end or payment processor base URL


# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
async def generate_link_id(session: AsyncSession) -> str:
    """Generate a unique PaymentLink ID."""
    while True:
        link_id = str(uuid.uuid4())[:7]
        stmt = select(PaymentLink).where(PaymentLink.id == link_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            return link_id
    
async def generate_link_reference(session: AsyncSession)-> str:
    """Generate a unique payment reference"""
    while True:
        link_reference = str(uuid.uuid4())[:7]
        stmt = select(PaymentLink).where(PaymentLink.reference == link_reference)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            return link_reference

async def get_current_uses(session: AsyncSession, link_id: str) -> int:
    stmt = (
        select(func.count(Transaction.id))
        .where(Transaction.payment_link_id == link_id)
        .where(Transaction.status == TransactionStatus.SUCCESS)
    )
    result = await session.execute(stmt)
    return result.scalar_one()

async def link_exists(session: AsyncSession, reference: str) -> bool:
    stmt = select(PaymentLink).where(PaymentLink.reference == reference)
    result = await session.execute(stmt)
    return bool(result.scalar_one_or_none())


def to_naive_utc(dt: datetime | None) -> datetime | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt  # already naive
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def normalize_gateway_code(gateway_code: str | None) -> str | None:
    if not gateway_code:
        return None

    normalized = gateway_code.strip().lower()
    if not normalized:
        return None
    if normalized not in {
        TransactionProcessor.KORA.value,
        TransactionProcessor.PAYSTACK.value,
        TransactionProcessor.FLUTTERWAVE.value,
        TransactionProcessor.INTERSWITCH.value,
    }:
        raise ValueError("Invalid gateway code")
    return normalized


# -----------------------------
# CREATE / READ / UPDATE / DELETE
# -----------------------------
async def create_payment_link(
    session: AsyncSession,
    merchant: Merchant,
    data: PaymentLinkCreateRequest
) -> PaymentLink:
    """
    Create a new payment link for a merchant using the request schema directly.
    """

    # Validate static/dynamic amount
    if data.amount_type == "static" and (data.amount is None or data.amount <= 0):
        raise ValueError("Static amount links require a positive amount")
    if data.amount_type == "dynamic":
        data.amount = None  # dynamic links don't enforce a fixed amount
    if data.mode == LinkEnums.LinkMode.LIVE and not merchant.is_verified:
        raise ValueError("Unverified merchant cannot generate live payment links")

    gateway_code = normalize_gateway_code(data.gateway_code)
    
    link = PaymentLink(
        id=await generate_link_id(session),
        reference=await generate_link_reference(session),
        merchant=merchant,
        title=data.title,
        amount_type=data.amount_type,
        mode=data.mode,
        type=data.type,
        currency=data.currency,
        gateway_code=gateway_code,
        amount=data.amount,
        max_uses=data.max_uses,
        description=data.description,
        redirect_url=data.redirect_url if data.redirect_url else None,
        expires_at= to_naive_utc(data.expires_at) if data.expires_at else None,
        _metadata=data.metadata,
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link

async def get_payment_link_by_id(session: AsyncSession, link_id: str) -> Optional[PaymentLink]:
    stmt = select(PaymentLink).where(PaymentLink.id == link_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_payment_link_by_id_txn(session: AsyncSession, link_id: str) -> Optional[PaymentLink]:
    """Loads link transactions and returns link if found else none"""
    stmt = select(PaymentLink).where(PaymentLink.id == link_id).options(selectinload(PaymentLink.transactions).selectinload(Transaction.customer))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_payment_link_by_reference(session: AsyncSession, reference: str) -> Optional[PaymentLink]:
    stmt = select(PaymentLink).where(PaymentLink.reference == reference)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_payment_link_by_reference_txn(session: AsyncSession, reference: str) -> Optional[PaymentLink]:
    stmt = select(PaymentLink).where(PaymentLink.reference == reference).options(selectinload(PaymentLink.transactions).selectinload(Transaction.customer))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_links_by_merchant(session: AsyncSession, merchant: Merchant) -> List[PaymentLink]:
    stmt = select(PaymentLink).where(PaymentLink.merchant_id == merchant.id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_payment_link(
    session: AsyncSession,
    link: PaymentLink,
    title: Optional[str] = None,
    amount: Optional[float] = None,
    max_uses: Optional[int] = None,
    gateway_code: Optional[str] = None,
    description: Optional[str] = None,
    redirect_url: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    metadata: Optional[str] = None,
    is_active: Optional[bool] = None
) -> PaymentLink:
    """Update editable fields on a payment link."""
    if title:
        link.title = title
    if amount is not None:
        if link.amount_type == LinkEnums.AmountType.STATIC and amount <= 0:
            raise ValueError("Static amount must be positive")
        link.amount = amount
    if max_uses is not None:
        if max_uses < link.current_uses:
            raise ValueError(f"Max uses cannot be less than the current number of uses: {link.current_uses}")
        link.max_uses = max_uses
    if gateway_code is not None:
        link.gateway_code = normalize_gateway_code(gateway_code)
    if description:
        link.description = description
    if redirect_url:
        link.redirect_url = redirect_url
    if expires_at:
        link.expires_at = to_naive_utc(expires_at) 
    if metadata:
        link._metadata = metadata
    if is_active is not None:
        link.is_active = is_active

    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def soft_delete_payment_link(session: AsyncSession, link: PaymentLink) -> PaymentLink:
    """Soft delete a link."""
    link.is_active = False
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


# -----------------------------
# LINK VALIDATION & USAGE
# -----------------------------
async def validate_link(session: AsyncSession, reference: str, amount: Optional[float] = None) -> PaymentLink:
    """Check if a link exists and is valid, optionally validate dynamic amount."""
    link = await get_payment_link_by_reference_txn(session, reference)
    if not link:
        raise ValueError("Payment link not found")
    if not link.is_valid():
        raise ValueError("Payment link is not active or has expired/used up")
    
    # Validate static/dynamic amount
    # if link.amount_type == "static" and amount is not None and amount != float(link.amount):
    #     raise ValueError("Amount must match static link amount")
    if link.amount_type == LinkEnums.AmountType.DYNAMIC and (amount is None or amount <= 0):
        raise ValueError("Dynamic link requires a positive amount")
    return link


async def increment_link_usage(session: AsyncSession, link: PaymentLink) -> None:
    """Increment usage count when a transaction succeeds."""
    link.current_uses += 1
    # deactivate if one-time or max uses reached
    if link.type == "one_time" or (link.type == "subgroup" and link.max_uses and link.current_uses >= link.max_uses):
        link.is_active = False
    session.add(link)
    await session.commit()


# -----------------------------
# TRANSACTIONS FOR LINKS
# -----------------------------
async def record_transaction_for_link(
    session: AsyncSession,
    link: PaymentLink,
    transaction: Transaction
) -> Transaction:
    """Attach a transaction to a payment link and increment usage if successful."""
    transaction.payment_link = link
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)

    if transaction.status.name.lower() == "success":
        await increment_link_usage(session, link)
        #TODO: add to webhook
    return transaction


async def get_transactions_for_link(session: AsyncSession, link: PaymentLink) -> List[Transaction]:
    """Fetch all transactions associated with a link."""
    stmt = select(Transaction).where(Transaction.payment_link_id == link.id)
    result = await session.execute(stmt)
    return result.scalars().all()


# -----------------------------
# RECURRING LINKS
# -----------------------------
async def is_recurring(link: PaymentLink) -> bool:
    """Check if a link is recurring."""
    return link.type == LinkEnums.LinkType.RECURRING


async def validate_recurring_link(session: AsyncSession, reference: str, amount: Optional[float] = None) -> PaymentLink:
    """Validate a recurring link and dynamic/static amount rules."""
    link = await validate_link(session, reference, amount)
    if not await is_recurring(link):
        raise ValueError("Link is not a recurring type")
    return link


# -----------------------------
# PAYMENT LINK URL HELPERS
# -----------------------------
def generate_payment_link_url(link: PaymentLink, base_url: str = SERVER_URL) -> str:
    """Generate a full URL for a payment link."""
    params = {"ref": link.reference}
    if link.expires_at:
        params["expires"] = link.expires_at.isoformat()
    if link._metadata:
        params["meta"] = link._metadata
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"


def generate_unique_reference() -> str:
    """Generate a short unique reference string for a link."""
    return str(uuid.uuid4())[:12]


def generate_payment_link_with_reference(
    title: str,
    amount_type: str,
    mode: str,
    amount: Optional[float] = None,
    max_uses: Optional[int] = None,
    description: Optional[str] = None,
    redirect_url: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    metadata: Optional[str] = None
) -> dict:
    """Create a dict containing a link reference and prebuilt URL for client use."""
    reference = generate_unique_reference()
    link_data = {
        "reference": reference,
        "title": title,
        "amount_type": amount_type,
        "mode": mode,
        "amount": amount,
        "max_uses": max_uses,
        "description": description,
        "redirect_url": redirect_url,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "metadata": metadata,
        "url": f"{SERVER_URL}/?ref={reference}" + (f"&meta={urllib.parse.quote(metadata)}" if metadata else "")
    }
    return link_data


async def get_payment_link_response(session: AsyncSession, link_id: str) -> PaymentLinkResponse:
    link: PaymentLink = await session.get(PaymentLink, link_id)

    current_uses = await session.scalar(
        select(func.count(Transaction.id))
        .where(Transaction.payment_link_id == link.id)
        .where(Transaction.status == TransactionStatus.SUCCESS)
    )

    return PaymentLinkResponse(
        id=link.id,
        reference=link.reference,
        title=link.title,
        merchant_id=link.merchant_id,
        url=link.url,
        description=link.description,
        amount_type=link.amount_type,
        mode=link.mode,
        type=link.type,
        currency=link.currency,
        gateway_code=link.gateway_code,
        amount=float(link.amount) if link.amount is not None else None,
        max_uses=link.max_uses,
        current_uses=current_uses,
        redirect_url=link.redirect_url,
        expires_at=link.expires_at,
        _metadata=link._metadata,
        is_active=link.is_active,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )

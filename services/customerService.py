from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Result
from sqlalchemy.exc import NoResultFound
from database.models.Customer import Customer
from database.models.Merchant import Merchant
from typing import Optional, Tuple
from sqlalchemy.orm import selectinload
# Assuming you have a session getter
from database.session import get_async_session


async def get_by_id_or_email(session: AsyncSession, id: Optional[int] = None, email: Optional[str] = None) -> Customer | None:
    """Return Customer object if found else raise\n\n
    Raises ValueError if neither id nor email provided"""
    if not id and not email:
        raise ValueError("Either id or email must be provided")

    
    stmt = None
    if email:
        stmt = select(Customer).where(Customer.email == email)
    elif id:
        stmt = select(Customer).where(Customer.id == id)
    result: Result = await session.execute(stmt)
    customer = result.scalar_one_or_none()
    return customer


from sqlalchemy.orm import selectinload

async def add_get_or_create_customer(session: AsyncSession, email: str, merchant: Merchant) -> Tuple[Customer, bool]:
    """Adds a customer to a merchant.

    Email required. User does not have to exist.
    """

    # First try to find customer linked to this merchant
    stmt = select(Customer).where(
        Customer.email == email,
        Customer.merchants.any(Merchant.id == merchant.id)
    )
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()
    if customer:
        return customer, False  # Already associated with this merchant
     
    customer = Customer(email=email)
    session.add(customer)
    created = True

    # Associate with merchant
    customer.merchants.append(merchant)
    await session.commit()
    await session.refresh(customer)
    return customer, created

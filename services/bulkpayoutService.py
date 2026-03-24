from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from sqlalchemy.orm import selectinload
from database.models.BulkPayout import BulkPayout
from database.models.Transaction import Transaction
from enums.BulkPayoutEnums import BulkPayoutStatus, BulkPayoutTransactionKeys, BulkPayoutStatusMessage
from enums.transactionEnums import TransactionStatus, TransactionType, TransactionCurrency
from database.models.Merchant import Merchant
import uuid
from typing import Optional, List
from database.models.BulkPayout import BulkPayout, PayoutCategory, PayoutBeneficiary
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from schemas.transactionSchema import BulkPayoutItem, BulkPayoutCustomerDetails
from lib import bank

async def generate_bulk_payout_reference(session:AsyncSession):
    """ Generates unique bulk payout reference """
    while True:
        reference = uuid.uuid4().hex[:7]
        bpt = await session.execute(select(BulkPayout).where(BulkPayout.reference == reference))
        if not bpt.scalar_one_or_none():
            return reference
        
# async def create_bulk_payout(
#     session: AsyncSession,
#     merchant: Merchant,
#     name: Optional[str] = None,
#     remarks: Optional[str] = None,
#     category_id: Optional[int] = None
# ) -> BulkPayout:
#     """ Creates a bulk payout object """
#     reference = uuid.uuid4().hex[:10]
#     payout = BulkPayout(
#         reference=reference,
#         name=name,
#         remarks=remarks,
#         merchant_id=merchant.id,
#         status=BulkPayoutStatus.PENDING,
#         category_id=category_id
#     )
#     session.add(payout)
#     await session.commit()
#     await session.refresh(payout)
#     return payout

async def create_bulk_payout(
    session: AsyncSession,
    merchant: Merchant,
    name: Optional[str] = None,
    remarks: Optional[str] = None,
    category_ids: Optional[List[int]] = None,
) -> BulkPayout:
    """ Creates a bulk payout object and links it to categories """
    reference = uuid.uuid4().hex[:10]
    payout = BulkPayout(
        reference=reference,
        name=name,
        remarks=remarks,
        merchant_id=merchant.id,
        status=BulkPayoutStatus.PENDING,
    )
    session.add(payout)

    if category_ids:
        stmt = select(PayoutCategory).where(
            PayoutCategory.id.in_(category_ids),
            PayoutCategory.merchant_id == merchant.id
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()
        payout.categories.extend(categories)

    await session.commit()
    await session.refresh(payout)
    return payout

async def save_bulk_payout_obj(session: AsyncSession, bulk_payout: BulkPayout):
    """Saves the bulk payout in the db"""
    await session.commit()
    await session.refresh(bulk_payout)
    return bulk_payout

async def get_bulk_payout_by_id(session: AsyncSession, payout_id: int) -> Optional[BulkPayout]:
    stmt = (
        select(BulkPayout)
        .options(selectinload(BulkPayout.transactions), selectinload(BulkPayout.merchant))
        .where(BulkPayout.id == payout_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_bulk_payout_by_reference(session: AsyncSession, reference: str) -> Optional[BulkPayout]:
    stmt = (
        select(BulkPayout)
        .options(
            selectinload(BulkPayout.transactions).selectinload(Transaction.customer),
            selectinload(BulkPayout.merchant))
        .where(BulkPayout.reference == reference)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_paginated_bulk_payout(
    merchant_id: str,
    mode: str,
    page: int,
    page_size: int,
    session: AsyncSession
):
    offset = (page - 1) * page_size

    # Subquery to check if at least one transaction has the required mode
    subquery = (
        select(Transaction.id)
        .where(
            Transaction.bulk_payout_id == BulkPayout.id,
            Transaction.mode == mode
        )
        .limit(1)
    )

    stmt = (
        select(BulkPayout)
        .where(
            BulkPayout.merchant_id == merchant_id,
            exists(subquery)  
        )
        .order_by(BulkPayout.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(
            selectinload(BulkPayout.transactions)
        )
    )

    result = await session.execute(stmt)
    return result.scalars().all()

async def bp_count_by_status(session: AsyncSession, merchant_id: str, status: BulkPayoutStatus):
    stmt = (
        select(func.count(BulkPayout.id))
        .where(
            BulkPayout.merchant_id == merchant_id,
            BulkPayout.status == status
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one()

# async def add_transactions_to_payout(
#     session: AsyncSession,
#     payout: BulkPayout,
#     transaction_ids: List[int],
#     transaction_details: list[dict: {"txn_id": str, "status": bool, "message": str, "http_status": int}]= None
# ):
#     stmt = select(Transaction).where(Transaction.id.in_(transaction_ids))
#     result = await session.execute(stmt)
#     transactions = result.scalars().all()

#     for txn in transactions:
#         if txn:
#             txn.bulk_payout_id = payout.id
#     if transaction_details:
#         payout.transaction_details =  transaction_details

#     await session.commit()
#     await session.refresh(payout)
#     await transaction_based_update(session, payout)


async def add_transaction_to_payout(
    session: AsyncSession,
    payout: BulkPayout,
    transaction_id: int,
    # transaction_details: dict
):
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await session.execute(stmt)
    txn = result.scalar_one_or_none()
    if txn:
        txn.bulk_payout_id = payout.id
    await session.commit()

async def calculate_success_rate(session: AsyncSession, payout_id: int) -> float:
    total_stmt = select(func.count()).select_from(Transaction).where(
        Transaction.bulk_payout_id == payout_id,
        Transaction.type == TransactionType.DEBIT
    )
    success_stmt = select(func.count()).select_from(Transaction).where(
        Transaction.bulk_payout_id == payout_id,
        Transaction.type == TransactionType.DEBIT,
        Transaction.status == TransactionStatus.SUCCESS
    )

    total_result = await session.execute(total_stmt)
    success_result = await session.execute(success_stmt)

    total = total_result.scalar() or 0
    success = success_result.scalar() or 0

    return round((success / total) * 100, 2) if total > 0 else 0.0


async def update_bulk_payout_status(
    session: AsyncSession,
    payout: BulkPayout,
    status: BulkPayoutStatus
):
    payout.status = status
    await session.commit()
    await session.refresh(payout)
    return payout


async def transaction_based_update(
    session: AsyncSession,
    bulk_payout: BulkPayout,
):
    """
    Updates the overall bulk payout status accordingly.
    """
    transaction_details = bulk_payout.transaction_details or []
    
    statuses = [item.get(BulkPayoutTransactionKeys.TXN_STATUS) for item in transaction_details]

    if all(s == TransactionStatus.SUCCESS.value for s in statuses):
        bulk_payout.status = BulkPayoutStatus.SUCCESSFUL.value
    elif all(s == TransactionStatus.FAILED.value for s in statuses):
        bulk_payout.status = BulkPayoutStatus.FAILED.value
    else:
        bulk_payout.status = BulkPayoutStatus.PARTIAL.value

    bulk_payout = await save_bulk_payout_obj(session= session, bulk_payout= bulk_payout)
    return bulk_payout

async def get_total_bp(session: AsyncSession, merchant_id, mode: str):
    subquery = (
        select(Transaction.id)
        .where(
            Transaction.bulk_payout_id == BulkPayout.id,
            Transaction.mode == mode
        )
        .limit(1)
    )

    count_stmt = select(func.count()).select_from(BulkPayout).where(BulkPayout.merchant_id == merchant_id, exists(subquery))
    total_result = await session.execute(count_stmt)
    total_items = total_result.scalar() or 0
    return total_items



### ======================
### CATEGORY FUNCTIONS
### ======================

async def create_payout_category(
    session: AsyncSession,
    merchant_id: str,
    name: str,
    description: Optional[str] = None
) -> PayoutCategory:
    """Create a new payout category for a merchant"""
    category = PayoutCategory(
        name=name,
        merchant_id=merchant_id,
        description=description
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category

async def get_payout_categories(
    session: AsyncSession,
    merchant_id: str
) -> List[PayoutCategory]:
    stmt = (
        select(PayoutCategory)
        .where(PayoutCategory.merchant_id == merchant_id)
        .options(selectinload(PayoutCategory.beneficiaries))
    )
    result = await session.execute(stmt)
    return result.scalars().all()

# async def get_category_by_id(
#     session: AsyncSession,
#     merchant_id: str,
#     category_id: int
# ) -> PayoutCategory | None:
#     stmt = (
#         select(PayoutCategory)
#         .where(PayoutCategory.merchant_id == merchant_id)
#         .where(PayoutCategory.id == category_id)
#         .options(selectinload(PayoutCategory.beneficiaries))
#     )
#     result = await session.execute(stmt)
#     return result.scalars().one_or_none()

async def add_categories_to_bulk_payout(
    session: AsyncSession,
    payout: BulkPayout,
    category_ids: List[int],
):
    """Attach multiple categories to a bulk payout"""
    stmt = select(PayoutCategory).where(
        PayoutCategory.id.in_(category_ids),
        PayoutCategory.merchant_id == payout.merchant_id
    )
    result = await session.execute(stmt)
    categories = result.scalars().all()
    for category in categories:
        if category not in payout.categories:
            payout.categories.append(category)

    await session.commit()
    await session.refresh(payout)
    return payout

async def remove_category_from_bulk_payout(
    session: AsyncSession,
    payout: BulkPayout,
    category_id: int,
):
    """Detach a category from a bulk payout"""
    payout.categories = [c for c in payout.categories if c.id != category_id]
    await session.commit()
    await session.refresh(payout)
    return payout

### ======================
### BENEFICIARY FUNCTIONS
### ======================

async def create_payout_beneficiary(
    session: AsyncSession,
    name: str,
    bank_code: str,
    account_number: str,
    email: str,
    merchant_id: str,
    category_id: Optional[int] = None,
    phone_number: Optional[str] = None,
    whatsapp_number: Optional[str] = None,
    default_amount: Optional[float] = None,
    narration: Optional[str] = None,
) -> PayoutBeneficiary:
    """Create a beneficiary (optionally linked to a category)"""
    beneficiary = PayoutBeneficiary(
        name=name,
        bank_code=bank_code,
        account_number=account_number,
        email=email,
        phone_number=phone_number,
        whatsapp_number=whatsapp_number,
        default_amount=default_amount,
        narration=narration,
        category_id=category_id,
        merchant_id = merchant_id
    )
    session.add(beneficiary)
    await session.commit()
    await session.refresh(beneficiary)
    return beneficiary


async def get_beneficiaries_by_category(
    session: AsyncSession,
    category_id: int
) -> List[PayoutBeneficiary]:
    stmt = (
        select(PayoutBeneficiary)
        .where(PayoutBeneficiary.category_id == category_id, PayoutBeneficiary.is_active == True)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all_beneficiaries_for_merchant(
    session: AsyncSession,
    merchant_id: str
) -> List[PayoutBeneficiary]:
    """Fetch beneficiaries across all categories for a merchant"""
    stmt = (
        select(PayoutBeneficiary)
        .join(PayoutCategory, PayoutCategory.id == PayoutBeneficiary.category_id)
        .where(PayoutCategory.merchant_id == merchant_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


### ======================
### BULK PAYOUT EXTENSIONS
### ======================

# async def create_bulk_payout_by_category(
#     session: AsyncSession,
#     merchant_id: str,
#     category_id: int,
#     remarks: Optional[str] = None
# ) -> BulkPayout:
#     """
#     Create a bulk payout linked to a category.
#     Automatically prepares payout records for all category beneficiaries.
#     """
#     # Get the category and beneficiaries
#     category = await session.get(PayoutCategory, category_id)
#     if not category or category.merchant_id != merchant_id:
#         raise ValueError("Invalid category for this merchant")

#     reference = uuid.uuid4().hex[:10]
#     payout = BulkPayout(
#         reference=reference,
#         name=f"Payout to {category.name}",
#         remarks=remarks,
#         merchant_id=merchant_id,
#         category_id=category_id,
#         status=BulkPayoutStatus.PENDING,
#         transaction_details=[]
#     )
#     session.add(payout)
#     await session.flush()  # so payout has an ID

#     # Attach beneficiaries to transaction_details draft
#     transaction_details = []
#     for b in category.beneficiaries:
#         transaction_details.append({
#             "beneficiary_id": b.id,
#             "account_number": b.account_number,
#             "bank_code": b.bank_code,
#             "amount": float(b.default_amount or 0),
#             "narration": b.narration,
#             "txn_status": None,
#             "created_at": datetime.now(timezone.utc).isoformat()
#         })

#     payout.transaction_details = transaction_details
#     await session.commit()
#     await session.refresh(payout)
#     return payout


async def get_bulk_payouts_by_category(
    session: AsyncSession,
    category_id: int
) -> List[BulkPayout]:
    """Fetch all bulk payouts linked to a category (M:M join)"""
    stmt = (
        select(BulkPayout)
        .join(BulkPayout.categories)
        .where(PayoutCategory.id == category_id)
        .options(selectinload(BulkPayout.transactions))
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_beneficiary_count_by_category(category_id: int, db: AsyncSession) -> int:
    """
    Return the total number of beneficiaries in a given category.
    """
    result = await db.execute(
        select(func.count(PayoutBeneficiary.id)).where(
            PayoutBeneficiary.category_id == category_id
        )
    )
    return result.scalar() or 0


# -------------------------
# Sum default amounts
# -------------------------
async def get_total_default_amount_by_category(category_id: int, db: AsyncSession) -> float:
    """
    Return the total of default_amount for all beneficiaries in a given category.
    """
    result = await db.execute(
        select(func.coalesce(func.sum(PayoutBeneficiary.default_amount), 0)).where(
            PayoutBeneficiary.category_id == category_id
        )
    )
    return float(result.scalar() or 0.0)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update
from database.models.BulkPayout import PayoutCategory, PayoutBeneficiary
from schemas.transactionSchema import (
    PayoutCategoryCreate, PayoutCategoryUpdate,
    PayoutBeneficiaryCreate, PayoutBeneficiaryUpdate
)
from typing import Optional, List


# -------------------------
# CATEGORY SERVICES
# -------------------------

async def create_category(session: AsyncSession, data: PayoutCategoryCreate) -> PayoutCategory:
    category = PayoutCategory(
        name=data.name,
        merchant_id=data.merchant_id,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def get_category_by_id(session: AsyncSession, category_id: int) -> Optional[PayoutCategory]:
    stmt = select(PayoutCategory).where(PayoutCategory.id == category_id).where(PayoutCategory.is_active == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_category_by_name(session: AsyncSession, category_name: str) -> Optional[PayoutCategory]:
    stmt = select(PayoutCategory).where(PayoutCategory.name == category_name).where(PayoutCategory.is_active == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_category(session: AsyncSession, category_id: int, data: PayoutCategoryUpdate) -> Optional[PayoutCategory]:
    stmt = select(PayoutCategory).where(PayoutCategory.id == category_id)
    result = await session.execute(stmt)
    category = result.scalar_one_or_none()
    if not category:
        return None

    for field, value in data.model_dump().items():
        setattr(category, field, value)

    await session.commit()
    await session.refresh(category)
    return category


async def soft_delete_category(session: AsyncSession, category_id: int) -> bool:
    category = await get_category_by_id(session=session,  category_id= category_id)
    if not category: 
        return False
    
    category.is_active = False

    await session.commit()
    await session.refresh(category)
    return True


async def get_beneficiary_count_by_category(category_id: int, session: AsyncSession) -> int:
    stmt = select(func.count(PayoutBeneficiary.id)).where(PayoutBeneficiary.category_id == category_id, PayoutBeneficiary.is_active == True)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_total_default_amount_by_category(category_id: int, session: AsyncSession) -> float:
    stmt = (
        select(func.coalesce(func.sum(PayoutBeneficiary.default_amount), 0))
        .where(
            PayoutBeneficiary.category_id == category_id,
            PayoutBeneficiary.is_active == True
        )
    )
    result = await session.execute(stmt)
    return float(result.scalar() or 0)

async def get_category_payout_data(
    session: AsyncSession, 
    cats: list[PayoutCategory]
) -> List[BulkPayoutItem]:
    payout_list: List[BulkPayoutItem] = []

    for cat in cats:
        bnfs = await get_beneficiaries_by_category(
            session=session,
            category_id=cat.id
        )
        
        payout_data = await get_beneficiary_payout_data(bnfs=bnfs)
        payout_list.extend(payout_data)   # ✅ fixed concatenation
    
    return payout_list

# -------------------------
# BENEFICIARY SERVICES
# -------------------------

async def create_beneficiary(session: AsyncSession, data: PayoutBeneficiaryCreate) -> PayoutBeneficiary:
    beneficiary = PayoutBeneficiary(
        name=data.name,
        bank_code=data.bank_code,
        account_number=data.account_number,
        email=data.email,
        phone_number=data.phone_number,
        whatsapp_number=data.whatsapp_number,
        default_amount=data.default_amount,
        narration=data.narration,
        merchant_id = data.merchant_id,
        category_id=data.category_id if data.category_id else None
    )
    session.add(beneficiary)
    await session.commit()
    await session.refresh(beneficiary)
    return beneficiary


async def get_beneficiary_by_id(session: AsyncSession, beneficiary_id: int) -> Optional[PayoutBeneficiary]:
    stmt = select(PayoutBeneficiary).where(PayoutBeneficiary.id == beneficiary_id).where(PayoutBeneficiary.is_active == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_beneficiary(session: AsyncSession, beneficiary_id: int, data: PayoutBeneficiaryUpdate) -> Optional[PayoutBeneficiary]:
    stmt = select(PayoutBeneficiary).where(PayoutBeneficiary.id == beneficiary_id)
    result = await session.execute(stmt)
    beneficiary = result.scalar_one_or_none()
    if not beneficiary:
        return None

    for field, value in data.model_dump(exclude_unset= True).items():
        setattr(beneficiary, field, value)

    await session.commit()
    await session.refresh(beneficiary)
    return beneficiary


async def soft_delete_beneficiary(session: AsyncSession, beneficiary_id: int) -> bool:
    beneficiary = await get_beneficiary_by_id(session = session, beneficiary_id= beneficiary_id)

    if not beneficiary:
        return False
    
    beneficiary.is_active = False
    await session.commit()
    await session.refresh(beneficiary)
    return beneficiary

async def get_all_beneficiaries(
    session: AsyncSession,
    merchant_id: int,
    page: int = 1,
    size: int = 10,
    category_id: int | None = None,
):
    """
    Get paginated list of beneficiaries for a merchant.
    Optionally filter by category_id.
    """
    offset = (page - 1) * size

    stmt = select(PayoutBeneficiary).where(PayoutBeneficiary.merchant_id == merchant_id, PayoutBeneficiary.is_active == True)

    if category_id:
        stmt = stmt.where(PayoutBeneficiary.category_id == category_id, PayoutBeneficiary.is_active == True)

    # Paginated query
    paginated_stmt = stmt.offset(offset).limit(size)
    result = await session.execute(paginated_stmt)
    beneficiaries = result.scalars().all()

    # Total count for pagination metadata
    total_stmt = select(func.count(PayoutBeneficiary.id)).where(PayoutBeneficiary.merchant_id == merchant_id, PayoutBeneficiary.is_active == True)
    if category_id:
        total_stmt = total_stmt.where(PayoutBeneficiary.category_id == category_id)

    total_result = await session.execute(total_stmt)
    total = total_result.scalar() or 0

    return {
        "beneficiaries": beneficiaries,
        "current_page": page,
        "page_size": size,
        "total_items": total,
        "total_pages": (total + size - 1) // size,
    }

async def get_beneficiary_payout_data(bnfs: List[PayoutBeneficiary]) -> List[BulkPayoutItem]:
    payout_data = []
    for bnf in bnfs:
        bank_obj = bank.find_bank_by_code(code= bnf.bank_code)
        if bank_obj is None:
            raise ValueError("Bank slug does not exist")

        customer_obj = BulkPayoutCustomerDetails(
            account_number= bnf.account_number,
            bank_slug= bank_obj.slug,
            email= bnf.email,
            whatsapp_number= bnf.whatsapp_number,
            phone_number= bnf.phone_number
        )
        payout_data.append(BulkPayoutItem(
            merchant_id= bnf.merchant_id,
            amount= bnf.default_amount,
            currency= TransactionCurrency.NIGERIA,
            customer= customer_obj,
            narration= bnf.narration
        ))
    return payout_data


# ---------------------- Categories ----------------------

async def get_all_categories(
    session: AsyncSession,
    merchant_id: int,
):
    """
    Get all payout categories for a merchant
    """
    stmt = select(PayoutCategory).where(PayoutCategory.merchant_id == merchant_id, PayoutCategory.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().all()
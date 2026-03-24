from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON, Numeric, Boolean, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enums.BulkPayoutEnums import BulkPayoutStatus, BulkPayoutMode
from database.models.base import Base

bulk_payout_category = Table(
    "bulk_payout_category",
    Base.metadata,
    Column("bulk_payout_id", Integer, ForeignKey("bulk_payout.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("payout_categories.id", ondelete="CASCADE"), primary_key=True),
)

class BulkPayout(Base):
    __tablename__ = "bulk_payout"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable= True)
    reference = Column(String(100), unique=True, nullable=False)
    merchant_id = Column(String(50), ForeignKey("merchant.id"), nullable=True)
    status = Column(String(20), default=BulkPayoutStatus.PENDING)
    transaction_details = Column(JSONB, nullable= True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    merchant = relationship("Merchant")
    transactions = relationship("Transaction", primaryjoin="and_(BulkPayout.id==Transaction.bulk_payout_id, Transaction.type=='debit')", backref="bulk_payout")
    categories = relationship(
        "PayoutCategory",
        secondary=bulk_payout_category,
        back_populates="bulk_payouts"
    )
class PayoutCategory(Base):
    __tablename__ = "payout_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable= True)
    merchant_id = Column(String(50), ForeignKey("merchant.id", ondelete="CASCADE"))
    is_active = Column(Boolean, default= True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    beneficiaries = relationship("PayoutBeneficiary", back_populates="category")
    bulk_payouts = relationship(
        "BulkPayout",
        secondary=bulk_payout_category,
        back_populates="categories"
    )

    merchant = relationship("Merchant", back_populates="categories")



class PayoutBeneficiary(Base):
    __tablename__ = "payout_beneficiaries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    bank_code = Column(String(10), nullable=False)
    account_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    whatsapp_number = Column(String(20), nullable=True)
    default_amount = Column(Numeric(18, 2), nullable=True) 
    narration = Column(String(255), nullable= True)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    category_id = Column(Integer, ForeignKey("payout_categories.id", ondelete="CASCADE"), nullable= True)
    merchant_id = Column(String(50), ForeignKey("merchant.id", ondelete="CASCADE"))
    merchant = relationship("Merchant", back_populates="beneficiaries")
    category = relationship("PayoutCategory", back_populates="beneficiaries")

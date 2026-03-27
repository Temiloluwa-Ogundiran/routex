from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enums.BulkPayoutEnums import BulkPayoutStatus, BulkPayoutMode
from database.models.base import Base
from enums.LinkEnums import *
from enums.transactionEnums import TransactionCurrency
from enums.transactionEnums import TransactionProcessor
from settings import SERVER_URL, FRONTEND_BASE_URL
from enums.transactionEnums import TransactionStatus
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func

class PaymentLink(Base):
    __tablename__ = "payment_links"

    id = Column(String(50), primary_key=True)

    reference = Column(String(50), unique=True, index=True, nullable=False)  
    title = Column(String(255), nullable=False)  
    description = Column(Text, nullable=True)
    currency = Column(String(10), nullable = False)
    gateway_code = Column(String(10), nullable=True)
    amount_type = Column(String(20), nullable=False)  
    amount = Column(Numeric(12, 2), nullable=True)  # only for static links

    type = Column(String(20), nullable=False)  
    mode = Column(String(20), nullable= False) #test or live
    max_uses = Column(Integer, nullable=True)      # only for subgroup mode
    # current_uses = Column(Integer, default=0, nullable=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone= True), nullable=True)

    redirect_url = Column(String(500), nullable=True)  # optional post-payment redirect
    _metadata = Column(Text, nullable=True)  # JSON string for extra info (branding, notes, etc.)

    # Merchant/owner of the link
    merchant_id = Column(String(50), ForeignKey("merchant.id"))
    merchant = relationship("Merchant", back_populates="payment_links")

    transactions = relationship("Transaction", back_populates="payment_link", cascade="all, delete-orphan")

    # --- METHODS ---
    def is_valid(self):
        """Check if link is usable based on mode, usage, expiry, and active flag."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        if self.type == LinkType.ONE_TIME and self.current_uses >= 1:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True
    
    @property
    def url(self):
        return f"https://checkout.xoropay.com/pay/{self.reference}"
    
    @hybrid_property
    def current_uses(self):
        """Count successful transactions in Python when object is loaded."""
        return sum(1 for t in self.transactions if t.status == TransactionStatus.SUCCESS)

    @current_uses.expression
    def current_uses(cls):
        """Generate SQL expression for current_uses."""
        from database.models.Transaction import Transaction  # import inside to avoid circular
        return (
            select(func.count(Transaction.id))
            .where(Transaction.payment_link_id == cls.id)
            .where(Transaction.status == TransactionStatus.SUCCESS)
            .correlate_except(Transaction)
            .scalar_subquery()
        )

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database.models.base import Base
from datetime import datetime, timezone

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String(50), ForeignKey("merchant.id"), nullable=False)
    currency = Column(String(10), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    mode = Column(String(10), nullable=False)  # 'test' or 'live'

    # Charge configuration for pay-ins (credits)
    percentage_charge = Column(Float, default=1.5, nullable=False)
    flat_charge = Column(Float, default=0.0, nullable=False)

    # Charge configuration for payouts (debits)
    payout_percentage_charge = Column(Float, default=0.0, nullable=False)
    payout_flat_charge = Column(Float, default=50.0, nullable=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    merchant = relationship("Merchant", back_populates="wallets")
    transactions = relationship("Transaction", back_populates="wallet")

    # Ensure one wallet per merchant-currency-mode combination
    __table_args__ = (
        UniqueConstraint('merchant_id', 'currency', 'mode', name='uq_merchant_currency_mode'),
    )

    def __repr__(self):
        return f"<Wallet(id={self.id}, merchant_id={self.merchant_id}, currency={self.currency}, mode={self.mode}, balance={self.balance})>"

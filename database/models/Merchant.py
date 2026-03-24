from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from database.models.base import Base
from datetime import datetime, timezone
from .association import merchant_processor

class Merchant(Base):
    __tablename__ = "merchant"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    # ... other fields ...

    user_merchants = relationship("UserMerchant", back_populates="merchant")
    users = relationship(
        "User",
        secondary="user_merchants",
        back_populates="merchants",
        viewonly=True,
    )
    email = Column(String(100), unique=True, nullable=False)
    joined_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc))
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    percentage_charge = Column(Float, default=1.5)
    flat_charge = Column(Float, default=0.0)
    payout_percentage_charge = Column(Float, default=0, nullable = False)
    payout_flat_charge = Column(Float, default= 50, nullable = False)
    test_balance = Column(Float, default=0.0)
    live_balance = Column(Float, default=0.0)
    live_webhook_url = Column(Text, nullable= True)
    test_webhook_url = Column(Text, nullable= True)
    customers = relationship(
        "Customer",  # Model name of the related class
        secondary="customer_merchant",  # Association table
        back_populates="merchants",  # Reverse relationship in the Customer model
    )
    processors = relationship("Processor", secondary=merchant_processor, back_populates="merchants")
    payment_links = relationship("PaymentLink", back_populates="merchant")
    categories = relationship("PayoutCategory", back_populates="merchant")
    beneficiaries = relationship("PayoutBeneficiary", back_populates= "merchant")
    wallets = relationship("Wallet", back_populates="merchant")
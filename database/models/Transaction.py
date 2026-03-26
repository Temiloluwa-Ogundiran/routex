from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship, declarative_base
import uuid
from datetime import datetime,timezone
import enum
from settings import PREFIX
from enums.transactionEnums import *
from database.models.base import Base
from database.models.base import Base

class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(TransactionType, name="transactiontype"), nullable=True)
    mode = Column(String(10), nullable=True)
    processor = Column(Enum(TransactionProcessor, name="transactionprocessor"), nullable=False)
    merchant_id = Column(String(50), ForeignKey("merchant.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)
    processor_reference = Column(String(100), unique=True)
    reference = Column(String(100))
    amount = Column(Float)
    charge = Column(Float, default=0.0)
    processor_charge = Column(Float, default=0.0)
    details = Column(JSON, nullable=True)
    currency = Column(String(10), default="NGN")
    status = Column(
        Enum(TransactionStatus, name="transactionstatus", native_enum=False),
        default=TransactionStatus.PENDING,
    )
    selected_gateway = Column(String(20), nullable=True)
    redirect_url = Column(Text, nullable=True)
    notification_url = Column(Text, nullable=True)
    metadata_payload = Column(JSON, nullable=True)
    narration = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    merchant = relationship("Merchant")
    customer = relationship("Customer")
    wallet = relationship("Wallet", back_populates="transactions")
    routing_attempts = relationship("RoutingAttempt", back_populates="transaction")
    routing_decisions = relationship("RoutingDecisionAudit", back_populates="transaction")
    bulk_payout_id = Column(Integer, ForeignKey("bulk_payout.id"), nullable=True)
    payment_link_id = Column(String, ForeignKey("payment_links.id"), nullable=True)
    payment_link = relationship("PaymentLink", back_populates="transactions")



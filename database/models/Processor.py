# processor.py
from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy.orm import relationship

from database.models.association import merchant_processor
from database.models.base import Base


class Processor(Base):
    __tablename__ = "processor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True)
    name = Column(String(50), nullable=True)
    charge = Column(Float)
    markup = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    supports_collections = Column(Boolean, default=True)
    supports_payouts = Column(Boolean, default=True)
    priority_weight = Column(Float, default=1.0)

    merchants = relationship("Merchant", secondary=merchant_processor, back_populates="processors")
    routing_attempts = relationship("RoutingAttempt", back_populates="processor")
    health_snapshots = relationship("GatewayHealthSnapshot", back_populates="processor")
    routing_decisions = relationship("RoutingDecisionAudit", back_populates="processor")

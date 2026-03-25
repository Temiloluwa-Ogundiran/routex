from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from database.models.base import Base


class RoutingDecisionAudit(Base):
    __tablename__ = "routing_decision_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(
        String(50),
        default=lambda: f"route_{uuid.uuid4().hex[:12]}",
        unique=True,
        nullable=False,
    )
    transaction_id = Column(Integer, ForeignKey("transaction.id"), nullable=False)
    selected_gateway = Column(String(10), ForeignKey("processor.code"), nullable=False)
    eligible_gateways = Column(JSON, nullable=True)
    rejected_gateways = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    score_breakdown = Column(JSON, nullable=True)
    fallback_order = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    transaction = relationship("Transaction", back_populates="routing_decisions")
    processor = relationship("Processor", back_populates="routing_decisions")

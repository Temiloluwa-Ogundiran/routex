from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.models.base import Base


class RoutingAttempt(Base):
    __tablename__ = "routing_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transaction.id"), nullable=False)
    attempt_no = Column(Integer, nullable=False)
    gateway_code = Column(String(10), ForeignKey("processor.code"), nullable=False)
    operation = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    request_hash = Column(String(128), nullable=True)
    gateway_reference = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    score_snapshot = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    transaction = relationship("Transaction", back_populates="routing_attempts")
    processor = relationship("Processor", back_populates="routing_attempts")

    __table_args__ = (
        UniqueConstraint("transaction_id", "attempt_no", name="uq_routing_attempt_txn_attempt"),
    )

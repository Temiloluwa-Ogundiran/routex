from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.models.base import Base


class GatewayHealthSnapshot(Base):
    __tablename__ = "gateway_health_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gateway_code = Column(String(10), ForeignKey("processor.code"), nullable=False)
    success_rate_5m = Column(Float, default=0.0, nullable=False)
    success_rate_1h = Column(Float, default=0.0, nullable=False)
    timeout_rate_5m = Column(Float, default=0.0, nullable=False)
    p95_latency_ms = Column(Float, default=0.0, nullable=False)
    circuit_state = Column(String(20), default="closed", nullable=False)
    last_checked_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    processor = relationship("Processor", back_populates="health_snapshots")

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String

from database.models.base import Base


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    operation = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=True)
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    allow_gateways = Column(JSON, default=list, nullable=False)
    deny_gateways = Column(JSON, default=list, nullable=False)
    force_priority_order = Column(JSON, default=list, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

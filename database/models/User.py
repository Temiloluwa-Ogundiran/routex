from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database.models.base import Base
from datetime import datetime, timezone
class User(Base):
    __tablename__ = "users"

    id = Column(String(10), primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100))
    password = Column(String(100))
    created_at = Column(DateTime(timezone= True), default= lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    user_merchants = relationship("UserMerchant", back_populates="user")
    merchants = relationship(
        "Merchant",
        secondary="user_merchants",
        back_populates="users",
        viewonly=True,
    )

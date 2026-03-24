from sqlalchemy import Column, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.models.User import User
from database.models.Merchant import Merchant
from database.models.base import Base
from enums.userEnums import UserRole
from datetime import datetime, timezone
class UserMerchant(Base):
    __tablename__ = "user_merchants"

    user_id = Column(String(10), ForeignKey("users.id"), primary_key=True)
    merchant_id = Column(String(50), ForeignKey("merchant.id"), primary_key=True)
    role = Column(String(20), default=UserRole.ADMIN.value)
    user = relationship(User, back_populates="user_merchants")
    joined_at = Column(DateTime(timezone= True), default= lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone= True), default= lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    merchant = relationship(Merchant, back_populates="user_merchants")

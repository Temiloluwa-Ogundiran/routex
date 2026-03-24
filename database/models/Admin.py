from sqlalchemy import Column, String, DateTime, Boolean, Integer
from database.models.base import Base
from datetime import datetime, timezone

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement= True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100))
    password = Column(String(100))
    created_at = Column(DateTime(timezone= True), default= lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)


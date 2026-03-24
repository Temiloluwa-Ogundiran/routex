from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, Integer, Table, ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship, declarative_base
import uuid
from datetime import datetime, timezone
import enum
from enums.tokenEnums import *
from settings import PREFIX

from database.models.base import Base

class Token(Base):
    __tablename__ = "token"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String(50), ForeignKey("merchant.id"))
    secret_key = Column(Text)
    public_key = Column(Text)
    type = Column(String(10), Enum(TokenMode), default= TokenMode.TEST.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc))
    last_used = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    merchant = relationship("Merchant")
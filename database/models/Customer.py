# customer.py
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from database.models.base import Base
from database.models.association import customer_merchant

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100),  nullable=False)
    name = Column(String(100), nullable= True)
    created_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone= True), default=lambda: datetime.now(timezone.utc), onupdate= lambda: datetime.now(timezone.utc))

    merchants = relationship(
        "Merchant",  # Model name of the related class
        secondary="customer_merchant",  # Association table
        back_populates="customers",  # Reverse relationship in the Merchant model
    )
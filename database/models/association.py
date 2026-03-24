# database/models/association.py
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from database.models.base import Base

customer_merchant = Table(
    "customer_merchant", Base.metadata,
    Column("customer_id", Integer, ForeignKey("customers.id"), primary_key=True),
    Column("merchant_id", String(50), ForeignKey("merchant.id"), primary_key=True)
)

merchant_processor = Table(
    "merchant_processor", Base.metadata,
    Column("merchant_id", String(50), ForeignKey("merchant.id"), primary_key=True),
    Column("processor_id", Integer, ForeignKey("processor.id"), primary_key=True)
)

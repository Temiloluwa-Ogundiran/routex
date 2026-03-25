# from sqlalchemy import (
#     Column, String, Boolean, DateTime, Float, Integer, Table, ForeignKey, Text, Enum, JSON
# )
# from sqlalchemy.orm import relationship, declarative_base
# import uuid
# from datetime import datetime
# import enum
# from settings import PREFIX
# from enums.transactionEnums import *
# from database.models.base import Base

# # ENUMS
# class TransactionType(str, enum.Enum):
#     CREDIT = "credit"
#     DEBIT = "debit"

# class TransactionMode(str, enum.Enum):
#     CARD = "card"
#     TRANSFER = "transfer"
#     USSD = "ussd"

# class TransactionProcessor(str, enum.Enum):
#     PAYSTACK = "paystack"
#     FLUTTERWAVE = "flutterwave"

# class TransactionStatus(str, enum.Enum):
#     PENDING = "pending"
#     SUCCESSFUL = "successful"
#     FAILED = "failed"

# class UserRole(str, enum.Enum):
#     OWNER = "owner"
#     OPERATIONS = "operations"
#     DEVELOPER = "developer"
#     ADMIN = "admin"
#     SUPPORT = "support"

# # ASSOCIATIONS
# customer_merchant = Table(
#     "customer_merchant", Base.metadata,
#     Column("customer_id", Integer, ForeignKey("customers.id"), primary_key=True),
#     Column("merchant_id", String(50), ForeignKey("merchant.id"), primary_key=True)
# )

# merchant_processor = Table(
#     "merchant_processor", Base.metadata,
#     Column("merchant_id", String(50), ForeignKey("merchant.id"), primary_key=True),
#     Column("processor_id", Integer, ForeignKey("processor.id"), primary_key=True)
# )

# user_merchant = Table(
#     "user_merchants", Base.metadata,
#     Column("user_id", String(10), ForeignKey("users.id"), primary_key=True),
#     Column("merchant_id", String(50), ForeignKey("merchant.id"), primary_key=True),
#     Column("role", Enum(UserRole), default=UserRole.OWNER)
# )

# # MODELS
# class Customer(Base):
#     __tablename__ = "customers"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     email = Column(String(100), unique=True, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     merchants = relationship("Merchant", secondary=customer_merchant, back_populates="customers")

# class Merchant(Base):
#     __tablename__ = "merchant"

#     id = Column(String(50), primary_key=True, default=lambda: (PREFIX + str(uuid.uuid4())[:7]).lower())
#     name = Column(String(100), nullable=False)
#     email = Column(String(100), unique=True, nullable=False)
#     joined_at = Column(DateTime, default=datetime.utcnow)
#     is_verified = Column(Boolean, default=False)
#     is_active = Column(Boolean, default=True)
#     percentage_charge = Column(Float, default=1.5)
#     flat_charge = Column(Float, default=0.0)
#     test_balance = Column(Float, default=0.0)
#     live_balance = Column(Float, default=0.0)

#     processors = relationship("Processor", secondary=merchant_processor, back_populates="merchants")
#     customers = relationship("Customer", secondary=customer_merchant, back_populates="merchants")
#     users = relationship("User", secondary=user_merchant, back_populates="merchants")

# class Processor(Base):
#     __tablename__ = "processor"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     code = Column(String(10), unique=True)
#     charge = Column(Float)
#     markup = Column(Float, default=0)

#     merchants = relationship("Merchant", secondary=merchant_processor, back_populates="processors")

# class Token(Base):
#     __tablename__ = "token"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     merchant_id = Column(String(50), ForeignKey("merchant.id"))
#     secret_key = Column(Text)
#     public_key = Column(Text)
#     type = Column(String(10), default="test")
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     last_used = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     merchant = relationship("Merchant")

# class Transaction(Base):
#     __tablename__ = "transaction"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     type = Column(Enum(TransactionType), nullable=True)
#     mode = Column(Enum(TransactionMode), nullable=True)
#     processor = Column(Enum(TransactionProcessor), nullable=False)
#     merchant_id = Column(String(50), ForeignKey("merchant.id"))
#     customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
#     processor_reference = Column(String(100), unique=True)
#     reference = Column(String(100), unique=True)
#     amount = Column(Float)
#     charge = Column(Float, default=0.0)
#     details = Column(JSON, nullable=True)
#     currency = Column(String(3), default="NGN")
#     status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
#     redirect_url = Column(Text, nullable=True)
#     notification_url = Column(Text, nullable=True)
#     metadata = Column(JSON, nullable=True)
#     narration = Column(Text, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     merchant = relationship("Merchant")
#     customer = relationship("Customer")

# class User(Base):
#     __tablename__ = "users"

#     id = Column(String(10), primary_key=True, unique=True)
#     name = Column(String(100))
#     email = Column(String(100), unique=True)
#     password = Column(String(100))
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     is_verified = Column(Boolean, default=False)
#     is_active = Column(Boolean, default=True)

#     merchants = relationship("Merchant", secondary=user_merchant, back_populates="users")

from .RoutingRule import RoutingRule

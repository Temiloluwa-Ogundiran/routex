# processor.py
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from database.models.base import Base
from database.models.association import merchant_processor

class Processor(Base):
    __tablename__ = "processor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True)
    charge = Column(Float)
    markup = Column(Float, default=0.0)

    merchants = relationship("Merchant", secondary=merchant_processor, back_populates="processors")

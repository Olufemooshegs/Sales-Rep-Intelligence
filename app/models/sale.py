from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    rep_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_type = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    revenue = Column(Numeric(12, 2), nullable=False)
    week_start = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    rep = relationship("User", back_populates="sales")

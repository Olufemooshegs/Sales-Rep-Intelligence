from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class SaleCreate(BaseModel):
    product_type: str
    quantity: int
    revenue: float
    week_start: Optional[date] = None

class SaleRead(BaseModel):
    id: int
    rep_id: int
    product_type: str
    quantity: int
    revenue: float
    week_start: date
    created_at: datetime

    class Config:
        orm_mode = True

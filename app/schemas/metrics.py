from pydantic import BaseModel

class LeaderboardEntry(BaseModel):
    rep_id: int
    email: str
    total_sales: float
    growth_rate: float
    consistency: float
    score: float
    rank: int

    class Config:
        orm_mode = True

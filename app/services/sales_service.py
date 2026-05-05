from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sale import Sale
from datetime import datetime, timedelta

async def create_sale(db: AsyncSession, rep_id: int, *, product_type: str, quantity: int, revenue: float, week_start=None) -> Sale:
    # Determine week_start (Monday) if not provided
    if week_start is None:
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
    sale = Sale(rep_id=rep_id, product_type=product_type, quantity=quantity, revenue=revenue, week_start=week_start)
    db.add(sale)
    await db.commit()
    await db.refresh(sale)
    return sale

async def list_sales_for_rep(db: AsyncSession, rep_id: int):
    result = await db.execute(
        "SELECT * FROM sales WHERE rep_id = :rep_id ORDER BY week_start DESC, created_at DESC",
        {"rep_id": rep_id},
    )
    # Use ORM mapping by querying Sale instead for more robust approach
    # Implemented quickly using raw SQL for simplicity
    return result.fetchall()

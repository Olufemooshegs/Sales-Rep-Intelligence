from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session, get_current_user
from app.schemas.sale import SaleCreate, SaleRead
from app.services.sales_service import create_sale

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/submit", response_model=SaleRead)
async def submit_sale(sale_in: SaleCreate, db: AsyncSession = Depends(get_db_session), current_user=Depends(get_current_user)):
    # Sales reps (and admins) can submit
    sale = await create_sale(db, rep_id=current_user.id, product_type=sale_in.product_type, quantity=sale_in.quantity, revenue=sale_in.revenue, week_start=sale_in.week_start)
    return sale


@router.get("/me")
async def my_sales(db: AsyncSession = Depends(get_db_session), current_user=Depends(get_current_user)):
    # Return sales for current user
    result = await db.execute(
        "SELECT id, rep_id, product_type, quantity, revenue, week_start, created_at FROM sales WHERE rep_id = :rep_id ORDER BY week_start DESC",
        {"rep_id": current_user.id},
    )
    rows = result.fetchall()
    # Format simply
    return [dict(r) for r in rows]

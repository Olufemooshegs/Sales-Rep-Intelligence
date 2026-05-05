from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.services.metrics_service import compute_leaderboard, detect_anomalies
from app.utils.cache import cache
from app.utils.csv import generate_csv_stream
from typing import List

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/leaderboard")
async def leaderboard(top_n: int = Query(10, ge=1), db: AsyncSession = Depends(get_db_session)):
    cache_key = f"leaderboard:{top_n}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    board = await compute_leaderboard(db, top_n=top_n)
    cache.set(cache_key, board, ttl=60)
    return board


@router.get("/leaderboard/csv")
async def leaderboard_csv(top_n: int = Query(100, ge=1), db: AsyncSession = Depends(get_db_session)):
    board = await compute_leaderboard(db, top_n=top_n)
    headers = ["rank", "rep_id", "email", "total_sales", "growth_rate", "consistency", "score"]
    rows = [{
        "rank": e.get("rank"),
        "rep_id": e.get("rep_id"),
        "email": e.get("email"),
        "total_sales": e.get("total_sales"),
        "growth_rate": e.get("growth_rate"),
        "consistency": e.get("consistency"),
        "score": e.get("score"),
    } for e in board]
    return generate_csv_stream(rows, headers, filename="leaderboard.csv")


@router.get("/insights/top_performer")
async def top_performer(db: AsyncSession = Depends(get_db_session)):
    board = await compute_leaderboard(db, top_n=1)
    if not board:
        raise HTTPException(status_code=404, detail="No data")
    return board[0]


@router.get("/insights/most_improved")
async def most_improved(db: AsyncSession = Depends(get_db_session)):
    board = await compute_leaderboard(db, top_n=1000)
    if not board:
        raise HTTPException(status_code=404, detail="No data")
    # most improved == highest growth_rate
    best = max(board, key=lambda x: x.get("growth_rate", 0))
    return best


@router.get("/insights/worst_decline")
async def worst_decline(db: AsyncSession = Depends(get_db_session)):
    board = await compute_leaderboard(db, top_n=1000)
    if not board:
        raise HTTPException(status_code=404, detail="No data")
    worst = min(board, key=lambda x: x.get("growth_rate", 0))
    return worst


@router.get("/anomalies")
async def anomalies(db: AsyncSession = Depends(get_db_session)):
    items = await detect_anomalies(db)
    return items

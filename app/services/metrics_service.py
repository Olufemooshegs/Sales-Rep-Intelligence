from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sale import Sale
from app.models.user import User
from collections import defaultdict
import math
from typing import List, Dict


async def compute_leaderboard(db: AsyncSession, top_n: int = 10) -> List[Dict]:
    # Aggregate weekly revenue per rep
    q = select(Sale.rep_id, Sale.week_start, func.sum(Sale.revenue).label("sum_revenue")).group_by(Sale.rep_id, Sale.week_start)
    res = await db.execute(q)
    rows = res.all()

    by_rep = defaultdict(dict)  # rep_id -> {week_start: revenue}
    for rep_id, week_start, sum_rev in rows:
        # sum_rev may be Decimal; convert to float
        by_rep[rep_id][week_start] = float(sum_rev)

    metrics = []
    for rep_id, weeks in by_rep.items():
        weekly = [(ws, weeks[ws]) for ws in sorted(weeks.keys())]
        revenues = [v for ws, v in weekly]
        total_sales = sum(revenues)

        # growth_rate = last_week vs previous_week
        growth = 0.0
        if len(revenues) >= 2:
            last = revenues[-1]
            prev = revenues[-2]
            if prev != 0:
                growth = (last - prev) / prev
            else:
                growth = float(last)
        elif len(revenues) == 1:
            growth = float(revenues[-1])

        # consistency: inverse of coefficient of variation
        consistency = 0.0
        if len(revenues) > 0:
            mean = sum(revenues) / len(revenues)
            if mean > 0:
                var = sum((r - mean) ** 2 for r in revenues) / len(revenues)
                std = math.sqrt(var)
                cv = std / mean if mean else float('inf')
                consistency = 1.0 / (1.0 + cv)
            else:
                consistency = 0.0

        metrics.append({
            "rep_id": rep_id,
            "total_sales": float(total_sales),
            "growth": float(growth),
            "consistency": float(consistency),
        })

    # Fetch emails for reps
    rep_ids = [m["rep_id"] for m in metrics]
    users = {}
    if rep_ids:
        q2 = select(User.id, User.email).where(User.id.in_(rep_ids))
        ures = await db.execute(q2)
        urows = ures.all()
        for uid, email in urows:
            users[uid] = email

    # Normalize metrics
    totals = [m["total_sales"] for m in metrics] if metrics else [0]
    growths = [m["growth"] for m in metrics] if metrics else [0]
    consistencies = [m["consistency"] for m in metrics] if metrics else [0]

    min_t, max_t = (min(totals), max(totals)) if totals else (0, 0)
    min_g, max_g = (min(growths), max(growths)) if growths else (0, 0)
    min_c, max_c = (min(consistencies), max(consistencies)) if consistencies else (0, 0)

    entries = []
    for m in metrics:
        norm_total = (m["total_sales"] - min_t) / (max_t - min_t) if max_t != min_t else (1.0 if max_t != 0 else 0.0)
        norm_growth = (m["growth"] - min_g) / (max_g - min_g) if max_g != min_g else (0.0)
        norm_consistency = (m["consistency"] - min_c) / (max_c - min_c) if max_c != min_c else m["consistency"]

        score = norm_total * 0.5 + norm_growth * 0.3 + norm_consistency * 0.2

        entries.append({
            "rep_id": m["rep_id"],
            "email": users.get(m["rep_id"], "unknown"),
            "total_sales": m["total_sales"],
            "growth_rate": m["growth"],
            "consistency": m["consistency"],
            "score": float(score),
        })

    # Sort and assign ranks
    entries_sorted = sorted(entries, key=lambda x: x["score"], reverse=True)
    for idx, e in enumerate(entries_sorted, start=1):
        e["rank"] = idx

    return entries_sorted[:top_n]


async def detect_anomalies(db: AsyncSession, z_thresh: float = 2.5, pct_thresh: float = 3.0):
    # Find unusual spikes or drops per rep using z-score and percent-change thresholds
    q = select(Sale.rep_id, Sale.week_start, func.sum(Sale.revenue).label("sum_revenue")).group_by(Sale.rep_id, Sale.week_start)
    res = await db.execute(q)
    rows = res.all()

    by_rep = defaultdict(list)
    for rep_id, week_start, sum_rev in rows:
        by_rep[rep_id].append((week_start, float(sum_rev)))

    anomalies = []
    for rep_id, weekly in by_rep.items():
        weekly_sorted = sorted(weekly, key=lambda x: x[0])
        revenues = [v for _, v in weekly_sorted]
        if not revenues:
            continue
        mean = sum(revenues) / len(revenues)
        var = sum((r - mean) ** 2 for r in revenues) / len(revenues)
        std = math.sqrt(var)
        for idx, (wk, rev) in enumerate(weekly_sorted):
            z = (rev - mean) / std if std > 0 else 0
            pct_change = 0
            if idx >= 1:
                prev = weekly_sorted[idx - 1][1]
                if prev != 0:
                    pct_change = rev / prev
            if abs(z) >= z_thresh or pct_change >= pct_thresh or pct_change <= 1.0 / pct_thresh:
                anomalies.append({"rep_id": rep_id, "week_start": wk.isoformat(), "revenue": rev, "z": z, "pct_change": pct_change})

    return anomalies

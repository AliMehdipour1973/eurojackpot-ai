from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from apps.api.src.db.connection import get_db
from typing import Optional

router = APIRouter()

@router.get("/draws")
def get_draws(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    from_date: Optional[int] = Query(default=None),
    to_date: Optional[int] = Query(default=None)
):
    query = """
        SELECT draw_date, n1, n2, n3, n4, n5, e1, e2
        FROM core.draws
        WHERE 1=1
    """
    params = {}
    if from_date:
        query += " AND draw_date >= :from_date"
        params["from_date"] = from_date
    if to_date:
        query += " AND draw_date <= :to_date"
        params["to_date"] = to_date
    query += " ORDER BY draw_date DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    rows = db.execute(text(query), params).fetchall()
    total = db.execute(
        text("SELECT COUNT(*) FROM core.draws")
    ).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "draws": [
            {
                "draw_date": r[0],
                "main_numbers": [r[1], r[2], r[3], r[4], r[5]],
                "euro_numbers": [r[6], r[7]]
            }
            for r in rows
        ]
    }

@router.get("/draws/{draw_date}")
def get_draw(draw_date: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT d.draw_date, d.n1, d.n2, d.n3, d.n4, d.n5, d.e1, d.e2,
                   dd.day_of_week, dd.ticket_sales_amount,
                   dd.prize_tier_1, dd.winners_tier_1
            FROM core.draws d
            LEFT JOIN core.draw_details dd ON dd.draw_date = d.draw_date
            WHERE d.draw_date = :draw_date
        """),
        {"draw_date": draw_date}
    ).fetchone()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Draw not found")

    return {
        "draw_date": row[0],
        "main_numbers": [row[1], row[2], row[3], row[4], row[5]],
        "euro_numbers": [row[6], row[7]],
        "day_of_week": row[8],
        "ticket_sales_amount": float(row[9]) if row[9] else None,
        "jackpot_amount": float(row[10]) if row[10] else None,
        "jackpot_winners": row[11]
    }

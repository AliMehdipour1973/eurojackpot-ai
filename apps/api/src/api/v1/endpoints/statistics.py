from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from apps.api.src.db.connection import get_db

router = APIRouter()

@router.get("/statistics/frequency")
def get_frequency(
    db: Session = Depends(get_db),
    window: int = Query(default=0, description="0=all time, or 5,7,10,20,30,50")
):
    if window == 0:
        table = "features.frq_numbers"
    elif window in [5, 7, 10, 20, 30, 50]:
        table = f"features.frq_numbers_{window}draws"
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="window must be 0, 5, 7, 10, 20, 30, or 50"
        )

    latest_date = db.execute(
        text(f"SELECT MAX(draw_date) FROM {table}")
    ).scalar()

    rows = db.execute(
        text(f"""
            SELECT number, frequency_count
            FROM {table}
            WHERE draw_date = :draw_date
            ORDER BY number ASC
        """),
        {"draw_date": latest_date}
    ).fetchall()

    return {
        "window": window,
        "as_of_draw": latest_date,
        "frequencies": [
            {"number": r[0], "frequency": r[1]}
            for r in rows
        ]
    }

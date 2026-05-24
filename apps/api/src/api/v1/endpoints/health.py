from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from apps.api.src.db.connection import get_db

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db.execute(text("SELECT COUNT(*) FROM core.draws"))
        result = db.execute(
            text("SELECT COUNT(*) FROM core.draws")
        ).scalar()
        return {
            "status": "ok",
            "database": "connected",
            "total_draws": result
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }

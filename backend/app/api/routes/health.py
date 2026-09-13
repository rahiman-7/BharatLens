from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.services.scheduler import ingestion_tracker

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Backend Health Check")
def get_health(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "BharatLens Backend API",
        "tagline": "News with a wider perspective — See India. See the World.",
        "database": db_status,
        "version": "1.0.0",
        "ingestion": ingestion_tracker.get_status(),
    }

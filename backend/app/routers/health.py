from fastapi import APIRouter
from app.database import db

router = APIRouter(prefix="", tags=["Health"])

@router.get("/health")
def get_health():
    """System health check endpoint verifying API and Neo4j connectivity."""
    db_health = db.check_health()
    return {
        "status": "healthy" if db_health.get("connected") else "degraded",
        "service": "financial-fraud-detection-api",
        "version": "1.0.0",
        "database": db_health
    }

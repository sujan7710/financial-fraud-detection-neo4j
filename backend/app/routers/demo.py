from fastapi import APIRouter, status
from app.services.demo_data_service import DemoDataService

router = APIRouter(prefix="/api/v1/data", tags=["Demo Data & Admin"])

@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_demo_data():
    """
    Idempotently load realistic financial fraud scenarios and benign records.
    Safe to execute multiple times without producing duplicate nodes or relationships.
    """
    return DemoDataService.seed_demo_data()

@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_database():
    """
    Purge all database records and re-apply schema constraints.
    """
    return DemoDataService.reset_database()

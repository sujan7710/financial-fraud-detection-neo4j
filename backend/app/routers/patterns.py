from typing import List, Optional
from fastapi import APIRouter, Query
from app.models.pattern import FlaggedPattern, FraudDetectionReport
from app.services.fraud_service import FraudDetectionService

router = APIRouter(prefix="/api/v1/patterns", tags=["Fraud Pattern Detection"])

@router.get("/detect", response_model=FraudDetectionReport)
def run_all_detection(
    large_threshold: Optional[float] = Query(None, ge=100.0, description="Minimum threshold for high-value outliers"),
    circular_min: Optional[int] = Query(3, ge=2, le=10, description="Minimum cycle length"),
    circular_max: Optional[int] = Query(5, ge=2, le=10, description="Maximum cycle length"),
    smurfing_min_acc: Optional[int] = Query(3, ge=2, le=20, description="Minimum accounts for structuring pattern")
):
    """
    Execute all graph-based fraud detection algorithms.
    Returns explainable findings with severity levels and regulatory reasoning.
    """
    return FraudDetectionService.run_all_detection(
        large_threshold=large_threshold,
        circular_min=circular_min,
        circular_max=circular_max,
        smurfing_min_acc=smurfing_min_acc
    )

@router.get("/circular", response_model=List[FlaggedPattern])
def detect_circular_patterns(
    min_depth: int = Query(3, ge=2, le=10),
    max_depth: int = Query(5, ge=2, le=10)
):
    """Detect circular layering transaction rings using Cypher variable-length paths."""
    return FraudDetectionService.detect_circular_transactions(
        min_depth=min_depth,
        max_depth=max_depth
    )

@router.get("/large", response_model=List[FlaggedPattern])
def detect_large_outliers(
    threshold: Optional[float] = Query(None, ge=100.0)
):
    """Detect outlier transactions exceeding the configured threshold."""
    return FraudDetectionService.detect_large_transactions(threshold=threshold)

@router.get("/smurfing", response_model=List[FlaggedPattern])
def detect_smurfing(
    sub_threshold: Optional[float] = Query(None, ge=100.0),
    min_accounts: Optional[int] = Query(3, ge=2, le=20)
):
    """Detect structuring / smurfing fan-in aggregation and fan-out dispersal."""
    return FraudDetectionService.detect_smurfing_structuring(
        sub_threshold=sub_threshold,
        min_accounts=min_accounts
    )

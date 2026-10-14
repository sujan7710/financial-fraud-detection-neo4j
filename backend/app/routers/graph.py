from typing import Optional
from fastapi import APIRouter, Query
from app.services.graph_service import GraphService

router = APIRouter(prefix="/api/v1/graph", tags=["Graph Network"])

@router.get("/subgraph", response_model=dict)
def get_graph_subgraph(
    account_id: Optional[str] = Query(None, description="Focus on ego-network around specific account"),
    flagged_only: bool = Query(False, description="Filter for suspicious/flagged edges only"),
    limit: int = Query(150, ge=1, le=500, description="Maximum relationships to return")
):
    """
    Extract graph topology (nodes and directed edges) for interactive network visualization.
    """
    return GraphService.get_graph_data(
        account_id=account_id,
        flagged_only=flagged_only,
        limit=limit
    )

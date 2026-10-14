from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.transaction import TransactionCreate, TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(tx_in: TransactionCreate):
    """Record a financial transfer between two accounts in Neo4j."""
    if tx_in.from_account_id == tx_in.to_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination account cannot be identical."
        )
    try:
        return TransactionService.create_transaction(tx_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("", response_model=dict)
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    flagged_only: bool = False,
    min_amount: Optional[float] = Query(None, ge=0.0),
    account_id: Optional[str] = None,
    channel: Optional[str] = None
):
    """List transactions with filtering by flags, amount, account, or channel."""
    return TransactionService.list_transactions(
        skip=skip,
        limit=limit,
        flagged_only=flagged_only,
        min_amount=min_amount,
        account_id=account_id,
        channel=channel
    )

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str):
    """Retrieve details for a specific transaction."""
    tx = TransactionService.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )
    return tx

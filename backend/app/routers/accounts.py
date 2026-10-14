from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])

@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account_in: AccountCreate):
    """Create a new account node in Neo4j."""
    # Check if account already exists
    existing = AccountService.get_account(account_in.account_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with ID '{account_in.account_id}' already exists."
        )
    try:
        return AccountService.create_account(account_in)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("", response_model=dict)
def list_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = None,
    min_risk: Optional[float] = Query(None, ge=0.0, le=100.0),
    account_type: Optional[str] = None,
    search: Optional[str] = None
):
    """List accounts with filtering and pagination."""
    return AccountService.list_accounts(
        skip=skip,
        limit=limit,
        status=status,
        min_risk=min_risk,
        account_type=account_type,
        search=search
    )

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: str):
    """Fetch details and transaction stats for a specific account."""
    acc = AccountService.get_account(account_id)
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found."
        )
    return acc

@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(account_id: str, update_in: AccountUpdate):
    """Update properties of an existing account."""
    updated = AccountService.update_account(account_id, update_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found."
        )
    return updated

@router.delete("/{account_id}", status_code=status.HTTP_200_OK)
def delete_account(account_id: str):
    """Delete an account and its connected relationships."""
    deleted = AccountService.delete_account(account_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_id}' not found or could not be deleted."
        )
    return {"status": "success", "message": f"Account '{account_id}' deleted successfully."}

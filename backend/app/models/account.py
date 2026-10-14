from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class AccountBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100, description="Customer or organization legal name")
    account_type: str = Field("Personal", description="Account classification: Personal, Business, Mule, Shell Company, etc.")
    balance: float = Field(0.0, ge=0.0, description="Current account balance")
    risk_score: float = Field(0.0, ge=0.0, le=100.0, description="Calculated baseline risk score (0-100)")
    status: str = Field("ACTIVE", description="Account status: ACTIVE, SUSPENDED, FROZEN, UNDER_INVESTIGATION")

class AccountCreate(AccountBase):
    account_id: str = Field(..., min_length=3, max_length=50, description="Unique account identifier (e.g., ACC-1001)")

class AccountUpdate(BaseModel):
    customer_name: Optional[str] = None
    account_type: Optional[str] = None
    balance: Optional[float] = Field(None, ge=0.0)
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    status: Optional[str] = None

class AccountResponse(AccountBase):
    account_id: str
    created_at: str
    outgoing_count: int = 0
    incoming_count: int = 0
    total_sent: float = 0.0
    total_received: float = 0.0

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class TransactionBase(BaseModel):
    from_account_id: str = Field(..., description="Source account identifier")
    to_account_id: str = Field(..., description="Destination account identifier")
    amount: float = Field(..., gt=0.0, description="Transaction monetary amount")
    currency: str = Field("INR", max_length=10, description="ISO currency code")
    channel: str = Field("WIRE", description="Transfer channel: WIRE, ACH, ONLINE, ATM, SWIFT, CRYPTO_GATEWAY")
    timestamp: Optional[str] = Field(None, description="ISO-8601 transaction timestamp")

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    transaction_id: str
    timestamp: str
    flagged: bool = False
    flag_reason: Optional[str] = None
    risk_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class TransactionListResponse(BaseModel):
    total: int
    items: List[TransactionResponse]

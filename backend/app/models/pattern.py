from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SuspiciousPatternType(str, Enum):
    CIRCULAR_TRANSACTION = "CIRCULAR_TRANSACTION"
    LARGE_TRANSACTION_OUTLIER = "LARGE_TRANSACTION_OUTLIER"
    SMURFING_FAN_IN = "SMURFING_FAN_IN"
    SMURFING_FAN_OUT = "SMURFING_FAN_OUT"
    HIGH_VELOCITY_BURST = "HIGH_VELOCITY_BURST"
    RAPID_PASS_THROUGH = "RAPID_PASS_THROUGH"

class PatternSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class FlaggedPattern(BaseModel):
    pattern_id: str
    pattern_type: SuspiciousPatternType
    severity: PatternSeverity
    rule_name: str
    summary: str
    explainability: str = Field(..., description="Explainable natural-language reasoning why this pattern was flagged")
    recommended_action: str = Field(..., description="Actionable recommendation for financial crime investigators")
    involved_accounts: List[str]
    involved_transactions: List[str]
    total_amount: float
    cypher_query_used: str = Field(..., description="Cypher query used to detect this graph pattern")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DetectionReportSummary(BaseModel):
    total_patterns_detected: int
    critical_severity_count: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    total_flagged_amount: float
    total_accounts_involved: int

class FraudDetectionReport(BaseModel):
    summary: DetectionReportSummary
    patterns: List[FlaggedPattern]
    generated_at: str
    execution_time_ms: float

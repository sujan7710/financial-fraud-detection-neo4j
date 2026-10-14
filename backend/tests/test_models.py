import pytest
from app.models.account import AccountCreate, AccountResponse, AccountUpdate
from app.models.transaction import TransactionCreate, TransactionResponse
from app.models.pattern import FlaggedPattern, PatternSeverity, SuspiciousPatternType

def test_account_create_validation():
    acc = AccountCreate(
        account_id="ACC-TEST-1",
        customer_name="Test Customer",
        account_type="Personal",
        balance=5000.0,
        risk_score=15.0,
        status="ACTIVE"
    )
    assert acc.account_id == "ACC-TEST-1"
    assert acc.customer_name == "Test Customer"
    assert acc.balance == 5000.0

def test_transaction_create_validation():
    tx = TransactionCreate(
        from_account_id="ACC-01",
        to_account_id="ACC-02",
        amount=12500.0,
        currency="USD",
        channel="WIRE"
    )
    assert tx.from_account_id == "ACC-01"
    assert tx.amount == 12500.0
    assert tx.channel == "WIRE"

def test_pattern_severity_ranking():
    pattern = FlaggedPattern(
        pattern_id="PAT-001",
        pattern_type=SuspiciousPatternType.CIRCULAR_TRANSACTION,
        severity=PatternSeverity.CRITICAL,
        rule_name="Circular Fund Routing",
        summary="Test cycle summary",
        explainability="Closed loop of length 3",
        recommended_action="Freeze accounts",
        involved_accounts=["A1", "A2", "A3"],
        involved_transactions=["TX1", "TX2", "TX3"],
        total_amount=50000.0,
        cypher_query_used="MATCH path = (a:Account)-[r:SENT*3..5]->(a) RETURN path"
    )
    assert pattern.severity == PatternSeverity.CRITICAL
    assert len(pattern.involved_accounts) == 3

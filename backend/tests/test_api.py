import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Graph-Based Financial Fraud Detection System"
    assert data["status"] == "operational"
    assert "endpoints" in data

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data

@patch("app.services.account_service.AccountService.list_accounts")
def test_list_accounts_endpoint(mock_list):
    mock_list.return_value = {
        "total": 1,
        "items": [
            {
                "account_id": "ACC-101",
                "customer_name": "Acme Corp",
                "account_type": "Business",
                "balance": 100000.0,
                "risk_score": 10.0,
                "status": "ACTIVE",
                "created_at": "2026-10-14T00:00:00Z",
                "outgoing_count": 0,
                "incoming_count": 0,
                "total_sent": 0.0,
                "total_received": 0.0
            }
        ],
        "skip": 0,
        "limit": 50
    }
    response = client.get("/api/v1/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["account_id"] == "ACC-101"

@patch("app.services.fraud_service.FraudDetectionService.run_all_detection")
def test_patterns_detect_endpoint(mock_detect):
    mock_detect.return_value = {
        "summary": {
            "total_patterns_detected": 1,
            "critical_severity_count": 1,
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
            "total_flagged_amount": 75000.0,
            "total_accounts_involved": 3
        },
        "patterns": [
            {
                "pattern_id": "PAT-CIRC-001",
                "pattern_type": "CIRCULAR_TRANSACTION",
                "severity": "CRITICAL",
                "rule_name": "Circular Fund Routing",
                "summary": "Detected 3-hop closed circular ring",
                "explainability": "Funds routed in loop",
                "recommended_action": "Freeze accounts",
                "involved_accounts": ["A1", "A2", "A3"],
                "involved_transactions": ["T1", "T2", "T3"],
                "total_amount": 75000.0,
                "cypher_query_used": "MATCH path = ...",
                "metadata": {}
            }
        ],
        "generated_at": "2026-10-14T20:00:00Z",
        "execution_time_ms": 12.5
    }
    response = client.get("/api/v1/patterns/detect")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_patterns_detected"] == 1
    assert data["patterns"][0]["pattern_id"] == "PAT-CIRC-001"

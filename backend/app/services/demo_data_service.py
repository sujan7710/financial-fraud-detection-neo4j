import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from app.database import db

logger = logging.getLogger("fraud_detection.services.demo_data")

DEMO_ACCOUNTS = [
    # Circular Laundering Ring 1
    {"account_id": "ACC-1001", "customer_name": "Apex Global Trading", "account_type": "Shell Company", "balance": 185000.0, "risk_score": 85.0, "status": "UNDER_INVESTIGATION"},
    {"account_id": "ACC-1002", "customer_name": "Panama Horizon Capital", "account_type": "Offshore Entity", "balance": 92000.0, "risk_score": 78.0, "status": "ACTIVE"},
    {"account_id": "ACC-1003", "customer_name": "Vanguard Logistics LLC", "account_type": "Intermediary", "balance": 64000.0, "risk_score": 65.0, "status": "ACTIVE"},
    {"account_id": "ACC-1004", "customer_name": "Lighthouse Meridian Inv.", "account_type": "Layering Hub", "balance": 120000.0, "risk_score": 80.0, "status": "ACTIVE"},

    # Structuring / Smurfing Fan-In Ring
    {"account_id": "ACC-2000", "customer_name": "Metropolis Cash Management", "account_type": "Mule Collector", "balance": 54000.0, "risk_score": 90.0, "status": "FROZEN"},
    {"account_id": "ACC-2001", "customer_name": "David Miller", "account_type": "Mule Account", "balance": 4500.0, "risk_score": 72.0, "status": "ACTIVE"},
    {"account_id": "ACC-2002", "customer_name": "Elena Rostova", "account_type": "Mule Account", "balance": 3200.0, "risk_score": 68.0, "status": "ACTIVE"},
    {"account_id": "ACC-2003", "customer_name": "Marcus Vance", "account_type": "Mule Account", "balance": 2100.0, "risk_score": 70.0, "status": "ACTIVE"},
    {"account_id": "ACC-2004", "customer_name": "Carlos Mendez", "account_type": "Mule Account", "balance": 5100.0, "risk_score": 69.0, "status": "ACTIVE"},

    # High-Value Outlier Corporate Accounts
    {"account_id": "ACC-3001", "customer_name": "Titanium Heavy Industries", "account_type": "Corporation", "balance": 4200000.0, "risk_score": 60.0, "status": "ACTIVE"},
    {"account_id": "ACC-3002", "customer_name": "Aegis Sovereign Fund", "account_type": "Investment Trust", "balance": 9500000.0, "risk_score": 55.0, "status": "ACTIVE"},
    {"account_id": "ACC-3003", "customer_name": "Orion Global Ventures", "account_type": "Venture Fund", "balance": 1850000.0, "risk_score": 45.0, "status": "ACTIVE"},
    {"account_id": "ACC-3004", "customer_name": "Nova FinTech Escrow", "account_type": "Escrow Service", "balance": 3100000.0, "risk_score": 40.0, "status": "ACTIVE"},

    # Fan-Out Dispersal Ring
    {"account_id": "ACC-4000", "customer_name": "Cascade Holdings Corp", "account_type": "Dispersal Source", "balance": 650000.0, "risk_score": 82.0, "status": "UNDER_INVESTIGATION"},
    {"account_id": "ACC-4001", "customer_name": "Brian Kelly", "account_type": "Personal", "balance": 14000.0, "risk_score": 62.0, "status": "ACTIVE"},
    {"account_id": "ACC-4002", "customer_name": "Sophia Chen", "account_type": "Personal", "balance": 18000.0, "risk_score": 64.0, "status": "ACTIVE"},
    {"account_id": "ACC-4003", "customer_name": "Tariq Al-Mansoor", "account_type": "Personal", "balance": 15500.0, "risk_score": 60.0, "status": "ACTIVE"},

    # Benign Legitimate Business & Retail Accounts
    {"account_id": "ACC-5001", "customer_name": "Nordic Coffee Roasters", "account_type": "Business", "balance": 28400.0, "risk_score": 12.0, "status": "ACTIVE"},
    {"account_id": "ACC-5002", "customer_name": "Fresh Bean Wholesale", "account_type": "Business", "balance": 64000.0, "risk_score": 8.0, "status": "ACTIVE"},
    {"account_id": "ACC-5003", "customer_name": "Alice Johnson", "account_type": "Personal", "balance": 6200.0, "risk_score": 5.0, "status": "ACTIVE"},
    {"account_id": "ACC-5004", "customer_name": "Robert Davis", "account_type": "Personal", "balance": 4100.0, "risk_score": 7.0, "status": "ACTIVE"},
    {"account_id": "ACC-5005", "customer_name": "Metro Power & Utility", "account_type": "Utility", "balance": 520000.0, "risk_score": 2.0, "status": "ACTIVE"}
]

DEMO_TRANSACTIONS = [
    # Ring 1: Circular Laundering Transfers
    {"tx_id": "TX-CIRC-101", "from_id": "ACC-1001", "to_id": "ACC-1002", "amount": 48500.0, "channel": "WIRE", "timestamp": "2026-10-10T09:15:00Z", "flagged": True, "reason": "Part of 4-hop circular laundering cycle"},
    {"tx_id": "TX-CIRC-102", "from_id": "ACC-1002", "to_id": "ACC-1003", "amount": 47900.0, "channel": "WIRE", "timestamp": "2026-10-10T11:30:00Z", "flagged": True, "reason": "Part of 4-hop circular laundering cycle"},
    {"tx_id": "TX-CIRC-103", "from_id": "ACC-1003", "to_id": "ACC-1004", "amount": 47200.0, "channel": "WIRE", "timestamp": "2026-10-10T14:45:00Z", "flagged": True, "reason": "Part of 4-hop circular laundering cycle"},
    {"tx_id": "TX-CIRC-104", "from_id": "ACC-1004", "to_id": "ACC-1001", "amount": 46800.0, "channel": "WIRE", "timestamp": "2026-10-10T17:10:00Z", "flagged": True, "reason": "Part of 4-hop circular laundering cycle"},

    # Ring 2: Structuring / Smurfing Fan-In (Sub-Threshold aggregation)
    {"tx_id": "TX-SMURF-201", "from_id": "ACC-2001", "to_id": "ACC-2000", "amount": 9650.0, "channel": "ONLINE", "timestamp": "2026-10-11T08:20:00Z", "flagged": True, "reason": "Structuring: Sub-threshold deposit to collector hub"},
    {"tx_id": "TX-SMURF-202", "from_id": "ACC-2002", "to_id": "ACC-2000", "amount": 9400.0, "channel": "ONLINE", "timestamp": "2026-10-11T09:40:00Z", "flagged": True, "reason": "Structuring: Sub-threshold deposit to collector hub"},
    {"tx_id": "TX-SMURF-203", "from_id": "ACC-2003", "to_id": "ACC-2000", "amount": 9800.0, "channel": "ONLINE", "timestamp": "2026-10-11T11:15:00Z", "flagged": True, "reason": "Structuring: Sub-threshold deposit to collector hub"},
    {"tx_id": "TX-SMURF-204", "from_id": "ACC-2004", "to_id": "ACC-2000", "amount": 9750.0, "channel": "ONLINE", "timestamp": "2026-10-11T13:05:00Z", "flagged": True, "reason": "Structuring: Sub-threshold deposit to collector hub"},

    # High-Value Outliers
    {"tx_id": "TX-OUTL-301", "from_id": "ACC-3001", "to_id": "ACC-3002", "amount": 850000.0, "channel": "SWIFT", "timestamp": "2026-10-12T10:00:00Z", "flagged": True, "reason": "Large outlier: $850,000 exceeds reporting threshold"},
    {"tx_id": "TX-OUTL-302", "from_id": "ACC-3003", "to_id": "ACC-3004", "amount": 250000.0, "channel": "WIRE", "timestamp": "2026-10-12T14:30:00Z", "flagged": True, "reason": "Large outlier: $250,000 exceeds reporting threshold"},

    # Fan-Out Dispersal
    {"tx_id": "TX-FOUT-401", "from_id": "ACC-4000", "to_id": "ACC-4001", "amount": 9500.0, "channel": "ACH", "timestamp": "2026-10-13T09:00:00Z", "flagged": True, "reason": "Structuring: Sub-threshold dispersal from source"},
    {"tx_id": "TX-FOUT-402", "from_id": "ACC-4000", "to_id": "ACC-4002", "amount": 9850.0, "channel": "ACH", "timestamp": "2026-10-13T09:30:00Z", "flagged": True, "reason": "Structuring: Sub-threshold dispersal from source"},
    {"tx_id": "TX-FOUT-403", "from_id": "ACC-4000", "to_id": "ACC-4003", "amount": 9200.0, "channel": "ACH", "timestamp": "2026-10-13T10:15:00Z", "flagged": True, "reason": "Structuring: Sub-threshold dispersal from source"},

    # Benign Routine Transactions
    {"tx_id": "TX-NORM-501", "from_id": "ACC-5001", "to_id": "ACC-5002", "amount": 3450.0, "channel": "ACH", "timestamp": "2026-10-14T08:00:00Z", "flagged": False, "reason": None},
    {"tx_id": "TX-NORM-502", "from_id": "ACC-5003", "to_id": "ACC-5001", "amount": 12.50, "channel": "ONLINE", "timestamp": "2026-10-14T08:30:00Z", "flagged": False, "reason": None},
    {"tx_id": "TX-NORM-503", "from_id": "ACC-5004", "to_id": "ACC-5005", "amount": 145.0, "channel": "ONLINE", "timestamp": "2026-10-14T09:00:00Z", "flagged": False, "reason": None}
]

class DemoDataService:
    @staticmethod
    def seed_demo_data() -> Dict[str, Any]:
        """
        Idempotently load realistic financial fraud and benign benchmark data.
        Uses MERGE to avoid duplicate nodes or relationships on repeated execution.
        """
        logger.info("Initializing schema constraints prior to demo seeding...")
        db.init_schema()

        # 1. Merge Accounts
        account_query = """
        UNWIND $accounts AS acc
        MERGE (a:Account {account_id: acc.account_id})
        ON CREATE SET
            a.customer_name = acc.customer_name,
            a.account_type = acc.account_type,
            a.balance = acc.balance,
            a.risk_score = acc.risk_score,
            a.status = acc.status,
            a.created_at = $now
        ON MATCH SET
            a.customer_name = acc.customer_name,
            a.account_type = acc.account_type,
            a.balance = acc.balance,
            a.risk_score = acc.risk_score,
            a.status = acc.status
        RETURN count(a) AS accounts_processed
        """
        now = datetime.now(timezone.utc).isoformat()
        acc_res = db.execute_write(account_query, {"accounts": DEMO_ACCOUNTS, "now": now})
        accounts_count = acc_res[0]["accounts_processed"] if acc_res else 0

        # 2. Merge Transactions (Relationships)
        tx_query = """
        UNWIND $transactions AS tx
        MATCH (src:Account {account_id: tx.from_id})
        MATCH (dst:Account {account_id: tx.to_id})
        MERGE (src)-[r:SENT {transaction_id: tx.tx_id}]->(dst)
        ON CREATE SET
            r.amount = tx.amount,
            r.currency = 'USD',
            r.channel = tx.channel,
            r.timestamp = tx.timestamp,
            r.flagged = tx.flagged,
            r.flag_reason = tx.reason,
            r.risk_score = CASE WHEN tx.flagged THEN 75.0 ELSE 0.0 END
        ON MATCH SET
            r.amount = tx.amount,
            r.channel = tx.channel,
            r.timestamp = tx.timestamp,
            r.flagged = tx.flagged,
            r.flag_reason = tx.reason
        RETURN count(r) AS tx_processed
        """
        tx_res = db.execute_write(tx_query, {"transactions": DEMO_TRANSACTIONS})
        tx_count = tx_res[0]["tx_processed"] if tx_res else 0

        return {
            "status": "success",
            "message": "Demo data loaded successfully using idempotent Cypher MERGE.",
            "accounts_seeded": accounts_count,
            "transactions_seeded": tx_count,
            "patterns_available": [
                "Circular Fund Routing (4-node cycle: ACC-1001 -> 1002 -> 1003 -> 1004 -> 1001)",
                "Structuring / Fan-In Smurfing (ACC-2000 hub collecting $38,600 from 4 mules)",
                "Structuring / Fan-Out Dispersal (ACC-4000 distributing to 3 personal accounts)",
                "High-Value Outliers ($850,000 SWIFT and $250,000 WIRE transfers)",
                "Benign baseline commerce (Retail coffee, utilities, packaging)"
            ]
        }

    @staticmethod
    def reset_database() -> Dict[str, Any]:
        """
        Clears all nodes and relationships in the database, then re-applies schema constraints.
        """
        logger.warning("Purging all database contents for clean reset...")
        clear_query = "MATCH (n) DETACH DELETE n"
        db.execute_write(clear_query)
        applied = db.init_schema()
        return {
            "status": "success",
            "message": "Database completely purged and schema constraints reapplied.",
            "schema_statements_applied": applied
        }

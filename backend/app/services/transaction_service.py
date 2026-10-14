import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.config import settings
from app.database import db
from app.models.transaction import TransactionCreate

logger = logging.getLogger("fraud_detection.services.transaction")

class TransactionService:
    @staticmethod
    def create_transaction(tx_in: TransactionCreate) -> Dict[str, Any]:
        """Create a new SENT relationship between two accounts in Neo4j."""
        now = tx_in.timestamp or datetime.now(timezone.utc).isoformat()
        tx_id = f"TX-{uuid.uuid4().hex[:10].upper()}"

        # Preliminary threshold evaluation
        flagged = False
        flag_reason = None
        risk_score = 0.0

        if tx_in.amount >= settings.LARGE_TRANSACTION_THRESHOLD:
            flagged = True
            flag_reason = f"High-Value Outlier: Transaction amount ₹{tx_in.amount:,.2f} meets or exceeds reporting threshold (₹{settings.LARGE_TRANSACTION_THRESHOLD:,.2f})"
            risk_score = min(85.0, 50.0 + (tx_in.amount / settings.LARGE_TRANSACTION_THRESHOLD) * 10.0)

        query = """
        MATCH (source:Account {account_id: $from_id})
        MATCH (target:Account {account_id: $to_id})
        CREATE (source)-[r:SENT {
            transaction_id: $transaction_id,
            amount: $amount,
            currency: $currency,
            channel: $channel,
            timestamp: $timestamp,
            flagged: $flagged,
            flag_reason: $flag_reason,
            risk_score: $risk_score
        }]->(target)
        SET source.balance = CASE WHEN source.balance >= $amount THEN round((source.balance - $amount) * 100.0) / 100.0 ELSE 0.0 END,
            target.balance = round((target.balance + $amount) * 100.0) / 100.0
        RETURN r.transaction_id AS transaction_id,
               source.account_id AS from_account_id,
               target.account_id AS to_account_id,
               r.amount AS amount,
               r.currency AS currency,
               r.channel AS channel,
               r.timestamp AS timestamp,
               r.flagged AS flagged,
               r.flag_reason AS flag_reason,
               r.risk_score AS risk_score
        """
        params = {
            "from_id": tx_in.from_account_id,
            "to_id": tx_in.to_account_id,
            "transaction_id": tx_id,
            "amount": float(tx_in.amount),
            "currency": tx_in.currency,
            "channel": tx_in.channel,
            "timestamp": now,
            "flagged": flagged,
            "flag_reason": flag_reason,
            "risk_score": float(risk_score)
        }
        res = db.execute_write(query, params)
        if not res:
            # Check if source or target account is missing
            src = db.execute_read("MATCH (a:Account {account_id: $id}) RETURN a.account_id", {"id": tx_in.from_account_id})
            dst = db.execute_read("MATCH (a:Account {account_id: $id}) RETURN a.account_id", {"id": tx_in.to_account_id})
            missing = []
            if not src:
                missing.append(f"Source account '{tx_in.from_account_id}'")
            if not dst:
                missing.append(f"Destination account '{tx_in.to_account_id}'")
            if missing:
                raise ValueError(f"Transaction failed: {', '.join(missing)} does not exist.")
            raise RuntimeError("Transaction execution failed unexpectedly.")
        return res[0]

    @staticmethod
    def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
        """Fetch transaction by transaction_id."""
        query = """
        MATCH (source:Account)-[r:SENT {transaction_id: $transaction_id}]->(target:Account)
        RETURN r.transaction_id AS transaction_id,
               source.account_id AS from_account_id,
               target.account_id AS to_account_id,
               r.amount AS amount,
               r.currency AS currency,
               r.channel AS channel,
               r.timestamp AS timestamp,
               r.flagged AS flagged,
               r.flag_reason AS flag_reason,
               r.risk_score AS risk_score
        """
        records = db.execute_read(query, {"transaction_id": transaction_id})
        return records[0] if records else None

    @staticmethod
    def list_transactions(
        skip: int = 0,
        limit: int = 50,
        flagged_only: bool = False,
        min_amount: Optional[float] = None,
        account_id: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """List transactions with filtering by account, flag, channel, and amount."""
        conditions = []
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if flagged_only:
            conditions.append("r.flagged = true")
        if min_amount is not None:
            conditions.append("r.amount >= $min_amount")
            params["min_amount"] = float(min_amount)
        if channel:
            conditions.append("r.channel = $channel")
            params["channel"] = channel
        if account_id:
            conditions.append("(source.account_id = $account_id OR target.account_id = $account_id)")
            params["account_id"] = account_id

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_query = f"""
        MATCH (source:Account)-[r:SENT]->(target:Account)
        {where_clause}
        RETURN count(r) AS total
        """
        count_res = db.execute_read(count_query, params)
        total = count_res[0]["total"] if count_res else 0

        query = f"""
        MATCH (source:Account)-[r:SENT]->(target:Account)
        {where_clause}
        RETURN r.transaction_id AS transaction_id,
               source.account_id AS from_account_id,
               target.account_id AS to_account_id,
               r.amount AS amount,
               r.currency AS currency,
               r.channel AS channel,
               r.timestamp AS timestamp,
               r.flagged AS flagged,
               r.flag_reason AS flag_reason,
               r.risk_score AS risk_score
        ORDER BY r.timestamp DESC
        SKIP $skip
        LIMIT $limit
        """
        records = db.execute_read(query, params)
        return {"total": total, "items": records, "skip": skip, "limit": limit}

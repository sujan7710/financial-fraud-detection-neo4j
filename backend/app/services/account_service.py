import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database import db
from app.models.account import AccountCreate, AccountUpdate

logger = logging.getLogger("fraud_detection.services.account")

class AccountService:
    @staticmethod
    def create_account(account_in: AccountCreate) -> Dict[str, Any]:
        """Create a new account node in Neo4j."""
        now = datetime.now(timezone.utc).isoformat()
        query = """
        CREATE (a:Account {
            account_id: $account_id,
            customer_name: $customer_name,
            account_type: $account_type,
            balance: $balance,
            risk_score: $risk_score,
            status: $status,
            created_at: $created_at
        })
        RETURN a.account_id AS account_id,
               a.customer_name AS customer_name,
               a.account_type AS account_type,
               a.balance AS balance,
               a.risk_score AS risk_score,
               a.status AS status,
               a.created_at AS created_at
        """
        params = {
            "account_id": account_in.account_id,
            "customer_name": account_in.customer_name,
            "account_type": account_in.account_type,
            "balance": float(account_in.balance),
            "risk_score": float(account_in.risk_score),
            "status": account_in.status,
            "created_at": now
        }
        res = db.execute_write(query, params)
        if not res:
            raise RuntimeError(f"Failed to create account '{account_in.account_id}'")
        item = res[0]
        item["outgoing_count"] = 0
        item["incoming_count"] = 0
        item["total_sent"] = 0.0
        item["total_received"] = 0.0
        return item

    @staticmethod
    def get_account(account_id: str) -> Optional[Dict[str, Any]]:
        """Fetch account details and transaction aggregation stats."""
        query = """
        MATCH (a:Account {account_id: $account_id})
        OPTIONAL MATCH (a)-[out:SENT]->()
        OPTIONAL MATCH ()-[inc:SENT]->(a)
        RETURN a.account_id AS account_id,
               a.customer_name AS customer_name,
               a.account_type AS account_type,
               a.balance AS balance,
               a.risk_score AS risk_score,
               a.status AS status,
               a.created_at AS created_at,
               count(DISTINCT out) AS outgoing_count,
               count(DISTINCT inc) AS incoming_count,
               coalesce(sum(DISTINCT out.amount), 0.0) AS total_sent,
               coalesce(sum(DISTINCT inc.amount), 0.0) AS total_received
        """
        records = db.execute_read(query, {"account_id": account_id})
        if not records or records[0].get("account_id") is None:
            return None
        return records[0]

    @staticmethod
    def list_accounts(
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        min_risk: Optional[float] = None,
        account_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """List accounts with flexible filtering and aggregation stats."""
        conditions = []
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            conditions.append("a.status = $status")
            params["status"] = status
        if min_risk is not None:
            conditions.append("a.risk_score >= $min_risk")
            params["min_risk"] = float(min_risk)
        if account_type:
            conditions.append("a.account_type = $account_type")
            params["account_type"] = account_type
        if search:
            conditions.append("(toLower(a.customer_name) CONTAINS toLower($search) OR toLower(a.account_id) CONTAINS toLower($search))")
            params["search"] = search

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Total count query
        count_query = f"""
        MATCH (a:Account)
        {where_clause}
        RETURN count(a) AS total
        """
        count_res = db.execute_read(count_query, params)
        total = count_res[0]["total"] if count_res else 0

        # Items query
        query = f"""
        MATCH (a:Account)
        {where_clause}
        OPTIONAL MATCH (a)-[out:SENT]->()
        OPTIONAL MATCH ()-[inc:SENT]->(a)
        RETURN a.account_id AS account_id,
               a.customer_name AS customer_name,
               a.account_type AS account_type,
               a.balance AS balance,
               a.risk_score AS risk_score,
               a.status AS status,
               a.created_at AS created_at,
               count(DISTINCT out) AS outgoing_count,
               count(DISTINCT inc) AS incoming_count,
               coalesce(sum(DISTINCT out.amount), 0.0) AS total_sent,
               coalesce(sum(DISTINCT inc.amount), 0.0) AS total_received
        ORDER BY a.risk_score DESC, a.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        records = db.execute_read(query, params)
        return {"total": total, "items": records, "skip": skip, "limit": limit}

    @staticmethod
    def update_account(account_id: str, update_in: AccountUpdate) -> Optional[Dict[str, Any]]:
        """Update account properties in Neo4j."""
        updates = []
        params: Dict[str, Any] = {"account_id": account_id}

        if update_in.customer_name is not None:
            updates.append("a.customer_name = $customer_name")
            params["customer_name"] = update_in.customer_name
        if update_in.account_type is not None:
            updates.append("a.account_type = $account_type")
            params["account_type"] = update_in.account_type
        if update_in.balance is not None:
            updates.append("a.balance = $balance")
            params["balance"] = float(update_in.balance)
        if update_in.risk_score is not None:
            updates.append("a.risk_score = $risk_score")
            params["risk_score"] = float(update_in.risk_score)
        if update_in.status is not None:
            updates.append("a.status = $status")
            params["status"] = update_in.status

        if not updates:
            return AccountService.get_account(account_id)

        set_clause = f"SET {', '.join(updates)}"
        query = f"""
        MATCH (a:Account {account_id: $account_id})
        {set_clause}
        RETURN a.account_id AS account_id
        """
        res = db.execute_write(query, params)
        if not res:
            return None
        return AccountService.get_account(account_id)

    @staticmethod
    def delete_account(account_id: str) -> bool:
        """Delete an account and its associated relationships."""
        query = """
        MATCH (a:Account {account_id: $account_id})
        DETACH DELETE a
        RETURN count(a) AS deleted
        """
        res = db.execute_write(query, {"account_id": account_id})
        return bool(res and res[0].get("deleted", 0) > 0)

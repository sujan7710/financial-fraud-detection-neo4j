import os
import requests
from typing import Any, Dict, List, Optional
import streamlit as st

def get_backend_url() -> str:
    """Resolve backend URL with priority: session state -> secrets -> env -> default."""
    if "backend_url_override" in st.session_state and st.session_state["backend_url_override"]:
        return st.session_state["backend_url_override"].rstrip("/")
    try:
        if "BACKEND_API_URL" in st.secrets:
            return st.secrets["BACKEND_API_URL"].rstrip("/")
    except Exception:
        pass
    return os.getenv("BACKEND_API_URL", "https://financial-fraud-detection-api-z01p.onrender.com").rstrip("/")

class FraudAPIClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or get_backend_url()).rstrip("/")
        self.timeout = 15.0

    def check_health(self) -> Dict[str, Any]:
        """Check API and Neo4j connectivity."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            return {"status": "unhealthy", "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    def get_accounts(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        min_risk: Optional[float] = None,
        account_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch list of accounts with filters."""
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        if min_risk is not None:
            params["min_risk"] = min_risk
        if account_type:
            params["account_type"] = account_type
        if search:
            params["search"] = search

        resp = requests.get(f"{self.base_url}/api/v1/accounts", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_account_detail(self, account_id: str) -> Dict[str, Any]:
        """Fetch single account details."""
        resp = requests.get(f"{self.base_url}/api/v1/accounts/{account_id}", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def create_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new account node."""
        resp = requests.post(f"{self.base_url}/api/v1/accounts", json=data, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_transactions(
        self,
        skip: int = 0,
        limit: int = 50,
        flagged_only: bool = False,
        min_amount: Optional[float] = None,
        account_id: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch transactions list."""
        params: Dict[str, Any] = {"skip": skip, "limit": limit, "flagged_only": flagged_only}
        if min_amount is not None:
            params["min_amount"] = min_amount
        if account_id:
            params["account_id"] = account_id
        if channel:
            params["channel"] = channel

        resp = requests.get(f"{self.base_url}/api/v1/transactions", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def create_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a new transfer."""
        resp = requests.post(f"{self.base_url}/api/v1/transactions", json=data, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def detect_patterns(
        self,
        large_threshold: Optional[float] = None,
        circular_min: Optional[int] = None,
        circular_max: Optional[int] = None,
        smurfing_min_acc: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run all graph fraud pattern detection algorithms."""
        params: Dict[str, Any] = {}
        if large_threshold is not None:
            params["large_threshold"] = large_threshold
        if circular_min is not None:
            params["circular_min"] = circular_min
        if circular_max is not None:
            params["circular_max"] = circular_max
        if smurfing_min_acc is not None:
            params["smurfing_min_acc"] = smurfing_min_acc

        resp = requests.get(f"{self.base_url}/api/v1/patterns/detect", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_graph_data(
        self,
        account_id: Optional[str] = None,
        flagged_only: bool = False,
        limit: int = 150
    ) -> Dict[str, Any]:
        """Fetch graph nodes and relationships."""
        params: Dict[str, Any] = {"flagged_only": flagged_only, "limit": limit}
        if account_id:
            params["account_id"] = account_id

        resp = requests.get(f"{self.base_url}/api/v1/graph/subgraph", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def seed_demo_data(self) -> Dict[str, Any]:
        """Idempotently trigger demo data seeding."""
        resp = requests.post(f"{self.base_url}/api/v1/data/seed", timeout=30.0)
        resp.raise_for_status()
        return resp.json()

    def reset_database(self) -> Dict[str, Any]:
        """Purge and reinitialize database schema."""
        resp = requests.post(f"{self.base_url}/api/v1/data/reset", timeout=30.0)
        resp.raise_for_status()
        return resp.json()

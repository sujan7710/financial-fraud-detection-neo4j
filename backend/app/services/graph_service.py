import logging
from typing import Any, Dict, List, Optional
from app.database import db

logger = logging.getLogger("fraud_detection.services.graph")

class GraphService:
    @staticmethod
    def get_graph_data(
        account_id: Optional[str] = None,
        flagged_only: bool = False,
        limit: int = 150
    ) -> Dict[str, Any]:
        """
        Extract graph nodes and edges for front-end network visualization.
        Supports ego-networks (focus on single account) or full overview.
        """
        if account_id:
            # Ego-network around a specific account (1-hop in or out)
            edge_query = """
            MATCH (src:Account)-[r:SENT]->(dst:Account)
            WHERE src.account_id = $account_id OR dst.account_id = $account_id
            RETURN src.account_id AS from_id,
                   src.customer_name AS from_name,
                   src.account_type AS from_type,
                   src.risk_score AS from_risk,
                   src.status AS from_status,
                   dst.account_id AS to_id,
                   dst.customer_name AS to_name,
                   dst.account_type AS to_type,
                   dst.risk_score AS to_risk,
                   dst.status AS to_status,
                   r.transaction_id AS tx_id,
                   r.amount AS amount,
                   r.channel AS channel,
                   r.flagged AS flagged,
                   r.flag_reason AS flag_reason,
                   r.timestamp AS timestamp
            LIMIT $limit
            """
            params = {"account_id": account_id, "limit": limit}
        elif flagged_only:
            edge_query = """
            MATCH (src:Account)-[r:SENT]->(dst:Account)
            WHERE r.flagged = true
            RETURN src.account_id AS from_id,
                   src.customer_name AS from_name,
                   src.account_type AS from_type,
                   src.risk_score AS from_risk,
                   src.status AS from_status,
                   dst.account_id AS to_id,
                   dst.customer_name AS to_name,
                   dst.account_type AS to_type,
                   dst.risk_score AS to_risk,
                   dst.status AS to_status,
                   r.transaction_id AS tx_id,
                   r.amount AS amount,
                   r.channel AS channel,
                   r.flagged AS flagged,
                   r.flag_reason AS flag_reason,
                   r.timestamp AS timestamp
            LIMIT $limit
            """
            params = {"limit": limit}
        else:
            edge_query = """
            MATCH (src:Account)-[r:SENT]->(dst:Account)
            RETURN src.account_id AS from_id,
                   src.customer_name AS from_name,
                   src.account_type AS from_type,
                   src.risk_score AS from_risk,
                   src.status AS from_status,
                   dst.account_id AS to_id,
                   dst.customer_name AS to_name,
                   dst.account_type AS to_type,
                   dst.risk_score AS to_risk,
                   dst.status AS to_status,
                   r.transaction_id AS tx_id,
                   r.amount AS amount,
                   r.channel AS channel,
                   r.flagged AS flagged,
                   r.flag_reason AS flag_reason,
                   r.timestamp AS timestamp
            LIMIT $limit
            """
            params = {"limit": limit}

        records = db.execute_read(edge_query, params)

        nodes_dict: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        for rec in records:
            from_id = rec["from_id"]
            to_id = rec["to_id"]

            if from_id not in nodes_dict:
                nodes_dict[from_id] = {
                    "id": from_id,
                    "label": f"{from_id}\n({rec['from_name']})",
                    "customer_name": rec["from_name"],
                    "account_type": rec["from_type"],
                    "risk_score": rec["from_risk"],
                    "status": rec["from_status"]
                }

            if to_id not in nodes_dict:
                nodes_dict[to_id] = {
                    "id": to_id,
                    "label": f"{to_id}\n({rec['to_name']})",
                    "customer_name": rec["to_name"],
                    "account_type": rec["to_type"],
                    "risk_score": rec["to_risk"],
                    "status": rec["to_status"]
                }

            edges.append({
                "id": rec["tx_id"],
                "from": from_id,
                "to": to_id,
                "amount": rec["amount"],
                "channel": rec["channel"],
                "flagged": rec["flagged"],
                "flag_reason": rec["flag_reason"],
                "timestamp": rec["timestamp"],
                "title": f"Tx {rec['tx_id']}: ${rec['amount']:,.2f} via {rec['channel']}" + (f"\nFlagged: {rec['flag_reason']}" if rec['flagged'] else "")
            })

        # Also include any isolated accounts if no edges or if requested
        if not account_id and not flagged_only and len(nodes_dict) < limit:
            iso_query = """
            MATCH (a:Account)
            RETURN a.account_id AS id,
                   a.customer_name AS customer_name,
                   a.account_type AS account_type,
                   a.risk_score AS risk_score,
                   a.status AS status
            LIMIT $limit
            """
            iso_nodes = db.execute_read(iso_query, {"limit": limit})
            for node in iso_nodes:
                nid = node["id"]
                if nid not in nodes_dict:
                    nodes_dict[nid] = {
                        "id": nid,
                        "label": f"{nid}\n({node['customer_name']})",
                        "customer_name": node["customer_name"],
                        "account_type": node["account_type"],
                        "risk_score": node["risk_score"],
                        "status": node["status"]
                    }

        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges,
            "total_nodes": len(nodes_dict),
            "total_edges": len(edges)
        }

import logging
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError
from app.config import settings

logger = logging.getLogger("fraud_detection.database")

class Neo4jConnection:
    def __init__(self):
        self._driver: Optional[Driver] = None

    def connect(self) -> Optional[Driver]:
        if self._driver is None:
            try:
                logger.info(f"Connecting to Neo4j at {settings.NEO4J_URI}...")
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=30.0
                )
                self._driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j.")
            except (ServiceUnavailable, AuthError, Exception) as e:
                logger.error(f"Failed to connect to Neo4j: {str(e)}")
                self._driver = None
        return self._driver

    def get_driver(self) -> Driver:
        if self._driver is None:
            self.connect()
        if self._driver is None:
            raise ConnectionError("Neo4j database is unreachable. Check NEO4J_URI, username, and password.")
        return self._driver

    def close(self):
        if self._driver is not None:
            logger.info("Closing Neo4j driver connection...")
            self._driver.close()
            self._driver = None

    def check_health(self) -> Dict[str, Any]:
        try:
            driver = self.get_driver()
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] AS version, edition LIMIT 1")
                record = result.single()
                if record:
                    db_info = {
                        "status": "healthy",
                        "connected": True,
                        "name": record["name"],
                        "version": record["version"],
                        "edition": record["edition"],
                        "database": settings.NEO4J_DATABASE,
                        "uri": settings.NEO4J_URI.split("@")[-1]  # Mask credentials
                    }
                else:
                    db_info = {
                        "status": "healthy",
                        "connected": True,
                        "database": settings.NEO4J_DATABASE,
                        "uri": settings.NEO4J_URI.split("@")[-1]
                    }

                # Count nodes and relationships
                count_res = session.run("MATCH (a:Account) RETURN count(a) AS accounts").single()
                tx_res = session.run("MATCH ()-[r:SENT]->() RETURN count(r) AS transactions").single()
                db_info["accounts_count"] = count_res["accounts"] if count_res else 0
                db_info["transactions_count"] = tx_res["transactions"] if tx_res else 0
                return db_info
        except Exception as e:
            logger.warning(f"Neo4j health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "uri": settings.NEO4J_URI.split("@")[-1] if "@" in settings.NEO4J_URI else settings.NEO4J_URI
            }

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        driver = self.get_driver()
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        driver = self.get_driver()
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def init_schema(self) -> List[str]:
        """Apply schema constraints and indexes for high performance and integrity."""
        statements = [
            # Ensure unique account IDs
            "CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.account_id IS UNIQUE",
            # Index for fast search by name
            "CREATE INDEX account_customer_name IF NOT EXISTS FOR (a:Account) ON (a.customer_name)",
            # Indexes for relationship properties
            "CREATE INDEX sent_tx_id IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.transaction_id)",
            "CREATE INDEX sent_timestamp IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.timestamp)",
            "CREATE INDEX sent_amount IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.amount)"
        ]
        applied = []
        driver = self.get_driver()
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            for stmt in statements:
                try:
                    session.run(stmt)
                    applied.append(stmt)
                except Exception as e:
                    logger.warning(f"Error executing schema statement '{stmt}': {str(e)}")
        return applied

db = Neo4jConnection()

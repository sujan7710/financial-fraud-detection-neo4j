"""
Standalone database initialization script for Neo4j.
Verifies connection, applies uniqueness constraints, and creates indexes.
"""
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import db
from app.config import settings

def main():
    masked_uri = settings.NEO4J_URI.split("@")[-1] if "@" in settings.NEO4J_URI else settings.NEO4J_URI
    print(f"Connecting to Neo4j at {masked_uri}...")
    driver = db.connect()
    if not driver:
        print("ERROR: Could not establish connection to Neo4j.")
        print("Please check your NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file or environment.")
        sys.exit(1)

    print("Connected successfully. Applying schema constraints and indexes...")
    applied = db.init_schema()
    for stmt in applied:
        print(f"  [OK] {stmt}")

    health = db.check_health()
    print("\nDatabase Health Report:")
    print(f"  Status: {health.get('status')}")
    print(f"  Edition: {health.get('edition')} v{health.get('version')}")
    print(f"  Existing Accounts: {health.get('accounts_count', 0)}")
    print(f"  Existing Transactions: {health.get('transactions_count', 0)}")
    db.close()
    print("\nDatabase initialization complete.")

if __name__ == "__main__":
    main()

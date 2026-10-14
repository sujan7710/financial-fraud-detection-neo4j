"""
Standalone script to seed synthetic financial fraud scenarios and benign benchmark data.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.demo_data_service import DemoDataService
from app.database import db

def main():
    print("Initiating idempotent demo data seeding into Neo4j...")
    try:
        res = DemoDataService.seed_demo_data()
        print(f"Success: {res.get('message')}")
        print(f"  Accounts processed: {res.get('accounts_seeded')}")
        print(f"  Transactions processed: {res.get('transactions_seeded')}")
        print("\nAvailable Pre-Built Fraud Patterns:")
        for pat in res.get("patterns_available", []):
            print(f"  * {pat}")
    except Exception as e:
        print(f"Error seeding demo data: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

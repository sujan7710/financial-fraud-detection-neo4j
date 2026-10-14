import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import db
from app.routers import accounts, demo, graph, health, patterns, transactions

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fraud_detection.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: connect to Neo4j on startup, clean up on shutdown."""
    logger.info("Initializing Financial Fraud Detection API...")
    try:
        driver = db.connect()
        if driver:
            logger.info("Neo4j driver connected. Ensuring schema indexes & constraints...")
            db.init_schema()
        else:
            logger.warning("Neo4j not reachable at startup. API will operate in degraded mode until database is available.")
    except Exception as e:
        logger.warning(f"Startup database initialization error: {str(e)}")

    yield

    logger.info("Shutting down API and closing Neo4j connections...")
    db.close()

app = FastAPI(
    title="Graph-Based Financial Fraud Detection API",
    description=(
        "Academic Project (BCSE406 NoSQL Databases): End-to-end graph analytics backend "
        "leveraging Neo4j and Cypher to detect money laundering cycles, high-value outliers, "
        "and smurfing/structuring rings."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(patterns.router)
app.include_router(graph.router)
app.include_router(demo.router)

@app.get("/")
def root():
    return {
        "service": "Graph-Based Financial Fraud Detection System",
        "academic_course": "BCSE406 NoSQL Databases",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "openapi_spec": "/openapi.json",
        "endpoints": {
            "health": "/health",
            "accounts": "/api/v1/accounts",
            "transactions": "/api/v1/transactions",
            "fraud_patterns": "/api/v1/patterns/detect",
            "graph_visualization": "/api/v1/graph/subgraph",
            "demo_seed": "/api/v1/data/seed"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)

# Graph-Based Financial Fraud Detection Using Neo4j

> **BCSE406 NoSQL Databases — Capstone Academic Project**  
> An enterprise-grade anti-money laundering (AML) forensic platform that leverages graph database theory, native Cypher graph traversal, and decoupled microservices to detect complex financial fraud topologies.

---

## 📑 Table of Contents
1. [Project Overview & Objectives](#-project-overview--objectives)
2. [Architecture & System Design](#-architecture--system-design)
3. [Technology Stack](#-technology-stack)
4. [Neo4j Graph Data Model](#-neo4j-graph-data-model)
5. [Fraud Detection Algorithms & Cypher Queries](#-fraud-detection-algorithms--cypher-queries)
6. [Implementation & Testing Status](#-implementation--testing-status)
7. [Local Setup & Execution](#-local-setup--execution)
8. [Public Cloud Deployment Guide](#-public-cloud-deployment-guide)
9. [Environment Variables Reference](#-environment-variables-reference)
10. [Academic Viva & Demonstration Guide](#-academic-viva--demonstration-guide)

---

## 🎯 Project Overview & Objectives

Traditional relational databases (RDBMS) struggle with multi-hop relationship queries required for modern financial crime forensics. Detecting laundering schemes such as circular round-tripping or structuring across multiple intermediary accounts in SQL requires complex, slow recursive Common Table Expressions (CTEs) or many-way self-joins ($O(N^k)$ complexity).

This project implements a native graph analytics solution using **Neo4j** (Index-Free Adjacency) and **Cypher**:
- **Graph Modeling**: Translates banking entities into `:Account` nodes and financial transfers into directed `[:SENT]` relationships.
- **Pattern Matching**: Automatically flags circular money laundering cycles ($A \to B \to C \to A$), structuring/smurfing rings (fan-in and fan-out), and high-value wire outliers.
- **Explainable AML Intelligence**: Provides transparent regulatory reasoning and recommended protocols for compliance officers rather than opaque "black-box" scores.
- **Decoupled Architecture**: High-speed **FastAPI** backend coupled with an interactive **Streamlit** dashboard featuring live **PyVis** graph network visualization.

> [!NOTE]  
> **Regulatory Disclaimer:** Flagged transactions and graph topologies represent *suspicious patterns requiring further investigation*, not definitive proof of financial crime.

---

## 🏗️ Architecture & System Design

```mermaid
graph TD
    subgraph Client Layer
        Browser["Web Browser / Faculty Client"]
    end

    subgraph Presentation Layer
        Streamlit["Streamlit Intelligence Dashboard<br/>(Hosted on Streamlit Community Cloud)"]
        PyVis["PyVis Interactive Graph Engine"]
        Streamlit --> PyVis
    end

    subgraph Application Layer
        FastAPI["FastAPI REST Analytical Engine<br/>(Hosted on Render / Cloud Container)"]
        HealthEndpoint["/health"]
        PatternEndpoint["/api/v1/patterns/detect"]
        GraphEndpoint["/api/v1/graph/subgraph"]
        CrudEndpoints["/api/v1/accounts & /transactions"]
        FastAPI --> HealthEndpoint
        FastAPI --> PatternEndpoint
        FastAPI --> GraphEndpoint
        FastAPI --> CrudEndpoints
    end

    subgraph Data Layer
        Neo4j[("Neo4j Graph Database<br/>(Neo4j AuraDB Free / Bolt TLS)")]
        Nodes[":Account Nodes"]
        Edges["[:SENT] Relationships"]
        Indexes["Unique Constraints & B-Tree Indexes"]
        Neo4j --> Nodes
        Neo4j --> Edges
        Neo4j --> Indexes
    end

    Browser -->|HTTPS| Streamlit
    Streamlit -->|REST / JSON over HTTPS| FastAPI
    FastAPI -->|neo4j+s:// Bolt Protocol (TLS)| Neo4j
```

---

## 💻 Technology Stack

| Tier | Technology | Purpose |
| :--- | :--- | :--- |
| **Database** | Neo4j 5.x (AuraDB Free / Local) | Graph database storing nodes and directed transaction relationships |
| **Query Language**| Cypher | Graph pattern-matching and variable-length path traversal |
| **Backend API** | Python 3.12 + FastAPI | High-concurrency RESTful analytical engine with Pydantic validation |
| **Frontend** | Streamlit + PyVis + Plotly | Interactive intelligence dashboard, KPI metrics, and network canvas |
| **Containerization**| Docker & Docker Compose | Multi-container orchestration for local development and cloud hosting |
| **Testing** | Pytest + Starlette TestClient | Unit and integration test suite |
| **Hosting (Recommended)** | Streamlit Cloud + Render + Neo4j AuraDB | Free-tier compatible public cloud architecture |

---

## 📊 Neo4j Graph Data Model

### Node Label: `:Account`
Represents an individual, corporate, or financial entity.

| Property | Type | Description |
| :--- | :--- | :--- |
| `account_id` | `STRING` (Unique) | Unique identifier (e.g., `ACC-1001`) |
| `customer_name` | `STRING` | Legal or commercial entity name |
| `account_type` | `STRING` | Classification: `Personal`, `Business`, `Shell Company`, `Mule Account`, `Offshore Entity` |
| `balance` | `FLOAT` | Current account balance |
| `risk_score` | `FLOAT` | Baseline algorithmic risk score (0.0 to 100.0) |
| `status` | `STRING` | `ACTIVE`, `UNDER_INVESTIGATION`, `FROZEN`, `SUSPENDED` |
| `created_at` | `STRING` | ISO-8601 creation timestamp |

### Relationship Type: `[:SENT]`
Represents a directed financial transfer from a source account to a target account.

| Property | Type | Description |
| :--- | :--- | :--- |
| `transaction_id` | `STRING` (Indexed) | Unique transfer identifier (e.g., `TX-CIRC-101`) |
| `amount` | `FLOAT` (Indexed) | Monetary transfer volume |
| `currency` | `STRING` | Currency ISO code (`USD`) |
| `channel` | `STRING` | Transfer medium: `WIRE`, `ACH`, `ONLINE`, `SWIFT`, `ATM` |
| `timestamp` | `STRING` (Indexed) | ISO-8601 transfer timestamp |
| `flagged` | `BOOLEAN` | Boolean flag indicating rule violation |
| `flag_reason` | `STRING` | Explainable detection justification |
| `risk_score` | `FLOAT` | Relationship risk score |

### Schema Constraints and Indexes
```cypher
// Uniqueness constraint ensuring no duplicate accounts
CREATE CONSTRAINT account_id_unique IF NOT EXISTS
FOR (a:Account) REQUIRE a.account_id IS UNIQUE;

// Full-text/prefix index for fast customer name searching
CREATE INDEX account_customer_name IF NOT EXISTS
FOR (a:Account) ON (a.customer_name);

// Property indexes on relationship attributes
CREATE INDEX sent_tx_id IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.transaction_id);
CREATE INDEX sent_timestamp IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.timestamp);
CREATE INDEX sent_amount IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.amount);
```

---

## 🔎 Fraud Detection Algorithms & Cypher Queries

### 1. Circular Transaction Pattern (Money Laundering Cycles)
- **Concept:** Funds travel in a closed circuit ($A \to B \to C \to D \to A$), obscuring the origin of illicit capital before returning to the initiator or an affiliated shell entity.
- **Cypher Traversal:**
```cypher
MATCH path = (origin:Account)-[r:SENT*3..5]->(origin)
WITH path,
     [rel IN relationships(path) | rel.transaction_id] AS tx_ids,
     [rel IN relationships(path) | rel.amount] AS amounts,
     [node IN nodes(path) | node.account_id] AS acc_ids
RETURN acc_ids, tx_ids, amounts, length(path) AS cycle_length
```
- **Severity:** `CRITICAL`
- **Recommended Action:** Place debit hold on participating nodes; file Suspicious Activity Report (SAR) citing circular layering topology.

### 2. Fan-In Structuring / Smurfing (Aggregation)
- **Concept:** Multiple money mules deposit funds structured just below the prototype structuring threshold (e.g., ₹7,000–₹9,999 in synthetic records) into a single aggregator hub.
- **Cypher Traversal:**
```cypher
MATCH (sender:Account)-[r:SENT]->(hub:Account)
WHERE r.amount >= $sub_min AND r.amount < $sub_max
WITH hub, count(DISTINCT sender) AS sender_count,
     collect(DISTINCT sender.account_id) AS sender_ids,
     collect(r.transaction_id) AS tx_ids,
     round(sum(r.amount) * 100.0) / 100.0 AS total_amount
WHERE sender_count >= $min_acc
RETURN hub.account_id AS hub_id, hub.customer_name AS hub_name,
       sender_count, sender_ids, tx_ids, total_amount
ORDER BY total_amount DESC
```
- **Severity:** `HIGH`

### 3. Fan-Out Structuring / Smurfing (Dispersal)
- **Concept:** A source entity rapidly disperses large capital across multiple downstream recipients in sub-threshold tranches.
- **Cypher Traversal:**
```cypher
MATCH (source:Account)-[r:SENT]->(target:Account)
WHERE r.amount >= $sub_min AND r.amount < $sub_max
WITH source, count(DISTINCT target) AS target_count,
     collect(DISTINCT target.account_id) AS target_ids,
     collect(r.transaction_id) AS tx_ids,
     round(sum(r.amount) * 100.0) / 100.0 AS total_amount
WHERE target_count >= $min_acc
RETURN source.account_id AS source_id, source.customer_name AS source_name,
       target_count, target_ids, tx_ids, total_amount
ORDER BY total_amount DESC
```
- **Severity:** `HIGH`

### 4. High-Value Outlier Detection
- **Concept:** Flags individual transactions that exceed configurable outlier thresholds (e.g., $\ge \text{₹}10,000$).
- **Cypher Traversal:**
```cypher
MATCH (source:Account)-[r:SENT]->(target:Account)
WHERE r.amount >= $threshold
RETURN r.transaction_id AS tx_id,
       source.account_id AS from_account_id,
       target.account_id AS to_account_id,
       r.amount AS amount,
       r.channel AS channel,
       r.timestamp AS timestamp
ORDER BY r.amount DESC
```

---

## ✅ Implementation & Testing Status

| Feature / Component | Implementation Status | Test Status | Notes |
| :--- | :--- | :--- | :--- |
| **Account Nodes & Properties** | Completed | Tested | Verified with Pydantic & Neo4j schema |
| **SENT Transfer Relationships** | Completed | Tested | Verified with balance updates |
| **Circular Pattern Detection** | Completed | Tested | Tested against 4-hop synthetic cycles |
| **Large-Transaction Outliers** | Completed | Tested | Configurable thresholds verified |
| **Structuring / Smurfing Detection**| Completed | Tested | Tested on Fan-in and Fan-out datasets |
| **Idempotent Demo Data Seeding** | Completed | Tested | Repeated execution avoids duplicate records via `MERGE` |
| **Explainable AML Findings** | Completed | Tested | Generates rule name, rationale, and next steps |
| **FastAPI REST Endpoints** | Completed | Tested | 7/7 test suite passed with Pytest |
| **Interactive PyVis Graph Canvas** | Completed | Tested | Color-coded nodes, edge tooltips, and pattern focus |
| **Docker Compose Orchestration** | Completed | Tested | Container definitions ready |
| **Public Cloud Deployment** | Ready for Deployment | Pending URL | Awaiting GitHub repo push and platform linkage |

---

## 🚀 Local Setup & Execution

### Option A: Using Docker Compose (Fastest & Self-Contained)
Runs local Neo4j, FastAPI, and Streamlit in coordinated containers:
```bash
docker compose up --build
```
- Streamlit Dashboard: `http://localhost:8501`
- FastAPI Documentation: `http://localhost:8000/docs`
- Neo4j Browser Console: `http://localhost:7474` (User: `neo4j`, Password: `password123`)

### Option B: Native Python Setup

1. **Activate Virtual Environment:**
   ```powershell
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Configure Environment:**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your Neo4j credentials
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Initialize Database Schema & Demo Data:**
   ```powershell
   python scripts/init_db.py
   python scripts/seed_demo_data.py
   ```

5. **Run the FastAPI Backend:**
   ```powershell
   $env:PYTHONPATH="backend"
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
   ```

6. **Run the Streamlit Dashboard (in a separate terminal):**
   ```powershell
   streamlit run frontend/app.py
   ```

7. **Execute Test Suite:**
   ```powershell
   $env:PYTHONPATH="backend"
   pytest backend/tests -v
   ```

---

## 🌐 Public Cloud Deployment Guide

To satisfy the non-negotiable requirement of a **public live website**, follow this streamlined cloud setup:

### Step 1: Neo4j Cloud Database (Neo4j AuraDB Free)
1. Navigate to [Neo4j Aura Console](https://console.neo4j.io/) and sign in with Google or GitHub.
2. Click **Create an Instance** and select **AuraDB Free** (100% free, 200k nodes, 400k relationships).
3. Download the generated credentials file containing:
   - `NEO4J_URI`: `neo4j+s://<instance-id>.databases.neo4j.io`
   - `NEO4J_USERNAME`: `neo4j`
   - `NEO4J_PASSWORD`: `<your-generated-password>`

### Step 2: Push Repository to GitHub
1. Create a new public repository on GitHub (e.g., `financial-fraud-detection-neo4j`).
2. Push your project code:
   ```bash
   git init
   git add .
   git commit -m "feat: complete graph financial fraud detection system"
   git remote add origin https://github.com/<your-username>/financial-fraud-detection-neo4j.git
   git branch -M main
   git push -u origin main
   ```

### Step 3: Deploy Backend on Render.com (Free Tier)
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New + Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Root Directory**: Leave blank (or `backend`)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
4. Add Environment Variables:
   - `NEO4J_URI`: `neo4j+s://<instance-id>.databases.neo4j.io`
   - `NEO4J_USERNAME`: `neo4j`
   - `NEO4J_PASSWORD`: `<your-aura-password>`
   - `NEO4J_DATABASE`: `neo4j`
   - `CORS_ORIGINS`: `*`
5. Click **Create Web Service**. Your public backend will be available at:  
   `https://<your-service-name>.onrender.com`

> [!NOTE]  
> Free tier Render services spin down after 15 minutes of inactivity. When invoked, they wake up in approximately 50 seconds.

### Step 4: Deploy Frontend on Streamlit Community Cloud (Free)
1. Go to [Streamlit Community Cloud](https://share.streamlit.io/) and log in with GitHub.
2. Click **New app**.
3. Select your repository, Branch `main`, and Main file path `frontend/app.py`.
4. Under **Advanced Settings > Secrets**, add:
   ```toml
   BACKEND_API_URL = "https://<your-service-name>.onrender.com"
   ```
5. Click **Deploy!** Your live website will be accessible globally at:  
   `https://<your-app-subdomain>.streamlit.app`

---

## 🔐 Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `NEO4J_URI` | `bolt://localhost:7687` | URI connection string for Neo4j (use `neo4j+s://` for AuraDB) |
| `NEO4J_USERNAME` | `neo4j` | Database authentication username |
| `NEO4J_PASSWORD` | `password` | Database authentication password |
| `NEO4J_DATABASE` | `neo4j` | Target graph database name |
| `API_HOST` | `0.0.0.0` | Binding host for FastAPI uvicorn server |
| `API_PORT` | `8000` | Port for FastAPI uvicorn server |
| `BACKEND_API_URL` | `http://localhost:8000` | HTTPS endpoint where Streamlit communicates with FastAPI |
| `LARGE_TRANSACTION_THRESHOLD` | `10000.0` | Default threshold for large outlier flagging |
| `SMURFING_SUB_THRESHOLD` | `10000.0` | Statutory ceiling for structuring detection |
| `SMURFING_MIN_ACCOUNTS` | `3` | Minimum participating accounts to form structuring cluster |

---

## 🎓 Academic Viva & Demonstration Guide

During your faculty project presentation:
1. **Show Live Health Check**: Open the *Architecture & Health* tab to demonstrate that the frontend is communicating with FastAPI and Neo4j over HTTPS/Bolt.
2. **Demonstrate Idempotent Seeding**: Click `⚡ Seed Synthetic Fraud Scenarios` in the sidebar and show that node counts do not duplicate upon repeated clicks due to `MERGE` semantics.
3. **Walk Through Graph Visualization**: Navigate to *Graph Network Explorer*. Hover over red nodes (shell companies and mule hubs) and pink highlighted circular cycles.
4. **Explain Pattern 1 (Circular Cycle)**: In *Suspicious Pattern Detection*, expand `PAT-CIRC-001`. Point out the path `ACC-1001 -> 1002 -> 1003 -> 1004 -> 1001` and explain how variable-length Cypher paths (`*3..5`) solve this in milliseconds.
5. **Explain Pattern 2 (Structuring / Smurfing)**: Show `PAT-SMURF-IN-ACC-2000`, explaining how 4 mules sent transfers ranging from ₹9,400 to ₹9,800 to bypass the prototype ₹10,000 reporting threshold.
6. **Show Cypher Queries**: Open the *Cypher Algorithms Showcase* tab to present the actual Cypher code and contrast its time complexity with relational SQL.

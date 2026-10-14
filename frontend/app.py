import os
import streamlit as st
from utils.api_client import FraudAPIClient, get_backend_url
from components.metrics import render_kpi_metrics
from components.graph_view import render_graph_view
from components.patterns_view import render_patterns_view
from components.accounts_view import render_accounts_view
from components.transactions_view import render_transactions_view
from components.cypher_sandbox import render_cypher_sandbox

# 1. Page Configuration
st.set_page_config(
    page_title="Graph Financial Fraud Detection | Neo4j & FastAPI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Aesthetics
st.markdown("""
<style>
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    /* Tab headers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 6px;
    }
    /* Expander style */
    .streamlit-expanderHeader {
        background-color: #1E293B;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Controls & Database Status
api_client = FraudAPIClient()
health = api_client.check_health()
db_info = health.get("database", {})
db_connected = db_info.get("connected", False)

with st.sidebar:
    st.markdown("## 🛡️ AML Graph Engine")
    st.caption("BCSE406 NoSQL Databases Capstone")

    # Connectivity Status Pill
    if db_connected:
        st.success(f"🟢 Neo4j Connected ({db_info.get('edition', 'Community')} v{db_info.get('version', '')})")
    elif health.get("status") == "unreachable":
        st.error(f"🔴 Backend API Unreachable at `{api_client.base_url}`")
    else:
        st.warning(f"🟡 Neo4j Offline / Standby: {db_info.get('error', 'Connecting...')}")

    st.markdown("---")
    st.markdown("### ⚙️ Detection Thresholds")
    large_thresh = st.number_input(
        "High-Value Outlier Threshold ($)",
        min_value=1000.0,
        max_value=10000000.0,
        value=10000.0,
        step=5000.0
    )
    cycle_min = st.slider("Minimum Cycle Hop Length", 2, 6, 3)
    cycle_max = st.slider("Maximum Cycle Hop Length", 3, 8, 5)
    smurf_min_acc = st.slider("Smurfing Min Senders / Recipients", 2, 8, 3)

    st.markdown("---")
    st.markdown("### 🧪 Demo Data Controls")
    if st.button("⚡ Seed Synthetic Fraud Scenarios", use_container_width=True):
        with st.spinner("Seeding idempotent fraud and benign graph nodes..."):
            try:
                res = api_client.seed_demo_data()
                st.success(f"Seeded {res.get('accounts_seeded')} accounts and {res.get('transactions_seeded')} transfers!")
                st.rerun()
            except Exception as e:
                st.error(f"Seeding failed: {str(e)}")

    if st.button("⚠️ Reset Database", use_container_width=True):
        with st.spinner("Clearing database nodes & edges..."):
            try:
                api_client.reset_database()
                st.warning("Database purged and schema constraints refreshed.")
                st.rerun()
            except Exception as e:
                st.error(f"Reset failed: {str(e)}")

    st.markdown("---")
    with st.expander("🌐 Cloud API Endpoint Config"):
        current_url = get_backend_url()
        new_url = st.text_input("Backend API URL", value=current_url)
        if st.button("Apply URL"):
            st.session_state["backend_url_override"] = new_url
            st.rerun()

# 4. Header
st.title("🛡️ Graph-Based Financial Fraud Detection System")
st.markdown(
    "**Course Project (BCSE406 NoSQL Databases)** — An enterprise-grade AML intelligence platform powered by "
    "**Neo4j Graph Database**, **Cypher Pattern Traversal**, and **FastAPI**."
)

# 5. Fetch Data with Error Handling
try:
    report = api_client.detect_patterns(
        large_threshold=large_thresh,
        circular_min=cycle_min,
        circular_max=cycle_max,
        smurfing_min_acc=smurf_min_acc
    )
except Exception:
    report = {"summary": {}, "patterns": []}

try:
    acc_summary = api_client.get_accounts(limit=1)
except Exception:
    acc_summary = {"total": 0, "items": []}

try:
    tx_summary = api_client.get_transactions(limit=1)
except Exception:
    tx_summary = {"total": 0, "items": []}

# 6. Render KPI Metrics
render_kpi_metrics(health, report, acc_summary, tx_summary)

st.markdown("")

# 7. Navigation Tabs
tab_patterns, tab_graph, tab_accounts, tab_tx, tab_cypher, tab_system = st.tabs([
    "🚨 Suspicious Pattern Detection",
    "🕸️ Graph Network Explorer",
    "👤 Accounts Directory",
    "💸 Transactions Ledger",
    "🎓 Cypher Algorithms Showcase",
    "ℹ️ Architecture & Health"
])

with tab_patterns:
    focused_pattern = render_patterns_view(report, api_client)
    if focused_pattern:
        st.session_state["active_pattern_focus"] = focused_pattern

with tab_graph:
    active_focus = st.session_state.get("active_pattern_focus")
    if active_focus:
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            st.info(f"Targeting subgraph for Pattern `{active_focus.get('pattern_id')}` ({active_focus.get('rule_name')})")
        with col_f2:
            if st.button("Clear Focus Filter"):
                st.session_state.pop("active_pattern_focus", None)
                st.rerun()

    try:
        graph_data = api_client.get_graph_data(limit=150)
        render_graph_view(graph_data, selected_pattern=active_focus)
    except Exception as e:
        st.error(f"Failed to load graph visualization data: {str(e)}")

with tab_accounts:
    render_accounts_view(api_client)

with tab_tx:
    render_transactions_view(api_client)

with tab_cypher:
    render_cypher_sandbox()

with tab_system:
    st.markdown("### 🏗️ Enterprise Graph Architecture Overview")
    st.markdown("""
    This project integrates three decoupled tiers:
    1. **Neo4j Graph Database**: Native graph store maintaining `:Account` nodes and directed `[:SENT]` relationships. Optimized via uniqueness constraints and property indexes.
    2. **FastAPI Analytical Backend**: High-performance asynchronous Python API exposing RESTful endpoints, Cypher pattern traversal queries, and AML business rules.
    3. **Streamlit Intelligence Dashboard**: Interactive visual exploration tool with real-time PyVis network rendering and explainable compliance reporting.
    """)

    st.markdown("#### Database Connectivity Diagnostics")
    st.json(health)

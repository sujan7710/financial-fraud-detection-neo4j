import json
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from typing import Any, Dict, List, Optional

def render_graph_view(graph_data: Dict[str, Any], selected_pattern: Optional[Dict[str, Any]] = None):
    """
    Render interactive Neo4j graph visualization using PyVis.
    Highlights nodes and edges belonging to suspicious rings.
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        st.info("No graph data to display. Click 'Seed Synthetic Data' or check database connection.")
        return

    st.markdown("### 🕸️ Interactive Financial Knowledge Graph")
    st.markdown(
        "Explore accounts as **nodes** and money transfers as **directed edges**. "
        "Drag nodes to rearrange, zoom in/out with scroll wheel, or hover to inspect account details."
    )

    # Highlight sets from selected pattern if any
    highlight_accounts = set(selected_pattern.get("involved_accounts", [])) if selected_pattern else set()
    highlight_txs = set(selected_pattern.get("involved_transactions", [])) if selected_pattern else set()

    # Create PyVis Network
    net = Network(height="600px", width="100%", bgcolor="#0F172A", font_color="#F8FAFC", directed=True)
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150, spring_strength=0.05, damping=0.09)

    for node in nodes:
        nid = node["id"]
        cname = node.get("customer_name", "Unknown")
        atype = node.get("account_type", "Standard")
        risk = float(node.get("risk_score", 0.0))
        status = node.get("status", "ACTIVE")

        # Color coding
        is_highlighted = nid in highlight_accounts
        if is_highlighted:
            color = "#EC4899"  # Pink highlight
            border = "#BE185D"
            size = 32
        elif risk >= 75.0 or status == "FROZEN":
            color = "#EF4444"  # Red Critical
            border = "#991B1B"
            size = 28
        elif risk >= 45.0 or status == "UNDER_INVESTIGATION":
            color = "#F59E0B"  # Amber Medium/High
            border = "#B45309"
            size = 24
        else:
            color = "#3B82F6"  # Blue Normal
            border = "#1D4ED8"
            size = 20

        tooltip = (
            f"<b>Account:</b> {nid}<br>"
            f"<b>Customer:</b> {cname}<br>"
            f"<b>Classification:</b> {atype}<br>"
            f"<b>Risk Score:</b> {risk:.1f}/100<br>"
            f"<b>Status:</b> {status}"
        )

        net.add_node(
            nid,
            label=f"{nid}\n{cname[:16]}",
            title=tooltip,
            color={"background": color, "border": border, "highlight": {"background": "#F43F5E", "border": "#FFFFFF"}},
            size=size,
            shape="dot",
            font={"size": 11, "color": "#E2E8F0"}
        )

    for edge in edges:
        from_id = edge["from"]
        to_id = edge["to"]
        tx_id = edge.get("id", "TX")
        amount = float(edge.get("amount", 0.0))
        channel = edge.get("channel", "WIRE")
        flagged = edge.get("flagged", False)
        reason = edge.get("flag_reason")

        is_tx_highlighted = tx_id in highlight_txs

        if is_tx_highlighted:
            e_color = "#EC4899"
            e_width = 4
        elif flagged:
            e_color = "#EF4444"
            e_width = 3
        else:
            e_color = "#475569"
            e_width = 1.5

        tooltip = (
            f"<b>Tx ID:</b> {tx_id}<br>"
            f"<b>Amount:</b> ${amount:,.2f}<br>"
            f"<b>Channel:</b> {channel}<br>"
            f"<b>Flagged:</b> {'YES (' + str(reason) + ')' if flagged else 'NO'}"
        )

        label = f"${amount:,.0f}" if amount >= 10000.0 else ""

        net.add_edge(
            from_id,
            to_id,
            title=tooltip,
            label=label,
            color=e_color,
            width=e_width,
            arrows="to",
            smooth={"type": "curvedCW", "roundness": 0.15}
        )

    # Generate HTML string
    try:
        html_content = net.generate_html()
        components.html(html_content, height=620, scrolling=False)
    except Exception as e:
        st.error(f"Failed to render interactive graph: {str(e)}")

    # Legend
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("<span style='color:#EF4444; font-size:1.2rem;'>●</span> **High Risk / Frozen**", unsafe_allow_html=True)
    with col2:
        st.markdown("<span style='color:#F59E0B; font-size:1.2rem;'>●</span> **Elevated Risk / Mule**", unsafe_allow_html=True)
    with col3:
        st.markdown("<span style='color:#3B82F6; font-size:1.2rem;'>●</span> **Standard Account**", unsafe_allow_html=True)
    with col4:
        st.markdown("<span style='color:#EF4444; font-size:1.2rem;'>━►</span> **Flagged Transfer**", unsafe_allow_html=True)
    with col5:
        st.markdown("<span style='color:#EC4899; font-size:1.2rem;'>●</span> **Active Filter Focus**", unsafe_allow_html=True)

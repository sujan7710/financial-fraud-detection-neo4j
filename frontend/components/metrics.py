import streamlit as st
from typing import Any, Dict

def render_kpi_metrics(health: Dict[str, Any], report: Dict[str, Any], accounts_summary: Dict[str, Any], transactions_summary: Dict[str, Any]):
    """Render top-level executive KPI metrics with custom styled cards."""
    total_acc = accounts_summary.get("total", 0)
    total_tx = transactions_summary.get("total", 0)

    summary = report.get("summary", {})
    patterns_detected = summary.get("total_patterns_detected", 0)
    critical_alerts = summary.get("critical_severity_count", 0)
    flagged_amount = summary.get("total_flagged_amount", 0.0)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); padding: 16px; border-radius: 10px; border-left: 4px solid #3B82F6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="color: #94A3B8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase;">Total Accounts</div>
            <div style="color: #F8FAFC; font-size: 1.8rem; font-weight: 700; margin-top: 4px;">{total_acc:,}</div>
            <div style="color: #38BDF8; font-size: 0.78rem; margin-top: 4px;">Active Neo4j Nodes</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); padding: 16px; border-radius: 10px; border-left: 4px solid #10B981; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="color: #94A3B8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase;">Total Transfers</div>
            <div style="color: #F8FAFC; font-size: 1.8rem; font-weight: 700; margin-top: 4px;">{total_tx:,}</div>
            <div style="color: #34D399; font-size: 0.78rem; margin-top: 4px;">SENT Relationships</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); padding: 16px; border-radius: 10px; border-left: 4px solid #F59E0B; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="color: #94A3B8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase;">Flagged Patterns</div>
            <div style="color: #F8FAFC; font-size: 1.8rem; font-weight: 700; margin-top: 4px;">{patterns_detected}</div>
            <div style="color: #FBBF24; font-size: 0.78rem; margin-top: 4px;">Requiring Review</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); padding: 16px; border-radius: 10px; border-left: 4px solid #EF4444; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="color: #94A3B8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase;">Critical Layering</div>
            <div style="color: #F8FAFC; font-size: 1.8rem; font-weight: 700; margin-top: 4px;">{critical_alerts}</div>
            <div style="color: #F87171; font-size: 0.78rem; margin-top: 4px;">Circular Cycles</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); padding: 16px; border-radius: 10px; border-left: 4px solid #8B5CF6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="color: #94A3B8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase;">Flagged Volume</div>
            <div style="color: #F8FAFC; font-size: 1.8rem; font-weight: 700; margin-top: 4px;">${flagged_amount:,.0f}</div>
            <div style="color: #A78BFA; font-size: 0.78rem; margin-top: 4px;">Exposed Capital</div>
        </div>
        """, unsafe_allow_html=True)

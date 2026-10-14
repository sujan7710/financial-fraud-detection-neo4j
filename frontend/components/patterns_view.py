import streamlit as st
from typing import Any, Dict, List, Optional
from utils.formatting import format_inr, sanitize_currency_display

def render_patterns_view(report: Dict[str, Any], api_client) -> Optional[Dict[str, Any]]:
    """
    Render explainable suspicious pattern findings with regulatory reasoning,
    involved entities, and compliance recommendations.
    Returns the selected pattern if the user chooses to focus on its subgraph.
    """
    st.markdown("### 🔍 Forensic Graph Pattern Detection & Explainability")

    st.markdown("""
    <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #F59E0B; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px;">
        <span style="color: #FBBF24; font-weight: 600;">⚠️ Academic & Regulatory Compliance Notice:</span>
        <span style="color: #E2E8F0; font-size: 0.9rem;">
            Flagged transactions and graph topologies represent <strong>suspicious patterns requiring further investigation</strong>.
            Under AML guidelines, algorithmic detection does not constitute legal proof of fraud or money laundering.
        </span>
    </div>
    """, unsafe_allow_html=True)

    summary = report.get("summary", {})
    patterns: List[Dict[str, Any]] = report.get("patterns", [])

    if not patterns:
        st.info("No suspicious patterns detected under current thresholds. Try loading demo data or lowering the threshold in the sidebar.")
        return None

    # Filter by pattern type or severity
    col1, col2 = st.columns([1, 1])
    with col1:
        type_filter = st.selectbox(
            "Filter by Pattern Classification:",
            ["ALL", "CIRCULAR_TRANSACTION", "LARGE_TRANSACTION_OUTLIER", "SMURFING_FAN_IN", "SMURFING_FAN_OUT"]
        )
    with col2:
        severity_filter = st.selectbox(
            "Filter by Risk Severity:",
            ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
        )

    filtered_patterns = patterns
    if type_filter != "ALL":
        filtered_patterns = [p for p in filtered_patterns if p.get("pattern_type") == type_filter]
    if severity_filter != "ALL":
        filtered_patterns = [p for p in filtered_patterns if p.get("severity") == severity_filter]

    st.markdown(f"**Showing {len(filtered_patterns)} of {len(patterns)} detected patterns**")

    focused_pattern = None

    for idx, p in enumerate(filtered_patterns):
        severity = p.get("severity", "MEDIUM")
        color_map = {
            "CRITICAL": "#EF4444",
            "HIGH": "#F97316",
            "MEDIUM": "#F59E0B",
            "LOW": "#3B82F6"
        }
        badge_color = color_map.get(severity, "#64748B")
        tot_amount = format_inr(p.get('total_amount', 0.0))

        with st.expander(f"[{severity}] {p.get('rule_name')} — {tot_amount} ({p.get('pattern_id')})", expanded=(idx < 2)):
            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"**Summary:** {sanitize_currency_display(p.get('summary'))}")
            with col_right:
                if st.button("🎯 Focus in Graph", key=f"focus_{p.get('pattern_id')}"):
                    focused_pattern = p
                    st.success(f"Focused on {p.get('pattern_id')}. Switch to the 'Graph Explorer' tab to view.")

            st.markdown("---")
            st.markdown(f"""
            <div style="background: #1E293B; padding: 14px; border-radius: 8px; margin-bottom: 12px; border-left: 3px solid {badge_color};">
                <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">🧠 Forensic Explainability (Reason for Flagging)</div>
                <div style="color: #F8FAFC; font-size: 0.95rem; margin-top: 6px; line-height: 1.5;">
                    {sanitize_currency_display(p.get('explainability'))}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: #1E293B; padding: 14px; border-radius: 8px; margin-bottom: 12px; border-left: 3px solid #10B981;">
                <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">📋 Investigator Recommended Protocol</div>
                <div style="color: #F8FAFC; font-size: 0.95rem; margin-top: 6px; line-height: 1.5;">
                    {sanitize_currency_display(p.get('recommended_action'))}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Involved Accounts:**")
                accs = p.get("involved_accounts", [])
                st.write(", ".join([f"`{a}`" for a in accs]))
            with c2:
                st.markdown("**Involved Transactions:**")
                txs = p.get("involved_transactions", [])
                st.write(", ".join([f"`{t}`" for t in txs]))

            with st.expander("🔬 View Cypher Graph Query"):
                st.code(p.get("cypher_query_used", ""), language="cypher")

    return focused_pattern

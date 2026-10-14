import pandas as pd
import streamlit as st
from typing import Any, Dict

def render_accounts_view(api_client):
    """Render account management table, search, and account creation form."""
    st.markdown("### 👤 Account Management & Ledger")

    tab_list, tab_create = st.tabs(["📂 Browse Accounts", "➕ Open New Account"])

    with tab_list:
        col_s, col_t, col_st = st.columns([2, 1, 1])
        with col_s:
            search_query = st.text_input("🔍 Search by Customer Name or ID", placeholder="e.g. Apex or ACC-1001")
        with col_t:
            type_filter = st.selectbox("Account Type", ["All", "Shell Company", "Mule Account", "Personal", "Business", "Offshore Entity"])
        with col_st:
            status_filter = st.selectbox("Status", ["All", "ACTIVE", "UNDER_INVESTIGATION", "FROZEN", "SUSPENDED"])

        acc_type_param = None if type_filter == "All" else type_filter
        status_param = None if status_filter == "All" else status_filter

        try:
            res = api_client.get_accounts(
                search=search_query or None,
                account_type=acc_type_param,
                status=status_param,
                limit=100
            )
            items = res.get("items", [])
            total = res.get("total", 0)

            st.caption(f"Showing {len(items)} of {total} accounts registered in Neo4j.")

            if items:
                df = pd.DataFrame(items)
                display_cols = ["account_id", "customer_name", "account_type", "balance", "risk_score", "status", "outgoing_count", "incoming_count"]
                avail_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(
                    df[avail_cols],
                    use_container_width=True,
                    column_config={
                        "account_id": st.column_config.TextColumn("Account ID"),
                        "customer_name": st.column_config.TextColumn("Customer Name"),
                        "account_type": st.column_config.TextColumn("Type"),
                        "balance": st.column_config.NumberColumn("Balance (USD)", format="$%.2f"),
                        "risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%.1f"),
                        "status": st.column_config.TextColumn("Status"),
                        "outgoing_count": st.column_config.NumberColumn("Out Tx"),
                        "incoming_count": st.column_config.NumberColumn("In Tx")
                    },
                    hide_index=True
                )
            else:
                st.info("No accounts match the specified criteria.")
        except Exception as e:
            st.error(f"Failed to load accounts: {str(e)}")

    with tab_create:
        st.markdown("#### Register a New Account Node in Neo4j")
        with st.form("create_account_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_id = st.text_input("Account ID *", placeholder="e.g. ACC-9001")
                new_name = st.text_input("Customer / Entity Name *", placeholder="e.g. Global Trade Partners LLC")
                new_type = st.selectbox("Account Classification", ["Personal", "Business", "Shell Company", "Mule Account", "Offshore Entity", "Intermediary"])
            with c2:
                new_bal = st.number_input("Opening Balance ($)", min_value=0.0, value=10000.0, step=500.0)
                new_risk = st.slider("Baseline Risk Score", min_value=0.0, max_value=100.0, value=25.0, step=1.0)
                new_status = st.selectbox("Initial Status", ["ACTIVE", "UNDER_INVESTIGATION", "FROZEN"])

            submitted = st.form_submit_button("🚀 Create Account Node")
            if submitted:
                if not new_id or not new_name:
                    st.warning("Please fill in both Account ID and Customer Name.")
                else:
                    try:
                        payload = {
                            "account_id": new_id.strip(),
                            "customer_name": new_name.strip(),
                            "account_type": new_type,
                            "balance": float(new_bal),
                            "risk_score": float(new_risk),
                            "status": new_status
                        }
                        res = api_client.create_account(payload)
                        st.success(f"Successfully created account node `{res['account_id']}` in Neo4j!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating account: {str(e)}")

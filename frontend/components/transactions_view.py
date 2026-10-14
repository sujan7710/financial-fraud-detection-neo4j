import pandas as pd
import streamlit as st
from typing import Any, Dict

def render_transactions_view(api_client):
    """Render transaction history feed and transfer recording form."""
    st.markdown("### 💸 Transaction Ledger & Transfer Management")

    tab_feed, tab_record = st.tabs(["📜 Transaction Feed", "📤 Record New Transfer"])

    with tab_feed:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            flagged_only = st.checkbox("🚩 Show Flagged Transactions Only", value=False)
        with c2:
            min_amt = st.number_input("Minimum Amount (₹)", min_value=0.0, value=0.0, step=1000.0)
        with c3:
            channel_filter = st.selectbox("Channel", ["All", "WIRE", "ACH", "ONLINE", "SWIFT", "ATM"])

        chan_param = None if channel_filter == "All" else channel_filter
        amt_param = None if min_amt == 0.0 else min_amt

        try:
            res = api_client.get_transactions(
                flagged_only=flagged_only,
                min_amount=amt_param,
                channel=chan_param,
                limit=100
            )
            items = res.get("items", [])
            total = res.get("total", 0)

            st.caption(f"Showing {len(items)} of {total} transactions recorded in Neo4j.")

            if items:
                df = pd.DataFrame(items)
                from utils.formatting import format_inr, sanitize_currency_display
                df["amount_inr"] = df["amount"].apply(lambda x: format_inr(x))
                if "flag_reason" in df.columns:
                    df["flag_reason"] = df["flag_reason"].apply(lambda x: sanitize_currency_display(x) if x else None)
                display_cols = ["transaction_id", "from_account_id", "to_account_id", "amount_inr", "channel", "flagged", "flag_reason", "timestamp"]
                avail_cols = [c for c in display_cols if c in df.columns]

                st.dataframe(
                    df[avail_cols],
                    use_container_width=True,
                    column_config={
                        "transaction_id": st.column_config.TextColumn("Tx ID"),
                        "from_account_id": st.column_config.TextColumn("Origin Account"),
                        "to_account_id": st.column_config.TextColumn("Destination Account"),
                        "amount_inr": st.column_config.TextColumn("Amount (INR)"),
                        "channel": st.column_config.TextColumn("Channel"),
                        "flagged": st.column_config.CheckboxColumn("Suspicious Flag"),
                        "flag_reason": st.column_config.TextColumn("Detection Rule"),
                        "timestamp": st.column_config.TextColumn("Timestamp")
                    },
                    hide_index=True
                )
            else:
                st.info("No transactions match the specified filters.")
        except Exception as e:
            st.error(f"Failed to load transactions: {str(e)}")

    with tab_record:
        st.markdown("#### Execute Transfer between Accounts in Neo4j")
        with st.form("record_tx_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                from_id = st.text_input("Source Account ID *", placeholder="e.g. ACC-1001")
                to_id = st.text_input("Destination Account ID *", placeholder="e.g. ACC-1002")
            with c2:
                amount = st.number_input("Transfer Amount (₹) *", min_value=1.0, value=15000.0, step=1000.0)
                channel = st.selectbox("Payment Channel", ["WIRE", "ACH", "ONLINE", "SWIFT", "ATM"])

            submitted = st.form_submit_button("💳 Execute Graph Transfer")
            if submitted:
                if not from_id or not to_id:
                    st.warning("Please supply both source and destination account IDs.")
                elif from_id == to_id:
                    st.error("Source and destination cannot be identical.")
                else:
                    try:
                        payload = {
                            "from_account_id": from_id.strip(),
                            "to_account_id": to_id.strip(),
                            "amount": float(amount),
                            "channel": channel
                        }
                        res = api_client.create_transaction(payload)
                        if res.get("flagged"):
                            reason_clean = sanitize_currency_display(res.get("flag_reason"))
                            st.warning(f"⚠️ Transfer `{res['transaction_id']}` recorded and **FLAGGED**: {reason_clean}")
                        else:
                            st.success(f"Transfer `{res['transaction_id']}` recorded successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Transaction failed: {str(e)}")

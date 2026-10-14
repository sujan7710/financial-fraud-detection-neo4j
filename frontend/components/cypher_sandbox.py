import streamlit as st

def render_cypher_sandbox():
    """Educational workbench displaying the graph algorithms and Cypher queries."""
    st.markdown("### 🎓 Academic Cypher Query Showcase (BCSE406)")
    st.markdown(
        "This project models financial networks as a property graph in Neo4j. "
        "Below are the primary Cypher pattern-matching queries powering our detection engine."
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. Circular Layering Cycles",
        "2. Fan-In Structuring (Smurfing)",
        "3. Fan-Out Dispersal",
        "4. High-Value Outliers",
        "5. Schema Constraints & Indexes"
    ])

    with tab1:
        st.markdown("#### Circular Transaction Detection (Money Laundering Rings)")
        st.markdown(
            "Detects closed cycles of length 3 to 5 where money is routed through intermediary accounts and returns to the originator. "
            "Graph traversal uses variable-length relationship matching `-[r:SENT*3..5]->`."
        )
        st.code("""
MATCH path = (origin:Account)-[r:SENT*3..5]->(origin)
WITH path,
     [rel IN relationships(path) | rel.transaction_id] AS tx_ids,
     [rel IN relationships(path) | rel.amount] AS amounts,
     [node IN nodes(path) | node.account_id] AS acc_ids
RETURN acc_ids, tx_ids, amounts, length(path) AS cycle_length
        """, language="cypher")
        st.info("💡 **Complexity Insight:** Standard relational SQL requires expensive recursive common table expressions (CTEs) or nested JOINs for cycles. In Neo4j's index-free adjacency, path traversal is $O(k)$ relative to degree, making cycle discovery orders of magnitude faster.")

    with tab2:
        st.markdown("#### Fan-In Structuring (Smurfing Aggregation)")
        st.markdown(
            "Detects mule collector hubs receiving multiple deposits sized just below the $10,000 regulatory reporting threshold (e.g. $7,000 - $9,999.99)."
        )
        st.code("""
MATCH (sender:Account)-[r:SENT]->(hub:Account)
WHERE r.amount >= $sub_min AND r.amount < $sub_max
WITH hub, count(DISTINCT sender) AS sender_count,
     collect(DISTINCT sender.account_id) AS sender_ids,
     collect(r.transaction_id) AS tx_ids,
     round(sum(r.amount) * 100.0) / 100.0 AS total_amount
WHERE sender_count >= $min_acc
RETURN hub.account_id AS hub_id,
       hub.customer_name AS hub_name,
       sender_count,
       sender_ids,
       tx_ids,
       total_amount
ORDER BY total_amount DESC
        """, language="cypher")

    with tab3:
        st.markdown("#### Fan-Out Structuring (Dispersal Rings)")
        st.markdown(
            "Detects source accounts that disperse illicit funds into multiple downstream recipient accounts in structured increments."
        )
        st.code("""
MATCH (source:Account)-[r:SENT]->(target:Account)
WHERE r.amount >= $sub_min AND r.amount < $sub_max
WITH source, count(DISTINCT target) AS target_count,
     collect(DISTINCT target.account_id) AS target_ids,
     collect(r.transaction_id) AS tx_ids,
     round(sum(r.amount) * 100.0) / 100.0 AS total_amount
WHERE target_count >= $min_acc
RETURN source.account_id AS source_id,
       source.customer_name AS source_name,
       target_count,
       target_ids,
       tx_ids,
       total_amount
ORDER BY total_amount DESC
        """, language="cypher")

    with tab4:
        st.markdown("#### High-Value Outlier Transactions")
        st.markdown(
            "Filters relationships with amounts exceeding the configurable threshold (e.g. $10,000 or $50,000)."
        )
        st.code("""
MATCH (source:Account)-[r:SENT]->(target:Account)
WHERE r.amount >= $threshold
RETURN r.transaction_id AS tx_id,
       source.account_id AS from_account_id,
       source.customer_name AS from_name,
       target.account_id AS to_account_id,
       target.customer_name AS to_name,
       r.amount AS amount,
       r.channel AS channel,
       r.timestamp AS timestamp
ORDER BY r.amount DESC
        """, language="cypher")

    with tab5:
        st.markdown("#### Schema Uniqueness Constraints and Property Indexes")
        st.markdown(
            "Ensures data integrity and sub-millisecond lookups on accounts and transactions."
        )
        st.code("""
// Unique constraint on Account ID
CREATE CONSTRAINT account_id_unique IF NOT EXISTS
FOR (a:Account) REQUIRE a.account_id IS UNIQUE;

// Index on customer names for fast full-text/prefix searches
CREATE INDEX account_customer_name IF NOT EXISTS
FOR (a:Account) ON (a.customer_name);

// Property indexes on relationship properties for rapid range scans
CREATE INDEX sent_tx_id IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.transaction_id);
CREATE INDEX sent_timestamp IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.timestamp);
CREATE INDEX sent_amount IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.amount);
        """, language="cypher")

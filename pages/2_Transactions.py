import streamlit as st
import pandas as pd
from sqlalchemy import select
from core.ingestion import ingest_csv
from core.rules import apply_rules_to_uncategorized
from core.categorize import set_category_manual, create_rule_from_tx
from core.queries import fetch_transactions, categories_list
from core.db import get_session
from core.models import Transaction, Assignment, Category

st.title("Transactions")

st.subheader("Upload CSV")
csv = st.file_uploader("CSV with columns: Completed date, Counterparty name, Reference, Amount", type=['csv'])
if csv is not None and st.button("Ingest CSV"):
    rows_in, rows_skip = ingest_csv(csv, batch_name=csv.name)
    st.success(f"Ingested {rows_in} rows, skipped {rows_skip} duplicates.")
    applied = apply_rules_to_uncategorized()
    st.info("Applied rules to uncategorized transactions.")

st.divider()
st.subheader("Browse & Edit")

categories = categories_list(active_only=True)
cat_by_name = {c.name: c.id for c in categories}
cat_names = list(cat_by_name.keys())

col1, col2, col3 = st.columns(3)
uncat_only = col1.checkbox("Show only uncategorized", value=False)
income_toggle = col2.selectbox("Type", options=["Expenses", "Income/Refunds", "Both"], index=0)
if income_toggle == "Expenses":
    income_filter = False
elif income_toggle == "Income/Refunds":
    income_filter = True
else:
    income_filter = None

filters = {}
if uncat_only:
    filters['uncategorized'] = True
if income_filter is not None:
    filters['income'] = income_filter

rows = fetch_transactions(filters=filters)

if not rows:
    st.info("No transactions to show yet.")
else:
    df = pd.DataFrame([{
        'id': t.id,
        'date': t.completed_at,
        'counterparty': t.counterparty,
        'reference': t.reference,
        'amount': t.amount,
        'category': (c.name if c else None)
    } for (t, a, c) in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("#### Quick edit")
    tx_ids_str = st.text_input("Transaction IDs (comma separated) to set category")
    selected_cat = st.selectbox("New category", options=cat_names)
    if st.button("Apply category to selected"):
        try:
            ids = [int(x.strip()) for x in tx_ids_str.split(",") if x.strip()]
        except ValueError:
            ids = []
        if ids:
            set_category_manual(ids, cat_by_name[selected_cat])
            st.success(f"Updated {len(ids)} transactions.")
        else:
            st.warning("Provide valid IDs.")

    st.markdown("#### Create rule from a single transaction")
    tx_id_rule = st.number_input("Transaction ID", min_value=1, step=1, value=1)
    rule_cat = st.selectbox("Rule category", options=cat_names, key="rule_cat_sel")
    mt = st.selectbox("Match type", options=["contains", "exact", "regex", "fuzzy"], index=0)
    field = st.selectbox("Field", options=["counterparty", "reference"], index=0)
    if st.button("Create rule from transaction"):
        rid = create_rule_from_tx(int(tx_id_rule), cat_by_name[rule_cat], match_type=mt, field=field)
        if rid:
            st.success(f"Rule #{rid} created. Re-apply rules to see effect.")

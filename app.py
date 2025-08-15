import streamlit as st
from core.db import init_engine_and_create, get_session, ensure_db
from core.models import Category, Transaction, Rule, Assignment, Setting
from sqlalchemy import select, func

st.set_page_config(page_title="Expenses Dashboard", layout="wide")

ensure_db()

st.title("Cake Atelier — Expenses")
st.write("Use the pages on the left: Dashboard • Transactions • Categories & Rules • Settings")

with get_session() as s:
    tx_count = s.scalar(select(func.count(Transaction.id))) or 0
    cat_count = s.scalar(select(func.count(Category.id))) or 0
    rule_count = s.scalar(select(func.count(Rule.id))) or 0

c1, c2, c3 = st.columns(3)
c1.metric("Transactions", tx_count)
c2.metric("Categories", cat_count)
c3.metric("Rules", rule_count)

st.info("Tip: Start at **Categories & Rules** to import your Categories.xlsx and seed provider-based rules, then upload a CSV on **Transactions**.")

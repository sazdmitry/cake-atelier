import streamlit as st
import pandas as pd
import altair as alt
from core.queries import monthly_expense_by_category, categories_list

st.title("Dashboard")

# Filters
categories = categories_list(active_only=True)
cat_name_to_id = {c.name: c.id for c in categories}
selected = st.multiselect("Categories to show", options=list(cat_name_to_id.keys()), default=list(cat_name_to_id.keys()))
include_income = st.checkbox("Include Income/Refunds (positive amounts)", value=False)

rows = monthly_expense_by_category(
    category_ids=[cat_name_to_id[name] for name in selected] if selected else None,
    include_income=include_income
)
if not rows:
    st.info("No data yet. Upload CSV on the Transactions page.")
else:
    df = pd.DataFrame([{'month': r[0], 'category': r[1] or 'Uncategorized', 'total': r[2]} for r in rows])
    chart = alt.Chart(df).mark_bar().encode(
        x='month:O',
        y='sum(total):Q',
        color='category:N',
        tooltip=['month', 'category', 'total']
    ).properties(height=420)
    st.altair_chart(chart, use_container_width=True)

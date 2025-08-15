import streamlit as st
import pandas as pd
import altair as alt
from core.queries import monthly_expense_by_category

st.title("Dashboard")

include_income = st.checkbox(
    "Include Income/Refunds (positive amounts)", value=False
)

rows = monthly_expense_by_category(include_income=include_income)
if not rows:
    st.info("No data yet. Upload CSV on the Transactions page.")
else:
    df = pd.DataFrame(
        [
            {
                "month": r[0],
                "category": r[1] or "Uncategorized",
                "total": r[2],
            }
            for r in rows
        ]
    )
    months = sorted(df["month"].unique())
    selected_month = st.selectbox(
        "Month", options=months, index=len(months) - 1
    )
    df_month = df[df["month"] == selected_month]
    categories = sorted(df_month["category"].unique())
    selected = st.multiselect(
        "Categories to show", options=categories, default=categories
    )
    df_month = df_month[df_month["category"].isin(selected)]
    df_month = df_month.sort_values("total", ascending=False)
    chart = (
        alt.Chart(df_month)
        .mark_bar()
        .encode(
            x=alt.X("category:N", sort="-y"),
            y=alt.Y("total:Q"),
            color="category:N",
            tooltip=["category", "total"],
        )
        .properties(height=420, title=f"Expenses for {selected_month}")
    )
    st.altair_chart(chart, use_container_width=True)

    st.markdown("### Thresholds")
    for cat in selected:
        st.number_input(
            f"{cat} threshold",
            value=0.0,
            step=10.0,
            key=f"th_{selected_month}_{cat}",
        )
    df_month["threshold"] = df_month["category"].map(
        lambda c: st.session_state.get(f"th_{selected_month}_{c}", 0.0)
    )
    df_month["over"] = df_month["total"] > df_month["threshold"]
    st.dataframe(
        df_month[["category", "total", "threshold", "over"]],
        use_container_width=True,
        hide_index=True,
    )

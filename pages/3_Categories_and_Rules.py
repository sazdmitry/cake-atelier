import streamlit as st
import pandas as pd
from sqlalchemy import select
from core.db import get_session
from core.models import Category, Rule
from core.rules import apply_rules_to_uncategorized

st.title("Categories & Rules")

st.subheader("Categories")
with get_session() as s:
    cats = s.query(Category).order_by(Category.name.asc()).all()
    df = pd.DataFrame([{'id': c.id, 'name': c.name, 'description': c.description, 'threshold': c.threshold_amount, 'active': c.is_active} for c in cats])
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.expander("Add / Update Category"):
    name = st.text_input("Name")
    desc = st.text_area("Description", value="", height=60)
    th = st.number_input("Threshold amount (optional)", value=0.0, step=10.0)
    active = st.checkbox("Active", value=True)
    if st.button("Save Category"):
        with get_session() as s:
            c = s.query(Category).filter(Category.name == name).one_or_none()
            if c:
                c.description = desc
                c.threshold_amount = th if th > 0 else None
                c.is_active = active
                st.success("Category updated")
            else:
                s.add(Category(name=name, description=desc, threshold_amount=(th if th>0 else None), is_active=active))
                st.success("Category added")

st.divider()
st.subheader("Import Categories.xlsx (creates 'contains' rules from Providers)")
file = st.file_uploader("Upload Categories.xlsx", type=["xlsx"])
if file is not None and st.button("Import & Seed Rules"):
    xdf = pd.read_excel(file)
    # Expect columns: Categories, Description, Providers, Additional comment
    required = ['Categories', 'Description', 'Providers']
    if any(col not in xdf.columns for col in required):
        st.error(f"Missing required columns in Excel. Found: {list(xdf.columns)}")
    else:
        added_cats = 0
        added_rules = 0
        with get_session() as s:
            for _, r in xdf.iterrows():
                name = str(r['Categories']).strip()
                desc = str(r.get('Description', '')).strip() or None
                comment = str(r.get('Additional comment', '')).strip() or None
                c = s.query(Category).filter(Category.name == name).one_or_none()
                if not c:
                    c = Category(name=name, description=desc, comment=comment, is_active=True)
                    s.add(c)
                    s.flush()
                    added_cats += 1
                providers = str(r.get('Providers', '') or '').strip()
                if providers:
                    for p in [x.strip() for x in providers.split(',') if x.strip()]:
                        # create 'contains' rule on counterparty
                        s.add(Rule(category_id=c.id, field='counterparty', match_type='contains', pattern=p, priority=100))
                        added_rules += 1
        st.success(f"Imported. Added categories: {added_cats}, rules: {added_rules}")
        st.info("Go to Transactions → Re-apply rules (ingest a CSV first).")

st.divider()
st.subheader("Rules")
with get_session() as s:
    rules = s.query(Rule).order_by(Rule.enabled.desc(), Rule.priority.asc()).all()
    df = pd.DataFrame([{
        'id': r.id, 'category_id': r.category_id, 'field': r.field, 'type': r.match_type,
        'pattern': r.pattern, 'priority': r.priority, 'enabled': r.enabled
    } for r in rules])
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.expander("Add Rule"):
    cat_name = st.text_input("Category name for the rule")
    field = st.selectbox("Field", options=['counterparty', 'reference'])
    mtype = st.selectbox("Match type", options=['contains', 'exact', 'regex', 'fuzzy'])
    pattern = st.text_input("Pattern")
    priority = st.number_input("Priority (lower is stronger)", value=100, step=1)
    if st.button("Save Rule"):
        with get_session() as s:
            c = s.query(Category).filter(Category.name == cat_name).one_or_none()
            if not c:
                st.error("Category not found")
            else:
                from core.models import Rule
                s.add(Rule(category_id=c.id, field=field, match_type=mtype, pattern=pattern, priority=int(priority)))
                st.success("Rule added")


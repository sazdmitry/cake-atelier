import streamlit as st
import pandas as pd
from core.db import get_session
from core.models import Category, Rule
from core.rules import (
    apply_rules_to_all,
    apply_rule_to_all_transactions,
)

st.title("Categories & Rules")

st.subheader("Categories")
with get_session() as s:
    cats = s.query(Category).order_by(Category.name.asc()).all()
    df = pd.DataFrame(
        [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "active": c.is_active,
            }
            for c in cats
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.expander("Add / Update Category"):
    name = st.text_input("Name")
    desc = st.text_area("Description", value="", height=60)
    active = st.checkbox("Active", value=True)
    if st.button("Save Category"):
        with get_session() as s:
            c = s.query(Category).filter(Category.name == name).one_or_none()
            if c:
                c.description = desc
                c.is_active = active
                st.success("Category updated")
            else:
                s.add(Category(name=name, description=desc, is_active=active))
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
                        s.add(
                            Rule(
                                category_id=c.id,
                                field="counterparty",
                                match_type="contains",
                                pattern=p,
                            )
                        )
                        added_rules += 1
        st.success(f"Imported. Added categories: {added_cats}, rules: {added_rules}")
        st.info("Go to Transactions → Re-apply rules (ingest a CSV first).")

st.divider()
st.subheader("Rules")
with get_session() as s:
    rules = s.query(Rule).order_by(Rule.enabled.desc(), Rule.id.asc()).all()
    df = pd.DataFrame(
        [
            {
                "id": r.id,
                "category_id": r.category_id,
                "category": r.category.name if r.category else None,
                "field": r.field,
                "type": r.match_type,
                "pattern": r.pattern,
                "enabled": r.enabled,
            }
            for r in rules
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.expander("Add Rule"):
    with get_session() as s:
        cat_options = [c.name for c in s.query(Category).order_by(Category.name.asc()).all()]
    cat_name = st.selectbox("Category", options=cat_options)
    field = st.selectbox("Field", options=['counterparty', 'reference'])
    mtype = st.selectbox("Match type", options=['contains', 'exact', 'regex', 'fuzzy'])
    pattern = st.text_input("Pattern")
    if st.button("Save Rule"):
        with get_session() as s:
            c = s.query(Category).filter(Category.name == cat_name).one_or_none()
            if not c:
                st.error("Category not found")
            else:
                from core.models import Rule
                s.add(Rule(category_id=c.id, field=field, match_type=mtype, pattern=pattern))
                st.success("Rule added")

st.markdown(
    """
**How to add a rule:**
* **Match types**
    * *contains* – pattern must appear in the field
    * *exact* – field must exactly match the pattern
    * *regex* – pattern is a regular expression
    * *fuzzy* – allows minor differences
* To disable a rule set its `enabled` flag to `False` in the database.
* Example: pattern `Uber` with match type `contains` matches any counterparty containing "Uber".
    """
)

st.divider()
st.subheader("Apply Rules")

if st.button("Apply all rules to all transactions"):
    changed = apply_rules_to_all()
    st.success(f"Rules applied to {changed} transactions")

rule_map = {f"#{r.id} {r.field}:{r.pattern}": r.id for r in rules}
selected_rule = st.selectbox("Rule to apply to all transactions", options=list(rule_map.keys()))
if st.button("Apply selected rule"):
    count = apply_rule_to_all_transactions(rule_map[selected_rule])
    st.success(f"Rule applied to {count} transactions")


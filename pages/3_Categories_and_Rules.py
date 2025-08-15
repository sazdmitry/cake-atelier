import streamlit as st
import pandas as pd
from core.db import get_session
from core.models import Category, Rule
from core.rules import (
    apply_rules_to_all,
    apply_rule_to_all_transactions,
)
from core import gdrive

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

    c_up, c_down = st.columns(2)
    if c_up.button("Upload Categories to Drive"):
        gdrive.upload_df(df, "categories.csv")
        st.success("Categories uploaded to Google Drive")
    if c_down.button("Download Categories from Drive"):
        drive_df = gdrive.download_df("categories.csv")
        if drive_df is None:
            st.error("categories.csv not found on Drive")
        else:
            with get_session() as s:
                for _, r in drive_df.iterrows():
                    name = str(r.get("name", "")).strip()
                    if not name:
                        continue
                    c = s.query(Category).filter(Category.name == name).one_or_none()
                    if not c:
                        c = Category(name=name)
                        s.add(c)
                    c.description = r.get("description")
                    c.is_active = bool(r.get("active", True))
            st.success("Categories imported from Drive")

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
                        existing = (
                            s.query(Rule)
                            .filter(
                                Rule.category_id == c.id,
                                Rule.field == "counterparty",
                                Rule.match_type == "contains",
                                Rule.pattern == p,
                            )
                            .one_or_none()
                        )
                        if not existing:
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
                "amount_min": r.amount_min,
                "amount_max": r.amount_max,
                "enabled": r.enabled,
            }
            for r in rules
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    r_up, r_down = st.columns(2)
    if r_up.button("Upload Rules to Drive"):
        gdrive.upload_df(df, "rules.csv")
        st.success("Rules uploaded to Google Drive")
    if r_down.button("Download Rules from Drive"):
        drive_df = gdrive.download_df("rules.csv")
        if drive_df is None:
            st.error("rules.csv not found on Drive")
        else:
            with get_session() as s:
                for _, r in drive_df.iterrows():
                    rid = r.get("id")
                    rule = s.get(Rule, int(rid)) if pd.notna(rid) else None
                    if not rule:
                        rule = Rule()
                        s.add(rule)
                    rule.category_id = int(r.get("category_id")) if pd.notna(r.get("category_id")) else None
                    rule.field = r.get("field")
                    rule.match_type = r.get("type")
                    rule.pattern = r.get("pattern")
                    rule.amount_min = r.get("amount_min") if pd.notna(r.get("amount_min")) else None
                    rule.amount_max = r.get("amount_max") if pd.notna(r.get("amount_max")) else None
                    rule.enabled = bool(r.get("enabled", True))
            st.success("Rules imported from Drive")

with st.expander("Add Rule"):
    with get_session() as s:
        cat_options = [c.name for c in s.query(Category).order_by(Category.name.asc()).all()]
    cat_name = st.selectbox("Category", options=cat_options)
    field = st.selectbox("Field", options=['counterparty', 'reference'])
    mtype = st.selectbox("Match type", options=['contains', 'exact', 'regex', 'fuzzy'])
    pattern = st.text_input("Pattern")
    amt_min = st.text_input("Min Amount (optional)")
    amt_max = st.text_input("Max Amount (optional)")
    if st.button("Save Rule"):
        with get_session() as s:
            c = s.query(Category).filter(Category.name == cat_name).one_or_none()
            if not c:
                st.error("Category not found")
            else:
                s.add(
                    Rule(
                        category_id=c.id,
                        field=field,
                        match_type=mtype,
                        pattern=pattern,
                        amount_min=float(amt_min) if amt_min else None,
                        amount_max=float(amt_max) if amt_max else None,
                    )
                )
                st.success("Rule added")

with st.expander("Edit / Delete Rule"):
    with get_session() as s:
        rule_opts = {
            f"#{r.id} {r.field}:{r.pattern}": r.id
            for r in s.query(Rule).order_by(Rule.id.asc()).all()
        }
    if rule_opts:
        sel = st.selectbox("Rule", options=list(rule_opts.keys()))
        rule_id = rule_opts[sel]
        with get_session() as s:
            rule = s.get(Rule, rule_id)
            enabled = st.checkbox("Enabled", value=rule.enabled, key=f"rule_enabled_{rule_id}")
            c1, c2 = st.columns(2)
            if c1.button("Save", key=f"rule_save_{rule_id}"):
                rule.enabled = enabled
                st.success("Rule updated")
            if c2.button("Delete", key=f"rule_delete_{rule_id}"):
                s.delete(rule)
                st.success("Rule deleted")
    else:
        st.info("No rules defined")

st.markdown(
    """
**How to add a rule:**
* **Match types**
    * *contains* – pattern must appear in the field
    * *exact* – field must exactly match the pattern
    * *regex* – pattern is a regular expression
    * *fuzzy* – allows minor differences
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


# Expenses Streamlit MVP

Local Streamlit app to ingest CSV statements, auto-categorize via rules, and visualize monthly expenses by category.

## Quickstart
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
- Database: `data/expenses.db` (created on first run)
- Seed categories: go to **Categories & Rules** → "Import Categories.xlsx" (drag & drop your file)
- Upload CSVs: **Transactions** → "Upload CSV" (Finom-like: Completed date, Counterparty name, Reference, Amount)
- Dashboard: see monthly totals by category; toggle Income, filters; optional big/small split.

## Notes
- Expenses are stored negative (from CSV) but shown as positive magnitudes in charts.
- Income/refunds (positive amounts) are grouped separately and hidden by default.
- Dedup via SHA-1 hash of `timestamp|amount|counterparty|reference` (normalized).
- Rules precedence: exact → contains → regex → fuzzy (disabled by default).

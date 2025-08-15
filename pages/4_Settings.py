import streamlit as st
from pathlib import Path
from core.db import DB_PATH

st.title("Settings & Data")

st.write(f"Database path: `{DB_PATH}`")

if st.button("Download SQLite database"):
    with open(DB_PATH, "rb") as f:
        st.download_button(label="Save expenses.db", data=f, file_name="expenses.db")

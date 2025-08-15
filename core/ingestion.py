from __future__ import annotations
import pandas as pd
from dateutil import parser as dparser
from sqlalchemy import select
from typing import Tuple
from .db import get_session
from .models import Transaction, IngestionBatch
from .utils_text import normalize_text, stable_hash

EXPECTED_COLS = ['Completed date', 'Counterparty name', 'Reference', 'Amount']

def parse_datetime(value: str):
    # Finom format: 'DD.MM.YYYY HH:MM:SS'
    return dparser.parse(value, dayfirst=True)

def ingest_csv(file, batch_name: str) -> Tuple[int, int]:
    df = pd.read_csv(file)
    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")
    df = df[EXPECTED_COLS].copy()

    df['completed_at'] = df['Completed date'].apply(parse_datetime)
    df['counterparty_norm'] = df['Counterparty name'].apply(normalize_text)
    df['reference_norm'] = df['Reference'].fillna('').apply(normalize_text)
    df['amount'] = df['Amount'].astype(float)
    df['is_income'] = df['amount'] > 0

    df['ext_hash'] = df.apply(
        lambda r: stable_hash([
            r['completed_at'].isoformat(),
            f"{r['amount']:.2f}",
            r['counterparty_norm'],
            r['reference_norm']
        ]), axis=1
    )

    rows_ingested = 0
    rows_skipped = 0

    with get_session() as s:
        batch = IngestionBatch(file_name=batch_name)
        s.add(batch)
        s.flush()

        existing_hashes = set(h for (h,) in s.execute(
            select(Transaction.ext_hash)
        ).all())

        for _, r in df.iterrows():
            if r['ext_hash'] in existing_hashes:
                rows_skipped += 1
                continue
            tx = Transaction(
                ext_hash=r['ext_hash'],
                completed_at=r['completed_at'],
                counterparty=str(r['Counterparty name']),
                reference=None if pd.isna(r['Reference']) else str(r['Reference']),
                amount=float(r['amount']),
                is_income=bool(r['is_income']),
                ingest_batch_id=batch.id,
            )
            s.add(tx)
            rows_ingested += 1

        batch.rows_ingested = rows_ingested
        batch.rows_skipped_dupe = rows_skipped

    return rows_ingested, rows_skipped

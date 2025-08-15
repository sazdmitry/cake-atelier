from __future__ import annotations
from sqlalchemy import select
from .db import get_session
from .models import Transaction, Assignment, Category, Rule

def set_category_manual(tx_ids: list[int], category_id: int):
    with get_session() as s:
        for tx_id in tx_ids:
            a = s.scalar(select(Assignment).where(Assignment.transaction_id == tx_id))
            if a:
                a.category_id = category_id
                a.source = 'manual'
                a.rule_id = None
            else:
                s.add(Assignment(transaction_id=tx_id, category_id=category_id, source='manual', rule_id=None))

def create_rule_from_tx(tx_id: int, category_id: int, match_type='contains', field='counterparty'):
    with get_session() as s:
        tx = s.get(Transaction, tx_id)
        if not tx:
            return None
        pattern = (tx.counterparty or '').strip()
        if field == 'reference':
            pattern = (tx.reference or '').strip()
        r = Rule(category_id=category_id, field=field, match_type=match_type, pattern=pattern, priority=100)
        s.add(r)
        s.flush()
        return r.id

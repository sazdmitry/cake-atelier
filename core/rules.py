from __future__ import annotations
import re
from typing import Optional, Iterable
from sqlalchemy import select
from rapidfuzz import fuzz
from .models import Rule, Transaction, Assignment
from .db import get_session
from .utils_text import normalize_text

def _field_value(tx: Transaction, field: str) -> str:
    if field == 'counterparty':
        return normalize_text(tx.counterparty or '')
    if field == 'reference':
        return normalize_text(tx.reference or '')
    return ''

def match_rule(rule: Rule, value: str) -> bool:
    test_val = value if rule.case_sensitive else value.lower()
    pat = rule.pattern if rule.case_sensitive else rule.pattern.lower()

    if rule.match_type == 'exact':
        return test_val == pat
    elif rule.match_type == 'contains':
        return pat in test_val
    elif rule.match_type == 'regex':
        flags = 0 if rule.case_sensitive else re.IGNORECASE
        try:
            return re.search(rule.pattern, value, flags=flags) is not None
        except re.error:
            return False
    elif rule.match_type == 'fuzzy':
        return fuzz.ratio(test_val, pat) >= 90
    return False

def choose_category_for(tx: Transaction, rules: Iterable[Rule]) -> Optional[tuple[int, int | None]]:
    # Priority order: exact > contains > regex > fuzzy, within that by rule.priority asc
    order = {'exact':0, 'contains':1, 'regex':2, 'fuzzy':3}
    sorted_rules = sorted([r for r in rules if r.enabled],
                          key=lambda r: (order.get(r.match_type, 9), r.priority))
    for r in sorted_rules:
        value = _field_value(tx, r.field)
        if not value:
            continue
        if match_rule(r, value):
            return r.category_id, r.id
    return None

def apply_rules_to_uncategorized():
    from .models import Transaction, Assignment, Rule
    from sqlalchemy import select
    with get_session() as s:
        rules = s.scalars(select(Rule)).all()
        txs = s.scalars(select(Transaction)).all()
        # build map of tx id -> has assignment
        assigned = {a.transaction_id for a in s.scalars(select(Assignment)).all()}
        changed = 0
        for tx in txs:
            if tx.id in assigned:
                continue
            if tx.is_income:
                # skip auto-categorizing income; treat separately
                continue
            result = choose_category_for(tx, rules)
            if result:
                cat_id, rule_id = result
                a = Assignment(transaction_id=tx.id, category_id=cat_id, source='rule', rule_id=rule_id)
                s.add(a)
                changed += 1
    return True

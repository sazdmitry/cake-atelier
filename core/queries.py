from sqlalchemy import select, func, case, and_
from .db import get_session
from .models import Transaction, Assignment, Category

def monthly_expense_by_category(category_ids: list[int] | None = None, include_income=False):
    # Sum abs(amount) for expenses; optionally include income
    with get_session() as s:
        amt = func.abs(Transaction.amount)
        month = func.strftime('%Y-%m', Transaction.completed_at).label('month')
        join = s.query(
            month,
            Category.name.label('category'),
            func.sum(amt).label('total')
        ).select_from(Transaction).join(Assignment, Assignment.transaction_id == Transaction.id, isouter=True)         .join(Category, Category.id == Assignment.category_id, isouter=True)

        conds = []
        if not include_income:
            conds.append(Transaction.is_income == False)  # noqa
        if category_ids:
            conds.append(Category.id.in_(category_ids))
        if conds:
            join = join.filter(and_(*conds))

        join = join.group_by(month, Category.name).order_by(month.asc(), Category.name.asc())
        rows = join.all()
        return rows

def fetch_transactions(filters: dict | None = None):
    with get_session() as s:
        q = s.query(Transaction, Assignment, Category)             .join(Assignment, Assignment.transaction_id == Transaction.id, isouter=True)             .join(Category, Category.id == Assignment.category_id, isouter=True)             .order_by(Transaction.completed_at.desc())
        f = filters or {}
        if 'uncategorized' in f and f['uncategorized']:
            q = q.filter(Assignment.id.is_(None))
        if 'category_id' in f and f['category_id']:
            q = q.filter(Category.id == f['category_id'])
        if 'income' in f:
            q = q.filter(Transaction.is_income == bool(f['income']))
        return q.all()

def categories_list(active_only=True):
    with get_session() as s:
        q = s.query(Category)
        if active_only:
            q = q.filter(Category.is_active == True)  # noqa
        return q.order_by(Category.name.asc()).all()

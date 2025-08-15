from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "expenses.db"

class Base(DeclarativeBase):
    pass

_engine = None
_Session = None

def init_engine_and_create():
    global _engine, _Session
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
    from .models import Base as MBase  # noqa
    MBase.metadata.create_all(_engine)
    _Session = sessionmaker(_engine, expire_on_commit=False, future=True)

def ensure_db():
    global _engine
    if _engine is None:
        init_engine_and_create()

@contextmanager
def get_session():
    ensure_db()
    s = _Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

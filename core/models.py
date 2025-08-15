from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Float, Boolean, ForeignKey, Text, UniqueConstraint, func
from datetime import datetime
from .db import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ext_hash: Mapped[str] = mapped_column(String(40), unique=True, index=True)  # sha1
    completed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    counterparty: Mapped[str] = mapped_column(Text)
    reference: Mapped[str] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float)  # negative for expense
    is_income: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    ingest_batch_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_batches.id"), nullable=True)

    assignment: Mapped["Assignment"] = relationship(back_populates="transaction", uselist=False)

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    threshold_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    rules: Mapped[list["Rule"]] = relationship(back_populates="category")

class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    field: Mapped[str] = mapped_column(String(20))  # 'counterparty' | 'reference'
    match_type: Mapped[str] = mapped_column(String(20))  # 'exact' | 'contains' | 'regex' | 'fuzzy'
    pattern: Mapped[str] = mapped_column(Text)
    amount_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category: Mapped["Category"] = relationship(back_populates="rules")

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    source: Mapped[str] = mapped_column(String(20))  # 'rule' | 'manual'
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("rules.id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transaction: Mapped["Transaction"] = relationship(back_populates="assignment")
    category: Mapped["Category"] = relationship()
    rule: Mapped["Rule"] = relationship()

class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    file_name: Mapped[str] = mapped_column(String(255))
    rows_ingested: Mapped[int] = mapped_column(Integer, default=0)
    rows_skipped_dupe: Mapped[int] = mapped_column(Integer, default=0)

class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)

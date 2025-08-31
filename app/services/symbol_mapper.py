"""Utilities for symbol mapping stored in the database."""
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.symbol_mapping import SymbolMapping


def get_mapped_symbol(symbol: str, db: Optional[Session] = None) -> str:
    """Return mapped broker symbol for given raw symbol.

    If no mapping is found or database is unavailable, returns the original
    symbol.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        mapping = (
            db.query(SymbolMapping)
            .filter(SymbolMapping.raw_symbol == symbol)
            .first()
        )
        return mapping.broker_symbol if mapping else symbol
    except Exception:
        # If anything goes wrong (e.g., DB not available), fall back
        return symbol
    finally:
        if close_db:
            db.close()


def upsert_symbol_mapping(
    raw_symbol: str, broker_symbol: str, db: Optional[Session] = None
) -> None:
    """Create or update a symbol mapping entry."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        mapping = (
            db.query(SymbolMapping)
            .filter(SymbolMapping.raw_symbol == raw_symbol)
            .first()
        )
        if mapping:
            mapping.broker_symbol = broker_symbol
        else:
            mapping = SymbolMapping(
                raw_symbol=raw_symbol, broker_symbol=broker_symbol
            )
            db.add(mapping)
        db.commit()
    finally:
        if close_db:
            db.close()

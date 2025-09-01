import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.signal import Signal


def test_signal_notes_persist():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    signal = Signal(symbol="AAPL", action="buy", strategy_id="strat", notes="test note")
    session.add(signal)
    session.commit()

    fetched = session.query(Signal).filter_by(id=signal.id).first()
    assert fetched is not None
    assert fetched.notes == "test note"

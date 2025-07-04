from sqlalchemy.orm import sessionmaker, Session

from ..database import SessionLocal
from ..models.trades import Trade
from .monte_carlo_analyzer import MonteCarloAnalyzer


class RiskManager:
    """Determine optimal position sizing."""

    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self.session_factory = session_factory
        self.base_percentage = 0.14  # default fraction of buying power

    def _load_trades(self, session: Session):
        return session.query(Trade).filter(Trade.status == "closed").all()

    def calculate_optimal_position_size(self, price: float, buying_power: float) -> float:
        """Return recommended quantity based on available data."""
        session = self.session_factory()
        try:
            trades = self._load_trades(session)
        finally:
            session.close()

        if len(trades) < 50:
            pct = self.base_percentage
        else:
            analyzer = MonteCarloAnalyzer(trades)
            pct = analyzer.kelly_fraction()
            if pct <= 0:
                pct = self.base_percentage
            else:
                pct = min(pct, self.base_percentage)
        position_value = buying_power * pct
        if price <= 0:
            return 0.0
        return position_value / price


# Global instance using the app session
risk_manager = RiskManager()

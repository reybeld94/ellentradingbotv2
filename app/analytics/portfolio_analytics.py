from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.models.trades import Trade
from decimal import Decimal
import pandas as pd


class PortfolioAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def get_performance_metrics(self, user_id: int, portfolio_id: int, timeframe: str = "1M") -> Dict[str, Any]:
        """Calcula métricas de performance para el portfolio"""
        end_date = datetime.utcnow()
        if timeframe == "1D":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "1W":
            start_date = end_date - timedelta(weeks=1)
        elif timeframe == "1M":
            start_date = end_date - timedelta(days=30)
        elif timeframe == "3M":
            start_date = end_date - timedelta(days=90)
        elif timeframe == "6M":
            start_date = end_date - timedelta(days=180)
        elif timeframe == "1Y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime(2020, 1, 1)

        base_query = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.opened_at >= start_date,
                Trade.opened_at <= end_date,
                Trade.status.in_(["open", "closed"]),
            )
        )

        return {
            "total_pnl": self._calculate_total_pnl(base_query),
            "total_pnl_percentage": self._calculate_total_pnl_percentage(base_query),
            "sharpe_ratio": self._calculate_sharpe_ratio(base_query),
            "max_drawdown": self._calculate_max_drawdown(base_query),
            "win_rate": self._calculate_win_rate(base_query),
            "avg_hold_time": self._calculate_avg_hold_time(base_query),
            "profit_factor": self._calculate_profit_factor(base_query),
            "total_trades": base_query.count(),
            "winning_trades": base_query.filter(Trade.pnl > 0).count(),
            "losing_trades": base_query.filter(Trade.pnl < 0).count(),
            "largest_win": self._get_largest_win(base_query),
            "largest_loss": self._get_largest_loss(base_query),
            "avg_win": self._get_avg_win(base_query),
            "avg_loss": self._get_avg_loss(base_query),
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    def _calculate_total_pnl(self, query) -> float:
        result = query.with_entities(func.sum(Trade.pnl)).scalar()
        return float(result) if result else 0.0

    def _calculate_total_pnl_percentage(self, query) -> float:
        total_invested = query.with_entities(func.sum(Trade.quantity * Trade.entry_price)).scalar()
        total_pnl = self._calculate_total_pnl(query)
        if not total_invested or total_invested == 0:
            return 0.0
        return (total_pnl / float(total_invested)) * 100

    def _calculate_sharpe_ratio(self, query) -> float:
        return 0.0

    def _calculate_max_drawdown(self, query) -> float:
        return 0.0

    def _calculate_win_rate(self, query) -> float:
        return 0.0

    def _calculate_avg_hold_time(self, query) -> float:
        return 0.0

    def _calculate_profit_factor(self, query) -> float:
        return 0.0

    def _get_largest_win(self, query) -> float:
        return 0.0

    def _get_largest_loss(self, query) -> float:
        return 0.0

    def _get_avg_win(self, query) -> float:
        return 0.0

    def _get_avg_loss(self, query) -> float:
        return 0.0

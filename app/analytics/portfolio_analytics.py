from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.models.trades import Trade
from decimal import Decimal
import pandas as pd
import statistics


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
        """Calcula Sharpe Ratio (retorno/riesgo)."""
        trades = query.all()
        if len(trades) < 2:
            return 0.0

        returns: List[float] = []
        for trade in trades:
            if trade.pnl is not None and trade.quantity and trade.entry_price:
                daily_return = (trade.pnl / (trade.quantity * trade.entry_price)) * 100
                returns.append(daily_return)

        if len(returns) < 2:
            return 0.0

        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)

        if std_return == 0:
            return 0.0

        risk_free_rate = 0.0055
        sharpe = (avg_return - risk_free_rate) / std_return
        return round(sharpe, 4)

    def _calculate_max_drawdown(self, query) -> float:
        """Calcula máximo drawdown (mayor pérdida desde peak)."""
        trades = query.order_by(Trade.opened_at.asc()).all()
        if not trades:
            return 0.0

        equity_curve: List[float] = []
        running_pnl = 0.0

        for trade in trades:
            if trade.pnl is not None:
                running_pnl += float(trade.pnl)
                equity_curve.append(running_pnl)

        if len(equity_curve) < 2:
            return 0.0

        peak = equity_curve[0]
        max_drawdown = 0.0

        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = ((equity - peak) / peak) * 100 if peak != 0 else 0.0
            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return round(max_drawdown, 2)

    def _calculate_win_rate(self, query) -> float:
        """Calcula win rate como porcentaje."""
        total_trades = query.count()
        if total_trades == 0:
            return 0.0

        winning_trades = query.filter(Trade.pnl > 0).count()
        win_rate = (winning_trades / total_trades) * 100
        return round(win_rate, 2)

    def _calculate_avg_hold_time(self, query) -> str:
        """Calcula tiempo promedio de hold en formato legible."""
        trades = query.filter(
            and_(Trade.opened_at.isnot(None), Trade.closed_at.isnot(None))
        ).all()

        if not trades:
            return "0m"

        total_seconds = 0.0
        valid_trades = 0

        for trade in trades:
            if trade.opened_at and trade.closed_at:
                hold_time = trade.closed_at - trade.opened_at
                total_seconds += hold_time.total_seconds()
                valid_trades += 1

        if valid_trades == 0:
            return "0m"

        avg_seconds = total_seconds / valid_trades

        days = int(avg_seconds // 86400)
        hours = int((avg_seconds % 86400) // 3600)
        minutes = int((avg_seconds % 3600) // 60)

        if days > 0:
            return f"{days}d {hours}h"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _calculate_profit_factor(self, query) -> float:
        """Calcula Profit Factor: Ganancia total / Pérdida total."""
        winning_trades = query.filter(Trade.pnl > 0)
        losing_trades = query.filter(Trade.pnl < 0)

        total_profit = winning_trades.with_entities(func.sum(Trade.pnl)).scalar() or 0
        total_loss = abs(losing_trades.with_entities(func.sum(Trade.pnl)).scalar() or 0)

        if total_loss == 0:
            return float("inf") if total_profit > 0 else 0.0

        profit_factor = total_profit / total_loss
        return round(profit_factor, 3)

    def _get_largest_win(self, query) -> float:
        """Retorna el trade más exitoso."""
        result = query.with_entities(func.max(Trade.pnl)).scalar()
        return float(result) if result else 0.0

    def _get_largest_loss(self, query) -> float:
        """Retorna la pérdida más grande."""
        result = query.with_entities(func.min(Trade.pnl)).scalar()
        return float(result) if result else 0.0

    def _get_avg_win(self, query) -> float:
        """Retorna ganancia promedio de trades ganadores."""
        winning_query = query.filter(Trade.pnl > 0)
        result = winning_query.with_entities(func.avg(Trade.pnl)).scalar()
        return float(result) if result else 0.0

    def _get_avg_loss(self, query) -> float:
        """Retorna pérdida promedio de trades perdedores."""
        losing_query = query.filter(Trade.pnl < 0)
        result = losing_query.with_entities(func.avg(Trade.pnl)).scalar()
        return float(result) if result else 0.0

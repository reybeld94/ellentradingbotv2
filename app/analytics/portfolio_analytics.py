from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.models.trades import Trade
from decimal import Decimal
import pandas as pd
import statistics
import numpy as np


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

    def get_trade_analytics(self, user_id: int, portfolio_id: int, timeframe: str = "3M") -> Dict[str, Any]:
        """
        Obtiene analytics avanzados de trades incluyendo equity curve y distribuciones
        """
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
        else:  # "ALL"
            start_date = datetime(2020, 1, 1)

        base_query = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.opened_at >= start_date,
                Trade.opened_at <= end_date,
                Trade.status.in_(["filled", "closed"])
            )
        )

        return {
            "equity_curve": self._build_equity_curve(base_query),
            "drawdown_periods": self._identify_drawdown_periods(base_query),
            "trade_distribution": self._analyze_trade_distribution(base_query),
            "holding_period_analysis": self._analyze_holding_periods(base_query),
            "monthly_returns": self._get_monthly_returns(base_query),
            "strategy_breakdown": self._get_strategy_performance(base_query),
            "risk_metrics": self._get_risk_metrics(base_query),
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

    def _build_equity_curve(self, query) -> List[Dict[str, Any]]:
        """
        Construye curva de equity acumulativa
        Retorna array de puntos [fecha, pnl_acumulado, drawdown]
        """
        trades = query.order_by(Trade.opened_at.asc()).all()
        if not trades:
            return []

        equity_curve = []
        running_pnl = 0.0
        peak_equity = 0.0

        for trade in trades:
            if trade.pnl:
                running_pnl += float(trade.pnl)

                if running_pnl > peak_equity:
                    peak_equity = running_pnl

                drawdown = ((running_pnl - peak_equity) / peak_equity * 100) if peak_equity != 0 else 0.0

                equity_curve.append({
                    "date": trade.opened_at.isoformat() if trade.opened_at else None,
                    "equity": round(running_pnl, 2),
                    "drawdown": round(drawdown, 2),
                    "trade_id": trade.id,
                    "symbol": trade.symbol,
                    "pnl": float(trade.pnl)
                })

        return equity_curve

    def _identify_drawdown_periods(self, query) -> List[Dict[str, Any]]:
        """
        Identifica períodos de drawdown significativos (>5%)
        """
        equity_curve = self._build_equity_curve(query)
        if len(equity_curve) < 2:
            return []

        drawdown_periods = []
        in_drawdown = False
        current_period = None

        for point in equity_curve:
            if point["drawdown"] <= -5.0 and not in_drawdown:
                in_drawdown = True
                current_period = {
                    "start_date": point["date"],
                    "start_equity": point["equity"],
                    "max_drawdown": point["drawdown"],
                    "duration_days": 0
                }
            elif point["drawdown"] <= -5.0 and in_drawdown:
                if point["drawdown"] < current_period["max_drawdown"]:
                    current_period["max_drawdown"] = point["drawdown"]
            elif point["drawdown"] > -5.0 and in_drawdown:
                in_drawdown = False
                current_period["end_date"] = point["date"]
                current_period["end_equity"] = point["equity"]

                start = datetime.fromisoformat(current_period["start_date"].replace('Z', '+00:00'))
                end = datetime.fromisoformat(point["date"].replace('Z', '+00:00'))
                current_period["duration_days"] = (end - start).days

                drawdown_periods.append(current_period)
                current_period = None

        if in_drawdown and current_period:
            current_period["end_date"] = equity_curve[-1]["date"]
            current_period["end_equity"] = equity_curve[-1]["equity"]

            start = datetime.fromisoformat(current_period["start_date"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(current_period["end_date"].replace('Z', '+00:00'))
            current_period["duration_days"] = (end - start).days

            drawdown_periods.append(current_period)

        return drawdown_periods

    def _analyze_trade_distribution(self, query) -> Dict[str, Any]:
        """
        Analiza distribución de trades por P&L
        """
        trades = query.all()
        if not trades:
            return {"bins": [], "win_distribution": [], "loss_distribution": []}

        pnl_values = [float(t.pnl) for t in trades if t.pnl]
        if not pnl_values:
            return {"bins": [], "win_distribution": [], "loss_distribution": []}

        winners = [pnl for pnl in pnl_values if pnl > 0]
        losers = [pnl for pnl in pnl_values if pnl < 0]

        win_distribution = []
        if winners:
            win_bins = np.histogram(winners, bins=10)
            for i, count in enumerate(win_bins[0]):
                win_distribution.append({
                    "range": f"${win_bins[1][i]:.0f} - ${win_bins[1][i+1]:.0f}",
                    "count": int(count),
                    "percentage": (count / len(winners)) * 100
                })

        loss_distribution = []
        if losers:
            loss_bins = np.histogram(losers, bins=10)
            for i, count in enumerate(loss_bins[0]):
                loss_distribution.append({
                    "range": f"${loss_bins[1][i]:.0f} - ${loss_bins[1][i+1]:.0f}",
                    "count": int(count),
                    "percentage": (count / len(losers)) * 100
                })

        return {
            "win_distribution": win_distribution,
            "loss_distribution": loss_distribution,
            "total_winners": len(winners),
            "total_losers": len(losers),
            "avg_winner": sum(winners) / len(winners) if winners else 0,
            "avg_loser": sum(losers) / len(losers) if losers else 0
        }

    def _analyze_holding_periods(self, query) -> Dict[str, Any]:
        """
        Analiza distribución de períodos de holding
        """
        trades = query.filter(
            and_(Trade.opened_at.isnot(None), Trade.closed_at.isnot(None))
        ).all()

        if not trades:
            return {"distribution": [], "avg_by_outcome": {}}

        holding_times = []
        winning_times = []
        losing_times = []

        for trade in trades:
            if trade.opened_at and trade.closed_at:
                hold_duration = trade.closed_at - trade.opened_at
                hours = hold_duration.total_seconds() / 3600

                holding_times.append(hours)

                if trade.pnl and trade.pnl > 0:
                    winning_times.append(hours)
                elif trade.pnl and trade.pnl < 0:
                    losing_times.append(hours)

        if not holding_times:
            return {"distribution": [], "avg_by_outcome": {}}

        bins = [0, 1, 4, 8, 24, 48, 168, float('inf')]
        labels = ["< 1h", "1-4h", "4-8h", "8-24h", "1-2d", "2-7d", "> 7d"]

        distribution = []
        for i in range(len(bins) - 1):
            count = sum(1 for h in holding_times if bins[i] <= h < bins[i+1])
            distribution.append({
                "range": labels[i],
                "count": count,
                "percentage": (count / len(holding_times)) * 100
            })

        return {
            "distribution": distribution,
            "avg_by_outcome": {
                "winners": sum(winning_times) / len(winning_times) if winning_times else 0,
                "losers": sum(losing_times) / len(losing_times) if losing_times else 0,
                "overall": sum(holding_times) / len(holding_times)
            }
        }

    def _get_monthly_returns(self, query) -> List[Dict[str, Any]]:
        """
        Calcula retornos mensuales
        """
        trades = query.order_by(Trade.opened_at.asc()).all()
        if not trades:
            return []

        monthly_data = {}

        for trade in trades:
            if trade.pnl and trade.opened_at:
                month_key = trade.opened_at.strftime("%Y-%m")

                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "month": month_key,
                        "pnl": 0.0,
                        "trades": 0,
                        "winners": 0,
                        "losers": 0
                    }

                monthly_data[month_key]["pnl"] += float(trade.pnl)
                monthly_data[month_key]["trades"] += 1

                if trade.pnl > 0:
                    monthly_data[month_key]["winners"] += 1
                else:
                    monthly_data[month_key]["losers"] += 1

        monthly_returns = []
        for month_key in sorted(monthly_data.keys()):
            data = monthly_data[month_key]
            win_rate = (data["winners"] / data["trades"]) * 100 if data["trades"] > 0 else 0

            monthly_returns.append({
                "month": month_key,
                "pnl": round(data["pnl"], 2),
                "trades": data["trades"],
                "win_rate": round(win_rate, 1)
            })

        return monthly_returns

    def _get_strategy_performance(self, query) -> List[Dict[str, Any]]:
        """
        Breakdown de performance por estrategia
        """
        from app.models.strategy import Strategy

        strategy_stats = self.db.query(
            Strategy.name,
            func.sum(Trade.pnl).label('total_pnl'),
            func.count(Trade.id).label('total_trades'),
            func.sum(func.case([(Trade.pnl > 0, 1)], else_=0)).label('winners'),
            func.avg(Trade.pnl).label('avg_pnl')
        ).join(
            Trade, Trade.strategy_id == Strategy.id
        ).filter(
            Trade.id.in_([t.id for t in query.all()])
        ).group_by(Strategy.id, Strategy.name).all()

        strategy_breakdown = []
        for stat in strategy_stats:
            win_rate = (stat.winners / stat.total_trades) * 100 if stat.total_trades > 0 else 0

            strategy_breakdown.append({
                "strategy_name": stat.name,
                "total_pnl": float(stat.total_pnl or 0),
                "total_trades": stat.total_trades,
                "win_rate": round(win_rate, 1),
                "avg_pnl": round(float(stat.avg_pnl or 0), 2)
            })

        return sorted(strategy_breakdown, key=lambda x: x["total_pnl"], reverse=True)

    def _get_risk_metrics(self, query) -> Dict[str, Any]:
        """
        Métricas de riesgo avanzadas
        """
        trades = query.all()
        if not trades:
            return {}

        pnl_values = [float(t.pnl) for t in trades if t.pnl]
        if len(pnl_values) < 2:
            return {}

        import statistics

        pnl_sorted = sorted(pnl_values)
        var_95_index = int(len(pnl_sorted) * 0.05)
        var_95 = pnl_sorted[var_95_index] if var_95_index < len(pnl_sorted) else pnl_sorted[0]

        worst_losses = pnl_sorted[:var_95_index] if var_95_index > 0 else [pnl_sorted[0]]
        expected_shortfall = statistics.mean(worst_losses) if worst_losses else 0

        volatility = statistics.stdev(pnl_values)

        total_return = sum(pnl_values)
        max_dd = abs(self._calculate_max_drawdown(query))
        calmar_ratio = (total_return / max_dd) if max_dd > 0 else 0

        return {
            "volatility": round(volatility, 2),
            "var_95": round(var_95, 2),
            "expected_shortfall": round(expected_shortfall, 2),
            "calmar_ratio": round(calmar_ratio, 3),
            "downside_deviation": round(statistics.stdev([p for p in pnl_values if p < 0]), 2) if any(p < 0 for p in pnl_values) else 0
        }

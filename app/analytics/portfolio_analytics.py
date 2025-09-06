from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import func, and_, case, select
from app.models.trades import Trade
from app.core.types import TradeStatus
from decimal import Decimal, getcontext
import pandas as pd
import statistics
import numpy as np


getcontext().prec = 28


class PortfolioAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def get_performance_metrics(self, user_id: int, portfolio_id: int, timeframe: str = "1M") -> Dict[str, Any]:
        """Calcula métricas de performance para el portfolio"""
        print(f"🔍 get_performance_metrics Debug:")
        print(f"  user_id: {user_id}")
        print(f"  portfolio_id: {portfolio_id}")
        print(f"  timeframe: {timeframe}")
        
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

        print(f"  date_range: {start_date} to {end_date}")

        base_query = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.opened_at >= start_date,
                Trade.opened_at <= end_date,
                Trade.status.in_([TradeStatus.OPEN, TradeStatus.CLOSED]),
            )
        )
        
        # Check how many trades we found
        trades_count = base_query.count()
        print(f"  trades_found: {trades_count}")
        
        # Check total trades for this portfolio (any date)
        total_trades = self.db.query(Trade).filter(
            and_(Trade.user_id == user_id, Trade.portfolio_id == portfolio_id)
        ).count()
        print(f"  total_trades_ever: {total_trades}")
        
        # Check trade status breakdown
        if total_trades > 0:
            status_breakdown = self.db.query(Trade.status, func.count(Trade.id)).filter(
                and_(Trade.user_id == user_id, Trade.portfolio_id == portfolio_id)
            ).group_by(Trade.status).all()
            print(f"  status_breakdown: {dict(status_breakdown)}")

        if trades_count == 0:
            print("  ⚠️ No trades found - returning zeros")
        else:
            # Debug: Show sample trade data
            sample_trades = base_query.limit(3).all()
            print(f"  📊 Sample trades data:")
            for i, trade in enumerate(sample_trades):
                print(f"    Trade {i+1}: {trade.symbol} | pnl: {trade.pnl} | qty: {trade.quantity} | entry: {trade.entry_price} | status: {trade.status}")

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

    def _calculate_total_pnl(self, query) -> Decimal:
        result = query.with_entities(func.sum(Trade.pnl)).scalar()
        print(f"    _calculate_total_pnl result: {result}")
        return Decimal(result) if result is not None else Decimal("0")

    def _calculate_total_pnl_percentage(self, query) -> Decimal:
        total_invested_raw = query.with_entities(
            func.sum(Trade.quantity * Trade.entry_price)
        ).scalar()
        total_invested = (
            Decimal(total_invested_raw)
            if total_invested_raw is not None
            else Decimal("0")
        )
        total_pnl = self._calculate_total_pnl(query)
        if total_invested == 0:
            return Decimal("0")
        return (total_pnl / total_invested) * Decimal("100")

    def _calculate_sharpe_ratio(self, query) -> float:
        """Calcula Sharpe Ratio (retorno/riesgo)."""
        trades = query.all()
        if len(trades) < 2:
            return 0.0

        returns: List[float] = []
        for trade in trades:
            if trade.pnl is not None and trade.quantity and trade.entry_price:
                daily_return = trade.pnl / (trade.quantity * trade.entry_price)
                returns.append(daily_return)

        if len(returns) < 2:
            return 0.0

        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)

        if std_return == 0:
            return 0.0

        risk_free_rate = 0.02 / 252
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
                Trade.status.in_([TradeStatus.OPEN, TradeStatus.CLOSED])
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
            if trade.pnl is not None:
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

        returns = [
            float(t.pnl) / (float(t.quantity) * float(t.entry_price))
            for t in trades
            if t.pnl is not None and t.quantity and t.entry_price
        ]
        if not returns:
            return {"bins": [], "win_distribution": [], "loss_distribution": []}

        winners = [r for r in returns if r > 0]
        losers = [r for r in returns if r < 0]

        win_distribution = []
        if winners:
            win_bins = np.histogram(winners, bins=10)
            for i, count in enumerate(win_bins[0]):
                win_distribution.append({
                    "range": f"{win_bins[1][i] * 100:.1f}% - {win_bins[1][i+1] * 100:.1f}%",
                    "count": int(count),
                    "percentage": (count / len(winners)) * 100
                })

        loss_distribution = []
        if losers:
            loss_bins = np.histogram(losers, bins=10)
            for i, count in enumerate(loss_bins[0]):
                loss_distribution.append({
                    "range": f"{loss_bins[1][i] * 100:.1f}% - {loss_bins[1][i+1] * 100:.1f}%",
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

                if trade.pnl is not None and trade.pnl > 0:
                    winning_times.append(hours)
                elif trade.pnl is not None and trade.pnl < 0:
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
            if trade.pnl is not None and trade.opened_at:
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

        trade_ids = query.with_entities(Trade.id).subquery()

        strategy_stats = self.db.query(
            Strategy.name,
            func.sum(Trade.pnl).label('total_pnl'),
            func.count(Trade.id).label('total_trades'),
            func.sum(case((Trade.pnl > 0, 1), else_=0)).label('winners'),
            func.avg(Trade.pnl).label('avg_pnl')
        ).join(
            Trade, Trade.strategy_id == Strategy.name
        ).filter(
            Trade.id.in_(select(trade_ids.c.id))
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

        returns = [
            float(t.pnl) / (float(t.quantity) * float(t.entry_price))
            for t in trades
            if t.pnl is not None and t.quantity and t.entry_price
        ]
        if len(returns) < 2:
            return {}
        import statistics

        returns_sorted = sorted(returns)
        var_95_index = int(len(returns_sorted) * 0.05)
        var_95 = returns_sorted[var_95_index] if var_95_index < len(returns_sorted) else returns_sorted[0]

        worst_losses = returns_sorted[:var_95_index] if var_95_index > 0 else [returns_sorted[0]]
        expected_shortfall = statistics.mean(worst_losses) if worst_losses else 0

        volatility = statistics.stdev(returns)

        total_return = sum(returns)
        max_dd = abs(self._calculate_max_drawdown(query))
        calmar_ratio = (total_return / max_dd) if max_dd > 0 else 0

        return {
            "volatility": round(volatility, 4),
            "var_95": round(var_95, 4),
            "expected_shortfall": round(expected_shortfall, 4),
            "calmar_ratio": round(calmar_ratio, 3),
            "downside_deviation": round(statistics.stdev([r for r in returns if r < 0]), 4) if any(r < 0 for r in returns) else 0,
        }

    def get_risk_dashboard_data(self, user_id: int, portfolio_id: int, timeframe: str = "3M") -> Dict[str, Any]:
        """Obtiene datos completos para dashboard de riesgo"""
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
                Trade.status.in_([TradeStatus.OPEN, TradeStatus.CLOSED])
            )
        )

        return {
            "risk_metrics": self._get_advanced_risk_metrics(base_query),
            "var_analysis": self._get_var_analysis(base_query),
            "position_sizing": self._analyze_position_sizing(base_query),
            "symbol_exposure": self._analyze_symbol_exposure(base_query),
            "time_based_risk": self._analyze_time_based_risk(base_query),
            "risk_adjusted_returns": self._calculate_risk_adjusted_returns(base_query),
            "correlation_analysis": self._analyze_correlations(base_query),
            "risk_limits_status": self._get_risk_limits_status(user_id, portfolio_id),
            "timeframe": timeframe,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _get_advanced_risk_metrics(self, query) -> Dict[str, Any]:
        """Métricas de riesgo avanzadas"""
        trades = query.all()
        if not trades:
            return {"error": "No trades available for risk analysis"}

        returns = [
            float(t.pnl) / (float(t.quantity) * float(t.entry_price))
            for t in trades
            if t.pnl is not None and t.quantity and t.entry_price
        ]
        if len(returns) < 2:
            return {"error": "Insufficient data for risk analysis"}

        import statistics

        total_return = sum(returns)
        avg_return = statistics.mean(returns)
        volatility = statistics.stdev(returns)

        equity_curve = []
        running_pnl = 0
        for trade in sorted(trades, key=lambda x: x.opened_at):
            if trade.pnl is not None:
                running_pnl += float(trade.pnl)
                equity_curve.append(running_pnl)

        if equity_curve:
            peak = equity_curve[0]
            max_drawdown = 0
            current_drawdown_start = None
            longest_drawdown = 0

            for i, equity in enumerate(equity_curve):
                if equity > peak:
                    peak = equity
                    if current_drawdown_start is not None:
                        longest_drawdown = max(longest_drawdown, i - current_drawdown_start)
                        current_drawdown_start = None

                drawdown = (equity - peak) / peak if peak != 0 else 0
                if drawdown < max_drawdown:
                    max_drawdown = drawdown

                if drawdown < -0.05 and current_drawdown_start is None:
                    current_drawdown_start = i
        else:
            max_drawdown = 0
            longest_drawdown = 0

        returns_sorted = sorted(returns)
        var_99 = returns_sorted[int(len(returns_sorted) * 0.01)] if len(returns_sorted) > 100 else returns_sorted[0]
        var_95 = returns_sorted[int(len(returns_sorted) * 0.05)] if len(returns_sorted) > 20 else returns_sorted[0]
        var_90 = returns_sorted[int(len(returns_sorted) * 0.10)] if len(returns_sorted) > 10 else returns_sorted[0]

        es_95_threshold = int(len(returns_sorted) * 0.05)
        expected_shortfall_95 = statistics.mean(returns_sorted[:es_95_threshold]) if es_95_threshold > 0 else 0

        sortino_ratio = 0
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_deviation = statistics.stdev(downside_returns)
            sortino_ratio = avg_return / downside_deviation if downside_deviation > 0 else 0

        calmar_ratio = (total_return / abs(max_drawdown)) if max_drawdown != 0 else 0

        n = len(returns)
        mean = avg_return
        skewness = 0
        kurtosis = 0
        if n > 2 and volatility > 0:
            third_moment = sum(((x - mean) ** 3) for x in returns) / n
            fourth_moment = sum(((x - mean) ** 4) for x in returns) / n

            skewness = third_moment / (volatility ** 3)
            kurtosis = (fourth_moment / (volatility ** 4)) - 3

        return {
            "total_return": round(total_return, 4),
            "volatility": round(volatility, 4),
            "sharpe_ratio": round((avg_return / volatility) if volatility > 0 else 0, 3),
            "sortino_ratio": round(sortino_ratio, 3),
            "calmar_ratio": round(calmar_ratio, 3),
            "max_drawdown": round(max_drawdown * 100, 2),
            "longest_drawdown_periods": longest_drawdown,
            "var_99": round(var_99, 4),
            "var_95": round(var_95, 4),
            "var_90": round(var_90, 4),
            "expected_shortfall_95": round(expected_shortfall_95, 4),
            "downside_deviation": round(statistics.stdev(downside_returns), 4) if downside_returns else 0,
            "skewness": round(skewness, 3),
            "kurtosis": round(kurtosis, 3),
            "total_trades": len(trades),
            "risk_score": self._calculate_risk_score(max_drawdown, volatility, sortino_ratio)
        }

    def _calculate_risk_score(self, max_drawdown: float, volatility: float, sortino_ratio: float) -> Dict[str, Any]:
        """Calcula un score de riesgo compuesto (1-100)"""
        drawdown_score = min(abs(max_drawdown) * 500, 100)
        volatility_score = min(volatility / 10 * 100, 100)
        sortino_score = max(0, 100 - (sortino_ratio * 50))

        composite_score = (drawdown_score * 0.4 + volatility_score * 0.4 + sortino_score * 0.2)

        if composite_score <= 25:
            risk_level = "Low"
            risk_color = "green"
        elif composite_score <= 50:
            risk_level = "Moderate"
            risk_color = "yellow"
        elif composite_score <= 75:
            risk_level = "High"
            risk_color = "orange"
        else:
            risk_level = "Very High"
            risk_color = "red"

        return {
            "score": round(composite_score, 1),
            "level": risk_level,
            "color": risk_color,
            "components": {
                "drawdown": round(drawdown_score, 1),
                "volatility": round(volatility_score, 1),
                "sortino": round(sortino_score, 1)
            }
        }

    def _get_var_analysis(self, query) -> Dict[str, Any]:
        """Análisis detallado de Value at Risk"""
        trades = query.all()
        if len(trades) < 10:
            return {"error": "Insufficient data for VaR analysis"}

        returns = [
            float(t.pnl) / (float(t.quantity) * float(t.entry_price))
            for t in trades
            if t.pnl is not None and t.quantity and t.entry_price
        ]
        returns_sorted = sorted(returns)

        var_levels = [0.01, 0.05, 0.10, 0.25]
        var_results = {}

        for level in var_levels:
            index = int(len(returns_sorted) * level)
            var_value = returns_sorted[index] if index < len(returns_sorted) else returns_sorted[0]
            confidence = int((1 - level) * 100)

            var_results[f"var_{confidence}"] = {
                "value": round(var_value, 4),
                "confidence": f"{confidence}%",
                "interpretation": f"{confidence}% confidence returns won't drop below {abs(var_value) * 100:.1f}%"
            }

        es_threshold = int(len(returns_sorted) * 0.05)
        tail_losses = returns_sorted[:es_threshold] if es_threshold > 0 else [returns_sorted[0]]
        expected_shortfall = statistics.mean(tail_losses)

        return {
            "var_levels": var_results,
            "expected_shortfall": {
                "value": round(expected_shortfall, 4),
                "interpretation": f"Average loss in worst 5% of cases: {abs(expected_shortfall) * 100:.1f}%"
            },
            "worst_case": {
                "single_trade": round(min(returns), 4),
                "percentile_1": var_results["var_99"]["value"]
            }
        }

    def _analyze_position_sizing(self, query) -> Dict[str, Any]:
        """Análisis de position sizing y concentración de riesgo"""
        trades = query.all()
        if not trades:
            return {"error": "No trades for position analysis"}

        position_sizes = []
        pnl_by_size = {}

        for trade in trades:
            if trade.quantity and trade.entry_price:
                position_value = float(trade.quantity * trade.entry_price)
                position_sizes.append(position_value)

                if position_value < 1000:
                    size_category = "Small (<$1K)"
                elif position_value < 5000:
                    size_category = "Medium ($1K-$5K)"
                elif position_value < 10000:
                    size_category = "Large ($5K-$10K)"
                else:
                    size_category = "Very Large (>$10K)"

                if size_category not in pnl_by_size:
                    pnl_by_size[size_category] = {"trades": 0, "total_pnl": 0, "positions": []}

                pnl_by_size[size_category]["trades"] += 1
                pnl_by_size[size_category]["total_pnl"] += float(trade.pnl or 0)
                pnl_by_size[size_category]["positions"].append(position_value)

        if position_sizes:
            import statistics
            avg_position = statistics.mean(position_sizes)
            max_position = max(position_sizes)
            concentration_ratio = max_position / avg_position if avg_position > 0 else 0

            sorted_positions = sorted(position_sizes, reverse=True)
            top_20_percent = sorted_positions[:max(1, len(sorted_positions) // 5)]
            concentration_top_20 = sum(top_20_percent) / sum(position_sizes) * 100
        else:
            avg_position = max_position = concentration_ratio = concentration_top_20 = 0

        size_analysis = []
        for category, data in pnl_by_size.items():
            avg_pnl = data["total_pnl"] / data["trades"] if data["trades"] > 0 else 0
            avg_position_size = statistics.mean(data["positions"]) if data["positions"] else 0

            size_analysis.append({
                "category": category,
                "trades": data["trades"],
                "total_pnl": round(data["total_pnl"], 2),
                "avg_pnl": round(avg_pnl, 2),
                "avg_position_size": round(avg_position_size, 2),
                "percentage_of_trades": round((data["trades"] / len(trades)) * 100, 1)
            })

        return {
            "position_analysis": size_analysis,
            "concentration_metrics": {
                "avg_position_size": round(avg_position, 2),
                "max_position_size": round(max_position, 2),
                "concentration_ratio": round(concentration_ratio, 2),
                "top_20_percent_concentration": round(concentration_top_20, 1)
            },
            "risk_assessment": {
                "diversification_score": min(100, 100 / concentration_ratio) if concentration_ratio > 0 else 100,
                "size_consistency": "Good" if concentration_ratio < 5 else "Poor"
            }
        }

    def _analyze_symbol_exposure(self, query) -> List[Dict[str, Any]]:
        """Análisis de exposición por símbolo"""
        trades = query.all()
        if not trades:
            return []

        symbol_stats = {}

        for trade in trades:
            symbol = trade.symbol
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    "trades": 0,
                    "total_pnl": 0,
                    "total_volume": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "max_win": 0,
                    "max_loss": 0,
                    "returns": []
                }

            symbol_stats[symbol]["trades"] += 1

            if trade.pnl is not None:
                pnl = float(trade.pnl)
                symbol_stats[symbol]["total_pnl"] += pnl
                if trade.quantity and trade.entry_price:
                    ret = pnl / (float(trade.quantity) * float(trade.entry_price))
                    symbol_stats[symbol]["returns"].append(ret)

                if pnl > 0:
                    symbol_stats[symbol]["winning_trades"] += 1
                    symbol_stats[symbol]["max_win"] = max(symbol_stats[symbol]["max_win"], pnl)
                else:
                    symbol_stats[symbol]["losing_trades"] += 1
                    symbol_stats[symbol]["max_loss"] = min(symbol_stats[symbol]["max_loss"], pnl)

            if trade.quantity and trade.entry_price:
                symbol_stats[symbol]["total_volume"] += float(trade.quantity * trade.entry_price)

        exposure_analysis = []
        total_pnl = sum(stats["total_pnl"] for stats in symbol_stats.values())
        total_volume = sum(stats["total_volume"] for stats in symbol_stats.values())

        for symbol, stats in symbol_stats.items():
            win_rate = (stats["winning_trades"] / stats["trades"]) * 100 if stats["trades"] > 0 else 0
            pnl_contribution = (stats["total_pnl"] / total_pnl) * 100 if total_pnl != 0 else 0
            volume_share = (stats["total_volume"] / total_volume) * 100 if total_volume > 0 else 0

            symbol_volatility = 0
            if len(stats["returns"]) > 1:
                import statistics
                symbol_volatility = statistics.stdev(stats["returns"])

            exposure_analysis.append({
                "symbol": symbol,
                "trades": stats["trades"],
                "total_pnl": round(stats["total_pnl"], 2),
                "win_rate": round(win_rate, 1),
                "pnl_contribution": round(pnl_contribution, 1),
                "volume_share": round(volume_share, 1),
                "max_win": round(stats["max_win"], 2),
                "max_loss": round(stats["max_loss"], 2),
                "volatility": round(symbol_volatility, 2),
                "risk_score": round((abs(stats["max_loss"]) + symbol_volatility) / 2, 2)
            })

        return sorted(exposure_analysis, key=lambda x: abs(x["pnl_contribution"]), reverse=True)

    def _analyze_time_based_risk(self, query) -> Dict[str, Any]:
        """Análisis de riesgo basado en tiempo"""
        trades = query.all()
        if not trades:
            return {"error": "No trades for time analysis"}

        hourly_stats = {}
        daily_stats = {}

        for trade in trades:
            if trade.opened_at and trade.pnl:
                hour = trade.opened_at.hour
                if hour not in hourly_stats:
                    hourly_stats[hour] = {"trades": 0, "total_pnl": 0, "returns": []}

                hourly_stats[hour]["trades"] += 1
                hourly_stats[hour]["total_pnl"] += float(trade.pnl)
                if trade.quantity and trade.entry_price:
                    hourly_stats[hour]["returns"].append(float(trade.pnl) / (float(trade.quantity) * float(trade.entry_price)))

                day_name = trade.opened_at.strftime("%A")
                if day_name not in daily_stats:
                    daily_stats[day_name] = {"trades": 0, "total_pnl": 0, "returns": []}

                daily_stats[day_name]["trades"] += 1
                daily_stats[day_name]["total_pnl"] += float(trade.pnl)
                if trade.quantity and trade.entry_price:
                    daily_stats[day_name]["returns"].append(float(trade.pnl) / (float(trade.quantity) * float(trade.entry_price)))

        hourly_analysis = []
        for hour in sorted(hourly_stats.keys()):
            stats = hourly_stats[hour]
            avg_pnl = stats["total_pnl"] / stats["trades"] if stats["trades"] > 0 else 0

            import statistics
            volatility = statistics.stdev(stats["returns"]) if len(stats["returns"]) > 1 else 0

            hourly_analysis.append({
                "hour": f"{hour:02d}:00",
                "trades": stats["trades"],
                "total_pnl": round(stats["total_pnl"], 2),
                "avg_pnl": round(avg_pnl, 2),
                "volatility": round(volatility, 2),
                "risk_score": round(volatility / max(abs(avg_pnl), 1), 2)
            })

        daily_analysis = []
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for day in days_order:
            if day in daily_stats:
                stats = daily_stats[day]
                avg_pnl = stats["total_pnl"] / stats["trades"] if stats["trades"] > 0 else 0

                volatility = statistics.stdev(stats["returns"]) if len(stats["returns"]) > 1 else 0

                daily_analysis.append({
                    "day": day,
                    "trades": stats["trades"],
                    "total_pnl": round(stats["total_pnl"], 2),
                    "avg_pnl": round(avg_pnl, 2),
                    "volatility": round(volatility, 2)
                })

        return {
            "hourly_analysis": hourly_analysis,
            "daily_analysis": daily_analysis,
            "best_trading_hours": sorted(hourly_analysis, key=lambda x: x["avg_pnl"], reverse=True)[:3],
            "worst_trading_hours": sorted(hourly_analysis, key=lambda x: x["avg_pnl"])[:3],
            "best_trading_days": sorted(daily_analysis, key=lambda x: x["avg_pnl"], reverse=True)[:3]
        }

    def _calculate_risk_adjusted_returns(self, query) -> Dict[str, Any]:
        """Calcula múltiples métricas de retorno ajustado por riesgo"""
        trades = query.all()
        if len(trades) < 2:
            return {"error": "Insufficient data for risk-adjusted returns"}

        returns = [
            float(t.pnl) / (float(t.quantity) * float(t.entry_price))
            for t in trades
            if t.pnl is not None and t.quantity and t.entry_price
        ]
        if len(returns) < 2:
            return {"error": "Insufficient return data"}

        import statistics

        avg_return = statistics.mean(returns)
        volatility = statistics.stdev(returns)
        total_return = sum(returns)

        risk_free_rate = 0.02 / 252

        sharpe = (avg_return - risk_free_rate) / volatility if volatility > 0 else 0

        downside_returns = [r for r in returns if r < risk_free_rate]
        sortino = 0
        if downside_returns:
            downside_deviation = statistics.stdev(downside_returns)
            sortino = (avg_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0

        information_ratio = avg_return / volatility if volatility > 0 else 0

        treynor = avg_return - risk_free_rate

        return {
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "information_ratio": round(information_ratio, 3),
            "treynor_ratio": round(treynor, 3),
            "jensen_alpha": round(avg_return - risk_free_rate, 3),
            "interpretation": {
                "sharpe": "Excellent" if sharpe > 2 else "Good" if sharpe > 1 else "Fair" if sharpe > 0 else "Poor",
                "sortino": "Excellent" if sortino > 3 else "Good" if sortino > 2 else "Fair" if sortino > 0 else "Poor"
            }
        }

    def _analyze_correlations(self, query) -> Dict[str, Any]:
        """Análisis básico de correlaciones entre símbolos"""
        trades = query.all()
        if not trades:
            return {"error": "No trades for correlation analysis"}

        symbol_daily_pnl = {}

        for trade in trades:
            if trade.symbol and trade.pnl and trade.opened_at:
                date_key = trade.opened_at.date()

                if trade.symbol not in symbol_daily_pnl:
                    symbol_daily_pnl[trade.symbol] = {}

                if date_key not in symbol_daily_pnl[trade.symbol]:
                    symbol_daily_pnl[trade.symbol][date_key] = 0

                symbol_daily_pnl[trade.symbol][date_key] += float(trade.pnl)

        symbols_with_data = [s for s, data in symbol_daily_pnl.items() if len(data) >= 5]

        if len(symbols_with_data) < 2:
            return {"message": "Insufficient data for correlation analysis (need 2+ symbols with 5+ trading days each)"}

        correlations = []
        symbols_subset = symbols_with_data[:5]

        for i, symbol1 in enumerate(symbols_subset):
            for symbol2 in symbols_subset[i + 1:]:
                dates1 = set(symbol_daily_pnl[symbol1].keys())
                dates2 = set(symbol_daily_pnl[symbol2].keys())
                common_dates = dates1.intersection(dates2)

                if len(common_dates) >= 3:
                    values1 = [symbol_daily_pnl[symbol1][date] for date in sorted(common_dates)]
                    values2 = [symbol_daily_pnl[symbol2][date] for date in sorted(common_dates)]

                    if len(values1) > 1:
                        import statistics
                        mean1, mean2 = statistics.mean(values1), statistics.mean(values2)

                        numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))

                        std1 = statistics.stdev(values1) if len(values1) > 1 else 1
                        std2 = statistics.stdev(values2) if len(values2) > 1 else 1

                        correlation = numerator / (len(values1) * std1 * std2) if std1 > 0 and std2 > 0 else 0

                        correlations.append({
                            "pair": f"{symbol1}/{symbol2}",
                            "correlation": round(correlation, 3),
                            "strength": "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.3 else "Weak",
                            "common_days": len(common_dates)
                        })

        return {
            "correlations": sorted(correlations, key=lambda x: abs(x["correlation"]), reverse=True),
            "diversification_score": 100 - (sum(abs(c["correlation"]) for c in correlations) / len(correlations) * 100) if correlations else 100,
            "analysis_summary": f"Analyzed {len(correlations)} symbol pairs from {len(symbols_subset)} most active symbols"
        }

    def _get_risk_limits_status(self, user_id: int, portfolio_id: int) -> Dict[str, Any]:
        """Obtiene estado actual de los límites de riesgo configurados"""
        from app.models.risk_limit import RiskLimit

        risk_limit = self.db.query(RiskLimit).filter(
            and_(
                RiskLimit.user_id == user_id,
                RiskLimit.portfolio_id == portfolio_id
            )
        ).first()

        if not risk_limit:
            return {"status": "No risk limits configured"}

        current_usage = {}

        recent_trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.opened_at >= datetime.utcnow() - timedelta(days=1)
            )
        ).all()

        daily_pnl = sum(float(t.pnl) for t in recent_trades if t.pnl is not None)

        return {
            "configured_limits": {
                "max_daily_drawdown": risk_limit.max_daily_drawdown,
                "max_weekly_drawdown": risk_limit.max_weekly_drawdown,
                "max_position_size": risk_limit.max_position_size,
                "max_orders_per_hour": risk_limit.max_orders_per_hour,
                "trading_hours": f"{risk_limit.trading_start_time} - {risk_limit.trading_end_time}"
            },
            "current_usage": {
                "daily_pnl": round(daily_pnl, 2),
                "daily_drawdown_used": round((abs(daily_pnl) / risk_limit.max_daily_drawdown) * 100, 1) if risk_limit.max_daily_drawdown else 0
            },
            "status": "Active" if risk_limit else "Inactive"
        }

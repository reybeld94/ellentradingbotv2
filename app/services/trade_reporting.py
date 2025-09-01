from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.models.trades import Trade
from app.models.strategy import Strategy
from app.models.user import User
from app.services.strategy_manager import StrategyManager
from app.services.advanced_position_manager import AdvancedPositionManager
from app.utils.time import now_eastern, to_eastern

logger = logging.getLogger(__name__)


class TradeReporting:
    def __init__(self, db: Session):
        self.db = db
        self.strategy_manager = StrategyManager(db)
        self.position_manager = AdvancedPositionManager(db)
    
    def generate_daily_report(self, user_id: int, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generar reporte completo del día"""
        try:
            target_date = date or now_eastern().date()
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            # Trades del día
            daily_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                or_(
                    and_(Trade.opened_at >= start_datetime, Trade.opened_at <= end_datetime),
                    and_(Trade.closed_at >= start_datetime, Trade.closed_at <= end_datetime)
                )
            ).all()
            
            # Separar trades abiertos y cerrados
            opened_today = [t for t in daily_trades if t.opened_at and 
                          start_datetime <= t.opened_at <= end_datetime]
            closed_today = [t for t in daily_trades if t.closed_at and 
                          start_datetime <= t.closed_at <= end_datetime]
            
            # Métricas del día
            daily_pnl = sum(t.pnl or 0 for t in closed_today)
            daily_volume = sum(t.quantity * t.entry_price for t in opened_today)
            
            # Análisis por estrategia
            strategy_performance = defaultdict(lambda: {
                'trades_opened': 0,
                'trades_closed': 0,
                'pnl': 0.0,
                'volume': 0.0
            })
            
            for trade in opened_today:
                strategy_id = trade.strategy_id or 'unknown'
                strategy_performance[strategy_id]['trades_opened'] += 1
                strategy_performance[strategy_id]['volume'] += trade.quantity * trade.entry_price
            
            for trade in closed_today:
                strategy_id = trade.strategy_id or 'unknown'
                strategy_performance[strategy_id]['trades_closed'] += 1
                strategy_performance[strategy_id]['pnl'] += trade.pnl or 0
            
            # Top symbols del día
            symbol_activity = defaultdict(lambda: {'trades': 0, 'volume': 0.0, 'pnl': 0.0})
            for trade in daily_trades:
                symbol_activity[trade.symbol]['trades'] += 1
                symbol_activity[trade.symbol]['volume'] += trade.quantity * trade.entry_price
                if trade.status == 'closed':
                    symbol_activity[trade.symbol]['pnl'] += trade.pnl or 0
            
            # Ordenar por volumen
            top_symbols = sorted(
                symbol_activity.items(), 
                key=lambda x: x[1]['volume'], 
                reverse=True
            )[:10]
            
            return {
                "report_date": target_date.isoformat(),
                "summary": {
                    "trades_opened": len(opened_today),
                    "trades_closed": len(closed_today),
                    "daily_pnl": round(daily_pnl, 2),
                    "daily_volume": round(daily_volume, 2),
                    "unique_symbols": len(symbol_activity),
                    "active_strategies": len([s for s in strategy_performance.keys() if strategy_performance[s]['trades_opened'] > 0])
                },
                "strategy_breakdown": dict(strategy_performance),
                "top_symbols": [{"symbol": symbol, **data} for symbol, data in top_symbols],
                "winning_trades": len([t for t in closed_today if t.pnl and t.pnl > 0]),
                "losing_trades": len([t for t in closed_today if t.pnl and t.pnl < 0]),
                "win_rate": len([t for t in closed_today if t.pnl and t.pnl > 0]) / len(closed_today) if closed_today else 0,
                "generated_at": now_eastern().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {"error": str(e)}
    
    def generate_weekly_report(self, user_id: int, weeks_back: int = 0) -> Dict[str, Any]:
        """Generar reporte semanal"""
        try:
            # Calcular fechas de la semana
            today = now_eastern().date()
            start_of_week = today - timedelta(days=today.weekday() + (weeks_back * 7))
            end_of_week = start_of_week + timedelta(days=6)
            
            start_datetime = datetime.combine(start_of_week, datetime.min.time())
            end_datetime = datetime.combine(end_of_week, datetime.max.time())
            
            # Trades de la semana
            weekly_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.closed_at >= start_datetime,
                Trade.closed_at <= end_datetime,
                Trade.status == "closed"
            ).all()
            
            if not weekly_trades:
                return {
                    "week_start": start_of_week.isoformat(),
                    "week_end": end_of_week.isoformat(),
                    "message": "No trades found for this week"
                }
            
            # Análisis diario dentro de la semana
            daily_breakdown = defaultdict(lambda: {
                'trades': 0, 
                'pnl': 0.0, 
                'volume': 0.0,
                'winners': 0,
                'losers': 0
            })
            
            for trade in weekly_trades:
                if trade.closed_at:
                    day_key = trade.closed_at.strftime("%Y-%m-%d")
                    daily_breakdown[day_key]['trades'] += 1
                    daily_breakdown[day_key]['pnl'] += trade.pnl or 0
                    daily_breakdown[day_key]['volume'] += trade.quantity * trade.entry_price
                    
                    if trade.pnl and trade.pnl > 0:
                        daily_breakdown[day_key]['winners'] += 1
                    elif trade.pnl and trade.pnl < 0:
                        daily_breakdown[day_key]['losers'] += 1
            
            # Métricas de la semana
            weekly_pnl = sum(t.pnl or 0 for t in weekly_trades)
            weekly_volume = sum(t.quantity * t.entry_price for t in weekly_trades)
            winning_days = len([day for day in daily_breakdown.values() if day['pnl'] > 0])
            
            # Best y worst day
            best_day = max(daily_breakdown.items(), key=lambda x: x[1]['pnl']) if daily_breakdown else None
            worst_day = min(daily_breakdown.items(), key=lambda x: x[1]['pnl']) if daily_breakdown else None
            
            # Análisis de consistencia
            daily_pnls = [day['pnl'] for day in daily_breakdown.values()]
            consistency_score = self._calculate_consistency(daily_pnls)
            
            return {
                "week_start": start_of_week.isoformat(),
                "week_end": end_of_week.isoformat(),
                "summary": {
                    "total_trades": len(weekly_trades),
                    "weekly_pnl": round(weekly_pnl, 2),
                    "weekly_volume": round(weekly_volume, 2),
                    "trading_days": len(daily_breakdown),
                    "winning_days": winning_days,
                    "losing_days": len(daily_breakdown) - winning_days,
                    "consistency_score": round(consistency_score, 2),
                    "avg_daily_pnl": round(weekly_pnl / len(daily_breakdown), 2) if daily_breakdown else 0
                },
                "daily_breakdown": dict(daily_breakdown),
                "best_day": {"date": best_day[0], "pnl": round(best_day[1]['pnl'], 2)} if best_day else None,
                "worst_day": {"date": worst_day[0], "pnl": round(worst_day[1]['pnl'], 2)} if worst_day else None,
                "generated_at": now_eastern().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {"error": str(e)}
    
    def generate_strategy_comparison_report(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Comparar performance entre todas las estrategias activas"""
        try:
            # Obtener todas las estrategias del usuario
            user_strategies = self.strategy_manager.get_user_strategies(user_id, active_only=False)
            
            if not user_strategies:
                return {"error": "No strategies found"}
            
            strategy_comparisons = []
            
            for strategy in user_strategies:
                # Performance de cada estrategia
                performance = self.strategy_manager.get_strategy_performance(strategy.id, user_id)
                
                # Trades recientes (últimos N días)
                cutoff_date = now_eastern() - timedelta(days=days)
                recent_trades = self.db.query(Trade).filter(
                    Trade.user_id == user_id,
                    Trade.strategy_id == str(strategy.id),
                    Trade.closed_at >= cutoff_date,
                    Trade.status == "closed"
                ).count()
                
                # Agregar datos de actividad reciente
                performance.update({
                    "recent_trades_count": recent_trades,
                    "is_active": strategy.is_active,
                    "activity_score": self._calculate_activity_score(recent_trades, days)
                })
                
                strategy_comparisons.append(performance)
            
            # Ordenar por profit factor
            strategy_comparisons.sort(key=lambda x: x.get('profit_factor', 0), reverse=True)
            
            # Estadísticas del comparison
            total_strategies = len(strategy_comparisons)
            profitable_strategies = len([s for s in strategy_comparisons if s.get('total_pnl', 0) > 0])
            
            # Top performer
            top_strategy = strategy_comparisons[0] if strategy_comparisons else None
            
            # Estrategia más activa
            most_active = max(strategy_comparisons, key=lambda x: x.get('recent_trades_count', 0)) if strategy_comparisons else None
            
            return {
                "comparison_period_days": days,
                "strategies": strategy_comparisons,
                "summary": {
                    "total_strategies": total_strategies,
                    "profitable_strategies": profitable_strategies,
                    "unprofitable_strategies": total_strategies - profitable_strategies,
                    "profitability_rate": round((profitable_strategies / total_strategies) * 100, 2) if total_strategies > 0 else 0
                },
                "highlights": {
                    "top_performer": {
                        "strategy_name": top_strategy.get('strategy_name'),
                        "profit_factor": top_strategy.get('profit_factor'),
                        "total_pnl": top_strategy.get('total_pnl')
                    } if top_strategy else None,
                    "most_active": {
                        "strategy_name": most_active.get('strategy_name'),
                        "recent_trades": most_active.get('recent_trades_count')
                    } if most_active else None
                },
                "generated_at": now_eastern().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating strategy comparison: {e}")
            return {"error": str(e)}
    
    def generate_portfolio_health_report(self, user_id: int) -> Dict[str, Any]:
        """Reporte completo de salud del portfolio"""
        try:
            # Obtener datos de diferentes servicios
            positions_data = self.position_manager.track_open_positions(user_id)
            exposure_data = self.position_manager.calculate_exposure(user_id)
            daily_report = self.generate_daily_report(user_id)
            
            # Análisis de riesgo
            risk_indicators = []
            risk_score = 0
            
            # Check 1: Concentración
            if exposure_data.get("concentration_analysis", {}).get("concentration_score", 0) > 2:
                risk_indicators.append("High position concentration detected")
                risk_score += 20
            
            # Check 2: Exposición total
            total_exposure = exposure_data.get("total_exposure_pct", 0)
            if total_exposure > 95:
                risk_indicators.append("Very high portfolio exposure")
                risk_score += 30
            elif total_exposure > 80:
                risk_indicators.append("High portfolio exposure")
                risk_score += 15
            
            # Check 3: Número de posiciones abiertas
            open_positions = positions_data.get("summary", {}).get("total_positions", 0)
            if open_positions > 15:
                risk_indicators.append("High number of open positions")
                risk_score += 10
            
            # Check 4: PnL no realizado
            unrealized_pnl = positions_data.get("summary", {}).get("total_unrealized_pnl", 0)
            if unrealized_pnl < -5000:  # Más de $5k en pérdidas no realizadas
                risk_indicators.append("Significant unrealized losses")
                risk_score += 25
            
            # Determinar nivel de riesgo
            if risk_score <= 20:
                risk_level = "Low"
                risk_color = "green"
            elif risk_score <= 50:
                risk_level = "Medium" 
                risk_color = "yellow"
            else:
                risk_level = "High"
                risk_color = "red"
            
            # Recomendaciones
            recommendations = []
            
            if total_exposure > 90:
                recommendations.append("Consider reducing overall exposure")
            
            if open_positions > 10:
                recommendations.append("Consider consolidating positions")
            
            if len(exposure_data.get("exposure", {}).get("by_sector", {})) < 3:
                recommendations.append("Improve sector diversification")
            
            return {
                "portfolio_health": {
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "risk_color": risk_color,
                    "risk_indicators": risk_indicators
                },
                "current_positions": positions_data.get("summary", {}),
                "exposure_analysis": exposure_data.get("exposure", {}),
                "today_performance": daily_report.get("summary", {}),
                "recommendations": recommendations,
                "health_metrics": {
                    "diversification_score": len(exposure_data.get("exposure", {}).get("by_sector", {})) * 20,
                    "activity_level": "High" if daily_report.get("summary", {}).get("trades_opened", 0) > 5 else "Normal",
                    "position_management": "Good" if open_positions <= 10 else "Needs Attention"
                },
                "generated_at": now_eastern().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating portfolio health report: {e}")
            return {"error": str(e)}
    
    def _calculate_consistency(self, daily_pnls: List[float]) -> float:
        """Calcular score de consistencia basado en volatilidad de PnL diario"""
        if len(daily_pnls) <= 1:
            return 0.0
        
        mean_pnl = sum(daily_pnls) / len(daily_pnls)
        variance = sum((pnl - mean_pnl) ** 2 for pnl in daily_pnls) / len(daily_pnls)
        std_dev = variance ** 0.5
        
        # Score inverso a la volatilidad (más consistente = menos volátil)
        consistency = max(0, 100 - (std_dev / abs(mean_pnl) * 100)) if mean_pnl != 0 else 50
        return min(100, consistency)
    
    def _calculate_activity_score(self, recent_trades: int, days: int) -> str:
        """Calcular nivel de actividad de una estrategia"""
        trades_per_day = recent_trades / days if days > 0 else 0
        
        if trades_per_day >= 2:
            return "Very Active"
        elif trades_per_day >= 0.5:
            return "Active"
        elif trades_per_day >= 0.1:
            return "Moderate"
        else:
            return "Inactive"

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.models.strategy_position import StrategyPosition
from app.models.trades import Trade
from app.core.types import TradeStatus
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services import portfolio_service
from app.utils.time import now_eastern

logger = logging.getLogger(__name__)


class AdvancedPositionManager:
    def __init__(self, db: Session):
        self.db = db
    
    def track_open_positions(self, user_id: int, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
        """Estado actual de todas las posiciones abiertas"""
        try:
            # Si no se especifica portfolio, usar el activo
            if not portfolio_id:
                portfolio = portfolio_service.get_active(self.db, User(id=user_id))
                portfolio_id = portfolio.id if portfolio else None
            
            if not portfolio_id:
                return {"error": "No active portfolio found"}
            
            # Query posiciones abiertas
            open_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.portfolio_id == portfolio_id,
                Trade.status == TradeStatus.OPEN
            ).all()
            
            positions_summary = []
            total_exposure = 0.0
            total_unrealized_pnl = 0.0
            
            # Agrupar por símbolo y estrategia
            position_groups = defaultdict(list)
            for trade in open_trades:
                key = f"{trade.symbol}_{trade.strategy_id}"
                position_groups[key].append(trade)
            
            for group_key, trades in position_groups.items():
                symbol = trades[0].symbol
                strategy_id = trades[0].strategy_id
                
                # Consolidar información de la posición
                total_qty = sum(trade.quantity for trade in trades)
                total_cost = sum(trade.quantity * trade.entry_price for trade in trades)
                avg_price = total_cost / total_qty if total_qty != 0 else 0
                
                # Calcular unrealized PnL (necesitaría precio actual - placeholder)
                current_price = avg_price * 1.02  # Placeholder - integrar con precio real
                unrealized_pnl = (current_price - avg_price) * total_qty
                position_value = current_price * total_qty
                
                position_info = {
                    "symbol": symbol,
                    "strategy_id": strategy_id,
                    "quantity": round(total_qty, 4),
                    "avg_entry_price": round(avg_price, 2),
                    "current_price": round(current_price, 2),  # Placeholder
                    "position_value": round(position_value, 2),
                    "unrealized_pnl": round(unrealized_pnl, 2),
                    "unrealized_pnl_pct": round((unrealized_pnl / total_cost) * 100, 2) if total_cost > 0 else 0,
                    "trades_count": len(trades),
                    "oldest_trade": min(trade.opened_at for trade in trades if trade.opened_at),
                    "side": "long" if total_qty > 0 else "short"
                }
                
                positions_summary.append(position_info)
                total_exposure += abs(position_value)
                total_unrealized_pnl += unrealized_pnl
            
            return {
                "positions": positions_summary,
                "summary": {
                    "total_positions": len(positions_summary),
                    "total_exposure": round(total_exposure, 2),
                    "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                    "long_positions": len([p for p in positions_summary if p["side"] == "long"]),
                    "short_positions": len([p for p in positions_summary if p["side"] == "short"]),
                    "updated_at": now_eastern().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error tracking positions: {e}")
            return {"error": str(e)}
    
    def calculate_exposure(self, user_id: int, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
        """Calcular exposición por sector, símbolo y estrategia"""
        try:
            positions_data = self.track_open_positions(user_id, portfolio_id)
            if "error" in positions_data:
                return positions_data
            
            positions = positions_data.get("positions", [])
            total_portfolio_value = 100000  # Placeholder - obtener del portfolio real
            
            # Exposición por símbolo
            symbol_exposure = defaultdict(float)
            for pos in positions:
                symbol_exposure[pos["symbol"]] += abs(pos["position_value"])
            
            # Convertir a porcentajes
            symbol_exposure_pct = {
                symbol: round((value / total_portfolio_value) * 100, 2)
                for symbol, value in symbol_exposure.items()
            }
            
            # Exposición por estrategia
            strategy_exposure = defaultdict(float)
            strategy_pnl = defaultdict(float)
            for pos in positions:
                strategy_id = pos["strategy_id"]
                strategy_exposure[strategy_id] += abs(pos["position_value"])
                strategy_pnl[strategy_id] += pos["unrealized_pnl"]
            
            strategy_exposure_pct = {
                strategy: round((value / total_portfolio_value) * 100, 2)
                for strategy, value in strategy_exposure.items()
            }
            
            # Exposición por sector (placeholder - necesita mapeo de símbolos a sectores)
            sector_mapping = self._get_sector_mapping()
            sector_exposure = defaultdict(float)
            
            for pos in positions:
                sector = sector_mapping.get(pos["symbol"], "Unknown")
                sector_exposure[sector] += abs(pos["position_value"])
            
            sector_exposure_pct = {
                sector: round((value / total_portfolio_value) * 100, 2)
                for sector, value in sector_exposure.items()
            }
            
            # Análisis de concentración
            concentration_analysis = self._analyze_concentration(
                symbol_exposure_pct, 
                sector_exposure_pct, 
                strategy_exposure_pct
            )
            
            return {
                "exposure": {
                    "by_symbol": dict(symbol_exposure_pct),
                    "by_sector": dict(sector_exposure_pct),
                    "by_strategy": dict(strategy_exposure_pct)
                },
                "concentration_analysis": concentration_analysis,
                "total_exposure_pct": round(sum(symbol_exposure.values()) / total_portfolio_value * 100, 2),
                "portfolio_value": total_portfolio_value,
                "analysis_date": now_eastern().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating exposure: {e}")
            return {"error": str(e)}
    
    def get_position_history(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Historial de posiciones en los últimos N días"""
        try:
            end_date = now_eastern()
            start_date = end_date - timedelta(days=days)
            
            # Trades cerrados en el período
            closed_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.closed_at >= start_date,
                Trade.closed_at <= end_date
            ).order_by(Trade.closed_at.desc()).all()
            
            # Análisis por día
            daily_analysis = defaultdict(lambda: {
                "trades_opened": 0,
                "trades_closed": 0,
                "realized_pnl": 0.0,
                "symbols_traded": set()
            })
            
            for trade in closed_trades:
                if trade.closed_at:
                    day_key = trade.closed_at.strftime("%Y-%m-%d")
                    daily_analysis[day_key]["trades_closed"] += 1
                    daily_analysis[day_key]["realized_pnl"] += trade.pnl or 0
                    daily_analysis[day_key]["symbols_traded"].add(trade.symbol)
                
                if trade.opened_at and trade.opened_at >= start_date:
                    open_day_key = trade.opened_at.strftime("%Y-%m-%d")
                    daily_analysis[open_day_key]["trades_opened"] += 1
            
            # Convertir sets a listas para JSON serialization
            for day_data in daily_analysis.values():
                day_data["symbols_traded"] = list(day_data["symbols_traded"])
                day_data["unique_symbols"] = len(day_data["symbols_traded"])
            
            return {
                "period": f"{days} days",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily_breakdown": dict(daily_analysis),
                "summary": {
                    "total_trades_closed": len(closed_trades),
                    "total_realized_pnl": round(sum(t.pnl or 0 for t in closed_trades), 2),
                    "unique_symbols": len(set(t.symbol for t in closed_trades)),
                    "unique_strategies": len(set(t.strategy_id for t in closed_trades if t.strategy_id)),
                    "avg_daily_trades": round(len(closed_trades) / days, 2) if days > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting position history: {e}")
            return {"error": str(e)}
    
    def analyze_position_sizing(self, user_id: int) -> Dict[str, Any]:
        """Analizar patrones de position sizing"""
        try:
            # Obtener todas las posiciones (abiertas y cerradas)
            all_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id
            ).all()
            
            if not all_trades:
                return {"error": "No trades found"}
            
            # Análisis por estrategia
            strategy_analysis = defaultdict(list)
            for trade in all_trades:
                position_size = trade.quantity * trade.entry_price
                strategy_analysis[trade.strategy_id or "unknown"].append(position_size)
            
            strategy_stats = {}
            for strategy, sizes in strategy_analysis.items():
                if sizes:
                    strategy_stats[strategy] = {
                        "avg_position_size": round(sum(sizes) / len(sizes), 2),
                        "max_position_size": round(max(sizes), 2),
                        "min_position_size": round(min(sizes), 2),
                        "total_positions": len(sizes),
                        "std_deviation": round(self._calculate_std_dev(sizes), 2)
                    }
            
            # Análisis temporal (últimos 30 días vs anteriores)
            thirty_days_ago = now_eastern() - timedelta(days=30)
            recent_trades = [t for t in all_trades if t.opened_at and t.opened_at >= thirty_days_ago]
            older_trades = [t for t in all_trades if t.opened_at and t.opened_at < thirty_days_ago]
            
            recent_sizes = [t.quantity * t.entry_price for t in recent_trades]
            older_sizes = [t.quantity * t.entry_price for t in older_trades]
            
            temporal_comparison = {
                "recent_30_days": {
                    "avg_size": round(sum(recent_sizes) / len(recent_sizes), 2) if recent_sizes else 0,
                    "count": len(recent_sizes)
                },
                "before_30_days": {
                    "avg_size": round(sum(older_sizes) / len(older_sizes), 2) if older_sizes else 0,
                    "count": len(older_sizes)
                }
            }
            
            return {
                "strategy_analysis": strategy_stats,
                "temporal_comparison": temporal_comparison,
                "overall_stats": {
                    "total_trades": len(all_trades),
                    "avg_position_size": round(sum(t.quantity * t.entry_price for t in all_trades) / len(all_trades), 2),
                    "largest_position": round(max(t.quantity * t.entry_price for t in all_trades), 2),
                    "smallest_position": round(min(t.quantity * t.entry_price for t in all_trades), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing position sizing: {e}")
            return {"error": str(e)}
    
    def _get_sector_mapping(self) -> Dict[str, str]:
        """Mapeo básico de símbolos a sectores (expandir según necesidad)"""
        return {
            "AAPL": "Technology",
            "MSFT": "Technology", 
            "GOOGL": "Technology",
            "AMZN": "Consumer Discretionary",
            "TSLA": "Consumer Discretionary",
            "NVDA": "Technology",
            "JPM": "Financial Services",
            "JNJ": "Healthcare",
            "V": "Financial Services",
            "PG": "Consumer Staples"
        }
    
    def _analyze_concentration(self, symbol_exp: Dict, sector_exp: Dict, strategy_exp: Dict) -> Dict[str, Any]:
        """Analizar concentración de riesgo"""
        warnings = []
        recommendations = []
        
        # Verificar concentración por símbolo
        for symbol, pct in symbol_exp.items():
            if pct > 20:  # Más del 20% en un símbolo
                warnings.append(f"High concentration in {symbol}: {pct}%")
        
        # Verificar concentración por sector
        for sector, pct in sector_exp.items():
            if pct > 30:  # Más del 30% en un sector
                warnings.append(f"High sector concentration in {sector}: {pct}%")
        
        # Verificar concentración por estrategia
        for strategy, pct in strategy_exp.items():
            if pct > 50:  # Más del 50% en una estrategia
                warnings.append(f"High strategy concentration in {strategy}: {pct}%")
        
        # Recomendaciones basadas en concentración
        if len(symbol_exp) < 5:
            recommendations.append("Consider diversifying across more symbols")
        
        if len(sector_exp) < 3:
            recommendations.append("Consider diversifying across more sectors")
        
        return {
            "concentration_score": len(warnings),  # 0 = bien diversificado
            "warnings": warnings,
            "recommendations": recommendations,
            "diversification_level": "High" if len(warnings) == 0 else "Medium" if len(warnings) <= 2 else "Low"
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calcular desviación estándar"""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

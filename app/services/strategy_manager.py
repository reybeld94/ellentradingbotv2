from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.utils.time import now_eastern
import logging

logger = logging.getLogger(__name__)


class StrategyManager:
    def __init__(self, db: Session):
        self.db = db
    
    def create_strategy(self, user_id: int, config: StrategyCreate) -> Strategy:
        """Crear estrategia con configuración completa"""
        try:
            strategy = Strategy(
                name=config.name,
                description=config.description,
                user_id=user_id,
                entry_rules=config.entry_rules.dict(),
                exit_rules=config.exit_rules.dict(),
                risk_parameters=config.risk_parameters.dict(),
                position_sizing=config.position_sizing.dict(),
                is_active=config.is_active
            )
            
            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)
            
            logger.info(f"Strategy created: {strategy.name} for user {user_id}")
            return strategy
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating strategy: {e}")
            raise
    
    def get_user_strategies(self, user_id: int, active_only: bool = False) -> List[Strategy]:
        """Obtener todas las estrategias de un usuario"""
        query = self.db.query(Strategy).filter(Strategy.user_id == user_id)
        
        if active_only:
            query = query.filter(Strategy.is_active == True)
            
        return query.order_by(Strategy.created_at.desc()).all()
    
    def get_strategy_by_id(self, strategy_id: int, user_id: int) -> Optional[Strategy]:
        """Obtener estrategia por ID validando que pertenezca al usuario"""
        return self.db.query(Strategy).filter(
            Strategy.id == strategy_id,
            Strategy.user_id == user_id
        ).first()
    
    def update_strategy(self, strategy_id: int, user_id: int, updates: StrategyUpdate) -> Optional[Strategy]:
        """Actualizar estrategia existente"""
        strategy = self.get_strategy_by_id(strategy_id, user_id)
        if not strategy:
            return None
        
        try:
            update_data = updates.dict(exclude_unset=True)
            
            # Convertir objetos Pydantic a dict si es necesario
            for field, value in update_data.items():
                if hasattr(value, 'dict'):
                    setattr(strategy, field, value.dict())
                else:
                    setattr(strategy, field, value)
            
            strategy.updated_at = now_eastern()
            
            self.db.commit()
            self.db.refresh(strategy)
            
            logger.info(f"Strategy updated: {strategy.name}")
            return strategy
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating strategy: {e}")
            raise
    
    def delete_strategy(self, strategy_id: int, user_id: int) -> bool:
        """Eliminar estrategia (soft delete desactivando)"""
        strategy = self.get_strategy_by_id(strategy_id, user_id)
        if not strategy:
            return False
        
        try:
            strategy.is_active = False
            strategy.updated_at = now_eastern()
            
            self.db.commit()
            logger.info(f"Strategy deactivated: {strategy.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating strategy: {e}")
            raise
    
    def validate_strategy_config(self, config: StrategyCreate) -> Dict[str, Any]:
        """Validar configuración de estrategia"""
        errors = []
        warnings = []
        
        # Validar risk parameters
        if config.risk_parameters.max_position_size > 0.20:  # 20%
            warnings.append("Position size > 20% is risky")
        
        if config.risk_parameters.max_position_size <= 0:
            errors.append("Position size must be positive")
        
        # Validar exit rules
        if config.exit_rules.stop_loss and config.exit_rules.stop_loss >= 0:
            errors.append("Stop loss should be negative (loss)")
        
        if config.exit_rules.take_profit and config.exit_rules.take_profit <= 0:
            errors.append("Take profit should be positive (gain)")
        
        # Validar position sizing
        if config.position_sizing.type == "fixed" and not config.position_sizing.amount:
            errors.append("Fixed position sizing requires amount")
        
        if config.position_sizing.type == "percentage" and not config.position_sizing.percentage:
            errors.append("Percentage position sizing requires percentage")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def get_strategy_performance(self, strategy_id: int, user_id: int) -> Dict[str, Any]:
        """Performance individual por estrategia"""
        from app.models.trades import Trade
        from sqlalchemy import func

        strategy = self.get_strategy_by_id(strategy_id, user_id)
        if not strategy:
            return {}

        trades_query = self.db.query(Trade).filter(
            Trade.strategy_id == str(strategy_id),
            Trade.user_id == user_id,
            Trade.status == "closed",
        )

        total_trades = trades_query.count()
        if total_trades == 0:
            return self._empty_performance_metrics(strategy_id)

        total_pnl = trades_query.with_entities(func.sum(Trade.pnl)).scalar() or 0.0
        winning_trades = trades_query.filter(Trade.pnl > 0).count()
        losing_trades = trades_query.filter(Trade.pnl < 0).count()

        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0

        avg_winner = 0
        avg_loser = 0

        if winning_trades > 0:
            avg_winner = (
                trades_query.filter(Trade.pnl > 0)
                .with_entities(func.avg(Trade.pnl))
                .scalar()
                or 0
            )

        if losing_trades > 0:
            avg_loser = (
                trades_query.filter(Trade.pnl < 0)
                .with_entities(func.avg(Trade.pnl))
                .scalar()
                or 0
            )

        gross_profit = (
            trades_query.filter(Trade.pnl > 0)
            .with_entities(func.sum(Trade.pnl))
            .scalar()
            or 0
        )

        gross_loss = abs(
            trades_query.filter(Trade.pnl < 0)
            .with_entities(func.sum(Trade.pnl))
            .scalar()
            or 0
        )

        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

        trades_list = trades_query.all()
        if len(trades_list) > 1:
            pnls = [t.pnl for t in trades_list if t.pnl is not None]
            if pnls:
                mean_pnl = sum(pnls) / len(pnls)
                variance = sum((pnl - mean_pnl) ** 2 for pnl in pnls) / len(pnls)
                std_dev = variance ** 0.5
                sharpe_ratio = (mean_pnl / std_dev) if std_dev > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0

        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 2),
            "avg_winner": round(avg_winner, 2),
            "avg_loser": round(avg_loser, 2),
            "profit_factor": round(profit_factor, 3),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(abs(gross_loss), 2),
            "largest_win": round(
                trades_query.with_entities(func.max(Trade.pnl)).scalar() or 0,
                2,
            ),
            "largest_loss": round(
                trades_query.with_entities(func.min(Trade.pnl)).scalar() or 0,
                2,
            ),
        }

    def _empty_performance_metrics(self, strategy_id: int) -> Dict[str, Any]:
        """Métricas vacías para estrategias sin trades"""
        return {
            "strategy_id": strategy_id,
            "strategy_name": "",
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_winner": 0.0,
            "avg_loser": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
        }

    def compare_strategies(self, user_id: int, strategy_ids: List[int]) -> Dict[str, Any]:
        """Comparar performance entre múltiples estrategias"""
        comparisons = []

        for strategy_id in strategy_ids:
            performance = self.get_strategy_performance(strategy_id, user_id)
            if performance.get("total_trades", 0) > 0:
                comparisons.append(performance)

        comparisons.sort(key=lambda x: x.get("profit_factor", 0), reverse=True)

        return {
            "strategies": comparisons,
            "best_strategy": comparisons[0] if comparisons else None,
            "total_strategies": len(comparisons),
            "comparison_date": now_eastern().isoformat(),
        }

    def get_strategy_equity_curve(
        self, strategy_id: int, user_id: int
    ) -> List[Dict[str, Any]]:
        """Curva de equity para una estrategia específica"""
        from app.models.trades import Trade

        trades = (
            self.db.query(Trade)
            .filter(
                Trade.strategy_id == str(strategy_id),
                Trade.user_id == user_id,
                Trade.status == "closed",
                Trade.closed_at.isnot(None),
            )
            .order_by(Trade.closed_at.asc())
            .all()
        )

        equity_curve = []
        cumulative_pnl = 0.0

        for trade in trades:
            if trade.pnl is not None:
                cumulative_pnl += trade.pnl
                equity_curve.append(
                    {
                        "date": trade.closed_at.isoformat() if trade.closed_at else "",
                        "cumulative_pnl": round(cumulative_pnl, 2),
                        "trade_pnl": round(trade.pnl, 2),
                        "symbol": trade.symbol,
                        "trade_id": trade.id,
                    }
                )

        return equity_curve

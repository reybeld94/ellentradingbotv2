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

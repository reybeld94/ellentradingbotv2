from sqlalchemy.orm import Session
from app.models.strategy_exit_rules import StrategyExitRules
from typing import Optional, Dict, Any
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class ExitRulesService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_rules(self, strategy_id: str) -> StrategyExitRules:
        """Obtener reglas de salida para una estrategia, crear defaults si no existen"""
        rules = self.db.query(StrategyExitRules).filter(
            StrategyExitRules.id == strategy_id
        ).first()
        
        if not rules:
            logger.info(f"Creating default exit rules for strategy: {strategy_id}")
            rules = self.create_default_rules(strategy_id)
            
        return rules
    
    def create_default_rules(self, strategy_id: str) -> StrategyExitRules:
        """Crear reglas por defecto para una estrategia"""
        rules = StrategyExitRules(
            id=strategy_id,
            stop_loss_pct=0.02,      # 2%
            take_profit_pct=0.04,    # 4% 
            trailing_stop_pct=0.015, # 1.5%
            use_trailing=True,
            risk_reward_ratio=2.0
        )
        
        self.db.add(rules)
        self.db.commit()
        self.db.refresh(rules)
        
        logger.info(f"Created default exit rules for {strategy_id}")
        return rules
    
    def update_rules(self, strategy_id: str, **kwargs) -> StrategyExitRules:
        """Actualizar reglas existentes"""
        rules = self.get_rules(strategy_id)
        
        # Campos permitidos para actualización
        allowed_fields = [
            'stop_loss_pct', 'take_profit_pct', 'trailing_stop_pct',
            'use_trailing', 'risk_reward_ratio'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(rules, field):
                setattr(rules, field, value)
                logger.info(f"Updated {field} = {value} for strategy {strategy_id}")
        
        self.db.commit()
        self.db.refresh(rules)
        return rules
    
    def calculate_exit_prices(self, strategy_id: str, entry_price: Decimal, side: str = "buy") -> Dict[str, Any]:
        """Calcular precios de salida para una estrategia específica"""
        rules = self.get_rules(strategy_id)
        entry_price = Decimal(str(entry_price))
        exit_prices = rules.calculate_exit_prices(entry_price, side)
        
        return {
            **exit_prices,
            "strategy_id": strategy_id,
            "rules": {
                "stop_loss_pct": rules.stop_loss_pct,
                "take_profit_pct": rules.take_profit_pct,
                "trailing_stop_pct": rules.trailing_stop_pct,
                "use_trailing": rules.use_trailing,
                "risk_reward_ratio": rules.risk_reward_ratio
            }
        }
    
    def get_all_rules(self) -> list[StrategyExitRules]:
        """Obtener todas las reglas configuradas"""
        return self.db.query(StrategyExitRules).all()
    
    def delete_rules(self, strategy_id: str) -> bool:
        """Eliminar reglas de una estrategia"""
        rules = self.db.query(StrategyExitRules).filter(
            StrategyExitRules.id == strategy_id
        ).first()
        
        if rules:
            self.db.delete(rules)
            self.db.commit()
            logger.info(f"Deleted exit rules for strategy {strategy_id}")
            return True
        
        return False

from typing import Dict, List, Optional
from app.core.types import NormalizedSignal
from app.models.strategy import Strategy
from sqlalchemy.orm import Session

class SignalValidationError(Exception):
    """Excepción para errores de validación de señales"""
    pass

class SignalValidator:
    """Valida señales normalizadas antes de procesarlas"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def validate(self, signal: NormalizedSignal) -> Dict[str, any]:
        """Validar una señal normalizada"""
        errors = []
        warnings = []
        
        # Validar símbolo
        if not self._is_valid_symbol(signal.symbol):
            errors.append(f"Invalid symbol format: {signal.symbol}")
        
        # Validar estrategia existe
        if not self._strategy_exists(signal.strategy_id):
            errors.append(f"Strategy not found: {signal.strategy_id}")
        
        # Validar cantidad
        if signal.quantity is not None and signal.quantity <= 0:
            errors.append(f"Invalid quantity: {signal.quantity}")
        
        # Validar confidence score
        if signal.confidence is not None:
            if not (0 <= signal.confidence <= 100):
                warnings.append(f"Confidence score outside 0-100 range: {signal.confidence}")
        
        # Validar precios stop loss y take profit
        if signal.stop_loss is not None and signal.stop_loss <= 0:
            errors.append(f"Invalid stop_loss price: {signal.stop_loss}")
            
        if signal.take_profit is not None and signal.take_profit <= 0:
            errors.append(f"Invalid take_profit price: {signal.take_profit}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Validar formato del símbolo"""
        if not symbol or len(symbol) < 1 or len(symbol) > 10:
            return False
        
        # Solo letras y números, sin espacios
        return symbol.replace(".", "").replace("-", "").isalnum()
    
    def _strategy_exists(self, strategy_id: str) -> bool:
        """Verificar que la estrategia existe en la base de datos"""
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id
            ).first()
            return strategy is not None
        except:
            return False

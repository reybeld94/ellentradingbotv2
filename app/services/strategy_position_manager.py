# backend/app/services/strategy_position_manager.py

from sqlalchemy.orm import Session
from app.models.strategy_position import StrategyPosition
import logging

logger = logging.getLogger(__name__)


class StrategyPositionManager:
    def __init__(self, db: Session):
        self.db = db

    def get_strategy_position(self, strategy_id: str, symbol: str) -> StrategyPosition:
        """Obtener posición de una estrategia específica para un símbolo"""
        position = self.db.query(StrategyPosition).filter(
            StrategyPosition.strategy_id == strategy_id,
            StrategyPosition.symbol == symbol
        ).first()

        # Si no existe, crear una nueva con cantidad 0
        if not position:
            position = StrategyPosition(
                strategy_id=strategy_id,
                symbol=symbol,
                quantity=0.0,
                total_invested=0.0
            )
            self.db.add(position)
            self.db.commit()
            self.db.refresh(position)

        return position

    def add_position(self, strategy_id: str, symbol: str, quantity: float, price: float):
        """Agregar a la posición de una estrategia (compra)"""
        position = self.get_strategy_position(strategy_id, symbol)

        # Calcular nuevo promedio
        if position.quantity == 0:
            # Primera compra
            new_avg_price = price
            new_total_invested = quantity * price
        else:
            # Compra adicional - calcular promedio ponderado
            current_value = position.quantity * position.avg_price
            additional_value = quantity * price
            new_total_quantity = position.quantity + quantity
            new_avg_price = (current_value + additional_value) / new_total_quantity
            new_total_invested = position.total_invested + (quantity * price)

        # Actualizar posición
        position.quantity = position.quantity + quantity
        position.avg_price = new_avg_price
        position.total_invested = new_total_invested

        self.db.commit()

        logger.info(
            f"Added position: {strategy_id}:{symbol} +{quantity} @ ${price} "
            f"(total: {position.quantity})"
        )
        return position

    def reduce_position(self, strategy_id: str, symbol: str, quantity: float) -> float:
        """Reducir posición de una estrategia (venta) - retorna cantidad vendida"""
        position = self.get_strategy_position(strategy_id, symbol)

        if position.quantity <= 0:
            logger.warning(f"No position to reduce for {strategy_id}:{symbol}")
            return 0.0

        # Determinar cuánto vender
        quantity_to_sell = min(quantity, position.quantity)

        # Actualizar posición
        position.quantity = position.quantity - quantity_to_sell

        # Truncar valores residuales muy pequeños para evitar errores de redondeo
        if 0 < position.quantity < 0.0001:
            position.quantity = 0.0

        # Si se vendió todo o quedó por debajo del umbral, resetear valores
        if position.quantity == 0:
            position.avg_price = None
            position.total_invested = 0.0
        else:
            # Reducir inversión proporcionalmente
            sell_ratio = quantity_to_sell / (
                position.quantity + quantity_to_sell
            )
            position.total_invested = position.total_invested * (1 - sell_ratio)

        self.db.commit()

        logger.info(
            f"Reduced position: {strategy_id}:{symbol} -{quantity_to_sell} "
            f"(remaining: {position.quantity})"
        )
        return quantity_to_sell

    def get_strategy_positions(self, strategy_id: str):
        """Obtener todas las posiciones de una estrategia"""
        return self.db.query(StrategyPosition).filter(
            StrategyPosition.strategy_id == strategy_id,
            StrategyPosition.quantity > 0
        ).all()

    def get_all_positions_by_symbol(self, symbol: str):
        """Obtener todas las posiciones de todas las estrategias para un símbolo"""
        return self.db.query(StrategyPosition).filter(
            StrategyPosition.symbol == symbol,
            StrategyPosition.quantity > 0
        ).all()

    def get_total_quantity_for_symbol(self, symbol: str) -> float:
        """Obtener cantidad total de un símbolo across todas las estrategias"""
        positions = self.get_all_positions_by_symbol(symbol)
        return sum(pos.quantity for pos in positions)

    def reset_position(self, strategy_id: str, symbol: str) -> None:
        """Restablecer completamente la posición de una estrategia"""
        position = self.get_strategy_position(strategy_id, symbol)
        position.quantity = 0.0
        position.avg_price = None
        position.total_invested = 0.0
        self.db.commit()
        logger.info(f"Reset position: {strategy_id}:{symbol}")


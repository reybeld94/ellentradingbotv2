from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.signal import Signal
from app.core.types import OrderStatus, OrderType, SignalAction
from app.core.auth import get_current_verified_user
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderManager:
    """Gestiona la creación y estado de órdenes"""

    def __init__(self, db: Session):
        self.db = db

    def create_order_from_signal(
        self,
        signal: Signal,
        user_id: int,
        portfolio_id: Optional[int] = None
    ) -> Order:
        """Crear una orden desde una señal validada"""

        # Generar client_order_id único
        client_order_id = f"order_{uuid.uuid4().hex[:8]}"

        # Mapear SignalAction a order side
        side = self._map_signal_action_to_side(signal.action)

        # Crear orden
        order = Order(
            client_order_id=client_order_id,
            symbol=signal.symbol,
            side=side,
            quantity=signal.quantity or 1.0,  # Default quantity si no viene
            order_type=OrderType.MARKET,  # Default market order
            status=OrderStatus.NEW,
            signal_id=signal.id,
            user_id=user_id,
            portfolio_id=portfolio_id,
            created_at=datetime.utcnow()
        )

        # Guardar en DB
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        logger.info(f"Created order {order.client_order_id} from signal {signal.id}")
        return order

    def update_order_status(
        self,
        order: Order,
        new_status: OrderStatus,
        broker_order_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Order:
        """Actualizar el estado de una orden"""

        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()

        # Actualizar campos específicos según el estado
        if new_status == OrderStatus.SENT:
            order.sent_at = datetime.utcnow()
        elif new_status == OrderStatus.FILLED:
            order.filled_at = datetime.utcnow()

        # Asignar broker order ID si viene
        if broker_order_id:
            order.broker_order_id = broker_order_id

        # Guardar error si hay
        if error_message:
            order.last_error = error_message
            order.retry_count += 1

        self.db.commit()
        self.db.refresh(order)

        logger.info(f"Order {order.client_order_id} status: {old_status} -> {new_status}")
        return order

    def get_active_orders(self, user_id: int) -> list[Order]:
        """Obtener órdenes activas del usuario"""
        active_statuses = [
            OrderStatus.NEW,
            OrderStatus.SENT,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED
        ]

        return (
            self.db.query(Order)
            .filter(
                Order.user_id == user_id,
                Order.status.in_(active_statuses)
            )
            .order_by(Order.created_at.desc())
            .all()
        )

    def get_order_by_client_id(self, client_order_id: str) -> Optional[Order]:
        """Buscar orden por client_order_id"""
        return (
            self.db.query(Order)
            .filter(Order.client_order_id == client_order_id)
            .first()
        )

    def get_order_by_broker_id(self, broker_order_id: str) -> Optional[Order]:
        """Buscar orden por broker_order_id"""
        return (
            self.db.query(Order)
            .filter(Order.broker_order_id == broker_order_id)
            .first()
        )

    def _map_signal_action_to_side(self, action: str) -> str:
        """Mapear SignalAction a order side (buy/sell)"""
        buy_actions = [SignalAction.BUY, SignalAction.LONG_ENTRY]
        sell_actions = [SignalAction.SELL, SignalAction.LONG_EXIT, SignalAction.SHORT_ENTRY]

        if action in buy_actions:
            return "buy"
        elif action in sell_actions:
            return "sell"
        else:
            # Default fallback
            return "buy" if action.lower() in ["buy", "long"] else "sell"

    def calculate_position_size(
        self,
        signal: Signal,
        available_capital: float,
        max_position_pct: float = 0.05  # 5% máximo por posición
    ) -> float:
        """Calcular tamaño de posición basado en capital disponible"""

        if signal.quantity:
            # Si la señal ya especifica cantidad, usar esa
            return float(signal.quantity)

        # Calcular basado en % del capital
        max_position_value = available_capital * max_position_pct

        # Para market orders, necesitaríamos el precio actual
        # Por ahora, usar quantity = 1 como default seguro
        # TODO: Integrar con precio actual del símbolo

        return 1.0  # Cantidad conservadora por defecto

from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.strategy_exit_rules import StrategyExitRules
from app.services.exit_rules_service import ExitRulesService
from app.core.types import OrderStatus, OrderType
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TrailingStopMonitor:
    def __init__(self, db: Session):
        self.db = db
        self.exit_rules_service = ExitRulesService(db)
    
    def check_and_update_trailing_stops(self) -> Dict[str, Any]:
        """Revisar y actualizar todos los trailing stops activos"""
        try:
            # 1. Obtener órdenes de stop loss activas con trailing habilitado
            active_stops = self._get_active_trailing_stops()
            
            results = {
                "checked": len(active_stops),
                "updated": 0,
                "errors": 0,
                "details": []
            }
            
            for stop_order in active_stops:
                try:
                    update_result = self._update_single_trailing_stop(stop_order)
                    results["details"].append(update_result)
                    
                    if update_result["updated"]:
                        results["updated"] += 1
                        
                except Exception as e:
                    logger.error(f"Error updating trailing stop {stop_order.id}: {str(e)}")
                    results["errors"] += 1
                    results["details"].append({
                        "order_id": stop_order.id,
                        "symbol": stop_order.symbol,
                        "error": str(e),
                        "updated": False
                    })
            
            logger.info(f"Trailing stops check: {results['checked']} checked, {results['updated']} updated")
            return results
            
        except Exception as e:
            logger.error(f"Error in trailing stop monitor: {str(e)}")
            return {"error": str(e), "checked": 0, "updated": 0}
    
    def _get_active_trailing_stops(self) -> List[Order]:
        """Obtener órdenes de stop loss activas que tienen trailing habilitado"""
        return (
            self.db.query(Order)
            .join(Order.signal)
            .filter(
                Order.order_type == OrderType.STOP.value,
                Order.status.in_(["new", "sent", "accepted"]),
                Order.parent_order_id.isnot(None)  # Es una orden de salida
            )
            .all()
        )
    
    def _update_single_trailing_stop(self, stop_order: Order) -> Dict[str, Any]:
        """Actualizar un trailing stop individual"""
        try:
            # 1. Obtener precio actual del símbolo
            current_price = self._get_current_price(stop_order.symbol)
            if current_price <= 0:
                return {
                    "order_id": stop_order.id,
                    "symbol": stop_order.symbol,
                    "error": "Could not get current price",
                    "updated": False
                }
            
            # 2. Obtener reglas de trailing para la estrategia
            signal = stop_order.signal
            strategy_rules = self.exit_rules_service.get_rules(
                signal.strategy_id, stop_order.user_id
            )
            
            if not strategy_rules.use_trailing:
                return {
                    "order_id": stop_order.id,
                    "symbol": stop_order.symbol,
                    "message": "Trailing disabled for strategy",
                    "updated": False
                }
            
            # 3. Calcular nuevo stop loss basado en precio actual
            new_stop_price = self._calculate_new_trailing_stop(
                stop_order, current_price, strategy_rules
            )
            
            # 4. Actualizar si el nuevo stop es mejor que el actual
            if self._should_update_stop(stop_order, new_stop_price):
                old_stop_price = stop_order.stop_price
                stop_order.stop_price = new_stop_price
                self.db.commit()
                
                logger.info(
                    f"Updated trailing stop {stop_order.id} {stop_order.symbol}: "
                    f"{old_stop_price} -> {new_stop_price}"
                )
                
                # TODO: Enviar actualización al broker en siguiente tarea
                
                return {
                    "order_id": stop_order.id,
                    "symbol": stop_order.symbol,
                    "old_stop_price": float(old_stop_price),
                    "new_stop_price": float(new_stop_price),
                    "current_price": current_price,
                    "updated": True
                }
            else:
                return {
                    "order_id": stop_order.id,
                    "symbol": stop_order.symbol,
                    "current_price": current_price,
                    "stop_price": float(stop_order.stop_price),
                    "message": "No update needed",
                    "updated": False
                }
                
        except Exception as e:
            logger.error(f"Error updating trailing stop {stop_order.id}: {str(e)}")
            raise
    
    def _calculate_new_trailing_stop(self, stop_order: Order, current_price: float, rules: StrategyExitRules) -> float:
        """Calcular nuevo precio de trailing stop"""
        # Obtener la orden padre para determinar la dirección
        parent_order = self.db.query(Order).filter(Order.id == stop_order.parent_order_id).first()
        
        if parent_order and parent_order.side == "buy":
            # Posición larga: trailing stop sube con el precio
            new_stop = current_price * (1 - rules.trailing_stop_pct)
        else:
            # Posición corta: trailing stop baja con el precio
            new_stop = current_price * (1 + rules.trailing_stop_pct)
        
        return round(new_stop, 2)
    
    def _should_update_stop(self, stop_order: Order, new_stop_price: float) -> bool:
        """Determinar si el stop loss debe actualizarse"""
        current_stop = float(stop_order.stop_price)
        
        # Obtener la orden padre para determinar la dirección
        parent_order = self.db.query(Order).filter(Order.id == stop_order.parent_order_id).first()
        
        if parent_order and parent_order.side == "buy":
            # Posición larga: solo actualizar si el nuevo stop es más alto (más protección)
            return new_stop_price > current_stop
        else:
            # Posición corta: solo actualizar si el nuevo stop es más bajo
            return new_stop_price < current_stop
    
    def _get_current_price(self, symbol: str) -> float:
        """Obtener precio actual del símbolo"""
        try:
            from app.integrations import broker_client
            trade = broker_client.get_latest_trade(symbol)
            return float(getattr(trade, "price", 0.0))
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    def get_trailing_stops_summary(self) -> Dict[str, Any]:
        """Obtener resumen de trailing stops activos"""
        active_stops = self._get_active_trailing_stops()
        
        summary = {
            "total_active": len(active_stops),
            "by_symbol": {},
            "by_strategy": {}
        }
        
        for stop in active_stops:
            # Por símbolo
            if stop.symbol not in summary["by_symbol"]:
                summary["by_symbol"][stop.symbol] = 0
            summary["by_symbol"][stop.symbol] += 1
            
            # Por estrategia
            strategy_id = stop.signal.strategy_id if stop.signal else "unknown"
            if strategy_id not in summary["by_strategy"]:
                summary["by_strategy"][strategy_id] = 0
            summary["by_strategy"][strategy_id] += 1
        
        return summary

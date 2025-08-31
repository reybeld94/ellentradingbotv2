import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.execution.order_processor import OrderProcessor
from app.models.order import Order
from app.core.types import OrderStatus

logger = logging.getLogger(__name__)


class ExecutionScheduler:
    """Scheduler para procesar órdenes automáticamente"""

    def __init__(self):
        self.is_running = False
        self.process_interval = 30  # Segundos entre procesamiento
        self.fill_update_interval = 60  # Segundos entre actualización de fills
        self.last_process_time = None
        self.last_fill_update_time = None

    async def start(self):
        """Iniciar el scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        self.is_running = True
        logger.info("Starting execution scheduler...")

        logger.info("Trailing stops task scheduled (60s interval)")

        # Iniciar tareas en paralelo
        await asyncio.gather(
            self._order_processing_loop(),
            self._fill_update_loop(),
            self._cleanup_loop(),
            self._trailing_stops_loop(),
        )

    def stop(self):
        """Detener el scheduler"""
        self.is_running = False
        logger.info("Execution scheduler stopped")

    async def _order_processing_loop(self):
        """Loop principal de procesamiento de órdenes"""
        while self.is_running:
            try:
                db: Session = next(get_db())
                processor = OrderProcessor(db)

                # Contar órdenes pendientes antes de procesar
                pending_count = (
                    db.query(Order).filter(Order.status == OrderStatus.NEW).count()
                )

                if pending_count > 0:
                    logger.info(f"Processing {pending_count} pending orders...")

                    result = processor.process_pending_orders()
                    self.last_process_time = datetime.utcnow()

                    if result["successful"] > 0 or result["failed"] > 0:
                        logger.info(
                            "Order processing completed: %s successful, %s failed, %s retries",
                            result["successful"],
                            result["failed"],
                            result["retries_scheduled"],
                        )
                else:
                    # Solo log detallado cada 5 minutos cuando no hay órdenes
                    if not hasattr(self, "_last_no_orders_log") or (
                        datetime.utcnow() - self._last_no_orders_log
                        > timedelta(minutes=5)
                    ):
                        logger.debug("No pending orders to process")
                        self._last_no_orders_log = datetime.utcnow()

                db.close()

            except Exception as e:  # pragma: no cover - just in case
                logger.error(f"Error in order processing loop: {e}")
                if "db" in locals():
                    db.close()

            # Esperar antes del siguiente ciclo
            await asyncio.sleep(self.process_interval)

    async def _fill_update_loop(self):
        """Loop para actualizar fills de órdenes activas"""
        while self.is_running:
            try:
                db: Session = next(get_db())
                processor = OrderProcessor(db)

                # Actualizar fills de órdenes activas
                result = processor.update_order_fills()
                self.last_fill_update_time = datetime.utcnow()

                if result["updated"] > 0:
                    logger.info(
                        "Fill update completed: %s checked, %s updated, %s filled",
                        result["checked"],
                        result["updated"],
                        result["filled"],
                    )

                db.close()

            except Exception as e:  # pragma: no cover - just in case
                logger.error(f"Error in fill update loop: {e}")
                if "db" in locals():
                    db.close()

            # Esperar antes del siguiente ciclo (menos frecuente)
            await asyncio.sleep(self.fill_update_interval)

    async def _cleanup_loop(self):
        """Loop para tareas de limpieza periódicas"""
        while self.is_running:
            try:
                db: Session = next(get_db())

                # Limpiar órdenes con errores muy antiguas (opcional)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                old_error_orders = (
                    db.query(Order)
                    .filter(
                        Order.status == OrderStatus.ERROR,
                        Order.created_at < cutoff_date,
                    )
                    .count()
                )

                if old_error_orders > 0:
                    logger.info(
                        "Found %s old error orders (cleanup could be implemented)",
                        old_error_orders,
                    )

                # Estadísticas periódicas (cada 30 minutos)
                processor = OrderProcessor(db)
                stats = processor.get_order_statistics()

                logger.info("Execution stats: %s", stats["status_breakdown"])

                db.close()

            except Exception as e:  # pragma: no cover - just in case
                logger.error(f"Error in cleanup loop: {e}")
                if "db" in locals():
                    db.close()

            # Cleanup cada 30 minutos
            await asyncio.sleep(30 * 60)

    async def _trailing_stops_loop(self):
        """Loop para revisar trailing stops periódicamente"""
        while self.is_running:
            try:
                await self.run_trailing_stops_check()
            except Exception as e:  # pragma: no cover - safeguard
                logger.error(f"Error in trailing stops loop: {e}")
            await asyncio.sleep(60)

    async def run_trailing_stops_check(self):
        """Ejecutar check de trailing stops"""
        if not self.is_running:
            return

        try:
            from contextlib import closing
            from app.execution.trailing_stop_monitor import TrailingStopMonitor

            with closing(next(get_db())) as db:
                monitor = TrailingStopMonitor(db)
                result = monitor.check_and_update_trailing_stops()

            logger.info(f"Trailing stops check completed: {result}")

        except Exception as e:
            logger.error(f"Error in trailing stops check: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del scheduler"""
        return {
            "is_running": self.is_running,
            "process_interval": self.process_interval,
            "fill_update_interval": self.fill_update_interval,
            "last_process_time": self.last_process_time.isoformat()
            if self.last_process_time
            else None,
            "last_fill_update_time": self.last_fill_update_time.isoformat()
            if self.last_fill_update_time
            else None,
        }


# Instancia global del scheduler
execution_scheduler = ExecutionScheduler()


async def start_execution_scheduler():
    """Función para iniciar el scheduler desde FastAPI"""
    await execution_scheduler.start()


def stop_execution_scheduler():
    """Función para detener el scheduler"""
    execution_scheduler.stop()

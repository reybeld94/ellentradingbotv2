import asyncio
import logging
from contextlib import asynccontextmanager
from app.execution.scheduler import execution_scheduler

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manager para tareas en background del execution engine"""

    def __init__(self):
        self.tasks = []
        self.is_running = False

    async def start_all_tasks(self):
        """Iniciar todas las tareas en background"""
        if self.is_running:
            logger.warning("Background tasks already running")
            return

        self.is_running = True
        logger.info("Starting execution background tasks...")

        try:
            # Crear task para el scheduler
            scheduler_task = asyncio.create_task(
                execution_scheduler.start(),
                name="execution_scheduler",
            )
            self.tasks.append(scheduler_task)

            # Esperar a que todas las tareas terminen
            await asyncio.gather(*self.tasks, return_exceptions=True)

        except Exception as e:  # pragma: no cover - safeguard
            logger.error(f"Error in background tasks: {e}")
            await self.stop_all_tasks()

    async def stop_all_tasks(self):
        """Detener todas las tareas en background"""
        if not self.is_running:
            return

        logger.info("Stopping execution background tasks...")
        self.is_running = False

        # Detener scheduler
        execution_scheduler.stop()

        # Cancelar todas las tareas
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Esperar a que se cancelen
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        self.tasks.clear()
        logger.info("All execution background tasks stopped")


# Instancia global del manager
background_task_manager = BackgroundTaskManager()


@asynccontextmanager
async def execution_lifespan(app):
    """Context manager para manejar el lifecycle de las tareas en background"""
    # Startup
    logger.info("Starting execution engine background tasks...")
    task = asyncio.create_task(background_task_manager.start_all_tasks())

    yield

    # Shutdown
    logger.info("Shutting down execution engine background tasks...")
    await background_task_manager.stop_all_tasks()

    if not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:  # pragma: no cover - silence cancellation
            pass

from . import execution
from fastapi import FastAPI
from .exit_rules import router as exit_rules_router
from .bracket_orders import router as bracket_orders_router


def include_all_routers(app: FastAPI):
    app.include_router(exit_rules_router, prefix="/api/v1/exit-rules", tags=["Exit Rules"])
    app.include_router(bracket_orders_router, prefix="/api/v1/bracket-orders", tags=["Bracket Orders"])

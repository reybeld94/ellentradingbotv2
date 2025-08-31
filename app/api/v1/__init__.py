from . import execution
from fastapi import FastAPI
from .exit_rules import router as exit_rules_router


def include_all_routers(app: FastAPI):
    app.include_router(exit_rules_router, prefix="/api/v1/exit-rules", tags=["Exit Rules"])

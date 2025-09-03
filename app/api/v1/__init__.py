from fastapi import APIRouter
from .auth import router as auth_router
from .trades import router as trades_router
from .portfolios import router as portfolios_router
from .strategies import router as strategies_router
from .risk import router as risk_router
from .analytics import router as analytics_router
from .portfolio_performance import router as portfolio_performance_router

api_router = APIRouter()

# Incluir todos los routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(trades_router, prefix="/trades", tags=["trades"])
api_router.include_router(portfolios_router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
api_router.include_router(risk_router, prefix="/risk", tags=["risk"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(portfolio_performance_router, tags=["portfolio"])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.orders import router as orders_router
from app.api.v1.trading import router as trading_router
from app.api.v1.portfolios import router as portfolios_router
from app.api.v1.streaming import router as streaming_router
from app.api.v1.exit_rules import router as exit_rules_router
from app.api.v1.bracket_orders import router as bracket_orders_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.portfolio_performance import (
    router as portfolio_performance_router,
)
from app.api.ws import router as ws_router
from app.api.v1 import auth, trades, strategies, portfolio, risk, system, positions, reports
from app.database import SessionLocal
from app.services import portfolio_service
from app.integrations import refresh_broker_client

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# CORS para el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(webhooks_router, prefix="/api/v1", tags=["webhooks"])
app.include_router(orders_router, prefix="/api/v1", tags=["orders"])
app.include_router(trading_router, prefix="/api/v1", tags=["trading"])
app.include_router(trades.router, prefix="/api/v1", tags=["trades"])
app.include_router(strategies.router, prefix="/api/v1", tags=["strategies"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(portfolios_router, prefix="/api/v1", tags=["portfolios"])
app.include_router(streaming_router, prefix="/api/v1", tags=["streaming"])
app.include_router(risk.router, prefix="/api/v1", tags=["risk"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])
app.include_router(portfolio_performance_router, prefix="/api/v1", tags=["portfolio"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(exit_rules_router, prefix="/api/v1/exit-rules", tags=["Exit Rules"])
app.include_router(bracket_orders_router, prefix="/api/v1/bracket-orders", tags=["Bracket Orders"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(positions.router, prefix="/api/v1", tags=["positions"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(ws_router)


@app.on_event("startup")
async def start_streams():
    """Refresh the active portfolio on startup."""
    db = SessionLocal()
    try:
        portfolio_service.get_active(db)
    finally:
        db.close()
    refresh_broker_client()


@app.get("/")
async def root():
    return {"message": "Trading Bot API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}

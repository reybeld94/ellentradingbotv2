from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.v1.webhooks import router as webhooks_router
from .api.v1.orders import router as orders_router
from .api.v1.auth import router as auth_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
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
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])

@app.get("/")
async def root():
    return {"message": "Trading Bot API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}
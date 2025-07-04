from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Cargar el archivo .env manualmente
load_dotenv()


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./trading_bot.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Alpaca
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str = "https://paper-api.alpaca.markets/v2"

    # App
    app_name: str = "Trading Bot"
    debug: bool = True
    secret_key: str

    # Webhook
    webhook_secret: Optional[str] = None
    webhook_api_key: Optional[str] = "ELLENTRADING0408"

    # JWT Configuration - AGREGAR ESTAS LÍNEAS
    jwt_secret_key: str = "ELLENTRADING0408"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 días

    # Email configuration (opcional por ahora)
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
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
    alpaca_portfolio: str = "DEFAULT"
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
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

    def __init__(self, **values):
        super().__init__(**values)
        prefix = self.alpaca_portfolio.upper() if self.alpaca_portfolio else "DEFAULT"
        self.alpaca_api_key = os.getenv(
            f"ALPACA_{prefix}_API_KEY",
            os.getenv("ALPACA_API_KEY", self.alpaca_api_key),
        )
        self.alpaca_secret_key = os.getenv(
            f"ALPACA_{prefix}_SECRET_KEY",
            os.getenv("ALPACA_SECRET_KEY", self.alpaca_secret_key),
        )
        self.alpaca_base_url = os.getenv(
            f"ALPACA_{prefix}_BASE_URL",
            os.getenv("ALPACA_BASE_URL", self.alpaca_base_url),
        )

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()


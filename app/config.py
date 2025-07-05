from pydantic_settings import BaseSettings
from typing import Optional
import base64
import hashlib

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None

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
    secret_key: str = "changeme"

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

    def clear_alpaca_credentials(self) -> None:
        """Reset Alpaca credentials to ensure no connections are made."""
        self.alpaca_api_key = None
        self.alpaca_secret_key = None

    def update_from_portfolio(self, portfolio) -> None:
        """Update Alpaca credentials from a Portfolio instance."""
        if portfolio:
            if Fernet:
                key = base64.urlsafe_b64encode(
                    hashlib.sha256(self.secret_key.encode()).digest()
                )
                f = Fernet(key)
                self.alpaca_api_key = f.decrypt(
                    portfolio.api_key_encrypted.encode()
                ).decode()
                self.alpaca_secret_key = f.decrypt(
                    portfolio.secret_key_encrypted.encode()
                ).decode()
            else:
                self.alpaca_api_key = portfolio.api_key_encrypted
                self.alpaca_secret_key = portfolio.secret_key_encrypted
            self.alpaca_base_url = portfolio.base_url

    def __init__(self, **values):
        super().__init__(**values)

settings = Settings()

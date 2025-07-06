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
    database_url: str = "postgresql://postgres:ellentrading@localhost:5432/ellentrading"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Kraken
    kraken_api_key: Optional[str] = None
    kraken_secret_key: Optional[str] = None
    kraken_base_url: str = "https://api.kraken.com"

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

    def clear_kraken_credentials(self) -> None:
        """Reset Kraken credentials."""
        self.kraken_api_key = None
        self.kraken_secret_key = None

    def update_from_portfolio(self, portfolio) -> None:
        """Update API credentials from a Portfolio instance."""
        if portfolio:
            if Fernet:
                key = base64.urlsafe_b64encode(
                    hashlib.sha256(self.secret_key.encode()).digest()
                )
                f = Fernet(key)
                api_key = f.decrypt(portfolio.api_key_encrypted.encode()).decode()
                secret_key = f.decrypt(
                    portfolio.secret_key_encrypted.encode()
                ).decode()
            else:
                api_key = portfolio.api_key_encrypted
                secret_key = portfolio.secret_key_encrypted

            self.kraken_api_key = api_key
            self.kraken_secret_key = secret_key
            self.kraken_base_url = portfolio.base_url

    def __init__(self, **values):
        super().__init__(**values)

settings = Settings()

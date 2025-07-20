from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field
import base64
import hashlib
import os
import secrets
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def _load_secret_key() -> str:
    """Load the SECRET_KEY from env or generate a persistent one."""
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key
    # Ensure the key file is stored relative to the project root
    base_dir = Path(__file__).resolve().parent.parent
    key_file = base_dir / "secret.key"
    if key_file.exists():
        return key_file.read_text().strip()
    if Fernet:
        new_key = Fernet.generate_key().decode()
    else:
        new_key = secrets.token_urlsafe(32)
    key_file.write_text(new_key)
    return new_key

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

    # Alpaca
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    # Active broker identifier
    active_broker: Optional[str] = None

    # App
    app_name: str = "Trading Bot"
    debug: bool = True
    secret_key: str = Field(default_factory=_load_secret_key)

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
        """Reset credentials based on the currently active broker."""
        if self.active_broker == "alpaca":
            self.clear_alpaca_credentials()
            return
        self.kraken_api_key = None
        self.kraken_secret_key = None
        if self.active_broker == "kraken":
            self.active_broker = None

    def clear_alpaca_credentials(self) -> None:
        """Reset Alpaca credentials."""
        self.alpaca_api_key = None
        self.alpaca_secret_key = None
        if self.active_broker == "alpaca":
            self.active_broker = None

    def update_from_portfolio(self, portfolio) -> None:
        """Update API credentials from a Portfolio instance."""
        if portfolio:
            if Fernet:
                key = base64.urlsafe_b64encode(
                    hashlib.sha256(self.secret_key.encode()).digest()
                )
                f = Fernet(key)
                try:
                    api_key = f.decrypt(portfolio.api_key_encrypted.encode()).decode()
                    secret_key = f.decrypt(
                        portfolio.secret_key_encrypted.encode()
                    ).decode()
                except Exception:
                    logger.error(
                        "Failed to decrypt stored API credentials. "
                        "Ensure SECRET_KEY matches the key used during encryption."
                    )
                    return
            else:
                api_key = portfolio.api_key_encrypted
                secret_key = portfolio.secret_key_encrypted

            base_url = portfolio.base_url.rstrip("/")
            if base_url.endswith("/0"):
                base_url = base_url[:-2]

            if "alpaca.markets" in base_url:
                self.alpaca_api_key = api_key
                self.alpaca_secret_key = secret_key
                self.alpaca_base_url = base_url
                self.kraken_api_key = None
                self.kraken_secret_key = None
                self.active_broker = "alpaca"
            else:
                self.kraken_api_key = api_key
                self.kraken_secret_key = secret_key
                self.kraken_base_url = base_url
                self.alpaca_api_key = None
                self.alpaca_secret_key = None
                self.active_broker = "kraken"

    def __init__(self, **values):
        super().__init__(**values)

settings = Settings()

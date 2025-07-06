from app.config import settings
from .alpaca.client import alpaca_client
from .kraken.client import kraken_client


def _select_client():
    if settings.kraken_api_key and settings.kraken_secret_key:
        return kraken_client
    return alpaca_client


broker_client = _select_client()


def refresh_broker_client():
    """Update the global ``broker_client`` reference based on settings."""
    global broker_client
    broker_client = _select_client()

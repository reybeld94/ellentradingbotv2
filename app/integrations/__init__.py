"""Integration facade exposing the active broker client and stream."""

from .alpaca import alpaca_client, alpaca_stream
from .kraken import kraken_client, kraken_stream
from app.config import settings

__all__ = ["broker_client", "broker_stream", "refresh_broker_client"]


broker_client = kraken_client
broker_stream = kraken_stream


def refresh_broker_client() -> None:
    """Refresh and switch the global broker client/stream based on settings."""
    global broker_client, broker_stream

    if settings.active_broker == "alpaca":
        alpaca_client.refresh()
        broker_client = alpaca_client
        broker_stream = alpaca_stream
    else:
        kraken_client.refresh()
        broker_client = kraken_client
        broker_stream = kraken_stream


# Initialize the broker globals on import
refresh_broker_client()

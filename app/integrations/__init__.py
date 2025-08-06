"""Integration facade exposing the Alpaca client and stream."""

from .alpaca import alpaca_client, alpaca_stream

__all__ = ["broker_client", "broker_stream", "refresh_broker_client"]


broker_client = alpaca_client
broker_stream = alpaca_stream


def refresh_broker_client() -> None:
    """Refresh the global broker client and stream."""
    alpaca_client.refresh()


# Initialize the broker globals on import
refresh_broker_client()

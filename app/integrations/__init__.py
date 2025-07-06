from .kraken.client import kraken_client


broker_client = kraken_client


def refresh_broker_client() -> None:
    """Refresh the global broker client instance."""
    kraken_client.refresh()

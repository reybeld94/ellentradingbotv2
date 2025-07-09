import os
os.environ.setdefault('SECRET_KEY', 'secret')

from app.integrations.kraken.client import KrakenClient


def test_get_position_alt_symbols(monkeypatch):
    client = KrakenClient()

    def fake_private_post(endpoint, data=None):
        if endpoint == "Balance":
            return {"XETH": "1.25", "ZUSD": "1000"}
        return {}

    monkeypatch.setattr(client, "_private_post", fake_private_post)

    pos = client.get_position("ETH/USD")
    assert pos is not None
    assert pos.qty == 1.25


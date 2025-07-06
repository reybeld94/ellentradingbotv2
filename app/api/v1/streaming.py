from fastapi import APIRouter

from app.integrations.kraken import kraken_stream

router = APIRouter()


@router.post("/stream/subscribe/{symbol}")
async def subscribe_symbol(symbol: str):
    """Subscribe to real time trades for a given symbol."""
    kraken_stream.subscribe(symbol)
    return {"status": "subscribed", "symbol": symbol}

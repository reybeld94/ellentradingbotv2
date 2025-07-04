from fastapi import APIRouter

from ...integrations.alpaca import alpaca_stream

router = APIRouter()


@router.post("/stream/subscribe/{symbol}")
async def subscribe_symbol(symbol: str):
    """Subscribe to real time trades for a given symbol."""
    alpaca_stream.subscribe(symbol)
    return {"status": "subscribed", "symbol": symbol}

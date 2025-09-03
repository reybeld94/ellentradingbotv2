"""Portfolio performance endpoints using Alpaca Portfolio History."""

# Endpoints to expose portfolio performance history
from datetime import datetime
import logging
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_verified_user
from app.integrations.alpaca.client import AlpacaClient
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


class TimeframeEnum(str, Enum):
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    ONE_YEAR = "1Y"
    ALL = "ALL"


# Mapping between our public timeframes and Alpaca's expected period/timeframe
TIMEFRAME_TO_PORTFOLIO_PARAMS = {
    TimeframeEnum.ONE_DAY: ("1Day", "1Min"),
    TimeframeEnum.ONE_WEEK: ("1W", "15Min"),
    TimeframeEnum.ONE_MONTH: ("1M", "1Hour"),
    TimeframeEnum.THREE_MONTHS: ("3M", "1Day"),
    # Alpaca uses "A" (annual) instead of "Y" for yearly periods
    TimeframeEnum.ONE_YEAR: ("1A", "1Day"),
    # "ALL" is a special value accepted by the API for full history
    TimeframeEnum.ALL: ("ALL", "1Day"),
}


@router.get("/portfolio/performance")
async def get_portfolio_performance(
    timeframe: TimeframeEnum = Query(
        TimeframeEnum.ONE_DAY, description="Timeframe for portfolio performance"
    ),
    current_user: User = Depends(get_current_verified_user),
):
    """Return portfolio performance data using Alpaca Portfolio History."""
    try:
        alpaca_client = AlpacaClient()

        # Determine parameters based on timeframe
        period, timeframe_alpaca = TIMEFRAME_TO_PORTFOLIO_PARAMS.get(
            timeframe, ("1Day", "1Min")
        )

        from alpaca.trading.requests import GetPortfolioHistoryRequest

        portfolio_history_request = GetPortfolioHistoryRequest(
            period=period, timeframe=timeframe_alpaca, extended_hours=True
        )

        portfolio_history = alpaca_client._trading.get_portfolio_history(
            portfolio_history_request
        )

        historical_data = []
        if portfolio_history.equity and portfolio_history.timestamp:
            for i, equity in enumerate(portfolio_history.equity):
                if equity is not None and i < len(portfolio_history.timestamp):
                    historical_data.append(
                        {
                            "timestamp": portfolio_history.timestamp[i].isoformat(),
                            "portfolio_value": float(equity),
                        }
                    )

        if not historical_data:
            raise HTTPException(
                status_code=404, detail="No portfolio history data available"
            )

        current_value = historical_data[-1]["portfolio_value"]
        initial_value = historical_data[0]["portfolio_value"]
        change_amount = current_value - initial_value
        change_percent = (change_amount / initial_value * 100) if initial_value else 0

        return {
            "current_value": current_value,
            "change_amount": change_amount,
            "change_percent": round(change_percent, 2),
            "initial_value": initial_value,
            "timeframe": timeframe.value,
            "last_updated": datetime.now().isoformat(),
            "historical_data": historical_data,
        }

    except Exception as exc:  # pragma: no cover - log and rethrow
        logger.error("Error getting portfolio performance: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio performance: {exc}",
        )


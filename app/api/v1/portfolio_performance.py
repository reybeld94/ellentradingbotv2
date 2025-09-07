"""Portfolio performance endpoints using Alpaca Portfolio History."""

# Endpoints to expose portfolio performance history
from datetime import datetime, timedelta
import logging
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_verified_user
from app.database import get_db
from app.integrations.alpaca.client import AlpacaClient
from app.models.user import User
from app.services import portfolio_service

router = APIRouter()
logger = logging.getLogger(__name__)


class TimeframeEnum(str, Enum):
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    ONE_YEAR = "1Y"
    ALL = "ALL"


@router.get("/portfolio/performance")
async def get_portfolio_performance(
    timeframe: TimeframeEnum = Query(
        TimeframeEnum.ONE_DAY, description="Timeframe for portfolio performance"
    ),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Return portfolio performance data using Alpaca Portfolio History."""
    try:
        active_portfolio = portfolio_service.get_active(db, current_user)
        if not active_portfolio:
            raise HTTPException(status_code=400, detail="No active portfolio found")

        alpaca_client = AlpacaClient(active_portfolio)

        # Calculate date range based on timeframe
        end_date = datetime.now()
        if timeframe == TimeframeEnum.ONE_DAY:
            start_date = end_date - timedelta(days=1)
            timeframe_alpaca = "1Min"  # Maximum detail for 1 day
        elif timeframe == TimeframeEnum.ONE_WEEK:
            start_date = end_date - timedelta(days=7)
            timeframe_alpaca = "15Min"  # Balance detail for 1 week
        elif timeframe == TimeframeEnum.ONE_MONTH:
            # Use 28 days to keep the range under 30 days
            start_date = end_date - timedelta(days=28)
            timeframe_alpaca = "1H"  # Hourly granularity
        elif timeframe == TimeframeEnum.THREE_MONTHS:
            start_date = end_date - timedelta(days=90)
            timeframe_alpaca = "1D"  # Daily required for >30 days
        elif timeframe == TimeframeEnum.ONE_YEAR:
            start_date = end_date - timedelta(days=365)
            timeframe_alpaca = "1D"  # Daily required for >30 days
        else:  # ALL
            start_date = end_date - timedelta(days=730)  # 2 years maximum
            timeframe_alpaca = "1D"  # Daily required for >30 days

        from alpaca.trading.requests import GetPortfolioHistoryRequest

        portfolio_history_request = GetPortfolioHistoryRequest(
            start=start_date,
            end=end_date,
            timeframe=timeframe_alpaca,
            extended_hours=True,
        )

        portfolio_history = alpaca_client._trading.get_portfolio_history(
            portfolio_history_request
        )

        # Process the data
        historical_data = []
        if portfolio_history.equity and portfolio_history.timestamp:
            for i, equity in enumerate(portfolio_history.equity):
                if equity is not None and i < len(portfolio_history.timestamp):
                    timestamp_raw = portfolio_history.timestamp[i]

                    try:
                        # Attempt to convert timestamp (can be int, float, or datetime)
                        if hasattr(timestamp_raw, "isoformat"):
                            # Already a datetime object
                            timestamp_str = timestamp_raw.isoformat()
                        else:
                            # Assume Unix timestamp in seconds
                            timestamp_dt = datetime.fromtimestamp(float(timestamp_raw))
                            timestamp_str = timestamp_dt.isoformat()

                        historical_data.append(
                            {
                                "timestamp": timestamp_str,
                                "portfolio_value": float(equity),
                            }
                        )

                    except (ValueError, TypeError, OSError) as e:
                        logger.warning(
                            f"Skipping invalid timestamp {timestamp_raw}: {e}"
                        )
                        continue

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

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - log and rethrow
        logger.error("Error getting portfolio performance: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio performance: {exc}",
        )


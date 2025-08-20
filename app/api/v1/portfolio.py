from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.core.auth import get_current_verified_user

router = APIRouter()

@router.get("/portfolio/realtime")
async def get_realtime_portfolio(current_user: User = Depends(get_current_verified_user)):
    """Get portfolio with real-time PnL from positions"""
    try:
        from app.integrations import broker_client
        from app.services.position_manager import position_manager

        # Obtener datos de cuenta base
        account = broker_client.get_account()
        buying_power = float(getattr(account, "buying_power", 0))
        portfolio_value = float(getattr(account, "portfolio_value", 0))
        cash = float(getattr(account, "cash", 0))

        # Obtener posiciones con PnL real
        detailed_positions = position_manager.get_detailed_positions()

        # Calcular PnL total no realizado
        total_unrealized_pl = sum(pos.get('unrealized_pl', 0.0) for pos in detailed_positions)

        return {
            "account": {
                "buying_power": str(buying_power),
                "portfolio_value": str(portfolio_value),
                "cash": str(cash),
                "unrealized_pl": total_unrealized_pl,
                "day_change": total_unrealized_pl,
                "day_change_percent": (total_unrealized_pl / (portfolio_value - total_unrealized_pl) * 100) if portfolio_value > total_unrealized_pl else 0
            },
            "positions": detailed_positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

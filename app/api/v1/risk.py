from fastapi import APIRouter, Depends, HTTPException
from alpaca.common.exceptions import APIError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.services.risk_manager import risk_manager
from app.services.position_manager import position_manager

# Symbols that should be treated as cash equivalents
STABLE_COINS = {"USD", "ZUSD", "USDC", "USDT"}

router = APIRouter()

@router.get("/risk/status")
async def get_risk_status(current_user: User = Depends(get_current_verified_user)):
    """Get current risk management status and allocation info"""
    try:
        from app.integrations import broker_client
        account = broker_client.get_account()
        buying_power = float(getattr(account, "buying_power", 0))
        portfolio_value = float(getattr(account, "portfolio_value", 0))

        allocation_info = risk_manager.get_allocation_info(buying_power)

        # Build detailed positions
        raw_positions = position_manager.get_current_positions()
        position_details = []
        for symbol, qty in raw_positions.items():
            if abs(float(qty)) < 0.001:
                continue
            price = 1.0 if symbol in STABLE_COINS else 0.0
            if symbol not in STABLE_COINS:
                try:
                    quote = broker_client.get_latest_quote(symbol)
                    price = float(getattr(quote, "ask_price", getattr(quote, "ap", 0)))
                except Exception:
                    price = 0.0
            market_value = price * float(qty)
            print(f"DBG Position {symbol} qty={qty} price={price} value={market_value}")
            position_details.append({
                "symbol": symbol,
                "quantity": float(qty),
                "market_value": market_value,
                "unrealized_pl": 0.0,
                "percentage": (market_value / portfolio_value * 100) if portfolio_value > 0 else 0,
            })

        # Simulate next positions
        symbols_to_simulate = ["AAPL", "MSFT", "AMZN", "GOOG"]
        next_positions_simulation = []
        for symbol in symbols_to_simulate:
            try:
                quote = broker_client.get_latest_quote(symbol)
                price = float(getattr(quote, "ask_price", getattr(quote, "ap", 100000)))
                simulated_qty = risk_manager.calculate_optimal_position_size(
                    price=price,
                    buying_power=buying_power,
                    symbol=symbol,
                )
                simulated_value = simulated_qty * price
                minimum_qty = risk_manager.get_symbol_minimum(symbol)
                next_positions_simulation.append({
                    "symbol": symbol,
                    "current_price": price,
                    "would_buy_qty": simulated_qty,
                    "would_invest_usd": simulated_value,
                    "minimum_required": minimum_qty,
                    "can_enter": simulated_qty >= minimum_qty,
                    "percentage_of_portfolio": (simulated_value / buying_power * 100) if buying_power > 0 else 0,
                })
            except Exception as e:
                print(f"Error simulating {symbol}: {e}")
                continue

        return {
            "account_info": {
                "buying_power": buying_power,
                "portfolio_value": portfolio_value,
                "cash_percentage": (buying_power / portfolio_value * 100) if portfolio_value > 0 else 100,
            },
            "allocation_info": allocation_info,
            "current_positions": position_details,
            "risk_metrics": {
                "position_count": len(position_details),
                "capital_utilization": ((portfolio_value - buying_power) / portfolio_value * 100) if portfolio_value > 0 else 0,
                "largest_position_pct": max([p["percentage"] for p in position_details], default=0),
                "concentration_risk": "High" if any(p["percentage"] > 40 for p in position_details) else "Medium" if any(p["percentage"] > 25 for p in position_details) else "Low",
            },
            "next_positions_simulation": next_positions_simulation,
        }
    except APIError as e:
        print(f"Error getting risk status: {e}")
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Alpaca API error: {getattr(e, 'message', str(e))}",
        )
    except Exception as e:
        print(f"Error getting risk status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/allocation-chart")
async def get_allocation_chart_data(current_user: User = Depends(get_current_verified_user)):
    """Get data for allocation pie chart"""
    try:
        raw_positions = position_manager.get_current_positions()
        from app.integrations import broker_client
        account = broker_client.get_account()
        buying_power = float(getattr(account, "buying_power", 0))

        chart_data = []
        for symbol, qty in raw_positions.items():
            if float(qty) <= 0:
                continue
            price = 1.0 if symbol in STABLE_COINS else 0.0
            if symbol not in STABLE_COINS:
                try:
                    quote = broker_client.get_latest_quote(symbol)
                    price = float(getattr(quote, "ask_price", getattr(quote, "ap", 0)))
                except Exception:
                    price = 0.0
            market_value = price * float(qty)
            print(f"DBG Chart {symbol} qty={qty} price={price} value={market_value}")
            if market_value > 0:
                chart_data.append({
                    "name": symbol,
                    "value": market_value,
                    "color": _get_symbol_color(symbol),
                })
        if buying_power > 0:
            chart_data.append({
                "name": "Available Cash",
                "value": buying_power,
                "color": "#10B981",
            })
        return {"chart_data": chart_data}
    except APIError as e:
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Alpaca API error: {getattr(e, 'message', str(e))}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_symbol_color(symbol: str) -> str:
    colors = {
        "AAPL": "#F59E0B",
        "MSFT": "#6366F1",
        "AMZN": "#8B5CF6",
        "GOOG": "#10B981",
    }
    return colors.get(symbol, "#6B7280")

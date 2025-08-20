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

        # DEBUG INFO - Vamos a incluir información de debug en la respuesta
        debug_info = {
            "alpaca_raw_positions": [],
            "processed_positions": [],
            "broker_client_type": str(type(broker_client)),
            "has_trading_client": hasattr(broker_client, '_trading') and broker_client._trading is not None
        }

        # Obtener posiciones directamente de Alpaca para debug
        if hasattr(broker_client, '_trading') and broker_client._trading:
            try:
                raw_alpaca_positions = broker_client._trading.get_all_positions()
                for p in raw_alpaca_positions:
                    debug_info["alpaca_raw_positions"].append({
                        "symbol": p.symbol,
                        "qty": str(p.qty),
                        "has_market_value": hasattr(p, 'market_value'),
                        "market_value_raw": str(getattr(p, 'market_value', 'NOT_FOUND')),
                        "has_unrealized_pl": hasattr(p, 'unrealized_pl'),
                        "unrealized_pl_raw": str(getattr(p, 'unrealized_pl', 'NOT_FOUND')),
                        "has_unrealized_intraday_pl": hasattr(p, 'unrealized_intraday_pl'),
                        "unrealized_intraday_pl_raw": str(getattr(p, 'unrealized_intraday_pl', 'NOT_FOUND')),
                        "has_unrealized_today_pl": hasattr(p, 'unrealized_today_pl'),
                        "unrealized_today_pl_raw": str(getattr(p, 'unrealized_today_pl', 'NOT_FOUND')),
                        "all_attributes": [attr for attr in dir(p) if not attr.startswith('_') and 'pl' in attr.lower()]
                    })
            except Exception as e:
                debug_info["alpaca_error"] = str(e)

        # Build detailed positions using the complete information of Alpaca
        detailed_positions = position_manager.get_detailed_positions()
        position_details = []

        for pos in detailed_positions:
            symbol = pos['symbol']

            # DEBUG: Agregar info de esta posición procesada
            debug_info["processed_positions"].append({
                "symbol": symbol,
                "original_pos_data": pos
            })

            # Para stable coins, usar valores directos
            if symbol in STABLE_COINS:
                market_value = pos['market_value']
                unrealized_pl = 0.0  # Las stable coins no tienen PnL
            else:
                # Para activos normales, usar los valores de Alpaca directamente
                market_value = pos['market_value']
                unrealized_pl = pos['unrealized_pl']

            position_details.append({
                "symbol": symbol,
                "quantity": pos['quantity'],
                "market_value": market_value,
                "unrealized_pl": unrealized_pl,
                "unrealized_plpc": pos.get('unrealized_plpc', 0.0),
                "cost_basis": pos.get('cost_basis', 0.0),
                "avg_entry_price": pos.get('avg_entry_price', 0.0),
                "current_price": pos.get('current_price', 0.0),
                "percentage": (market_value / portfolio_value * 100) if portfolio_value > 0 else 0,
            })

        # Simulate next positions (mantener igual)
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
                continue

        return {
            "account_info": {
                "buying_power": buying_power,
                "portfolio_value": portfolio_value,
                "cash_percentage": (buying_power / portfolio_value * 100) if portfolio_value > 0 else 100,
                "total_unrealized_pl": sum(pos["unrealized_pl"] for pos in position_details),
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
            "debug_info": debug_info  # NUEVA SECCIÓN DE DEBUG
        }
    except APIError as e:
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Alpaca API error: {getattr(e, 'message', str(e))}",
        )
    except Exception as e:
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

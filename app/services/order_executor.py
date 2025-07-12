# backend/app/services/order_executor.py
from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.config import settings
from app.services.position_manager import position_manager
from app.services.strategy_position_manager import StrategyPositionManager
from app.database import get_db
import logging
from app.models.trades import Trade
from sqlalchemy.sql import func
from app.websockets import ws_manager
import asyncio
import json
logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self):
        from app.integrations import broker_client
        self.broker = broker_client
        self.position_manager = position_manager

    def is_crypto(self, symbol):
        """Verificar si es un símbolo de crypto"""
        return '/' in symbol or symbol.endswith('USD')

    def map_symbol(self, symbol: str) -> str:
        """Convert TradingView symbols to Kraken format."""
        symbol_map = {
            'BTCUSD': 'BTC/USD',
            'ETHUSD': 'ETH/USD',
            'SOLUSD': 'SOL/USD',
            'BCHUSD': 'BCH/USD',
        }
        mapped = symbol_map.get(symbol, symbol)
        print(f"🔄 Symbol mapping: {symbol} -> {mapped}")
        return mapped

    def calculate_position_size(self, symbol, action):
        """Calcular tamaño de posición usando el RiskManager"""
        print(f"💰 Calculating position size for {symbol} ({action})")

        account = self.broker.get_account()
        buying_power = float(account.buying_power)
        print(f"💰 Account buying power: ${buying_power:,.2f}")

        mapped_symbol = self.map_symbol(symbol)
        final_symbol = mapped_symbol

        try:
            if self.is_crypto(symbol):
                print("🔍 Trying crypto quote...")
                quote = self.broker.get_latest_crypto_quote(mapped_symbol)
                current_price = float(getattr(quote, 'ask_price', getattr(quote, 'ap', None)))
                if current_price is None:
                    raise ValueError("No ask price found in crypto quote")
                print(f"📊 Crypto quote for {mapped_symbol}: ${current_price}")
            else:
                print("🔍 Trying stock quote...")
                quote = self.broker.get_latest_quote(mapped_symbol)
                current_price = float(quote.ask_price)
                print(f"📊 Stock quote for {mapped_symbol}: ${current_price}")
        except Exception as e:
            print(f"❌ Quote failed for {mapped_symbol}: {e}")
            raise

        is_fractionable = self.broker.is_asset_fractionable(final_symbol)
        print(f"🔍 Asset {final_symbol} is fractionable: {is_fractionable}")

        from app.services.risk_manager import risk_manager

        base_qty = risk_manager.calculate_optimal_position_size(
            price=current_price,
            buying_power=buying_power,
            symbol=mapped_symbol,
        )

        if base_qty == 0:
            raise ValueError(
                f"Insufficient capital for minimum quantity in {mapped_symbol}"
            )

        print(f"📐 Smart allocation quantity: {base_qty}")

        if self.is_crypto(symbol) or is_fractionable:
            final_quantity = max(0.000001, round(base_qty, 6))
            print(f"🔢 Fractionable quantity calculated: {final_quantity} {final_symbol}")
        else:
            final_quantity = max(1, int(base_qty))
            print(f"🔢 Stock quantity calculated: {final_quantity} shares of {final_symbol}")

        return final_quantity, final_symbol

    def execute_signal(self, signal: Signal, user):
        try:
            print(f"🚀 Executing signal: {signal.strategy_id} {signal.action} {signal.symbol}")

            from app.database import SessionLocal
            db = SessionLocal()
            strategy_manager = StrategyPositionManager(db)

            try:
                # MAPEAR símbolo
                correct_symbol = self.map_symbol(signal.symbol)

                if signal.action.lower() == 'buy':
                    if not signal.quantity:
                        quantity, correct_symbol = self.calculate_position_size(signal.symbol, signal.action)
                        signal.quantity = quantity

                    order = self._execute_buy_signal(signal, strategy_manager, correct_symbol, user.position_limit, db)


                elif signal.action.lower() == 'sell':
                    # Use entire strategy position but verify actual account quantity
                    strategy_position = strategy_manager.get_strategy_position(signal.strategy_id, signal.symbol)

                    if strategy_position.quantity <= 0:
                        raise ValueError(
                            f"Strategy {signal.strategy_id} has no position in {signal.symbol} to sell"
                        )

                    # Get current quantity from broker to avoid overselling due to rounding
                    account_qty = self.position_manager.get_position_quantity(correct_symbol)
                    print(f"📊 Account position for {correct_symbol}: {account_qty}")

                    if account_qty <= 0:
                        logger.warning(
                            f"No account position found for {correct_symbol} when processing sell signal"
                        )
                        strategy_manager.reset_position(signal.strategy_id, signal.symbol)
                        raise ValueError(
                            f"No account position found for {correct_symbol} to sell"
                        )

                    sell_qty = min(strategy_position.quantity, account_qty)
                    signal.quantity = sell_qty
                    order = self._execute_sell_signal(signal, strategy_manager, correct_symbol, db)

                else:
                    raise ValueError(f"Unknown action: {signal.action}")

                signal.status = "processed"
                signal.error_message = None

                print(f"✅ Signal executed successfully: {order.id}")
                logger.info(f"Order executed: {order.id} for {signal.symbol}")

                order_data = {
                    "id": str(order.id),
                    "symbol": signal.symbol,
                    "side": signal.action,
                    "status": str(getattr(order, "status", "")),
                }
                asyncio.create_task(
                    ws_manager.broadcast(
                        json.dumps({"event": "order_update", "payload": order_data})
                    )
                )

                return order

            finally:
                db.close()

        except Exception as e:
            signal.status = "error"
            signal.error_message = str(e)

            print(f"❌ Error executing signal: {e}")
            logger.error(f"Error executing signal for {signal.symbol}: {e}")
            raise

    def _execute_buy_signal(self, signal: Signal, strategy_manager: StrategyPositionManager, correct_symbol: str, limit: int, db: Session):

        print(f"🟢 Executing BUY for {signal.strategy_id}:{signal.symbol} (as {correct_symbol})")

        current_positions = self.position_manager.count_open_positions()
        print(f"📊 Current positions: {current_positions}/{limit}")

        if current_positions >= limit:
            raise ValueError(f"Maximum positions limit reached ({limit})")

        account = self.broker.get_account()
        available_cash = float(account.cash)
        print(f"💵 Available cash: ${available_cash:,.2f}")

        is_fractionable = self.broker.is_asset_fractionable(correct_symbol)
        print(f"🔍 Asset {correct_symbol} is fractionable: {is_fractionable}")

        if isinstance(signal.quantity, float) and signal.quantity != int(signal.quantity) and not is_fractionable:
            print(f"⚠️ Asset {correct_symbol} is not fractionable, converting {signal.quantity} to integer")
            signal.quantity = max(1, int(signal.quantity))
            print(f"🔄 Adjusted quantity: {signal.quantity}")

        try:
            if self.is_crypto(signal.symbol):
                quote = self.broker.get_latest_crypto_quote(correct_symbol)
                current_price = float(getattr(quote, 'ask_price', getattr(quote, 'ap', None)))
                if current_price is None:
                    raise ValueError("No ask price found in crypto quote")
            else:
                quote = self.broker.get_latest_quote(correct_symbol)
                current_price = float(quote.ask_price)
        except Exception as e:
            print(f"❌ Failed to get final quote for {correct_symbol}: {e}")
            raise

        estimated_cost = current_price * signal.quantity

        print("💰 Order details:")
        print(f"   - Original symbol: {signal.symbol}")
        print(f"   - Broker symbol: {correct_symbol}")
        print(f"   - Price: ${current_price}")
        print(f"   - Quantity: {signal.quantity}")
        print(f"   - Estimated cost: ${estimated_cost:,.2f}")
        print(f"   - Is fractionable: {is_fractionable}")

        if estimated_cost > available_cash:
            raise ValueError(f"Insufficient cash. Need: ${estimated_cost:.2f}, Available: ${available_cash:.2f}")

        print("📤 Submitting order to broker...")
        if self.is_crypto(signal.symbol):
            order = self.broker.submit_crypto_order(
                symbol=correct_symbol,
                qty=signal.quantity,
                side=signal.action
            )
            print(f"📤 Crypto order submitted: {order.id}")
        else:
            order = self.broker.submit_order(
                symbol=correct_symbol,
                qty=signal.quantity,
                side=signal.action
            )
            print(f"📤 Stock order submitted: {order.id}")
        new_trade = Trade(
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            action='buy',
            quantity=signal.quantity,
            entry_price=current_price,
            status='open',
            user_id=signal.user_id,
            portfolio_id=signal.portfolio_id
        )
        db.add(new_trade)
        db.commit()
        logger.info(f"💾 Trade created: {new_trade}")
        asyncio.create_task(
            ws_manager.broadcast(
                json.dumps({
                    "event": "trade_update",
                    "payload": {"symbol": signal.symbol, "action": "buy"}
                })
            )
        )
        print("📊 Updating strategy position...")
        strategy_manager.add_position(
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            quantity=signal.quantity,
            price=current_price
        )

        print(f"✅ Buy order completed: {signal.strategy_id} bought {signal.quantity} {signal.symbol}")
        logger.info(f"Buy order executed: {signal.strategy_id} bought {signal.quantity} {signal.symbol}")
        return order

    def _execute_sell_signal(self, signal: Signal, strategy_manager: StrategyPositionManager, correct_symbol: str, db: Session):

        print(f"🔴 Executing SELL for {signal.strategy_id}:{signal.symbol} (as {correct_symbol})")

        strategy_position = strategy_manager.get_strategy_position(signal.strategy_id, signal.symbol)
        print(f"📊 Current strategy position: {strategy_position.quantity} {signal.symbol}")

        if strategy_position.quantity <= 0:
            raise ValueError(f"Strategy {signal.strategy_id} has no position in {signal.symbol} to sell")

        quantity_to_sell = min(signal.quantity, strategy_position.quantity)
        signal.quantity = quantity_to_sell

        print(f"📊 Selling {quantity_to_sell} out of {strategy_position.quantity} available")

        try:
            if self.is_crypto(signal.symbol):
                quote = self.broker.get_latest_crypto_quote(correct_symbol)
                current_price = float(getattr(quote, 'ask_price', getattr(quote, 'ap', None)))
                if current_price is None:
                    raise ValueError("No ask price found in crypto quote")
            else:
                quote = self.broker.get_latest_quote(correct_symbol)
                current_price = float(quote.ask_price)
        except Exception as e:
            print(f"❌ Failed to get final quote for {correct_symbol}: {e}")
            raise

        print(f"📤 Submitting sell order to broker for {correct_symbol}...")
        if self.is_crypto(signal.symbol):
            order = self.broker.submit_crypto_order(
                symbol=correct_symbol,
                qty=quantity_to_sell,
                side=signal.action
            )
            print(f"📤 Crypto sell order submitted: {order.id}")
        else:
            order = self.broker.submit_order(
                symbol=correct_symbol,
                qty=quantity_to_sell,
                side=signal.action
            )
            print(f"📤 Stock sell order submitted: {order.id}")
        open_trades = db.query(Trade).filter_by(
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            status='open',
            user_id=signal.user_id,
            portfolio_id=signal.portfolio_id
        ).order_by(Trade.opened_at.desc()).all()

        if open_trades:
            now = func.now()
            for trade in open_trades:
                trade.exit_price = current_price
                trade.closed_at = now
                trade.status = 'closed'
                trade.pnl = (current_price - trade.entry_price) * trade.quantity
            db.commit()
            logger.info(
                f"💾 Closed {len(open_trades)} trade(s) for {signal.strategy_id}:{signal.symbol}"
            )
        else:
            logger.warning(
                f"⚠️ No open trades found to close for {signal.strategy_id}:{signal.symbol}"
            )
        print("📊 Reducing strategy position...")
        actual_sold = strategy_manager.reduce_position(
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            quantity=quantity_to_sell
        )

        asyncio.create_task(
            ws_manager.broadcast(
                json.dumps({
                    "event": "trade_update",
                    "payload": {"symbol": signal.symbol, "action": "sell"}
                })
            )
        )

        print(f"✅ Sell order completed: {signal.strategy_id} sold {actual_sold} {signal.symbol}")
        logger.info(f"Sell order executed: {signal.strategy_id} sold {actual_sold} {signal.symbol}")
        return order


# Instancia global
order_executor = OrderExecutor()

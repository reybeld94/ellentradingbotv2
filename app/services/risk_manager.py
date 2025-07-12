from sqlalchemy.orm import sessionmaker

from app.database import SessionLocal


class RiskManager:
    """Smart Dynamic Capital Allocation manager."""

    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self.session_factory = session_factory
        # Default reserved slots for future opportunities
        self.reserved_slots = 3
        # Minimum quantities required per symbol
        self.symbol_minimums = {
            "BTC/USD": 0.00005,
            "ETH/USD": 0.002,
            "SOL/USD": 0.02,
            "BCH/USD": 0.01,
            # TradingView format fallback
            "BTCUSD": 0.00005,
            "ETHUSD": 0.002,
            "SOLUSD": 0.02,
            "BCHUSD": 0.01,
        }

    def _get_open_positions_count(self) -> int:
        """Return the number of active positions at the broker."""
        from app.services.position_manager import position_manager

        try:
            positions = position_manager.get_current_positions()
            active_positions = [p for p in positions.values() if abs(float(p)) > 0.001]
            count = len(active_positions)

            print(f"📊 Active positions count: {count}")
            return count
        except Exception as e:
            print(f"❌ Error getting positions count: {e}")
            return 0

    def calculate_optimal_position_size(self, price: float, buying_power: float, symbol: str | None = None) -> float:
        """Calculate quantity to buy using Smart Dynamic Allocation."""
        open_positions_count = self._get_open_positions_count()

        capital_per_position = buying_power / (open_positions_count + self.reserved_slots)

        if price <= 0:
            return 0.0

        calculated_quantity = capital_per_position / price

        if symbol and symbol in self.symbol_minimums:
            minimum_qty = self.symbol_minimums[symbol]
            if calculated_quantity < minimum_qty:
                print(
                    f"⚠️ Insufficient quantity: calculated {calculated_quantity:.6f}, minimum {minimum_qty}"
                )
                return 0.0

        print("💰 Smart Allocation Debug:")
        print(f"   Available Capital: ${buying_power:,.2f}")
        print(f"   Open Positions: {open_positions_count}")
        print(f"   Reserved Slots: {self.reserved_slots}")
        print(f"   Capital per Position: ${capital_per_position:,.2f}")
        print(f"   Asset Price: ${price:,.2f}")
        print(f"   Calculated Quantity: {calculated_quantity:.6f}")
        if symbol and symbol in self.symbol_minimums:
            print(f"   Minimum Quantity Required: {self.symbol_minimums[symbol]}")
            print(
                f"   ✅ Minimum validation: {'PASSED' if calculated_quantity >= self.symbol_minimums[symbol] else 'FAILED'}"
            )

        return calculated_quantity

    def set_reserved_slots(self, slots: int):
        """Configure how many slots to reserve for future trades."""
        if slots < 1:
            raise ValueError("Reserved slots debe ser al menos 1")
        if slots > 10:
            raise ValueError("Reserved slots no debería exceder 10")
        self.reserved_slots = slots
        print(f"⚙️ Reserved slots updated to: {slots}")

    def get_allocation_info(self, buying_power: float) -> dict:
        """Return current allocation information."""
        open_positions = self._get_open_positions_count()
        capital_per_position = buying_power / (open_positions + self.reserved_slots)
        return {
            "available_capital": buying_power,
            "open_positions": open_positions,
            "reserved_slots": self.reserved_slots,
            "capital_per_position": capital_per_position,
            "next_position_percentage": (capital_per_position / buying_power * 100)
            if buying_power > 0
            else 0,
        }

    def update_symbol_minimum(self, symbol: str, minimum_quantity: float):
        """Update the minimum quantity required for a symbol."""
        self.symbol_minimums[symbol] = minimum_quantity
        print(f"⚙️ Updated minimum for {symbol}: {minimum_quantity}")

    def get_symbol_minimum(self, symbol: str) -> float:
        """Return minimum quantity for a symbol or 0 if not configured."""
        return self.symbol_minimums.get(symbol, 0.0)


# Global instance using the app session
risk_manager = RiskManager()

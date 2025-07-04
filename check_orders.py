# check_orders.py

from app.integrations.alpaca.client import alpaca_client

def run():
    print("🔍 Verificando órdenes en Alpaca...")
    orders = alpaca_client.list_orders(status='all', limit=10)

    if not orders:
        print("⚠️ No hay órdenes en Alpaca.")
        return

    for o in orders:
        print(f"🧾 {o.symbol} | {o.side} | {o.status} | qty={o.qty} | id={o.id}")

if __name__ == "__main__":
    run()

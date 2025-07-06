# check_orders.py

from app.integrations import broker_client


def run():
    print("🔍 Verificando órdenes en broker...")
    orders = broker_client.list_orders(status='all', limit=10)

    if not orders:
        print("⚠️ No hay órdenes en el broker.")
        return

    for o in orders:
        msg = (
            f"🧾 {o.symbol} | {o.side} | {o.status} | "
            f"qty={o.qty} | id={o.id}"
        )
        print(msg)

if __name__ == "__main__":
    run()

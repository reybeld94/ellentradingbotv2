#!/usr/bin/env python3
"""
Quick script to check and activate portfolio for analytics
"""

from app.database import SessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services import portfolio_service

def check_and_activate_portfolio():
    db = SessionLocal()
    
    try:
        # Find user (adjust email if needed)
        user = db.query(User).filter(User.email == "reybel@archintel.com").first()  # Based on the logs you showed
        if not user:
            print("❌ User not found")
            return
            
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        
        # Check portfolios
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        
        if not portfolios:
            print("❌ No portfolios found for user")
            return
            
        print(f"📁 Found {len(portfolios)} portfolios:")
        for p in portfolios:
            status = "🟢 ACTIVE" if p.is_active else "⚫ inactive"
            print(f"  - {p.name} (ID: {p.id}) [{p.broker}] {status}")
        
        # Check if any is active
        active = portfolio_service.get_active(db, user)
        if active:
            print(f"✅ Active portfolio: {active.name}")
        else:
            print("❌ No active portfolio found")
            
            # Activate the first portfolio
            first_portfolio = portfolios[0]
            print(f"🔄 Activating first portfolio: {first_portfolio.name}")
            portfolio_service.activate_portfolio(db, user, first_portfolio.id)
            print("✅ Portfolio activated!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_and_activate_portfolio()

from app import create_app
from database import db
from models.user import User
from models.portfolio import Portfolio, PortfolioItem
from models.alert import Alert
from models.watchlist import Watchlist, WatchlistSymbol
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            print("Creating admin user...")
            admin = User(
                id=str(uuid.uuid4()),
                name='Admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                created_at=datetime.now()
            )
            db.session.add(admin)
            db.session.commit()
            
            # Create default portfolio and watchlist for admin
            default_portfolio = Portfolio(user_id=admin.id)
            default_watchlist = Watchlist(user_id=admin.id)
            
            db.session.add(default_portfolio)
            db.session.add(default_watchlist)
            db.session.commit()
            
            # Add some sample data
            # Add portfolio items
            portfolio_items = [
                PortfolioItem(
                    portfolio_id=default_portfolio.id,
                    symbol='BTC',
                    quantity=0.5,
                    purchase_price=40000,
                    purchase_date=datetime.now(),
                    invested=20000
                ),
                PortfolioItem(
                    portfolio_id=default_portfolio.id,
                    symbol='ETH',
                    quantity=5,
                    purchase_price=2500,
                    purchase_date=datetime.now(),
                    invested=12500
                )
            ]
            
            db.session.add_all(portfolio_items)
            
            # Add watchlist items
            for symbol in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']:
                watchlist_symbol = WatchlistSymbol(
                    watchlist_id=default_watchlist.id,
                    symbol=symbol
                )
                db.session.add(watchlist_symbol)
            
            # Add sample alerts
            alerts = [
                Alert(
                    user_id=admin.id,
                    symbol='BTC',
                    alert_type='above',
                    target_price=60000,
                    created_at=datetime.now()
                ),
                Alert(
                    user_id=admin.id,
                    symbol='ETH',
                    alert_type='below',
                    target_price=2000,
                    created_at=datetime.now()
                )
            ]
            
            db.session.add_all(alerts)
            db.session.commit()
            
            print("Sample data created successfully.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    init_db()

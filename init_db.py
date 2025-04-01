from app import db
from models.user import User
from models.portfolio import Portfolio, PortfolioItem
from models.watchlist import Watchlist, WatchlistSymbol
from models.alert import Alert

def init_db():
    db.create_all()

    # Create an initial admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password='password123',
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()

    print('Database initialized.')

if __name__ == '__main__':
    init_db()

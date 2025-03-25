from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so they are registered with SQLAlchemy
from .user import User
from .portfolio import Portfolio, PortfolioItem
from .alert import Alert
from .watchlist import Watchlist, WatchlistSymbol

# Update model imports to use the shared db instance
User.db = db
Portfolio.db = db
PortfolioItem.db = db
Alert.db = db
Watchlist.db = db
WatchlistSymbol.db = db

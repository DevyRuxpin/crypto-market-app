import uuid
from datetime import datetime

class Watchlist:
    """Model for cryptocurrency watchlists"""
    
    # In-memory storage for watchlists
    watchlists = {}
    
    def __init__(self, user_id, name="Default Watchlist"):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.name = name
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.symbols = []  # List of cryptocurrency symbols in the watchlist
        
        # Save to in-memory storage
        if user_id not in Watchlist.watchlists:
            Watchlist.watchlists[user_id] = []
        Watchlist.watchlists[user_id].append(self)
    
    @staticmethod
    def get_user_watchlists(user_id):
        """Get all watchlists for a user"""
        return Watchlist.watchlists.get(user_id, [])
    
    @staticmethod
    def get_watchlist(watchlist_id):
        """Get a specific watchlist by ID"""
        for user_watchlists in Watchlist.watchlists.values():
            for watchlist in user_watchlists:
                if watchlist.id == watchlist_id:
                    return watchlist
        return None
    
    def add_symbol(self, symbol):
        """Add a cryptocurrency symbol to the watchlist"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self.updated_at = datetime.now()
            return True
        return False
    
    def remove_symbol(self, symbol):
        """Remove a cryptocurrency symbol from the watchlist"""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            self.updated_at = datetime.now()
            return True
        return False
    
    def to_dict(self):
        """Convert watchlist to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'symbols': self.symbols,
            'count': len(self.symbols)
        }

from ..database import db
from datetime import datetime
import uuid


class Watchlist(db.Model):
    __tablename__ = 'watchlists'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, default="Default Watchlist")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='watchlists')
    symbols = db.relationship('WatchlistSymbol', back_populates='watchlist', cascade='all, delete-orphan')
    
    @classmethod
    def get_user_watchlists(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_watchlist(cls, watchlist_id):
        return cls.query.get(watchlist_id)
    
    def add_symbol(self, symbol):
        # Check if symbol already exists
        existing = WatchlistSymbol.query.filter_by(
            watchlist_id=self.id, symbol=symbol).first()
        
        if not existing:
            new_symbol = WatchlistSymbol(watchlist_id=self.id, symbol=symbol)
            db.session.add(new_symbol)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def remove_symbol(self, symbol):
        symbol_obj = WatchlistSymbol.query.filter_by(
            watchlist_id=self.id, symbol=symbol).first()
        
        if symbol_obj:
            db.session.delete(symbol_obj)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'symbols': [s.symbol for s in self.symbols],
            'count': len(self.symbols)
        }

class WatchlistSymbol(db.Model):
    __tablename__ = 'watchlist_symbols'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    watchlist_id = db.Column(db.String(36), db.ForeignKey('watchlists.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlist = db.relationship('Watchlist', back_populates='symbols')
    
    # Ensure symbol uniqueness within a watchlist
    __table_args__ = (db.UniqueConstraint('watchlist_id', 'symbol'),)

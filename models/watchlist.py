from app import db
from models.user import User

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('watchlist', lazy='dynamic'))
    symbols = db.relationship('WatchlistSymbol', backref='watchlist', lazy='dynamic')

    def add_symbol(self, symbol):
        symbol_obj = WatchlistSymbol(symbol=symbol, watchlist_id=self.id)
        db.session.add(symbol_obj)
        db.session.commit()

    def remove_symbol(self, symbol_obj):
        db.session.delete(symbol_obj)
        db.session.commit()

class WatchlistSymbol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlist.id'), nullable=False)

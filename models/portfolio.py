from app import db
from models.user import User

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('portfolio', lazy='dynamic'))
    items = db.relationship('PortfolioItem', backref='portfolio', lazy='dynamic')

    def add_item(self, symbol, quantity, avg_price):
        item = PortfolioItem(symbol=symbol, quantity=quantity, avg_price=avg_price, portfolio_id=self.id)
        db.session.add(item)
        db.session.commit()

    def remove_item(self, item):
        db.session.delete(item)
        db.session.commit()

class PortfolioItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)

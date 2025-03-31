from database import db
from datetime import datetime
import uuid

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), default="Default Portfolio")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='portfolios')
    items = db.relationship('PortfolioItem', back_populates='portfolio', cascade='all, delete-orphan')
    
    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).first()
    
    def add_item(self, item):
        self.items.append(item)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_item(self, item_id, quantity, purchase_price, invested):
        item = PortfolioItem.query.get(item_id)
        if item and item.portfolio_id == self.id:
            item.quantity = quantity
            item.purchase_price = purchase_price
            item.invested = invested
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def remove_item(self, item_id):
        item = PortfolioItem.query.get(item_id)
        if item and item.portfolio_id == self.id:
            db.session.delete(item)
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
            'updated_at':  self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = db.Column(db.String(36), db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    invested = db.Column(db.Float, nullable=False)
    
    # Relationships
    portfolio = db.relationship('Portfolio', back_populates='items')
    
    # Relationships
    portfolio = db.relationship('Portfolio', back_populates='items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'purchase_price': self.purchase_price,
            'purchase_date': self.purchase_date.isoformat(),
            'invested': self.invested
        }

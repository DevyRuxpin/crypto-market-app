import uuid
from datetime import datetime

class PortfolioItem:
    def __init__(self, symbol, quantity, purchase_price, purchase_date, invested):
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.quantity = quantity
        self.purchase_price = purchase_price
        self.purchase_date = purchase_date
        self.invested = invested
        
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'purchase_price': self.purchase_price,
            'purchase_date': self.purchase_date,
            'invested': self.invested
        }

class Portfolio:
    # In-memory storage for portfolios (in a real app, this would be a database)
    _portfolios = {}
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.items = []
        
        # Save to in-memory storage
        Portfolio._portfolios[user_id] = self
    
    @classmethod
    def get_by_user_id(cls, user_id):
        return cls._portfolios.get(user_id)
    
    def add_item(self, item):
        self.items.append(item)
    
    def update_item(self, item_id, quantity, purchase_price, invested):
        for item in self.items:
            if item.id == item_id:
                item.quantity = quantity
                item.purchase_price = purchase_price
                item.invested = invested
                return True
        return False
    
    def remove_item(self, item_id):
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                return True
        return False
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items]
        }

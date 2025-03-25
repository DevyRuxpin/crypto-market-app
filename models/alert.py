import uuid
from datetime import datetime

class Alert:
    # In-memory storage for alerts (in a real app, this would be a database)
    _alerts = {}
    
    def __init__(self, user_id, symbol, alert_type, target_price, created_at, triggered=False, triggered_at=None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.symbol = symbol
        self.alert_type = alert_type  # 'above' or 'below'
        self.target_price = target_price
        self.created_at = created_at
        self.triggered = triggered
        self.triggered_at = triggered_at
        
        # Initialize user's alerts list if not exists
        if user_id not in Alert._alerts:
            Alert._alerts[user_id] = []
    
    def save(self):
        # Check if alert already exists (update) or is new (add)
        user_alerts = Alert._alerts.get(self.user_id, [])
        
        for i, alert in enumerate(user_alerts):
            if alert.id == self.id:
                user_alerts[i] = self
                return
        
        # If not found, add as new
        user_alerts.append(self)
        Alert._alerts[self.user_id] = user_alerts
    
    @classmethod
    def get_by_user_id(cls, user_id):
        return cls._alerts.get(user_id, [])
    
    @classmethod
    def delete(cls, alert_id, user_id):
        if user_id not in cls._alerts:
            return False
            
        user_alerts = cls._alerts[user_id]
        for i, alert in enumerate(user_alerts):
            if alert.id == alert_id:
                user_alerts.pop(i)
                return True
        
        return False
    
    @classmethod
    def reset(cls, alert_id, user_id):
        if user_id not in cls._alerts:
            return False
            
        user_alerts = cls._alerts[user_id]
        for alert in user_alerts:
            if alert.id == alert_id:
                alert.triggered = False
                alert.triggered_at = None
                return True
        
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'alert_type': self.alert_type,
            'target_price': self.target_price,
            'created_at': self.created_at,
            'triggered': self.triggered,
            'triggered_at': self.triggered_at
        }

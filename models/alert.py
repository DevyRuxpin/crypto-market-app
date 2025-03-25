import uuid
from datetime import datetime

class Alert:
    """Model for price alerts"""
    
    # In-memory storage for alerts
    alerts = {}
    
    # Alert types
    TYPE_PRICE_ABOVE = 'price_above'
    TYPE_PRICE_BELOW = 'price_below'
    TYPE_PERCENT_CHANGE = 'percent_change'
    
    # Alert statuses
    STATUS_ACTIVE = 'active'
    STATUS_TRIGGERED = 'triggered'
    STATUS_DISMISSED = 'dismissed'
    
    def __init__(self, user_id, symbol, alert_type, target_value, name=None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.symbol = symbol
        self.alert_type = alert_type
        self.target_value = float(target_value)
        self.name = name or f"{symbol} {alert_type} {target_value}"
        self.status = self.STATUS_ACTIVE
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.triggered_at = None
        
        # Save to in-memory storage
        if user_id not in Alert.alerts:
            Alert.alerts[user_id] = []
        Alert.alerts[user_id].append(self)
    
    @staticmethod
    def get_user_alerts(user_id, status=None):
        """Get all alerts for a user, optionally filtered by status"""
        user_alerts = Alert.alerts.get(user_id, [])
        
        if status:
            return [alert for alert in user_alerts if alert.status == status]
        return user_alerts
    
    @staticmethod
    def get_alert(alert_id):
        """Get a specific alert by ID"""
        for user_alerts in Alert.alerts.values():
            for alert in user_alerts:
                if alert.id == alert_id:
                    return alert
        return None
    
    def check_condition(self, current_price):
        """Check if the alert condition is met"""
        if self.status != self.STATUS_ACTIVE:
            return False
            
        triggered = False
        
        if self.alert_type == self.TYPE_PRICE_ABOVE:
            triggered = float(current_price) >= self.target_value
        elif self.alert_type == self.TYPE_PRICE_BELOW:
            triggered = float(current_price) <= self.target_value
        elif self.alert_type == self.TYPE_PERCENT_CHANGE:
            # For percent change, target_value is stored as the base price
            # and we check if the percent change exceeds the threshold
            percent_change = ((float(current_price) - self.target_value) / self.target_value) * 100
            triggered = abs(percent_change) >= self.threshold
        
        if triggered:
            self.trigger()
            
        return triggered
    
    def trigger(self):
        """Mark the alert as triggered"""
        self.status = self.STATUS_TRIGGERED
        self.triggered_at = datetime.now()
        self.updated_at = datetime.now()
        
        return self
    
    def dismiss(self):
        """Mark the alert as dismissed"""
        self.status = self.STATUS_DISMISSED
        self.updated_at = datetime.now()
        
        return self
    
    def reactivate(self):
        """Reactivate a dismissed alert"""
        if self.status == self.STATUS_DISMISSED:
            self.status = self.STATUS_ACTIVE
            self.updated_at = datetime.now()
            
        return self
    
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'alert_type': self.alert_type,
            'target_value': self.target_value,
            'name': self.name,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None
        }

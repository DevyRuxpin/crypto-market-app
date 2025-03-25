# models/alert.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # 'above' or 'below'
    target_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='alerts')
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def delete(cls, alert_id, user_id):
        alert = cls.query.filter_by(id=alert_id, user_id=user_id).first()
        if alert:
            db.session.delete(alert)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def reset(cls, alert_id, user_id):
        alert = cls.query.filter_by(id=alert_id, user_id=user_id).first()
        if alert:
            alert.triggered = False
            alert.triggered_at = None
            db.session.commit()
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'alert_type': self.alert_type,
            'target_price': self.target_price,
            'created_at': self.created_at.isoformat(),
            'triggered': self.triggered,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None
        }

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import json
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    _settings = db.Column(db.Text, default='{}')
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    
    # Relationships
    portfolios = db.relationship('Portfolio', back_populates='user', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', back_populates='user', cascade='all, delete-orphan')
    watchlists = db.relationship('Watchlist', back_populates='user', cascade='all, delete-orphan')
    
    @property
    def settings(self):
        if self._settings:
            return json.loads(self._settings)
        return {
            'theme': 'light',
            'currency': 'USD',
            'notification_enabled': True,
            'default_crypto_list': ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE']
        }
    
    @settings.setter
    def settings(self, value):
        self._settings = json.dumps(value)
    
    def update_settings(self, new_settings):
        current_settings = self.settings
        for key, value in new_settings.items():
            if key in current_settings:
                current_settings[key] = value
        self.settings = current_settings
        return current_settings

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

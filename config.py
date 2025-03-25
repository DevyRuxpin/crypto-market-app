# config.py
import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///crypto_market.db')
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    
    # Binance API configuration
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET', '')
    
    # CoinMarketCap API configuration
    CMC_API_KEY = os.environ.get('CMC_API_KEY', '')

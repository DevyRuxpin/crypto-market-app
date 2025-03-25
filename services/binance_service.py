import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode
import os

class BinanceService:
    """Service for interacting with the Binance API"""
    
    BASE_URL = 'https://api.binance.com'
    
    @staticmethod
    def get_ticker_prices():
        """Get all ticker prices"""
        try:
            response = requests.get(f"{BinanceService.BASE_URL}/api/v3/ticker/price")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting ticker prices: {e}")
            return None
    
    @staticmethod
    def get_ticker_price(symbol):
        """Get ticker price for a specific symbol"""
        try:
            response = requests.get(f"{BinanceService.BASE_URL}/api/v3/ticker/price", params={'symbol': symbol})
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting ticker price for {symbol}: {e}")
            return None
    
    @staticmethod
    def get_ticker_24hr(symbol):
        """Get 24hr ticker data for a specific symbol"""
        try:
            response = requests.get(f"{BinanceService.BASE_URL}/api/v3/ticker/24hr", params={'symbol': symbol})
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting 24hr ticker for {symbol}: {e}")
            return None
    
    @staticmethod
    def get_klines(symbol, interval='1d', limit=100):
        """Get klines/candlestick data for a specific symbol"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = requests.get(f"{BinanceService.BASE_URL}/api/v3/klines", params=params)
            if response.status_code == 200:
                klines = response.json()
                formatted_klines = []
                
                for k in klines:
                    formatted_klines.append({
                        'time': k[0],
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5])
                    })
                
                return formatted_klines
            return None
        except Exception as e:
            print(f"Error getting klines for {symbol}: {e}")
            return None
    
    @staticmethod
    def get_exchange_info(symbol=None):
        """Get exchange info for a specific symbol or all symbols"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
                
            response = requests.get(f"{BinanceService.BASE_URL}/api/v3/exchangeInfo", params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting exchange info: {e}")
            return None
    
    @staticmethod
    def get_market_depth(symbol, limit=100):
        """Get market depth for a specific symbol"""
        try:
            params = {
                'symbol': symbol,
                'limit': limit
            }
            response = requests.get(f"{BinanceService.BASE_URL}/api/v3/depth", params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting market depth for {symbol}: {e}")
            return None
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate Relative Strength Index (RSI)"""
        if len(prices) < period + 1:
            return None
            
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Calculate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate RS and RSI
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    @staticmethod
    def calculate_moving_average(prices, period):
        """Calculate Simple Moving Average (SMA)"""
        if len(prices) < period:
            return None
            
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_ema(prices, period):
        """Calculate Exponential Moving Average (EMA)"""
        if len(prices) < period:
            return None
            
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
            
        return ema


import requests
import json
import time
import websocket
from threading import Thread

class BinanceService:
    BASE_URL = 'https://data-api.binance.vision/api/v3'
    WS_BASE_URL = 'wss://data-stream.binance.vision/ws'
    
    @staticmethod
    def get_ticker_prices():
        """Get all ticker prices from Binance"""
        try:
            response = requests.get(f"{BinanceService.BASE_URL}/ticker/price")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error fetching ticker prices: {e}")
            return []
    
    @staticmethod
    def get_klines(symbol, interval='1d', limit=100):
        """Get kline/candlestick data for a specific symbol"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = requests.get(f"{BinanceService.BASE_URL}/klines", params=params)
            if response.status_code == 200:
                # Format the response for easier consumption
                klines = response.json()
                formatted_klines = []
                for k in klines:
                    formatted_klines.append({
                        'time': k[0],
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5]),
                        'close_time': k[6]
                    })
                return formatted_klines
            return []
        except Exception as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return []
            
    @staticmethod
    def get_ticker_24hr(symbol=None):
        """Get 24hr ticker price change statistics"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            response = requests.get(f"{BinanceService.BASE_URL}/ticker/24hr", params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error fetching 24hr ticker: {e}")
            return []

    @staticmethod
    def get_exchange_info(symbol=None):
        """Get exchange information"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
                
            response = requests.get(f"{BinanceService.BASE_URL}/exchangeInfo", params=params)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"Error fetching exchange info: {e}")
            return {}
    
    @staticmethod
    def get_market_depth(symbol, limit=100):
        """Get order book for a specific symbol"""
        try:
            params = {
                'symbol': symbol,
                'limit': limit
            }
            response = requests.get(f"{BinanceService.BASE_URL}/depth", params=params)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"Error fetching market depth: {e}")
            return {}
            
    @staticmethod
    def calculate_rsi(closes, period=14):
        """Calculate the RSI for a list of closing prices"""
        if len(closes) < period + 1:
            return None
            
        # Calculate price changes
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Calculate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate subsequent values
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
        # Calculate RS and RSI
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    @staticmethod
    def calculate_moving_average(prices, period):
        """Calculate moving average for a list of prices"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    @staticmethod
    def calculate_ema(prices, period):
        """Calculate exponential moving average"""
        if len(prices) < period:
            return None
            
        # Start with SMA
        ema = sum(prices[:period]) / period
        
        # Calculate multiplier
        multiplier = 2 / (period + 1)
        
        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
            
        return ema

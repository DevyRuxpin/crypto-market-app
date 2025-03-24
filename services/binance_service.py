import os
import requests
import numpy as np
from datetime import datetime

class BinanceService:
    API_BASE_URL = os.environ.get('BINANCE_API_BASE_URL', 'https://data-api.binance.vision')
    WS_BASE_URL = os.environ.get('BINANCE_WS_BASE_URL', 'wss://data-stream.binance.vision')
    
    @staticmethod
    def get_ticker_prices():
        try:
            print(f"Fetching ticker prices from {BinanceService.API_BASE_URL}/api/v3/ticker/price")
            response = requests.get(f"{BinanceService.API_BASE_URL}/api/v3/ticker/price", timeout=10)
            
            if response.status_code != 200:
                print(f"Binance API error: {response.status_code}, {response.text}")
                return []
                
            data = response.json()
            print(f"Received {len(data)} ticker prices from Binance")
            if data and len(data) > 0:
                print(f"Sample first item: {data[0]}")
            return data
        except Exception as e:
            print(f"Error fetching ticker prices: {e}")
            return []
    
    @staticmethod
    def get_klines(symbol, interval='1d', limit=100):
        try:
            print(f"Fetching klines for {symbol} with interval {interval}")
            url = f"{BinanceService.API_BASE_URL}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"Binance API error: {response.status_code}, {response.text}")
                return []
            
            klines = response.json()
            print(f"Received {len(klines)} klines from Binance")
            
            result = []
            for k in klines:
                result.append({
                    'time': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': k[6],
                    'quote_asset_volume': float(k[7]),
                    'trades': k[8],
                    'taker_buy_base': float(k[9]),
                    'taker_buy_quote': float(k[10])
                })
            return result
        except Exception as e:
            print(f"Error fetching klines: {e}")
            return []

    @staticmethod
    def get_ticker_24hr(symbol=None):
        try:
            url = f"{BinanceService.API_BASE_URL}/api/v3/ticker/24hr"
            params = {}
            if symbol:
                params['symbol'] = symbol
                
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"Binance API error: {response.status_code}, {response.text}")
                return [] if symbol is None else {}
                
            return response.json()
        except Exception as e:
            print(f"Error fetching 24hr ticker: {e}")
            return [] if symbol is None else {}

    @staticmethod
    def get_exchange_info(symbol=None):
        try:
            url = f"{BinanceService.API_BASE_URL}/api/v3/exchangeInfo"
            params = {}
            if symbol:
                params['symbol'] = symbol
                
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"Binance API error: {response.status_code}, {response.text}")
                return {}
                
            return response.json()
        except Exception as e:
            print(f"Error fetching exchange info: {e}")
            return {}

    @staticmethod
    def get_market_depth(symbol, limit=100):
        try:
            url = f"{BinanceService.API_BASE_URL}/api/v3/depth"
            params = {
                'symbol': symbol,
                'limit': limit
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"Binance API error: {response.status_code}, {response.text}")
                return {}
                
            return response.json()
        except Exception as e:
            print(f"Error fetching market depth: {e}")
            return {}

    @staticmethod
    def calculate_rsi(prices, period=14):
        try:
            if len(prices) < period + 1:
                return None
                
            # Calculate price changes
            deltas = np.diff(prices)
            
            # Create seed values
            up = np.zeros(len(deltas))
            down = np.zeros(len(deltas))
            
            # Separate upward and downward movements
            up[deltas >= 0] = deltas[deltas >= 0]
            down[-deltas >= 0] = -deltas[-deltas >= 0]
            
            # Calculate the rolling average of average up and average down
            avg_up = np.mean(up[:period])
            avg_down = np.mean(down[:period])
            
            if avg_down == 0:
                return 100
                
            rs = avg_up / avg_down
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return None

    @staticmethod
    def calculate_moving_average(prices, period):
        try:
            if len(prices) < period:
                return None
                
            return round(sum(prices[-period:]) / period, 2)
        except Exception as e:
            print(f"Error calculating moving average: {e}")
            return None

    @staticmethod
    def calculate_ema(prices, period):
        try:
            if len(prices) < period:
                return None
                
            # Calculate multiplier
            multiplier = 2 / (period + 1)
            
            # Calculate initial SMA
            sma = sum(prices[:period]) / period
            
            # Calculate EMA
            ema = sma
            for price in prices[period:]:
                ema = (price - ema) * multiplier + ema
                
            return round(ema, 2)
        except Exception as e:
            print(f"Error calculating EMA: {e}")
            return None


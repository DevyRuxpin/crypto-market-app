import os
import requests
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CoinMarketCapService:
    """Service for interacting with the CoinMarketCap API"""
    
    BASE_URL = "https://pro-api.coinmarketcap.com"
    API_KEY = os.environ.get("CMC_API_KEY", "bda79d78-5f5c-41c3-892e-3584b698e234")
    
    @classmethod
    def _make_request(cls, endpoint, params=None):
        """Make a request to the CoinMarketCap API with proper headers"""
        headers = {
            'X-CMC_PRO_API_KEY': cls.API_KEY,
            'Accept': 'application/json'
        }
        
        url = f"{cls.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to CoinMarketCap API: {e}")
            return None
    
    @classmethod
    def get_top_cryptocurrencies(cls, limit=100, convert="USD"):
        """Get top cryptocurrencies by market cap"""
        endpoint = "/v1/cryptocurrency/listings/latest"
        params = {
            'limit': limit,
            'convert': convert,
            'sort': 'market_cap',
            'sort_dir': 'desc'
        }
        
        data = cls._make_request(endpoint, params)
        if data and 'data' in data:
            return data['data']
        return []
    
    @classmethod
    def get_cryptocurrency_details(cls, symbol=None, id=None, convert="USD"):
        """Get detailed information about a specific cryptocurrency"""
        endpoint = "/v2/cryptocurrency/quotes/latest"
        params = {'convert': convert}
        
        if symbol:
            params['symbol'] = symbol
        elif id:
            params['id'] = id
        else:
            return None
        
        data = cls._make_request(endpoint, params)
        if data and 'data' in data:
            return data['data']
        return None
    
    @classmethod
    def get_cryptocurrency_map(cls):
        """Get a map of all cryptocurrencies (ID, name, symbol)"""
        endpoint = "/v1/cryptocurrency/map"
        
        data = cls._make_request(endpoint)
        if data and 'data' in data:
            return data['data']
        return []
    
    @classmethod
    def get_price_conversion(cls, amount, symbol, convert="USD"):
        """Convert an amount of one cryptocurrency to another currency"""
        endpoint = "/v2/tools/price-conversion"
        params = {
            'amount': amount,
            'symbol': symbol,
            'convert': convert
        }
        
        data = cls._make_request(endpoint, params)
        if data and 'data' in data:
            return data['data']
        return None
    
    @classmethod
    def get_global_metrics(cls, convert="USD"):
        """Get global cryptocurrency market metrics"""
        endpoint = "/v1/global-metrics/quotes/latest"
        params = {'convert': convert}
        
        data = cls._make_request(endpoint, params)
        if data and 'data' in data:
            return data['data']
        return None
    
    @classmethod
    def get_historical_data(cls, id, time_period="7d", convert="USD"):
        """Get historical data for a cryptocurrency"""
        endpoint = f"/v2/cryptocurrency/quotes/historical"
        params = {
            'id': id,
            'time_period': time_period,
            'convert': convert
        }
        
        data = cls._make_request(endpoint, params)
        if data and 'data' in data:
            return data['data']
        return None

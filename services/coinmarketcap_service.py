import os
import requests
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

class CoinMarketCapService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('CMC_API_KEY')
        self.base_url = 'https://pro-api.coinmarketcap.com/v1'
        self.session = Session()
        self.session.headers.update({
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json',
        })
    
    def _make_request(self, endpoint, params=None):
        """Make a request to the CoinMarketCap API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            data = json.loads(response.text)
            
            if response.status_code != 200:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                raise Exception(f"API Error: {error_msg}")
                
            return data.get('data', {})
            
        except (ConnectionError, Timeout, TooManyRedirects, Exception) as e:
            print(f"Error making request to {endpoint}: {e}")
            raise
    
    def get_latest_listings(self, limit=20, sort='market_cap', sort_dir='desc'):
        """Get latest cryptocurrency listings"""
        params = {
            'start': '1',
            'limit': str(limit),
            'sort': sort,
            'sort_dir': sort_dir,
            'convert': 'USD'
        }
        
        return self._make_request('cryptocurrency/listings/latest', params)
    
    def get_metadata(self, symbol):
        """Get metadata for a cryptocurrency"""
        params = {
            'symbol': symbol
        }
        
        return self._make_request('cryptocurrency/info', params)
    
    def get_quotes(self, symbol):
        """Get latest quotes for a cryptocurrency"""
        params = {
            'symbol': symbol,
            'convert': 'USD'
        }
        
        return self._make_request('cryptocurrency/quotes/latest', params)
    
    def get_global_metrics(self):
        """Get global cryptocurrency market metrics"""
        return self._make_request('global-metrics/quotes/latest')

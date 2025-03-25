# services/coinmarketcap_service.py
import requests
import os

class CoinMarketCapService:
    """Service for interacting with the CoinMarketCap API"""
    
    BASE_URL = 'https://pro-api.coinmarketcap.com/v1'
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('CMC_API_KEY', '')
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }
    
    def get_latest_listings(self, limit=20, sort='market_cap', sort_dir='desc'):
        """Get latest cryptocurrency listings"""
        try:
            params = {
                'start': 1,
                'limit': limit,
                'sort': sort,
                'sort_dir': sort_dir,
                'convert': 'USD'
            }
            
            response = requests.get(
                f"{self.BASE_URL}/cryptocurrency/listings/latest",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                print(f"Error from CoinMarketCap API: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error getting latest listings: {e}")
            return []
    
    def get_metadata(self, symbol):
        """Get metadata for a specific cryptocurrency"""
        try:
            params = {
                'symbol': symbol,
                'aux': 'urls,logo,description,tags,platform,date_added,notice'
            }
            
            response = requests.get(
                f"{self.BASE_URL}/cryptocurrency/info",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get(symbol, {})
            else:
                print(f"Error from CoinMarketCap API: {response.text}")
                return {}
                
        except Exception as e:
            print(f"Error getting metadata for {symbol}: {e}")
            return {}
    
    def get_quotes(self, symbols):
        """Get quotes for specific cryptocurrencies"""
        try:
            params = {
                'symbol': ','.join(symbols),
                'convert': 'USD'
            }
            
            response = requests.get(
                f"{self.BASE_URL}/cryptocurrency/quotes/latest",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            else:
                print(f"Error from CoinMarketCap API: {response.text}")
                return {}
                
        except Exception as e:
            print(f"Error getting quotes for {symbols}: {e}")
            return {}


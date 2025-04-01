import requests
from flask import current_app

class CryptoAPIService:
    def __init__(self):
        self.base_url = 'https://pro-api.coinmarketcap.com/v1'
        self.api_key = current_app.config['COINMARKETCAP_API_KEY']

    def get_market_data(self):
        url = f'{self.base_url}/global-metrics/quotes/latest'
        headers = {
            'X-CMC_PRO_API_KEY': self.api_key
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def get_coin_data(self, symbol=None):
        url = f'{self.base_url}/cryptocurrency/listings/latest'
        headers = {
            'X-CMC_PRO_API_KEY': self.api_key
        }
        params = {
            'start': 1,
            'limit': 100
        }
        if symbol:
            params['symbol'] = symbol
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()['data']

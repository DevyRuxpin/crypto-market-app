import requests
from flask import current_app

class BinanceService:
    def __init__(self):
        self.base_url = 'https://data-api.binance.vision/api/v3'
        

    def get_ticker_data(self, symbol):
        url = f'{self.base_url}/ticker/24hr'
        params = {
            'symbol': symbol
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_kline_data(self, symbol, interval):
        url = f'{self.base_url}/klines'
        params = {
            'symbol': symbol,
            'interval': interval
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def subscribe_to_symbol(self, symbol, client_id):
        # Implement WebSocket subscription logic here
        pass

    def unsubscribe_from_symbol(self, symbol, client_id):
        # Implement WebSocket unsubscription logic here
        pass

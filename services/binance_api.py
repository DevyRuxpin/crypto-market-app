import requests

BASE_URL = "https://data-api.binance.vision/api/v3"

class BinanceAPI:
    @staticmethod
    def get_agg_trades(symbol, limit=500):
        response = requests.get(f"{BASE_URL}/aggTrades", params={"symbol": symbol, "limit": limit})
        return response.json()

    @staticmethod
    def get_avg_price(symbol):
        response = requests.get(f"{BASE_URL}/avgPrice", params={"symbol": symbol})
        return response.json()

    @staticmethod
    def get_depth(symbol, limit=100):
        response = requests.get(f"{BASE_URL}/depth", params={"symbol": symbol, "limit": limit})
        return response.json()

    @staticmethod
    def get_exchange_info():
        response = requests.get(f"{BASE_URL}/exchangeInfo")
        return response.json()

    @staticmethod
    def get_klines(symbol, interval, limit=500):
        response = requests.get(f"{BASE_URL}/klines", params={"symbol": symbol, "interval": interval, "limit": limit})
        return response.json()

    @staticmethod
    def ping():
        response = requests.get(f"{BASE_URL}/ping")
        return response.status_code == 200

    @staticmethod
    def get_ticker(symbol=None):
        params = {"symbol": symbol} if symbol else {}
        response = requests.get(f"{BASE_URL}/ticker", params=params)
        return response.json()

    @staticmethod
    def get_24hr_ticker(symbol=None):
        params = {"symbol": symbol} if symbol else {}
        response = requests.get(f"{BASE_URL}/ticker/24hr", params=params)
        return response.json()

    @staticmethod
    def get_book_ticker(symbol=None):
        params = {"symbol": symbol} if symbol else {}
        response = requests.get(f"{BASE_URL}/ticker/bookTicker", params=params)
        return response.json()

    @staticmethod
    def get_price(symbol=None):
        """
        Fetches the latest price(s) for a symbol or all symbols.
        """
        params = {"symbol": symbol} if symbol else {}
        try:
            response = requests.get(f"{BASE_URL}/ticker/price", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching price: {e}")
            return None

    @staticmethod
    def get_server_time():
        response = requests.get(f"{BASE_URL}/time")
        return response.json()

    @staticmethod
    def get_trades(symbol, limit=500):
        response = requests.get(f"{BASE_URL}/trades", params={"symbol": symbol, "limit": limit})
        return response.json()

    @staticmethod
    def get_ui_klines(symbol, interval, limit=500):
        response = requests.get(f"{BASE_URL}/uiKlines", params={"symbol": symbol, "interval": interval, "limit": limit})
        return response.json()

from .binance_api import BinanceAPI  # Import BinanceAPI

class BinanceService:
    @staticmethod
    def get_ticker_prices():
        """
        Fetches the latest ticker prices from Binance API.
        """
        try:
            return BinanceAPI.get_price()  # Use BinanceAPI's get_price method
        except Exception as e:
            print(f"Error fetching ticker prices: {e}")
            return None

    @staticmethod
    def get_crypto_prices():
        """
        Fetches a dictionary of crypto prices.
        """
        try:
            prices = BinanceAPI.get_price()
            return {item['symbol']: float(item['price']) for item in prices}
        except Exception as e:
            print(f"Error fetching crypto prices: {e}")
            return None

    @staticmethod
    def get_crypto_details(crypto_symbol):
        """
        Fetches details for a specific cryptocurrency.
        """
        try:
            price_data = BinanceAPI.get_price(crypto_symbol)
            return {"symbol": crypto_symbol, "price": float(price_data['price'])}
        except Exception as e:
            print(f"Error fetching crypto details: {e}")
            return None

    @staticmethod
    def get_top_cryptos():
        """
        Fetches a list of top cryptocurrencies by market cap.
        """
        # Placeholder implementation; replace with actual logic if needed
        return ["BTC", "ETH", "BNB"]

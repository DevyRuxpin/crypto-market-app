from .binance_service import BinanceService

class BinanceService:
    def __init__(self):
        # Initialize BinanceService
        pass

    def get_market_data(self):
        """
        Fetches market data using BinanceService.
        """
        return BinanceService.get_ticker_prices()
